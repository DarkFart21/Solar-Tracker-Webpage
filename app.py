from flask import Flask, jsonify, send_from_directory, request
import os
import json
import requests
import csv
from datetime import datetime

app = Flask(__name__, static_folder='static')
DATA_FILE = "data.json"
CSV_FILE = "data_log.csv"

# ThingSpeak config
THINGSPEAK_CHANNEL_ID = os.environ.get("THINGSPEAK_CHANNEL_ID")
THINGSPEAK_API_KEY = os.environ.get("THINGSPEAK_READ_API_KEY")  # Optional if public

# 🆕 New channel for LED status
THINGSPEAK_LED_URL = "https://api.thingspeak.com/channels/YOUR_LED_CHANNEL_ID/fields/1.json?results=1"


# Map local variable names to ThingSpeak field names
FIELD_MAP = {
    "lt": "field1",
    "rt": "field2",
    "ld": "field3",
    "rd": "field4",
    "dvert": "field5",
    "dhoriz": "field6",
    "servovert": "field7",
    "servohori": "field8"
}

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/data', methods=['GET'])
def get_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({}), 404

@app.route("/led")
def get_led_status():
    try:
        response = requests.get(LED_API_URL)
        response.raise_for_status()
        data = response.json()

        # Get the most recent LED value from field1 (you can adjust if using another field)
        last_entry = data["feeds"][-1]
        led_value = last_entry["field1"]

        # Convert to ON/OFF (assuming 1 = ON, 0 = OFF)
        led_status = "ON" if led_value == "1" else "OFF"

        return jsonify({"led": led_status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()


def append_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['timestamp'] + list(data.keys()))
        if not file_exists:
            writer.writeheader()
        row = {"timestamp": datetime.now().isoformat(), **data}
        writer.writerow(row)

@app.route('/update', methods=['POST'])
def update_data():
    if not THINGSPEAK_CHANNEL_ID:
        return jsonify({"error": "Missing ThingSpeak channel ID"}), 500

    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json"
    params = {"api_key": THINGSPEAK_API_KEY} if THINGSPEAK_API_KEY else {}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        feed = response.json()

        data = {}
        for key, field in FIELD_MAP.items():
            raw_value = feed.get(field)
            try:
                data[key] = int(raw_value) if raw_value is not None and raw_value.isdigit() else raw_value
            except:
                data[key] = None

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)

        append_to_csv(data)

        return jsonify({"status": "updated", "data": data}), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch data from ThingSpeak", "details": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_csv():
    if os.path.exists(CSV_FILE):
        return send_from_directory('.', CSV_FILE, as_attachment=True)
    return jsonify({"error": "CSV not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
