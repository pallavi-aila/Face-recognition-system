import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'databaseURL': "https://faceattendancerealtime-336eb-default-rtdb.firebaseio.com/"})
ref = db.reference('Students')

data = {
    "3067":
        {
            "name": "A Pallavi",
            "branch": "CSE",
            "starting_year": 2021,
            "total_attendance": 80,
            "class": "CSEb",
            "last_attendance_time": "2025-04-01 11:00:00"

        },
    "3089":
        {
            "name": "hafsah",
            "branch": "CSE",
            "starting_year": 2021,
            "total_attendance": 85,
            "class": "CSEb",
            "last_attendance_time": "2025-04-01 11:00:00"

        },
    "3092":
        {
            "name": "Madhuri",
            "branch": "CSE",
            "starting_year": 2021,
            "total_attendance": 65,
            "class": "CSEb",
            "last_attendance_time": "2025-04-01 11:00:00"

        },
    "3104":
        {
            "name": "Niharika",
            "branch": "CSE",
            "starting_year": 2021,
            "total_attendance": 85,
            "class": "CSEb",
            "last_attendance_time": "2025-04-01 11:00:00"

        },
    "3117":
        {
            "name": "shivaani",
            "branch": "CSE",
            "starting_year": 2021,
            "total_attendance": 70,
            "class": "CSEb",
            "last_attendance_time": "2025-04-01 11:00:00"

        }
}

for key, value in data.items():
    ref.child(key).set(value)