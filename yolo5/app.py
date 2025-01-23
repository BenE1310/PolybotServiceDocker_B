
import time
from pathlib import Path
from flask import Flask, request
from detect import run
import uuid
import yaml
from loguru import logger
import os
import boto3
from pymongo import MongoClient

images_bucket = os.environ['BUCKET_NAME']

# S3 client setup
s3_client = boto3.client('s3')

# MongoDB client setup
mongo_client = MongoClient(os.environ['MONGO_URI'])
db = mongo_client['yolo_predictions']
collection = db['predictions']

with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    prediction_id = str(uuid.uuid4())
    logger.info(f'prediction: {prediction_id}. start processing')

    img_name = request.args.get('imgName')

    # Download the image from S3
    local_folder = 'static/images'
    os.makedirs(local_folder, exist_ok=True)
    original_img_path = os.path.join(local_folder, img_name)
    s3_client.download_file(images_bucket, img_name, original_img_path)
    logger.info(f'prediction: {prediction_id}/{original_img_path}. Download img completed')

    # Predict objects in the image
    run(
        weights='yolov5s.pt',
        data='data/coco128.yaml',
        source=original_img_path,
        project='static/data',
        name=prediction_id,
        save_txt=True
    )
    logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

    # This is the path for the predicted image with labels
    predicted_img_path = Path(f'static/data/{prediction_id}/{Path(original_img_path).name}')

    # Upload the predicted image to S3
    predicted_img_s3_path = f'predicted/{prediction_id}_{Path(original_img_path).name}'
    s3_client.upload_file(str(predicted_img_path), images_bucket, predicted_img_s3_path)

    # Parse prediction labels and create a summary
    pred_summary_path = Path(f'static/data/{prediction_id}/labels/{img_name.split(".")[0]}.txt')
    if pred_summary_path.exists():
        with open(pred_summary_path) as f:
            labels = f.read().splitlines()
            labels = [line.split(' ') for line in labels]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4]),
            } for l in labels]

        logger.info(f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

        prediction_summary = {
            'prediction_id': prediction_id,
            'original_img_path': original_img_path,
            'predicted_img_path': predicted_img_s3_path,
            'labels': labels,
            'time': time.time()
        }

        # Store the prediction_summary in MongoDB
        result = collection.insert_one(prediction_summary)
        prediction_summary['_id'] = str(result.inserted_id)
        return prediction_summary
    else:
        return f'prediction: {prediction_id}/{original_img_path}. prediction result not found', 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
