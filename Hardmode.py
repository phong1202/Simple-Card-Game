import cv2 as cv
from cv2 import aruco
import numpy as np
import os
import keyboard
from playsound import playsound
import random
from gtts import gTTS
import pygame
import csv

#Function
def read_images(dir_path):  # Tạo list chứa các ảnh trong file theo đường dẫn
    img_list = []
    files = os.listdir(dir_path)
    for file in files:
        img_path = os.path.join(dir_path, file)
        image = cv.imread(img_path)
        img_list.append(image)
    return img_list

def generate_speech(text):  # Chuyển số điểm của người chơi thành giọng nói 
    output = gTTS(text,lang="vi", slow=False)
    output.save("./data/sound/PointTemp.mp3")
    play('point')

def play(sound):    # Chạy các file ấm thanh
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(soundDict[sound])
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue
    pygame.quit()

def question_create():  # Tạo ra câu hỏi gồm ID 3 con vật ngẫu nhiên
    questionID = set()
    while len(questionID) < 3:
        questionID.add(random.randint(1,30))
    return questionID

def check_answer(question, answer): # Kiểm tra đáp án
    if len(answer) != len(question):
        global GameState 
        GameState = 4
        return -1
    else:
        status = 0
        for id in question:
            for ans in answer:
                if ans == id:
                    status += 1
                    break
        return status
            


#Constant variables
MARKER_DICT = aruco.Dictionary_get(aruco.DICT_5X5_250)
PARAM_MARKERS = aruco.DetectorParameters_create()
IMAGES_LIST = read_images(r'.\data\image_animals')
TOTAL_TIME = 30 * 120    # 120s
CHECK_FREQ = 30
CHECK_AGAIN_TIME = 30 * 5
REMINDTIME = 30 * 3


#Variables
GameState = 0   # 0=off, 1=start, 2=play, 3=final, 4=error
cap = cv.VideoCapture(1)
frameCount = 0
point = 0
timeIdx = 0
timeCheckIdx = 0
remindIdx = 0
questionID = []
checkStatus = 0
markerDetected = set()
answerStatus = 0

#sound
soundDict = {
    'intro':'./data/sound/Intro.mp3',
    'start':'./data/sound/Start.mp3',
    'question':'./data/sound/Question_2.mp3',
    'tenSec':'./data/sound/TenSec.mp3',
    'fiveSec':'./data/sound/FiveSec.mp3',
    'timeUp':'./data/sound/Timeup.mp3',
    '3Only':'./data/sound/3Only.mp3',
    'missing1':'./data/sound/missing1.mp3',
    'missing2':'./data/sound/missing2.mp3',
    '1of3':'./data/sound/1of3.mp3',
    '2of3':'./data/sound/2of3.mp3',
    '3of3':'./data/sound/3of3.mp3',
    'false':'./data/sound/False.mp3',
    'end':'./data/sound/End.mp3',
    'cancel':'./data/sound/Cancel.mp3',
    'wrongType':'./data/sound/wrongType.mp3',
    'point':'./data/sound/PointTemp.mp3',
    'error':'./data/sound/Error.mp3',
}

soundAnimal = {}
with open("sounds.csv") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) != 2:
            # print(f"Skipping row {row} because it doesn't have 2 columns")
            continue
        soundAnimal[int(row[0])] = row[1]

#Main function
play('intro')

    # Lấy frame
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frameCount += 1
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)  # convert to gray
    marker_corners, marker_IDs, reject = aruco.detectMarkers(gray_frame, MARKER_DICT, parameters=PARAM_MARKERS)
    markerDetected = set()
    if marker_corners:
        for id in marker_IDs:
            markerDetected.add(id[0])

    # gamestate 0
    if GameState == 0:
        point = 0   # reset point
        if keyboard.is_pressed('s') or 31 in markerDetected:    # bắt đầu game
           GameState = 1
           play('start')
        timeIdx = 0

    # gamestate 1    
    elif GameState == 1:
        # Random ID con vật
        questionID = sorted(question_create())
        #playsound
        play('question')
        for ID in questionID:
            playsound(soundAnimal[ID]) # tên con vật
        GameState = 2
    
    # gamestate 2    
    elif GameState == 2:
        timeIdx += 1
        if TOTAL_TIME - timeIdx == 30 * 10:  # còn 10s
            play('tenSec')
        if TOTAL_TIME - timeIdx == 30 * 5:   # còn 5s
            play('fiveSec')
        if TOTAL_TIME - timeIdx == 0:    # hết giờ
            play('timeUp')
            GameState = 3
        
        if frameCount % CHECK_FREQ == 0:
            # Xử lý ảnh k phải con vật
            if 31 in markerDetected or (32 in markerDetected and len(markerDetected) > 1):
                play('wrongType')
                continue
            # Cancel
            if keyboard.is_pressed('c') or (32 in markerDetected and len(markerDetected) == 1):
                play('cancel')
                GameState = 0
                continue

            if checkStatus == 0:
                if marker_corners:
                    if len(markerDetected) > 3:  # thừa ảnh
                        # Nhiều hơn 3 marker khác nhau đc nhận dạng
                        # playsound
                        play('3Only')
                        checkStatus = 1

                    elif len(markerDetected) == 1 or len(markerDetected) == 2:   # thiếu ảnh
                        remindIdx += 30
                        if REMINDTIME - remindIdx == 0:
                            if len(markerDetected) == 1:
                                play('missing2')
                            else:
                                play('missing1')
                            remindIdx = 0

                    elif len(markerDetected) == 3:
                        answer = sorted(markerDetected)
                        answerStatus = check_answer(questionID, answer)
                        if answerStatus == 1:
                            point += 10
                            play('1of3')
                            GameState = 1
                        elif answerStatus == 2:
                            point += 30
                            play('2of3')
                            GameState = 1
                        if answerStatus == 3:
                            point += 50
                            play('3of3')
                            GameState = 1
                        if answerStatus == 0:
                            play('false')
                            checkStatus = 1
                        remindIdx = 0

                        
            
            if checkStatus == 1:    # Thời gian sửa
                timeCheckIdx += 1
                if CHECK_AGAIN_TIME - timeCheckIdx == 0:    
                    checkStatus = 0 
                    timeCheckIdx = 0

        
    
        # gamestate 3    
    elif GameState == 3:
            #thông báo điểm
            # playsound
        play('end')
        generate_speech(str(point))
        GameState = 0

        # gamestate 4
    elif GameState == 4:
        play('error')
        
        if keyboard.is_pressed('c') or 32 in markerDetected:
            play('cancel')
            GameState = 0

    # show
    cv.imshow("frame", frame)
    key = cv.waitKey(1)
    if key == ord('q'):
           break
    
cap.release()
cv.destroyAllWindows()

