import socket
import threading
import time
import sys
import numpy as np
import cv2 as cv
import time

# from IPython.display import Video

import asyncio
import csv
import matplotlib.pyplot as plt
import os.path
from time import sleep
from queue import Queue
import threading
import time
#from BLE_client import run
import supervision as sv  # Importing a module named supervision as sv.

# Importing YOLO object detection model from ultralytics library.
from ultralytics import YOLO
import gradio as gr  # Importing Gradio library for creating web interfaces.
from PIL import Image



def analyze_photo():

            # Model 
    
    path03="C:\\Users\\desle\\runs\\detect\\train4\\weights\\best.pt"
    # path 03 is the best model so far
    path04= "C:\\Users\\desle\\runs\\detect\\train\\weights\\best.pt"

    model = YOLO(path03)

    # accepts all formats - image/dir/Path/URL/video/PIL/ndarray. 0 for webcam
    #result = model.predict("C:\\Users\\desle\\OneDrive\\004_PROJECT_ONE\\motion_detection_photos\\throwing_laundry.mp4", save=True)  # save predictions as labels
    #result = model.predict(source="0")
    #result = model.predict(source="C:\\Users\\desle\\OneDrive\\004_PROJECT_ONE\\photos_laundry\\test", show=True)  # Display preds. Accepts all YOLO predict arguments
    #result = model.predict(source="files/", save=True)  # save predictions as labels
    #result = model.predict(source="files/", show=True, save=True)  # save predictions as labels


    # Constants for the model
    conf_threshold = 0.45  # Confidence threshold for filtering out detections.
    laundryList = {"cotton-color-30": 0, "cotton-color-60": 0, "cotton-white-30": 0, "cotton-white-60": 0, "delicate-color-30": 0, "synthetic-color-30": 0, 'synthetic-color-60':0, 'wool':0, 'not recognized':0, 'nothing added':0}
    Predictionnames = {0: 'cotton-color-30', 1: 'cotton-color-60', 2: 'cotton-white-30', 3: 'cotton-white-60', 4: 'delicate-color-30', 5: 'synthetic-color-30', 6: 'synthetic-color-60', 7: 'wool'}
    detected = []
    detection_by_threshold_list = [] # list of detected photos
    photos_to_analyze = [] # selection of unique photos

    # to save the bounded boxed photos add save=True
    source_folder = "files/"
    result = model.predict(source=source_folder, save=True,)  # save predictions as labels

    # # from PIL
    # im1 = Image.open("bus.jpg")
    # results = model.predict(source=im1, save=True)  # save plotted images

    # # from ndarray
    # im2 = cv2.imread("bus.jpg")
    # results = model.predict(source=im2, save=True, save_txt=True)  # save predictions as labels

    # # from list of PIL/ndarray
    # results = model.predict(source=[im1, im2])

    for i in range(0,len(result)):
        res = result[i]
        print(res)

        result2 = res[0] if isinstance(res, list) else res

        # Converting predictions to a format compatible with supervision module.
        detections = sv.Detections.from_ultralytics(result2)
        detected.append(detections)

        # Filtering out detections based on confidence threshold.
        selected_detections_by_threshold = detections[detections.confidence > conf_threshold]
        
        detection_by_threshold_list.append(selected_detections_by_threshold)
        #print(len(detection_list))


    for im in range(0,len(detection_by_threshold_list)):
        if im == 0:
            photos_to_analyze.append(detection_by_threshold_list[im])
            try: 
                print("CLASS:",detection_by_threshold_list[im].class_id[0])
                laundryList[Predictionnames[detection_by_threshold_list[im].class_id[0]]] += 1
            except:
                print("NOT RECOGNIZED1")
                laundryList["not recognized"] += 1
                #continue
               

        else:
            if detection_by_threshold_list[im] != detection_by_threshold_list[im-1]:
                
                photos_to_analyze.append(detection_by_threshold_list[im])
                try:
                    print("CLASS:", detection_by_threshold_list[im].class_id[0])
                    laundryList[Predictionnames[detection_by_threshold_list[im].class_id[0]]] += 1
                except:

                    print("NOT RECOGNIZED2")
                    laundryList["not recognized"] += 1
                    
            else:
                # when motion is detected but nothing has been added
                # photo is the same as the previous photo
                print("SAME")
                laundryList["nothing added"] += 1
                #continue
            
                
    print("")  

    # let us some time to read this information (sleep(5))
    print("\n\n")
    os.system('cls' if os.name == 'nt' else 'clear')
    # print("LEN RESULTS: NR OF PHOTOS:", len(result))
    # print("DETECTED PHOTOS:", len(detected))   
    print(f"DETECTED PHOTOS BY THRESHOLD {conf_threshold} : {len(detection_by_threshold_list)}")
    print("NUMBER OF UNIQUE PHOTOS:", len(photos_to_analyze))
    print(laundryList)
    sleep(5)


    with open(file="csv/wash.csv", mode="w", newline="") as csv_file:
        try:
            writer = csv.writer(csv_file)
            header = ["Program", "Nr"]
            writer.writerow(header)
            for key, value in laundryList.items():
                writer.writerow([key, value])

        except:
            print("could not write to csv")
    
     #close the csv 
    csv_file.close()
       
    return laundryList

