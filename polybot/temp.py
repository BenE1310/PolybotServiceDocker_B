import os

import requests
import json
from collections import Counter


def test():

    url = "http://localhost:8081/predict"
    params = {"imgName": "file_33.jpg"}  # Query parameters

    try:
        # Send the POST request
        response = requests.post(url, params=params)

        # Check response status
        if response.status_code == 200:
            print("Response Data:", response.json())
            # Save to file if needed
            with open("response_output.json", "w") as file:
                file.write(response.text)
        else:
            print(f"Failed to fetch data. HTTP Status: {response.status_code}")
            print("Response:", response.text)  # Log the server's error message
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Load JSON file
def test2():
    with open("response_output.json", "r") as file:
        data = json.load(file)

    labels = (data["labels"])

    list_x = []

    for index in labels:
        x = (index["class"])
        list_x.append(x)


    name_counts = Counter(list_x)

    full_result = "The result is:\n"

    for name, count in name_counts.items():
        full_result+= f"{name}: {count}\n"

    return full_result

test()
print(test2())