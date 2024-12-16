import os
import torch
import cv2
import numpy as np
import json
from datetime import datetime
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import uuid

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
os.chdir(CURRENT_DIR)

def yolo_init():
    return YOLO('model/yolov8n-face.pt')

simulation_mp4_paths = ["video/moniter_1.mp4",
                        "video/moniter_2.mp4",
                        "video/moniter_3.mp4",
                        "video/moniter_3-1.mp4",
                        "video/moniter_4.mp4",
                        "video/moniter_4-1.mp4",
                        "video/moniter_5.mp4"]

# 定義最大線程數量
MAX_THREADS = 5
executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

# 定義累積偵測到幾張臉才發一個request
MIN_FACES = 5

# def send_to_remote_api(detection_resultss, url="http://127.0.0.1:5555/api/remote"): 
def send_to_remote_api(detection_resultss, url="http://127.0.0.1:59069/api/remote"):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(detection_resultss), headers=headers)
    return response.status_code

# def send_to_remote_api_async(detection_resultss, url="http://127.0.0.1:5555/api/remote"):
def send_to_remote_api_async(detection_resultss, url="http://127.0.0.1:59069/api/remote"):
    executor.submit(send_to_remote_api, detection_resultss, url)

def process_video(simulation_mp4_path, label, stop_event, uid):
    yolo = yolo_init()
    cap = cv2.VideoCapture(simulation_mp4_path)

    # 檢查是否成功打開視頻
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # 獲取視頻的幀率和尺寸
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rect_width = height // 500
    font_scale = height // 1000

    # 創建 VideoWriter 對象，用於保存視頻
    output_path = f"output/{os.path.basename(simulation_mp4_path).split('.')[0]}-{uid}.mp4"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    track_set = set()
    frame_count = -1
    track_count = defaultdict(lambda: int(0))
    sample_rate = 90  # 設定達到幾次出現次數才加入 detection_results
    face_count = 0

    def init_dectection_result():
        return {
            "time_stamp": [],
            "frame_num": [],
            "box": [],
            "face_image_rgb": [],
            "source": f"{simulation_mp4_path}-{uid}"
        }

    detection_results = init_dectection_result()

    while not stop_event.is_set():
        ret, frame = cap.read()

        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            yolo = yolo_init()
            continue

        frame_count += 1

        frame_draw = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 獲取當前時間戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 在框架上添加綠色當前時間戳(藍色邊匡)
        cv2.putText(frame_draw, timestamp, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 0, 0), 7)
        cv2.putText(frame_draw, timestamp, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), 3)

        # 使用 YOLOv8 人臉檢測模型進行人臉檢測(要用bgr)
        results = yolo.track(frame, persist=True, verbose=False)
        boxes = results[0].boxes.xyxy.int().tolist()
        try:# id有時會莫名為None，跳過就好
            track_ids = results[0].boxes.id.int().tolist()
        except:
            continue
        confidences = results[0].boxes.conf.cpu().numpy()

        flag = False

        # 繪製檢測到的人臉邊框並構建檢測結果
        for box, track_id, confidence in zip(boxes, track_ids, confidences):
            if confidence >= 0.7:  # 過濾檢測結果
                x1, y1, x2, y2 = box
                cv2.rectangle(frame_draw, (x1, y1), (x2, y2), (0, 0, 255), rect_width)
                cv2.putText(frame_draw, f'ID: {track_id}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), 2)
                track_count[track_id] += 1
                if track_count[track_id] % sample_rate == 1:
                    face_count += 1
                    flag = True
                    track_set.add(track_id)
                    detection_results["time_stamp"].append(timestamp)
                    detection_results["frame_num"].append(frame_count)
                    detection_results["box"].append(box)
                    detection_results["face_image_rgb"].append(rgb_frame[y1:y2, x1:x2, :].tolist())

        if face_count >= MIN_FACES:
            print(f"send request,{face_count=}")
            print(detection_results["box"])
            send_to_remote_api_async(detection_results)
            face_count = 0
            detection_results = init_dectection_result()

        # 顯示當前幀
        frame_draw_resized = cv2.resize(frame_draw, (640, 480), interpolation=cv2.INTER_AREA)
        img = Image.fromarray(cv2.cvtColor(frame_draw_resized, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        try:
            if not stop_event.is_set():
                label.imgtk = imgtk
                label.config(image=imgtk)
                label.update()
        except tk.TclError:
            break

        # 保存當前幀到視頻文件
        out.write(frame_draw)

        time.sleep(0.025)

    # 釋放資源
    cap.release()
    out.release()
    print("結束")

def create_new_window(simulation_mp4_path):
    uid = uuid.uuid4()
    new_window_title = f"{simulation_mp4_path}-{uid}"
    new_window = tk.Toplevel()
    new_window.title(new_window_title)

    video_label = tk.Label(new_window)
    video_label.pack()

    stop_event = threading.Event()

    def on_close():
        stop_event.set()
        new_window.destroy()

    new_window.protocol("WM_DELETE_WINDOW", on_close)

    thread = threading.Thread(target=process_video, args=(simulation_mp4_path, video_label, stop_event, uid))
    thread.start()

def create_ui():
    root = tk.Tk()
    root.title("Video Selection")

    label = ttk.Label(root, text="Select a video to process:")
    label.pack(padx=10, pady=10)

    selected_path = tk.StringVar()
    selected_path.set(simulation_mp4_paths[0])

    option_menu = tk.OptionMenu(root, selected_path, *simulation_mp4_paths)
    option_menu.pack(padx=10, pady=10)

    def on_start():
        create_new_window(selected_path.get())

    start_button = ttk.Button(root, text="Start Processing", command=on_start)
    start_button.pack(padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_ui()
