import os
import pickle
import numpy as np
import cv2
import face_recognition
#import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
        'databaseURL': "https://faceattendence-a6795-default-rtdb.firebaseio.com/",
        'storageBucket': "faceattendence-a6795.appspot.com"
})

ref = db.reference('Students')

def addDetails():

    data={}
    dataList = os.listdir('Images')
    for path in dataList:
        key= os.path.splitext(path)[0]
        my_dict={"Name":[],"Major":[],"Total_attendance":[],"last_attendance_time":[]}
        nam=input("Enter your name:")
        major=input("Enter Your major")
        tot_att=int(input("Enter total attendance"))
        print ("Date time format Y-m-d H:M:S")
        last_att_time=input("Enter date and time of last attendence")
        my_dict={"name":nam,"major":major,"total_attendance":tot_att,"last_attendance_time":last_att_time}
        temp={key:my_dict}
        data.update(temp)


    for key, value in data.items():
        ref.child(key).set(value)

def delete(k):


    ref.child(k).delete()
    os.remove("Images/"+str(k)+".jpg")

def update(k):


    dict = ref.child(k).get()
    for dic, val in dict.items():
        print(dic, ": ", val)

    cat=input("Select key to be updated")
    if cat=='total_attendance':
        val=int(input("Enter new value"))
    else:
        val=input("Enter new value")

    ref.child(k).child(cat).set(val)

def getAllKeys(k):

    dic=ref.child(k).get()
    dic.keys()

    for d in dic:
        print (d)

def Importstd(path_Img):
    folderPath = path_Img
    pathList = os.listdir(folderPath)
    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIds.append(os.path.splitext(path)[0])

        fileName = f'{folderPath}/{path}'
        bucket = storage.bucket()
        blob = bucket.blob(fileName)
        blob.upload_from_filename(fileName)
        # print(path)
        # print(os.path.splitext(path)[0])
    return imgList,studentIds



def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

def dump(imgList,studentIds):
    print("Encoding Started ...")
    encodeListKnown = findEncodings(imgList)
    encodeListKnownWithIds = [encodeListKnown, studentIds]
    print("Encoding Complete")

    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("File Saved")

def webC():


    bucket = storage.bucket()

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    imglist, stdIds = Importstd('Images')
    encodeList = findEncodings(imglist)
    dump(imglist, stdIds)

    # Load the encoding file
    print("Loading Encode File ...")
    file = open('EncodeFile.p', 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    # print(studentIds)
    print("Encode File Loaded")

    counter = 0
    id = -1
    imgStudent = []

    while True:
        success, img = cap.read()

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)



        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                # print("matches", matches)
                # print("faceDis", faceDis)

                matchIndex = np.argmin(faceDis)
                # print("Match Index", matchIndex)

                if matches[matchIndex]:
                    # print("Known Face Detected")
                    # print(studentIds[matchIndex])
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                    #imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
                    id = studentIds[matchIndex]
                    if counter == 0:
                        counter = 1

            if counter != 0:

                if counter == 1:
                    # Get the Data
                    studentInfo = db.reference(f'Students/{id}').get()
                    print(studentInfo)
                    blob = bucket.get_blob(f'Images/{id}.jpg')
                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                    cv2.imshow("std", imgStudent)
                    # Get the Image from the storage
                    # Update data of attendance
                    datetimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                       "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    print(secondsElapsed)
                    if secondsElapsed > 30:
                        ref = db.reference(f'Students/{id}')
                        studentInfo['total_attendance'] += 1
                        ref.child('total_attendance').set(studentInfo['total_attendance'])
                        ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        cv2.destroyWindow("std")
                    else:
                        counter = 0


                    counter += 1

                    if counter >= 20:
                        counter = 0
                        studentInfo = []
                        imgStudent = []

        else:
            counter = 0
        cv2.imshow("Webcam", img)
        cv2.waitKey(1)
        if cv2.waitKey(1) & 0xFF==ord('q'):
            break

    cv2.destroyAllWindows()