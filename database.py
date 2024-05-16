import cv2
import face_recognition as fr
import mysql.connector
from datetime import datetime
from glob import glob

# Connect to MySQL database
db = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='2060',
    database='python'
)
cursor = db.cursor()

# Load known faces and their encodings
known_face_encodings = []
known_face_names = []

known_faces_path = 'path_to_known_faces_folder'
for img_path in glob(known_faces_path + '/*.jpg'):  # Assuming jpg images
    img = fr.load_image_file(img_path)
    face_encoding = fr.face_encodings(img)[0]  # Assuming single face in each image
    name = img_path.split('/')[-1].split('.')[0]  # Extract name from file path
    known_face_encodings.append(face_encoding)
    known_face_names.append(name)

# Set face recognition threshold
face_recognition_threshold = 0.6

# Initialize webcam
cap = cv2.VideoCapture(0)  # Adjust camera index as needed

while cap.isOpened():
    ret, frame = cap.read()

    # Perform face recognition
    face_locations = fr.face_locations(frame)
    face_encodings = fr.face_encodings(frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        # Check if the face matches any known faces
        matches = fr.compare_faces(known_face_encodings, face_encoding, tolerance=face_recognition_threshold)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

            # Get current date and time
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_weekday = now.strftime("%A")
            current_month = now.strftime("%B")
            current_day_of_month = now.strftime("%d")

            # Insert attendance record into the database
            sql = "INSERT INTO attendance (name, weekday, month, day_of_month, time) VALUES (%s, %s, %s, %s, %s)"
            values = (name, current_weekday, current_month, current_day_of_month, current_time)
            cursor.execute(sql, values)
            db.commit()

            # Retrieve the generated roll_no for the inserted record
            roll_no = cursor.lastrowid
            print(f"Attendance recorded - Roll No: {roll_no}, Name: {name}, Time: {current_time}")

        # Draw a rectangle around the face on the frame
        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Put the recognized name below the face
        cv2.putText(frame, name, (left + 6, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Display the frame with face recognition results
    cv2.imshow('Attendance System', frame)

    # Check for 'q' key press to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()

# Close the MySQL connection
db.close()
