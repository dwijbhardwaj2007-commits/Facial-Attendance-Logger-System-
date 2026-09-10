# Facial Recognition Attendance Logger

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)]()
[![OpenCV Version](https://img.shields.io/badge/OpenCV-4.0%2B-green.svg)]()
[![MySQL Version](https://img.shields.io/badge/MySQL-8.0%2B-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

An enterprise-ready, automated attendance management system engineered from scratch. This project bypasses external cloud APIs by leveraging classical computer vision to perform real-time face detection, mathematical verification, and automated SQL logging from live IP/CCTV camera streams.

---

## Key Features

* **Network Camera Integration:** Directly compatible with RTP/RTSP video feeds from networked or cloud-based CCTV cameras.
* **Dual-Table SQL Architecture:** Uses a normalized MySQL schema separating the static employee directory from real-time scan logs via Foreign Keys.
* **High-Accuracy Onboarding:** Automatically captures a calibrated 100-image dataset per employee to train a custom LBPH model locally.
* **Real-Time Buffer Management:** Built-in frame-skipping logic prevents stale frame accumulation over network latency.
* **Spam Prevention:** Configurable scan cooldown timers stop the database from being flooded with duplicate logs.
* **Privacy-First Pipeline:** Raw image samples can be automatically shredded after the mathematical model is compiled.

---

## Technology Stack

* **Language:** Python 3.x
* **Computer Vision:** OpenCV (Haar Cascades for detection, LBPH for recognition)
* **Database:** MySQL
* **Hardware:** Compatible with standard Webcams and external IP/CCTV Cameras

---

## System Architecture & Flow

1. **Onboarding (`addface.py`):** Captures 100 images of the new employee, assigns them an auto-incrementing SQL ID, and registers their details in the `employees` table.
2. **Mathematical Compilation (`train.py`):** Parses the raw images, extracts the SQL Primary Keys directly from the filenames, and compiles an LBPH (Local Binary Patterns Histograms) model.
3. **Live Inference (`attendance.py`):** Connects to the CCTV RTP stream. When a face is detected, it calculates the mathematical distance. If the confidence matches the strict threshold, it instantly records the timestamp in the `scan_logs` table.

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/dwijbhardwaj2007-commits/Facial-Recognition-Attendance.git](https://github.com/dwijbhardwaj2007-commits/Facial-Recognition-Attendance.git)
cd Facial-Recognition-Attendance