server_address = ('192.168.168.167', 8500)  # Connect to RPi (or other server) on ip ... and port ... (the port is set in server.py)
# the ip address can also be the WiFi ip of your RPi, but this can change. You can print your WiFi IP on your LCD? (if needed)

# Global vars for use in methods/threads
client_socket = None
receive_thread = None
shutdown_flag = threading.Event() # see: https://docs.python.org/3/library/threading.html#event-objects

def setup_socket_client():
    global client_socket, receive_thread
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a socket instance
    client_socket.connect(server_address) # connect to specified server
    print("Connected to server")

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, shutdown_flag))
    receive_thread.start()

def receive_messages(sock, shutdown_flag):
    sock.settimeout(1)  # Set a timeout on the socket so when can check shutdown_flag.is_set in the loop, instead of blocking
    counter = 0 # count the incoming messages, part of demo
    try:
        while not shutdown_flag.is_set(): # as long as ctrl+c is not pressed
            try:
                data = sock.recv(1024) # try to receive 1024 bytes of data (maximum amount; can be less)
                if not data: # when no data is received, try again (and shutdown flag is checked again)
                    break
                
                if data.decode() == "0":
                    #print("")
                    continue

                elif data.decode() == "1":
                    print("motion")
                    cap = cv.VideoCapture(1)
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            print("Can't receive frame (stream end?). Exiting ...")
                            break

                        elif ret:
                            frame = cv.flip(frame, 0)
                            print("taking photo & analyse")


                            file_time = time.strftime("%Y_%m_%d_%H_%M")

                            # location of image
                            img_name = f"files/opencv_frame{file_time}.png"
                            cv.imwrite(img_name, frame)
                            all_laundry = analyze_photo()

                            break

                    # Release everything if job is finished
                    cap.release()
                    # out.release()
                    cv.destroyAllWindows()

                for k,v in all_laundry.items():
                    if int(v) > 5:
                        print("START MACHINE FOR: ", k)
                        response = "start machine   {}".format(k)
                        sock.sendall(response.encode())
                
                counter += 1 # up the count by 1

            except socket.timeout: # when no data comes within timeout, try again
                continue

    except Exception as e:
        if not shutdown_flag.is_set():
            print(f"Connection error: {e}")
    finally:
        sock.close()

def main():
    global client_socket, receive_thread
    setup_socket_client()

    if client_socket is None:
        print("Not connected, is server running on {}:{}?".format(server_address[0], server_address[1]))
        sys.exit()
    
    # send "hello I'm connected" message
    client_socket.sendall("Hello from AI".encode()) # send a "connected" message from client > server

    try:
        while True: # random loop for other things
            time.sleep(0.1)
            #print(" ")

    except KeyboardInterrupt:
        print("Client disconnecting...")
        shutdown_flag.set()
    finally:
        client_socket.close()
        receive_thread.join()
        print("Client stopped gracefully")

if __name__ == "__main__":
    main()
