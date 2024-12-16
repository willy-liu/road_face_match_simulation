import os
import torch
from torchvision import transforms
from facenet_pytorch import InceptionResnetV1
import numpy as np
import json
from flask import Flask, request, jsonify
from flaskext.mysql import MySQL
from threading import Lock

app = Flask(__name__)

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'willys_password'
app.config['MYSQL_DATABASE_DB'] = 'DistrSys_term_project'
app.config['MYSQL_DATABASE_HOST'] = os.getenv('DB_HOST', '127.0.0.1')
app.config['MYSQL_DATABASE_PORT'] = 3306

mysql = MySQL()
mysql.init_app(app)

# 加载预训练的FaceNet模型
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# 图像转换
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((160, 160)),
    # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 创建一个锁
request_lock = Lock()

def extract_features(img_rgb):
    # 转换图像
    image = transform(img_rgb).unsqueeze(0)  # 增加batch维度
    # 提取特征
    with torch.no_grad():
        features = resnet(image)
    return features[0]

def calculate_distance(features1, features2):
    distance = np.linalg.norm(features1 - features2)
    return distance

@app.before_request
def before_request():
    if request.path == '/api/remote':
        request_lock.acquire()

@app.after_request
def after_request(response):
    if request.path == '/api/remote':
        request_lock.release()
    return response

@app.route('/api/remote', methods=['POST'])
def remote_api():
    print("on call")
    detection_results = request.get_json()

    source = detection_results.get('source', 'known_source')
    conn = mysql.connect()
    cursor = conn.cursor()
    for box, face_image_rgb, time_stamp, frame_num in zip(detection_results['box'], detection_results['face_image_rgb'], detection_results['time_stamp'], detection_results['frame_num']):
        face_image_rgb = np.array(face_image_rgb, np.uint8)
        face_image_rgb_shape_str = json.dumps(face_image_rgb.shape)
        box_str = json.dumps(box)  # Convert bbox to JSON string
        feature = extract_features(face_image_rgb)
        # print(f"{feature.numpy().dtype=}")
        feature_blob = feature.numpy().tobytes()  # Convert feature array to bytes
        # 将数据插入 MySQL 数据库
        insert_query = """
        INSERT INTO face_data (source, box, face_image_rgb, face_image_rgb_shape, feature, time_stamp, frame_num)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (source, box_str, face_image_rgb.tobytes(), face_image_rgb_shape_str, feature_blob, time_stamp, frame_num))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route('/', methods=['GET'])
def hello():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello, world!'")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0]

# 這個端點用於 livenessProbe
@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify(status="ok"), 200

# 這個端點用於 readinessProbe
@app.route('/ready', methods=['GET'])
def readiness():
    # 這裡簡單返回 200 表示準備好了
    return jsonify(status="ready"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
