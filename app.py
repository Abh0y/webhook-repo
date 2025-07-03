from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

app = Flask(__name__)

# Setup MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['webhook_db']
events = db['events']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    print("✅ Webhook endpoint hit!")
    data = request.json
    print("🔁 Received JSON:", data)

    entry = {}
    if 'pusher' in data:
        action_type = 'push'
        author = data['pusher']['name']
        to_branch = data['ref'].split('/')[-1]
        timestamp = datetime.datetime.utcnow()

        entry = {
            "author": author,
            "action": action_type,
            "to_branch": to_branch,
            "timestamp": timestamp
        }

    elif 'pull_request' in data:
        pr = data['pull_request']
        author = pr['user']['login']
        from_branch = pr['head']['ref']
        to_branch = pr['base']['ref']
        timestamp = pr['created_at']
        action_type = 'merge' if pr.get('merged') else 'pull_request'

        entry = {
            "author": author,
            "action": action_type,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": timestamp
        }

    else:
        return jsonify({"message": "Unsupported event"}), 400

    try:
        result = events.insert_one(entry)
        print(f"✅ Inserted event with _id: {result.inserted_id}")
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print(f"❌ MongoDB insert failed: {e}")
        return jsonify({"message": "Database insert failed"}), 500

@app.route('/events', methods=['GET'])
def get_events():
    results = list(events.find().sort("timestamp", -1).limit(10))
    for r in results:
        r['_id'] = str(r['_id'])
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
