import numpy as np
import cv2
import face_recognition as fr
from glob import glob
import pickle
import utility
import random
import define_constants as const
import mysql.connector
from datetime import datetime


def update_attendance_in_database(name):
    try:
        print("[update_attendance]")
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host="DESKTOP-PML685D",
            user="root",
            password="2060",
            port=3306,
            database="your_mysql_database"
        )

        if connection.is_connected():
            # Get current date and time
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_weekday = now.strftime("%A")
            current_month = now.strftime("%B")
            current_day_of_month = now.strftime("%d")

            # Insert attendance record into the database
            cursor = connection.cursor()
            sql = "INSERT INTO attendance (name, weekday, month, day_of_month, time) VALUES (%s, %s, %s, %s, %s)"
            values = (name, current_weekday, current_month, current_day_of_month, current_time)
            cursor.execute(sql, values)
            connection.commit()

            # Print confirmation message
            print(f"Attendance recorded - Name: {name}, Time: {current_time}")

            # Close cursor and connection
            cursor.close()
            connection.close()
        else:
            print("Database connection failed.")
    except Exception as e:
        print(f"Error updating attendance: {str(e)}")


def main():
    print('-----------------------------------------------------\n')

    # Load expected number of files from the pickle file (n_people)
    with open('assets/pickles/n_people.pk', 'rb') as pickle_file:
        n_people_in_pickle = pickle.load(pickle_file)
    print(f"Expected number of files in '{const.PEOPLE_DIR}' directory : {n_people_in_pickle}")

    # Read all image files from PEOPLE_DIR
    people = glob(const.PEOPLE_DIR + '/*.*')
    print(f"Number of files in '{const.PEOPLE_DIR}' directory : {len(people)}")

    # Check if number of files matches the expected count from pickle
    if len(people) == n_people_in_pickle:
        # Get names corresponding to each image file
        names = list(map(utility.get_names, people))

        # Load pre-computed face encodings
        face_encode = np.load('assets/face_encodings/data.npy')

        # Initialize webcam
        print("\nInitializing camera...\n")
        cap = cv2.VideoCapture(const.n_camera)

        # Initialize eye blink detection parameters
        eye_blink_counter = 0
        eye_blink_total = 0
        random_blink_number = random.randint(const.n_min_eye_blink, const.n_max_eye_blink)
        frame_current_name = None

        # Connect to MySQL database for attendance logging
        connection = mysql.connector.connect(
            host="your_mysql_host",
            user="your_mysql_user",
            password="your_mysql_password",
            database="your_mysql_database"
        )
        cursor = connection.cursor()

        while cap.isOpened():
            # Read frame from webcam
            ret, frame = cap.read()
            if not ret:
                break

            # Locate faces in the frame and compute their encodings
            frame_face_loc = fr.face_locations(frame)
            frame_face_landmarks = fr.face_landmarks(frame, frame_face_loc)
            frame_face_encode = fr.face_encodings(frame, frame_face_loc)

            for loc, encode, landmarks in zip(frame_face_loc, frame_face_encode, frame_face_landmarks):
                # Compare current face encoding with stored encodings
                face_distances = fr.face_distance(face_encode, encode)
                match_index = np.argmin(face_distances)

                # Determine if the detected face matches any known face
                if face_distances[match_index] < const.face_recognition_threshold:
                    frame_current_name = names[match_index]
                else:
                    frame_current_name = "Unknown"

                if frame_current_name != "Unknown":
                    # Calculate eye aspect ratio (EAR) for blink detection
                    left_eye_points = np.array(landmarks['left_eye'], dtype=np.int32)
                    right_eye_points = np.array(landmarks['right_eye'], dtype=np.int32)
                    EAR_avg = (utility.get_EAR_ratio(left_eye_points) + utility.get_EAR_ratio(right_eye_points)) / 2

                    # Detect eye blinks
                    if EAR_avg < const.EAR_ratio_threshold:
                        eye_blink_counter += 1
                    else:
                        if eye_blink_counter >= const.min_frames_eyes_closed:
                            eye_blink_total += 1
                        eye_blink_counter = 0

                    # Check for blink completion
                    if eye_blink_total == random_blink_number:
                        # Record attendance if recognized face and blink count match
                        if face_distances[match_index] < const.face_recognition_threshold:
                            print("Updating attendance")
                            update_attendance_in_database(frame_current_name)
                            eye_blink_total = 0
                            random_blink_number = random.randint(const.n_min_eye_blink, const.n_max_eye_blink)

                # Draw face rectangle and name on the frame
                color = const.success_face_box_color if frame_current_name != "Unknown" else const.unknown_face_box_color
                cv2.rectangle(frame, (loc[3], loc[0]), (loc[1], loc[2]), color, 2)
                cv2.putText(frame, frame_current_name, (loc[3], loc[0] - 3), cv2.FONT_HERSHEY_PLAIN, 2,
                            const.text_in_frame_color, 2)

            # Display frame with information
            blink_message = f"Blink {random_blink_number} times, blinks: {eye_blink_total}"
            attendance_message = "Next Person" if utility.check_is_name_recorded(frame_current_name) else ""
            cv2.putText(frame, blink_message, (10, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, const.text_in_frame_color, 2)
            cv2.putText(frame, attendance_message, (20, 450), cv2.FONT_HERSHEY_PLAIN, 2, const.text_in_frame_color, 2)
            cv2.imshow("Webcam (Press 'q' to quit)", frame)

            # Check for user input to exit the loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release the webcam and close all windows
        cap.release()
        cv2.destroyAllWindows()

        # Close the MySQL connection
        cursor.close()
        connection.close()
    else:
        print(f"Run 'encode_faces.py' to encode all faces in '{const.PEOPLE_DIR}' directory...")


if __name__ == "__main__":
    main()
