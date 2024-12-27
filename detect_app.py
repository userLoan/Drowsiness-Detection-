import sqlite3
import cv2
import threading
import numpy as np
from keras.models import load_model
from pygame import mixer
import tkinter as tk
from tkinter import Label, Button, Toplevel, ttk
from PIL import Image, ImageTk
from datetime import datetime
import time
from threading import Lock

# Initialize Pygame mixer for sound
mixer.init()
sound = mixer.Sound("static/assets/alarm.wav")

# SQLite Database Setup
conn = sqlite3.connect("drowsiness_log.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS detection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    score INTEGER,
    duration REAL
)
""")
conn.commit()

# Create a lock for thread-safe database access
db_lock = Lock()


class DrowsinessDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drowsiness Detection System")
        self.root.geometry("800x600")
        self.root.configure(bg="lightgray")

        # Add a header
        self.header = Label(self.root, text="Drowsiness Detection System", font=("Helvetica", 20, "bold"), bg="blue", fg="white")
        self.header.pack(fill="x", pady=10)

        # Video feed label
        self.video_label = Label(self.root, bg="black")
        self.video_label.pack()

        # Control buttons
        self.start_button = Button(self.root, text="Start Detection", command=self.start_detection, bg="green", fg="white", font=("Helvetica", 14))
        self.start_button.pack(side="left", padx=20, pady=10)

        self.stop_button = Button(self.root, text="Stop Detection", command=self.stop_detection, bg="red", fg="white", font=("Helvetica", 14))
        self.stop_button.pack(side="right", padx=20, pady=10)

        self.log_button = Button(self.root, text="View Log", command=self.view_log, bg="blue", fg="white", font=("Helvetica", 14))
        self.log_button.pack(side="bottom", pady=10)

        # Variables
        self.running = False
        self.cap = cv2.VideoCapture(0)
        self.score = 0
        self.alert_active = False
        self.alert_start_time = None
        self.thicc = 2

    def start_detection(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.run_detection).start()

    def stop_detection(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.video_label.config(image="")

    def run_detection(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(25, 25))
            left_eye = left_eye_cascade.detectMultiScale(gray)
            right_eye = right_eye_cascade.detectMultiScale(gray)

            rpred, lpred = [99], [99]

            if len(right_eye) > 0:
                x, y, w, h = right_eye[0]
                r_eye = self.preprocess_eye(frame[y:y + h, x:x + w])
                rpred = np.argmax(model.predict(r_eye), axis=-1)

            if len(left_eye) > 0:
                x, y, w, h = left_eye[0]
                l_eye = self.preprocess_eye(frame[y:y + h, x:x + w])
                lpred = np.argmax(model.predict(l_eye), axis=-1)

            if rpred[0] == 0 and lpred[0] == 0:
                self.score += 1
            else:
                self.score -= 1

            self.score = max(0, self.score)

            if self.score > 12:
                self.trigger_alert(frame, frame.shape[1], frame.shape[0])

            color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(color_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.cap.release()
        cv2.destroyAllWindows()

    def preprocess_eye(self, eye):
        eye = cv2.cvtColor(eye, cv2.COLOR_BGR2RGB)
        eye = cv2.resize(eye, (32, 32))
        eye = eye / 255.0
        eye = eye.reshape((-1, 32, 32, 3))
        return eye

    def trigger_alert(self, frame, width, height):
        cv2.putText(frame, "ALERT: DROWSY!", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

        if not self.alert_active:
            self.alert_active = True
            self.alert_start_time = time.time()
            sound.play()
            threading.Timer(5, self.reset_alert).start()

        if self.thicc < 16:
            self.thicc += 2
        else:
            self.thicc = 2
        cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), self.thicc)

    def reset_alert(self):
        if self.alert_start_time:
            duration = time.time() - self.alert_start_time
            self.log_detection(self.score, duration)
        self.alert_active = False

    def log_detection(self, score, duration):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_lock:
            try:
                cursor.execute("INSERT INTO detection_log (timestamp, score, duration) VALUES (?, ?, ?)", (timestamp, score, duration))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error logging data: {e}")

    def view_log(self):
        log_window = Toplevel(self.root)
        log_window.title("Drowsiness Log")
        log_window.geometry("600x400")

        tree = ttk.Treeview(log_window, columns=("ID", "Timestamp", "Score", "Duration"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Score", text="Score")
        tree.heading("Duration", text="Duration (s)")
        tree.pack(fill="both", expand=True)

        with db_lock:
            cursor.execute("SELECT * FROM detection_log ORDER BY id DESC")
            rows = cursor.fetchall()
            for row in rows:
                tree.insert("", "end", values=row)


# Haar cascades and model
face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_alt.xml")
left_eye_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_lefteye_2splits.xml")
right_eye_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_righteye_2splits.xml")
model = load_model("model/main_cnn.h5")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrowsinessDetectorApp(root)
    root.mainloop()
    conn.close()
