import os
import torch
from torchvision import transforms
from facenet_pytorch import InceptionResnetV1
import numpy as np
from flask import Flask, request, jsonify, render_template, send_file
from flaskext.mysql import MySQL
from PIL import Image
import io
import base64
import json

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
])

def extract_features(img_rgb):
    # 转换图像
    image = transform(img_rgb).unsqueeze(0)  # 增加batch维度
    # 提取特征
    with torch.no_grad():
        features = resnet(image)
    return features[0].numpy()

def calculate_distance(features1, features2):
    distance = np.linalg.norm(features1 - features2)
    return distance

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.content_type in ['image/jpeg', 'image/png']:
        try:
            # 將影像檔轉換為PIL影像
            img = Image.open(file.stream)
            # 轉換為RGB模式（如果不是RGB模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # 提取圖片特徵
            features = extract_features(img)
            print(f"{features.shape=}")
            
            # 將上傳的圖片轉換為base64編碼以便在HTML中顯示
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            # 從資料庫中取得特徵數據
            conn = mysql.connect()
            cursor = conn.cursor()
            query = "SELECT id, feature FROM face_data"
            cursor.execute(query)
            data = cursor.fetchall()
            print(np.frombuffer(data[0][1], dtype=np.float32).shape)
            
            results = []
            for record in data:
                id = record[0]
                db_feature = np.frombuffer(record[1], dtype=np.float32)  # 假設feature存儲為BLOB
                distance = calculate_distance(features, db_feature)
                if distance < 0.7:
                    # query
                    source_query = "SELECT source, face_image_rgb, face_image_rgb_shape, time_stamp FROM face_data WHERE id = %s"
                    cursor.execute(source_query, (id,))
                    source_result = cursor.fetchone()
                    if source_result:
                        source = source_result[0]
                        face_image_rgb_blob = source_result[1]
                        face_image_rgb_shape = json.loads(source_result[2])
                        time_stamp = source_result[3]

                        # 將blob轉換回影像
                        face_image_rgb = np.frombuffer(face_image_rgb_blob, dtype=np.uint8).reshape(face_image_rgb_shape)
                        face_image_rgb = Image.fromarray(face_image_rgb)
                        buffered = io.BytesIO()
                        face_image_rgb.save(buffered, format="PNG")
                        face_image_rgb_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

                        # 將face_image_rgb_blob轉換為base64編碼
                        face_image_rgb = base64.b64encode(face_image_rgb_blob).decode()
                        results.append({'source': source, 'face_image_rgb': face_image_rgb_str, 'time_stamp': time_stamp})
            
            cursor.close()
            conn.close()

            # 返回並渲染HTML模板
            return render_template('results.html', uploaded_image=img_str, matches=results)
        except Exception as e:
            print(e)
            return jsonify({'error': 'Invalid image file'}), 400
    else:
        return jsonify({'error': 'Invalid file type. Only JPG and PNG are allowed.'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5556)
