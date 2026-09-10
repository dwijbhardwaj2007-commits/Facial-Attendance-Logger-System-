import cv2
import os
import mysql.connector
from mysql.connector import Error

# ==========================================
# 1. DATABASE CONFIGURATION & SETUP
# ==========================================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2402" # Your MySQL password
DB_NAME = "smart_office_attendance"

def setup_database():
    """Builds the database and tables if they don't exist yet."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # Create Database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        # Create the Master Employees Table
        create_employees_table = """
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_employees_table)
        
        # Safely try to set auto increment, ignore if table already has data
        try:
            cursor.execute("ALTER TABLE employees AUTO_INCREMENT = 1000")
        except:
            pass

        # Create the Scan Logs Table
        create_logs_table = """
        CREATE TABLE IF NOT EXISTS scan_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            emp_id INT NOT NULL,
            scan_time DATETIME NOT NULL,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
        """
        cursor.execute(create_logs_table)
        connection.commit()
        
    except Error as e:
        print(f"❌ Failed to setup database: {e}")
        exit()
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

setup_database()

os.makedirs("known_faces", exist_ok=True)
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

name = input("Enter the name of the person being enrolled: ").strip()
if not name:
    print("Name cannot be empty!")
    exit()

emp_id = None
try:
    print("Connecting to database...")
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = connection.cursor()
    
    # Insert the new employee into the Master Table
    insert_query = "INSERT INTO employees (name) VALUES (%s)"
    cursor.execute(insert_query, (name,))
    connection.commit()
    
    # Grab the auto-generated ID from MySQL
    emp_id = cursor.lastrowid
    print(f"✅ Successfully added {name} to Database!")
    print(f"🆔 Assigned Employee ID: {emp_id}")

except Error as e:
    print(f"❌ Database Error: {e}")
    exit()
finally:
    if 'connection' in locals() and connection is not None and connection.is_connected():
        cursor.close()
        connection.close()

# ==========================================
# 4. START 3D ENROLLMENT SCAN
# ==========================================
camera = cv2.VideoCapture(0)
print(f"📸 Look at the camera and press SPACEBAR to begin 3D enrollment for {name} (ID: {emp_id}).")

capturing = False
photo_count = 0
max_photos = 100

while True:
    ret, frame = camera.read()
    if not ret: break

    ui_frame = frame.copy()

    if not capturing:
        cv2.putText(ui_frame, f"Enrolling: {name} (ID: {emp_id})", (50, 50), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)
        cv2.putText(ui_frame, "Press SPACE to start scan", (50, 90), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
    else:
        cv2.putText(ui_frame, "Slowly rotate head (Up/Down/Left/Right)", (50, 50), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)
        
        progress_text = f"Captured: {photo_count} / {max_photos}"
        cv2.putText(ui_frame, progress_text, (50, 90), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        if len(faces) > 0:
            for (x, y, w, h) in faces:
                clean_face = gray[y:y+h, x:x+w]
                filename = f"known_faces/{emp_id}_{photo_count}.jpg" 
                cv2.imwrite(filename, clean_face)
                photo_count += 1
                break 
        
        if photo_count >= max_photos:
            print(f"✅ Successfully built a multi-pose profile for {name} (ID: {emp_id})!")
            break

    cv2.imshow("Security Setup - Enrollment", ui_frame)
    key = cv2.waitKey(1)
    
    if key % 256 == 32 and not capturing: 
        capturing = True
    elif key & 0xFF == ord('c'):
        print("Enrollment cancelled.")
        break

camera.release()
cv2.destroyAllWindows()