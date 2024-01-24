import cv2
import string
from datetime import datetime
from gtts import gTTS
from pygame import mixer
from multiprocessing import Pool
from scipy.spatial import distance as dist
import psycopg2
from psycopg2 import sql
import define_constants as const
import os

# Define the PostgreSQL connection parameters
db_params = {
    'host': 'localhost',
    'port': '5432',
    'database': 'student_data',
    'user': 'postgres',
    'password': '2060'
}

# Establish a connection to the PostgreSQL database
try:
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()
    print("Connected to PostgreSQL")
except psycopg2.Error as e:
    print("Error: Unable to connect to the PostgreSQL database")
    print(e)

# ... (Rest of your existing code)

# Update real-time data in the PostgreSQL database
def update_database(frame_current_name):
    try:
        # Create datetime object
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_weekday = now.strftime("%A")
        current_month = now.strftime("%B")
        current_day_of_month = now.strftime("%d")

        # Construct SQL query to insert data
        insert_query = sql.SQL("INSERT INTO your attendance_data (student_id, student_name, gender, arrival_time) VALUES ({}, {}, {}, {});").format(
            sql.Literal(student_id),  # Assuming frame_current_name is student_id
            sql.Literal(student_name),  # Replace with the actual student_name value
            sql.Literal(gender),  # Replace with the actual gender value
            sql.Literal(current_time)
        )

        # Execute the SQL query
        cursor.execute(insert_query)

        # Commit the changes to the database
        connection.commit()

        text_display = f"{frame_current_name}, your attendance is recorded"
        print(text_display)

        if const.text_to_speech:
            pool = Pool(processes=1)
            result = pool.apply_async(text_to_speech, [text_display])
    except psycopg2.Error as e:
        print("Error: Unable to update real-time data in the PostgreSQL database")
        print(e)

# ... (Rest of your existing code)

# Release the resources when the program exits

    if connection:
        cursor.close()
        connection.close()
        print("Connection to PostgreSQL closed")
