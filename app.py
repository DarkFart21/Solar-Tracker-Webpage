from flask import Flask, jsonify, request, send_from_directory
import os, json, csv, time

app = Flask(__name__, static_folder='static')
DATA_FILE = "data.json"
CSV_FILE = "data.csv"

# Field order for both JSON and CSV
FIELDS = ["lt", "rt", "ld", "rd", "dvert", "dhoriz", "servovert", "servohori", "timestamp"]

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/data', methods=['GET'])
def get_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({}), 404

@app.route('/update', methods=['POST'])
def update_data():
    try:
        incoming = request.get_json()
        incoming["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')

        # Save JSON
        with open(DATA_FILE, 'w') as f:
            json.dump(incoming, f)

        # Append to CSV
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(incoming)

        return jsonify({"status": "saved", "data": incoming}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
