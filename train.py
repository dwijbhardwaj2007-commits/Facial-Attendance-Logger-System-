import cv2
import numpy as np
import os

recognizer = cv2.face.LBPHFaceRecognizer_create()
folder_path = "known_faces"
vault_path = "trainer.yml"

face_samples = []
face_ids = []

print("Booting Smart Compiler...")

# 1. Extract Data from NEW photos only
photos_found = False
for filename in os.listdir(folder_path):
    if filename.endswith(".jpg"):
        photos_found = True
        
        # CRITICAL FIX: Extract the integer ID from the filename (e.g., "1000_24.jpg" -> 1000)
        id_for_this_person = int(filename.split("_")[0])
        
        # Convert image to mathematical array
        image_path = os.path.join(folder_path, filename)
        img_array = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        face_samples.append(img_array)
        face_ids.append(id_for_this_person)

if not photos_found:
    print("No new raw photos found in 'known_faces' to process.")
    exit()

# 2. THE SMART DECISION ENGINE: Train vs. Update
if os.path.exists(vault_path):
    print("Existing model found! Updating the AI with the new faces...")
    recognizer.read(vault_path)
    recognizer.update(face_samples, np.array(face_ids))
else:
    print("No existing model found. Training a new AI from scratch...")
    recognizer.train(face_samples, np.array(face_ids))

# 3. Save and Shred
recognizer.write(vault_path)

# Delete the photos now that the math is saved
for filename in os.listdir(folder_path):
    if filename.endswith(".jpg"):
        os.remove(os.path.join(folder_path, filename))

print("Compilation complete! Model saved and raw photos shredded.")