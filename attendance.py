import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time
import cv2
import os

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "2402" 
DB_NAME = "smart_office_attendance"

def setup_database():
    """Verifies tables exist without destroying data."""
    connection = None
    try:
        connection = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        cursor = connection.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        create_employees_table = """
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_employees_table)
        
        try:
            cursor.execute("ALTER TABLE employees AUTO_INCREMENT = 1000")
        except:
            pass

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
        print(f"Database '{DB_NAME}' tables verified.")

    except Error as e:
        print(f"Database Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_employee_dict():
    """Fetches all employees from MySQL."""
    names_dict = {}
    connection = None
    try:
        connection = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = connection.cursor()
        cursor.execute("SELECT emp_id, name FROM employees")
        records = cursor.fetchall()
        for row in records:
           
            names_dict[str(row[0])] = row[1] 
    except Error as e:
        print(f"Failed to fetch employees from MySQL: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    return names_dict

def mark_attendance(emp_id):
    """Logs the scan in the database."""
    connection = None
    try:
        connection = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = connection.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        insert_query = "INSERT INTO scan_logs (emp_id, scan_time) VALUES (%s, %s)"
        cursor.execute(insert_query, (emp_id, current_time))
        connection.commit()
        print(f"Logged! Employee {emp_id} scanned at {current_time}")

    except Error as e:
        print(f"Failed to insert record into MySQL: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    setup_database()

    print("\nStarting Facial Recognition Camera...")
    
    names = get_employee_dict()
    if not names:
        print("Warning: No employees found in the database. You will need to add them!")

    if not os.path.exists('trainer.yml'):
        print("Error: 'trainer.yml' not found. Run train.py first!")
        exit()

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('trainer.yml')

    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    cap = cv2.VideoCapture(0)
    
    frame_counts = {}        
    last_seen_times = {}     
    last_logged_times = {}   
    COOLDOWN_SECONDS = 4     
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
            
            for (x, y, w, h) in faces:
                id_num, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                str_id = str(id_num) 
                
                if confidence < 100:
                    recognized_name = names.get(str_id, f"Unknown-{str_id}")
                    
                    if "Unknown" not in recognized_name:
                        current_time = time.time()
                        
                        time_since_last_seen = current_time - last_seen_times.get(str_id, current_time)
                        if time_since_last_seen > 1.0:
                            frame_counts[str_id] = 0
                            
                        last_seen_times[str_id] = current_time
                        time_since_log = current_time - last_logged_times.get(str_id, 0)
                        
                        if time_since_log < COOLDOWN_SECONDS:
                            if time_since_log < 1.0:
                                color = (0, 255, 0) 
                                text = f"{recognized_name} (ID: {str_id}) - Logged!"
                            else:
                                color = (255, 0, 0) 
                                text = f"{recognized_name} (ID: {str_id}) - Cooldown"
                        else:
                            frame_counts[str_id] = frame_counts.get(str_id, 0) + 1
                            
                            if frame_counts[str_id] >= 45:
                                mark_attendance(id_num) 
                                last_logged_times[str_id] = current_time
                                frame_counts[str_id] = 0 
                                
                                color = (0, 255, 0) 
                                text = f"{recognized_name} (ID: {str_id}) - Logged!"
                            else:
                                color = (255, 255, 255) 
                                text = f"{recognized_name} ({frame_counts[str_id]}/45)"
                    else:
                        
                        color = (0, 165, 255)
                        text = f"Missing from DB! (Seen ID: {str_id})"
                else:
                    
                    color = (0, 0, 255)
                    text = f"Poor Match (Conf: {confidence:.0f})"
                    
                cv2.putText(frame, text, (x+5,y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    
            cv2.imshow('FaceSync Attendance Scanner', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('c'):
                break
    except Exception as e:
        print(f"Camera Error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()