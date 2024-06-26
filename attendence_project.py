import numpy as np
import cv2
import face_recognition as fr
from glob import glob
import pickle
import random
import mysql.connector
from datetime import datetime
import utility
import define_constants as const

def main():
    # Load expected number of files from the pickle file (n_people)
    with open('assets/pickles/n_people.pk', 'rb') as pickle_file:
        n_people_in_pickle = pickle.load(pickle_file)

    # Read all image files from PEOPLE_DIR
    people = glob(const.PEOPLE_DIR + '/*.*')

    # Check if number of files matches the expected count from pickle
    if len(people) == n_people_in_pickle:
        # Load names corresponding to each image file
        names = list(map(utility.get_names, people))

        # Load pre-computed face encodings
        face_encode = np.load('assets/face_encodings/data.npy')

        # Initialize webcam
        cap = cv2.VideoCapture(const.n_camera)

        # Initialize eye blink detection parameters
        eye_blink_counter = 0
        eye_blink_total = 0
        random_blink_number = random.randint(const.n_min_eye_blink, const.n_max_eye_blink)
        frame_current_name = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_face_loc = fr.face_locations(frame)
            frame_face_landmarks = fr.face_landmarks(frame, frame_face_loc)
            frame_face_encode = fr.face_encodings(frame, frame_face_loc)

            for loc, encode, landmarks in zip(frame_face_loc, frame_face_encode, frame_face_landmarks):
                face_distances = fr.face_distance(face_encode, encode)
                match_index = np.argmin(face_distances)

                if face_distances[match_index] < const.face_recognition_threshold:
                    frame_current_name = names[match_index]
                else:
                    frame_current_name = "Unknown"

                if frame_current_name != "Unknown":
                    left_eye_points = np.array(landmarks['left_eye'], dtype=np.int32)
                    right_eye_points = np.array(landmarks['right_eye'], dtype=np.int32)
                    EAR_avg = (utility.get_EAR_ratio(left_eye_points) + utility.get_EAR_ratio(right_eye_points)) / 2

                    if EAR_avg < const.EAR_ratio_threshold:
                        eye_blink_counter += 1
                    else:
                        if eye_blink_counter >= const.min_frames_eyes_closed:
                            eye_blink_total += 1
                        eye_blink_counter = 0

                    if eye_blink_total == random_blink_number:
                        update_attendance_in_database(frame_current_name)
                        eye_blink_total = 0
                        random_blink_number = random.randint(const.n_min_eye_blink, const.n_max_eye_blink)

                color = const.success_face_box_color if frame_current_name != "Unknown" else const.unknown_face_box_color
                cv2.rectangle(frame, (loc[3], loc[0]), (loc[1], loc[2]), color, 2)
                cv2.putText(frame, frame_current_name, (loc[3], loc[0] - 3), cv2.FONT_HERSHEY_PLAIN, 2, const.text_in_frame_color, 2)

            blink_message = f"Blink {random_blink_number} times, blinks: {eye_blink_total}"
            attendance_message = "Next Person" if utility.check_is_name_recorded(frame_current_name) else ""
            cv2.putText(frame, blink_message, (10, 50), cv2.FONT_HERSHEY_PLAIN, 1.5, const.text_in_frame_color, 2)
            cv2.putText(frame, attendance_message, (20, 450), cv2.FONT_HERSHEY_PLAIN, 2, const.text_in_frame_color, 2)
            cv2.imshow("Webcam (Press 'q' to quit)", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
    else:
        print(f"Run 'encode_faces.py' to encode all faces in '{const.PEOPLE_DIR}' directory...")

def update_attendance_in_database(name):
    try:
        # Connect to MySQL database
        db = mysql.connector.connect(
            host='localhost',
            user='your_username',
            password='your_password',
            database='your_database_name'
        )
        cursor = db.cursor()

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

        print(f"Attendance recorded for {name} at {current_time}")
    except mysql.connector.Error as error:
        print(f"Failed to update attendance in database: {error}")
    finally:
        if db.is_connected():
            cursor.close()
            db.close()

if __name__ == "__main__":
    main()
