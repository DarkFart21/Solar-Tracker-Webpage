from flask import Flask, jsonify, send_from_directory
import os
import json
import requests
import csv
from datetime import datetime

app = Flask(__name__, static_folder='static')
DATA_FILE = "data.json"
CSV_FILE = "data_log.csv"
BLYNK_TOKEN = os.environ.get("BLYNK_AUTH_TOKEN")

# Map friendly names to Blynk virtual pins
VIRTUAL_PINS = {
    "lt": "V2",
    "rt": "V3",
    "ld": "V4",
    "rd": "V5",
    "dvert": "V6",
    "dhoriz": "V7",
    "servovert": "V8",
    "servohori": "V9"
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
    if not BLYNK_TOKEN:
        return jsonify({"error": "Missing Blynk token"}), 500

    data = {}
    for key, pin in VIRTUAL_PINS.items():
        try:
            url = f"https://sgp1.blynk.cloud/external/api/get?token={BLYNK_TOKEN}&{pin}"
            res = requests.get(url)
            res.raise_for_status()
            value = res.text
            data[key] = int(value) if value.isdigit() else value
        except Exception as e:
            data[key] = None  # Or log error if needed

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

    append_to_csv(data)

    return jsonify({"status": "updated", "data": data}), 200

@app.route('/download', methods=['GET'])
def download_csv():
    if os.path.exists(CSV_FILE):
        return send_from_directory('.', CSV_FILE, as_attachment=True)
    return jsonify({"error": "CSV not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
