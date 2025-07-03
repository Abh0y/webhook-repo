from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['webhook_db']
events = db['events']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Determine event type
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

    events.insert_one(entry)
    return jsonify({"message": "Success"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    results = list(events.find().sort("timestamp", -1).limit(10))
    for r in results:
        r['_id'] = str(r['_id'])
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5000)
