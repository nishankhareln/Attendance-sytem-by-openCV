from multiprocessing import Pool

import numpy as np
import cv2 as cap
import face_recognition as fr
from glob import glob
import pickle
import utility
import random
import define_constants as const
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

from attendence_project import frame_current_name, score

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,
{
 'databaseURL': "https://face-attendance-real-tim-a0569-default-rtdb.asia-southeast1.firebasedatabase.app/"
}
)

ref = db.reference('Students') #create student in real time

data = {
    "312654":
        {
            "name":"Nishan Kharel",
            "major":"CSIT",
            "starting_year":2018,
            "total_attendance":6,
            "standing":"G",
            "year":4,
            "last_attendance_time":"2022-12-11 00:54:34"
        }


}

for key,value in data.items():
    ref.child(key).set(value)


def update_firebase_database(frame_current_name):
    pass


while cap.isOpened():
    # Read Frames
    ret, frame = cap.read()

    # ... (your existing code)

    # If random_blink_number and total blink number matches, then record attendance
    if random_blink_number == eye_blink_total:
        # Record Attendance only if score is at most 0.6
        if np.min(score) < const.face_recognition_threshold:
            # Update Firebase Realtime Database
            update_firebase_database(frame_current_name)

            # Reset random_blink_number, and eye blink constants
            random_blink_number = random.randint(const.n_min_eye_blink, const.n_max_eye_blink)
            eye_blink_total = 0
            eye_blink_counter = 0


# ... (your existing code)

# Helper function to update Firebase Realtime Database
def update_firebase_database(student_id):
    try:
        # Create datetime object
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        # Update Firebase Realtime Database
        ref.child(student_id).update({
            "total_attendance": db.FieldValue.increment(1),
            "last_attendance_time": current_time
        })

        text_display = f"{student_id}, your attendance is recorded"
        print(text_display)

        if const.text_to_speech:
            pool = Pool(processes=1)
            result = pool.apply_async(const.text_to_speech, [text_display])
    except Exception as e:
        print("Error: Unable to update real-time data in the Firebase Realtime Database")
        print(e)

