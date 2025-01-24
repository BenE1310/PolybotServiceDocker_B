import boto3
import telebot
from loguru import logger
import os
import time
from telebot.types import InputFile
import requests
import json
from collections import Counter


S3_BUCKET_NAME = "bene1310"
S3_REGION = "eu-west-1"


class Bot:

    def __init__(self, token, bot_app_url):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)
        self.list_of_images = []
        # self.caption_equal_concat = False
        self.concat_proof = []

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        self.telegram_bot_client.set_webhook(url=f'{bot_app_url}/{token}/', timeout=60)

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    def is_current_msg_photo(self, msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads all photos sent to the Bot to the 'photos' directory and returns a list of file paths.
        :return: List of file paths
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        # self.list_of_images.append(file_info.file_path)
        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        print(img_path)
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class QuoteBot(Bot):
    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if msg["text"] != 'Please don\'t quote me':
            self.send_text_with_quote(msg['chat']['id'], msg["text"], quoted_msg_id=msg["message_id"])


class ObjectDetectionBot(Bot):
    def __init__(self, token, bot_app_url):
        super().__init__(token, bot_app_url)
        self.s3_client = boto3.client('s3')
        self.full_result = "Detected objects:\n"

    def upload_to_s3(self, file_path, s3_key):
        try:
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=S3_BUCKET_NAME,
                Key=s3_key
            )
            file_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
            return file_url
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None


    def http_request_to_yolo5_service(self, s3_key):
        url = "http://yolo5-service:8081/predict"

        params = {"imgName": s3_key}  # Query parameters

        output_file = os.path.join(os.getcwd(), "response_output.json")
        print(f"Output File Path: {output_file}")  # Debug statement

        try:
            # Send the POST request
            response = requests.post(url, params=params)

            # Debugging HTTP response
            print(f"HTTP Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")

            # Check response status
            if response.status_code == 200:
                print("Response Data:", response.json())
                # Save to the current working directory
                with open(output_file, "w") as file:
                    file.write(response.text)
                print(f"File successfully written to: {output_file}")
            else:
                print(f"Failed to fetch data. HTTP Status: {response.status_code}")
                print("Response:", response.text)  # Log the server's error message
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the HTTP request: {e}")
        except OSError as e:
            print(f"An error occurred while writing the file: {e}")



    def reading_from_json(self):
        with open("response_output.json", "r") as file:
            data = json.load(file)

        labels = (data["labels"])

        list_x = []

        for index in labels:
            x = (index["class"])
            list_x.append(x)

        name_counts = Counter(list_x)

        for name, count in name_counts.items():
            self.full_result += f"{name}: {count}\n"


    def handle_message(self, msg):
        """
        Orchestrate the multistep process.
        """
        logger.info(f"Incoming message: {msg}")

        if self.is_current_msg_photo(msg):
            try:
                # Step 1: Download user photo
                photo_path = self.download_user_photo(msg)

                # Step 2: Upload to S3
                s3_key = f"{photo_path.split('/')[-1]}"
                s3_url = self.upload_to_s3(photo_path, s3_key)
                if not s3_url:
                    self.send_text(msg['chat']['id'], "Failed to upload photo to S3.")
                    return

                # Step 3: HTTP request to yolo5 service
                self.http_request_to_yolo5_service(s3_key)
                self.reading_from_json()

                # Step 4: Send the final product to the user
                self.send_text(msg['chat']['id'], self.full_result)

                # Reset self.full_result
                self.full_result = "Detected objects:\n"

                # Step 5: Clean up the photo
                os.remove(photo_path)

            except Exception as e:
                logger.error(f"Error in handle_message: {e}")
                self.send_text(msg['chat']['id'], "An error occurred during processing.")
















