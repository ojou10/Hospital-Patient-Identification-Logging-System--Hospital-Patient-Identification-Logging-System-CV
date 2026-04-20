import cv2
import numpy as np
import pandas as pd
import insightface
from insightface.app import FaceAnalysis
import pickle
import os
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
import time

# ==========================================
# CONFIGURATION
# ==========================================
CSV_FILE = "hospital_patients.csv"
EMBEDDINGS_FILE = "face_embeddings.pkl"
LOG_FILE = "visit_log.csv"  # ⚡ NEW: Log file
CHECKIN_COOLDOWN_SECONDS = 600  # ⚡ NEW: 10 Minute Cooldown
CONFIDENCE_THRESHOLD = 0.50  # ⚡ NEW: Threshold

# ==========================================
# AUDIO SETUP
# ==========================================
try:
    from win32com.client import Dispatch


    def speaker(text):
        try:
            speaker_obj = Dispatch("SAPI.spvoice")
            speaker_obj.Speak(text)
        except:
            pass
except:
    def speaker(text):
        print(f"Speech: {text}")


# ==========================================
# MAIN CLASS
# ==========================================
class HospitalFaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Patient Recognition System")
        self.root.geometry("1000x650")
        self.root.configure(bg='#f0f0f0')

        # State Variables
        self.app = None
        self.cap = None
        self.is_running = False
        self.collected_vectors = []
        self.registration_mode = False

        # ⚡ NEW: Track last check-in time for cooldowns
        self.last_logged_time = {}

        self.load_model_async()
        self.create_widgets()

    def load_model_async(self):
        def load():
            try:
                # ⚡ CHANGE: Ensuring we use 'buffalo_s' like the updated logic
                self.app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
                self.app.prepare(ctx_id=0, det_size=(640, 640))
                self.log_message("✅ Model loaded successfully!")
                self.update_status("System Ready", "green")
            except Exception as e:
                self.log_message(f"❌ Model loading error: {str(e)}")
                self.update_status("Model Error", "red")

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def create_widgets(self):
        # --- HEADER ---
        title = tk.Label(self.root, text="🏥 Hospital Patient Recognition System",
                         font=('Segoe UI', 20, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title.pack(pady=10)

        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # --- LEFT PANEL (CONTROLS) ---
        left_panel = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), ipadx=10)

        # Registration Section
        tk.Label(left_panel, text="Register New Patient", font=('Segoe UI', 12, 'bold'), bg='white').pack(pady=(20, 10))

        tk.Label(left_panel, text="Name:", bg='white').pack(anchor='w', padx=10)
        self.name_entry = tk.Entry(left_panel, font=('Segoe UI', 10), width=25)
        self.name_entry.pack(padx=10, pady=5)

        tk.Label(left_panel, text="Age:", bg='white').pack(anchor='w', padx=10)
        self.age_entry = tk.Entry(left_panel, font=('Segoe UI', 10), width=25)
        self.age_entry.pack(padx=10, pady=5)

        self.register_btn = tk.Button(left_panel, text="📸 Start Registration",
                                      command=self.start_registration,
                                      bg='#3498db', fg='white', font=('Segoe UI', 10, 'bold'),
                                      width=22, cursor='hand2')
        self.register_btn.pack(pady=15)

        tk.Frame(left_panel, height=2, bg='#ecf0f1').pack(fill=tk.X, padx=10, pady=10)

        # Surveillance Section
        tk.Label(left_panel, text="Surveillance", font=('Segoe UI', 12, 'bold'), bg='white').pack(pady=10)

        self.live_btn = tk.Button(left_panel, text="🎥 Start Live View",
                                  command=self.toggle_live_view,
                                  bg='#2ecc71', fg='white', font=('Segoe UI', 10, 'bold'),
                                  width=22, cursor='hand2')
        self.live_btn.pack(pady=5)

        self.db_info_label = tk.Label(left_panel, text="", bg='white', fg='#7f8c8d')
        self.db_info_label.pack(pady=20)
        self.update_db_info()

        # --- RIGHT PANEL (VIDEO & LOGS) ---
        right_panel = tk.Frame(main_frame, bg='#f0f0f0')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Video Area
        self.video_frame = tk.Label(right_panel, bg='black', text="Camera Inactive", fg='white', font=('Arial', 14))
        self.video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Log Area
        log_container = tk.Frame(right_panel, bg='white', relief=tk.RIDGE, bd=2, height=150)
        log_container.pack(fill=tk.X)
        log_container.pack_propagate(False)

        tk.Label(log_container, text="System Logs", font=('Segoe UI', 9, 'bold'), bg='white', anchor='w').pack(
            fill=tk.X, padx=5, pady=2)

        self.log_text = scrolledtext.ScrolledText(log_container, font=('Consolas', 9), bg='#ecf0f1')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_message("⏳ Initializing System...")

    # ==========================================
    # HELPER FUNCTIONS
    # ==========================================
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_status(self, text, color):
        # Helper to update video label text when camera is off
        if not self.is_running:
            self.video_frame.config(text=text, fg=color)

    def load_data(self):
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE, dtype={'patient_id': str})
        else:
            df = pd.DataFrame(columns=['patient_id', 'name', 'age', 'reg_date'])

        if os.path.exists(EMBEDDINGS_FILE):
            with open(EMBEDDINGS_FILE, 'rb') as f:
                embeddings_db = pickle.load(f)
        else:
            embeddings_db = {}
        return df, embeddings_db

    def save_data(self, df, embeddings_db):
        df.to_csv(CSV_FILE, index=False)
        with open(EMBEDDINGS_FILE, 'wb') as f:
            pickle.dump(embeddings_db, f)

    def update_db_info(self):
        df, _ = self.load_data()
        self.db_info_label.config(text=f"📊 Total Patients: {len(df)}")

    # ⚡ NEW: Log visit to CSV
    def log_visit_csv(self, patient_id, name):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w') as f:
                f.write("patient_id,name,date,time\n")

        with open(LOG_FILE, 'a') as f:
            f.write(f"{patient_id},{name},{date_str},{time_str}\n")

        self.log_message(f"✅ CHECK-IN LOGGED: {name}")

    # ==========================================
    # REGISTRATION LOGIC
    # ==========================================
    def start_registration(self):
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()

        if not name or not age:
            messagebox.showwarning("Input Error", "Please enter Name and Age.")
            return

        if not self.app:
            messagebox.showerror("Error", "AI Model is still loading...")
            return

        self.registration_mode = True
        self.collected_vectors = []
        self.patient_name = name
        self.patient_age = age

        # Disable buttons
        self.register_btn.config(state='disabled')
        self.live_btn.config(state='disabled')

        self.log_message(f"🔵 Starting registration for: {name}")
        speaker("Please look at the camera")

        self.is_running = True
        self.cap = cv2.VideoCapture(0)
        self.process_registration()

    def process_registration(self):
        if not self.is_running: return

        ret, frame = self.cap.read()
        if ret:
            display_frame = frame.copy()
            faces = self.app.get(frame)

            # ⚡ NEW: Strict check for multiple faces (from updated logic)
            if len(faces) == 0:
                cv2.putText(display_frame, "Searching for face...", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            elif len(faces) > 1:
                # Draw Red Boxes on everyone if too many people
                for face in faces:
                    box = face.bbox.astype(int)
                    cv2.rectangle(display_frame, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
                cv2.putText(display_frame, "⚠️ TOO MANY FACES", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            elif len(faces) == 1:
                # Perfect scenario
                face = faces[0]
                box = face.bbox.astype(int)

                # Draw Green Box
                cv2.rectangle(display_frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

                # Auto-capture logic
                self.collected_vectors.append(face.embedding)
                count = len(self.collected_vectors)

                cv2.putText(display_frame, f"Capturing: {count}/5", (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Wait a bit between captures so we don't get 5 identical frames instantly
                time.sleep(0.1)

                # Show progress
            cv2.putText(display_frame, f"Progress: {len(self.collected_vectors)}/5", (20, 450),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            self.show_frame(display_frame)

        # Check if done
        if len(self.collected_vectors) >= 5:
            self.complete_registration()
        else:
            self.root.after(10, self.process_registration)

    def complete_registration(self):
        new_id = str(uuid.uuid4())[:8]
        avg_vector = np.mean(self.collected_vectors, axis=0)

        df, embeddings_db = self.load_data()
        new_entry = {
            'patient_id': new_id,
            'name': self.patient_name,
            'age': self.patient_age,
            'reg_date': datetime.now().strftime("%Y-%m-%d")
        }

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        embeddings_db[new_id] = avg_vector
        self.save_data(df, embeddings_db)

        self.log_message(f"🎉 Success: {self.patient_name} registered!")
        speaker(f"Registered {self.patient_name} successfully")
        messagebox.showinfo("Registration Complete", f"Patient {self.patient_name} added to database.")

        self.stop_camera()
        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.update_db_info()

    # ==========================================
    # SURVEILLANCE LOGIC
    # ==========================================
    def toggle_live_view(self):
        if self.is_running:
            self.stop_live_view()
        else:
            self.start_live_view()

    def start_live_view(self):
        if not self.app:
            messagebox.showerror("Error", "Model not ready.")
            return

        df, embeddings_db = self.load_data()
        if not embeddings_db:
            messagebox.showwarning("Empty Database", "No patients registered yet.")
            return

        self.is_running = True
        self.cap = cv2.VideoCapture(0)
        self.df = df
        self.embeddings_db = embeddings_db

        self.live_btn.config(text="⏹ Stop Live View", bg='#e74c3c')
        self.register_btn.config(state='disabled')
        self.log_message("🎥 Live Surveillance Started")

        self.process_live_view()

    def stop_live_view(self):
        self.is_running = False
        self.stop_camera()
        self.live_btn.config(text="🎥 Start Live View", bg='#2ecc71')
        self.log_message("⏹ Surveillance Stopped")

    def process_live_view(self):
        if not self.is_running: return

        ret, frame = self.cap.read()
        if ret:
            # We process every 3rd frame to keep GUI responsive (simplified logic)
            # Or just process every frame if PC is fast. Let's do every frame for smoothness
            # but rely on 'buffalo_s' speed.

            faces = self.app.get(frame)

            for face in faces:
                curr_vector = face.embedding
                max_score = 0
                best_id = None

                # 1. Compare with Database
                for pid, db_vector in self.embeddings_db.items():
                    score = np.dot(curr_vector, db_vector) / (np.linalg.norm(curr_vector) * np.linalg.norm(db_vector))
                    if score > max_score:
                        max_score = score
                        best_id = pid

                # 2. Determine Identity
                if max_score > CONFIDENCE_THRESHOLD:
                    info = self.df[self.df['patient_id'] == best_id].iloc[0]
                    name = info['name']

                    # ⚡ NEW: Visit Logging & Cooldown Logic
                    now = datetime.now()
                    should_log = False

                    if best_id not in self.last_logged_time:
                        should_log = True
                    else:
                        time_diff = (now - self.last_logged_time[best_id]).total_seconds()
                        if time_diff > CHECKIN_COOLDOWN_SECONDS:
                            should_log = True

                    if should_log:
                        self.log_visit_csv(best_id, name)
                        self.last_logged_time[best_id] = now
                        # Flash Yellow/Cyan for fresh log
                        color = (255, 255, 0)
                        label = f"LOGGED: {name}"
                    else:
                        # Green for standard recognition
                        color = (0, 255, 0)
                        label = f"{name} ({max_score:.2f})"

                else:
                    color = (0, 0, 255)  # Red
                    label = "Unknown"

                # 3. Draw Box
                box = face.bbox.astype(int)
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame, label, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            self.show_frame(frame)

        self.root.after(10, self.process_live_view)

    # ==========================================
    # VIDEO UTILS
    # ==========================================
    def show_frame(self, frame):
        # Convert OpenCV BGR to Tkinter RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (640, 480))
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_frame.imgtk = imgtk
        self.video_frame.configure(image=imgtk, text="")

    def stop_camera(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_frame.configure(image='', text="Camera Inactive")
        self.register_btn.config(state='normal')
        self.live_btn.config(state='normal')


if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalFaceRecognitionApp(root)
    root.mainloop()