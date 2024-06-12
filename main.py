import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-336eb-default-rtdb.firebaseio.com/",
    'storageBucket': "faceattendancerealtime-336eb.appspot.com"
})

bucket = storage.bucket()

# Access the webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load the background image
background_image_path = 'Resource/background.jpeg'
imgBackground = cv2.imread(background_image_path)

# Check if the background image was loaded successfully
if imgBackground is None:
    print(
        f"Error: Unable to load background image from '{background_image_path}'. Please check the file path/integrity.")
    exit()

# Load mode images into a list
folderModePath = 'Resource/Modes'
if not os.path.isdir(folderModePath):
    print(f"Error: '{folderModePath}' is not a valid directory.")
    exit()

modePathList = os.listdir(folderModePath)
imgModeList = []

# Read mode images, resize if necessary, and append them to imgModeList
for path in modePathList:
    mode_image_path = os.path.join(folderModePath, path)
    mode_img = cv2.imread(mode_image_path)
    if mode_img is not None:
        if mode_img.shape[0] != 643 or mode_img.shape[1] != 414:
            mode_img = cv2.resize(mode_img, (414, 643))
        imgModeList.append(mode_img)
    else:
        print(f"Warning: Unable to read image '{mode_image_path}'. Skipping...")

print(f"Number of mode images loaded: {len(imgModeList)}")
# load the Encoding file
print("Loading Encode File")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
# print(studentIds)
print("Encode File Loaded")
modeType = 0
counter = 0
id = -1
studentInfo = None
imgStudent = []

try:

    while True:
        # Capture frame-by-frame
        success, img = cap.read()
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        # Check if the frame is captured successfully
        if not success:
            print("Error: Unable to capture frame from the webcam.")
            break

        # Update background image with webcam frame
        imgBackground[162:162 + 480, 55:55 + 640] = img

        # Update background image with mode image (if available)
        if imgModeList:
            imgMode = imgModeList[modeType]
            imgBackground[44:44 + 643, 808:808 + 414] = imgMode
        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                print("matches", matches)
                print("faceDis", faceDis)

                matchIndex = np.argmin(faceDis)
                # print("Match Index", matchIndex)

                if matches[matchIndex]:
                    # print("Known face Detected")
                    # print(studentIds[matchIndex])
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    id = studentIds[matchIndex]

                    if counter == 0:
                        counter = 1
                        modeType = 1

            if counter != 0:
                if counter == 1:
                    studentInfo = db.reference(f'Students/{id}').get()
                    print(studentInfo)
                    # get the image from the storage
                    blob = bucket.get_blob(f'Images/{id}.jpg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                    datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")

                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)
                    if secondsElapsed > 30:
                        ref = db.reference(f'Students/{id}')
                        studentInfo['total_attendance'] += 1
                        ref.child('total_attendance').set(studentInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        modeType = 3
                        counter = 0
                        imgMode = imgModeList[modeType]
                        imgBackground[44:44 + 643, 808:808 + 414] = imgMode
                if modeType != 3:
                    if 10 < counter < 20:
                        modeType = 2
                    imgMode = imgModeList[modeType]
                    imgBackground[44:44 + 643, 808:808 + 414] = imgMode
                    if counter <= 10:
                        cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(studentInfo['branch']), (1030, 560),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(id), (1020, 500),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(studentInfo['starting_year']), (1135, 635),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                        (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                        imgStudent_resized = cv2.resize(imgStudent, (252, 216))
                        imgBackground[175:175 + 216, 909:909 + 252] = imgStudent_resized

                    counter += 1

                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        studentInfo = []
                        imgStudent = []
                        imgMode = imgModeList[modeType]
                        imgBackground[44:44 + 643, 808:808 + 414] = imgMode
        else:
            modeType = 0
            counter = 0

        # cv2.imshow("Webcam", img)
        cv2.imshow("Face Attendance", imgBackground)
        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("KeyboardInterrupt: Program interrupted by the user.")

# Release the webcam and close all windows
cap.release()
cv2.destroyAllWindows()