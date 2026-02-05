# Hospital Patient Identification & Logging System 

An AI-powered biometric system designed to automate patient registration and check-in processes. This project utilizes deep learning for real-time face recognition and was developed as a final project for my NTI and Huawei AI course.

## 🚀 Key Features

* **Biometric Enrollment**: Captures multiple facial frames to generate a stable averaged embedding for high-accuracy registration.
* **Real-time Identification**: Uses the **InsightFace Buffalo_S** model for efficient, high-speed inference on CPU.
* **Automated Attendance Logging**: Automatically records visits to a CSV database with a built-in **60-second cooldown** to prevent duplicate entries.
* **Audio-Visual Feedback**: Integrated Windows SAPI for voice prompts and dynamic bounding boxes for user guidance.

## 🛠️ Technical Stack

* **Frameworks**: InsightFace, OpenCV
* **Core Logic**: Python, NumPy (Cosine Similarity)
* **Data Handling**: Pandas, Pickle, CSV
* **Architecture**: Optimized for real-time processing using frame-skipping techniques.

## 📋 System Logic

The system identifies patients by calculating the **Cosine Similarity** between live facial embeddings and the stored database:

A confidence threshold of **0.50** is applied to distinguish between registered patients and unknown individuals.

## ⚙️ Installation & Usage

1. **Clone the Repository**:
```bash
git clone https://github.com/ojou10/Hospital-Patient-Identification-Logging-System-CV.git
cd Hospital-Patient-Identification-Logging-System-CV

```


2. **Install Dependencies**:
```bash
pip install -r requirements.txt

```


3. **Run the System**:
```bash
python main.py

```



## 🎓 Academic Context

This project serves as a practical application of my studies as a **Senior Computer Science student** specializing in **Software Engineering**. It reflects the competencies gained through the **HCIA-AI V4.0 certification** and my focus on **Computer Vision** and **RAG-based systems**.

---
