import cv2 as cv
from cv2 import aruco
import numpy as np
import os
import keyboard
from playsound import playsound
import random
from gtts import gTTS
from io import BytesIO
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

def image_augmentation(frame, src_image, dst_points):   #
    src_h, src_w = src_image.shape[:2]
    frame_h, frame_w = frame.shape[:2]
    mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
    src_points = np.array([[0, 0], [src_w, 0], [src_w, src_h], [0, src_h]])
    H, _ = cv.findHomography(srcPoints=src_points, dstPoints=dst_points)
    warp_image = cv.warpPerspective(src_image, H, (frame_w, frame_h))
    cv.imshow("warp image", warp_image)
    cv.fillConvexPoly(mask, dst_points, 255)
    results = cv.bitwise_and(warp_image, warp_image, frame, mask=mask)

def generate_speech(text):
    output = gTTS(text,lang="vi", slow=False)
    output.save("./data/sound/PointTemp.mp3")
    play('point')

def play(sound):
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(soundDict[sound])
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue
    pygame.quit()


#Constant variables
MARKER_DICT = aruco.Dictionary_get(aruco.DICT_5X5_250)
PARAM_MARKERS = aruco.DetectorParameters_create()
IMAGES_LIST = read_images(r'.\data\image_animals')
TOTALTIME = 30 * 60    # 60s
CHECK_FREQ = 30
CHECK_AGAIN_FREQ = 30 * 5

#Variables
GameState = 0   # 0=off, 1=start, 2=play, 3=final, 4=
cap = cv.VideoCapture(1)
frameCount = 0
point = 0
timeIdx = 0
questionID = 0
checkStatus = 0
markerDetected = set()

#sound
soundDict = {
    'intro':'./data/sound/Intro.mp3',
    'start':'./data/sound/Start.mp3',
    'question':'./data/sound/Question.mp3',
    'tenSec':'./data/sound/TenSec.mp3',
    'fiveSec':'./data/sound/FiveSec.mp3',
    'timeUp':'./data/sound/Timeup.mp3',
    'oneOnly':'./data/sound/OneOnly.mp3',
    'true':'./data/sound/True.mp3',
    'false':'./data/sound/False.mp3',
    'end':'./data/sound/End.mp3',
    'cancel':'./data/sound/Cancel.mp3',
    'point':'./data/sound/PointTemp.mp3',
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

    # gamestate 0
    if GameState == 0:
        point = 0   # reset point
        if keyboard.is_pressed('s'):
           GameState = 1
           play('start')
        timeIdx = 0

    # gamestate 1    
    elif GameState == 1:
        # Random ID con vật
        questionID = random.randint(1,6)
        #playsound
        play('question')
        playsound(soundAnimal[questionID]) # tên con vật
        GameState = 2
    
    # gamestate 2    
    elif GameState == 2:
        timeIdx += 1
        if TOTALTIME - timeIdx == 30 * 10:  # còn 10s
            play('tenSec')
        if TOTALTIME - timeIdx == 30 * 5:   # còn 5s
            play('fiveSec')
        if TOTALTIME - timeIdx == 0:    # hết giờ
            play('timeUp')
            GameState = 3
        
        if frameCount % CHECK_FREQ == 0 and checkStatus == 0:
            markerDetected = set()
            if marker_corners:
                for id in marker_IDs:
                    markerDetected.add(id[0])
                if len(markerDetected) > 1:
                    # Nhiều marker khác nhau đc nhận dạng
                    # playsound
                    play('oneOnly')
                    checkStatus = 1
                    
                else:
                    answer = list(markerDetected)
                    if answer[0] == questionID:
                        point += 10
                    # playsound   
                        play('true') 
                        GameState = 1
                    else:
                        # playsound
                        play('false')
                        checkStatus = 1
        
        if checkStatus == 1 and frameCount % CHECK_AGAIN_FREQ == 0:
            checkStatus = 0

        if keyboard.is_pressed('c'):
            play('cancel')
            GameState = 0
    
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
        
        if keyboard.is_pressed('c'):
            play('cancel')
            GameState = 0


    # show
    cv.imshow("frame", frame)
    key = cv.waitKey(1)
    if key == ord('q'):
           break
    
cap.release()
cv.destroyAllWindows()

