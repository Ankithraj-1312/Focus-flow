from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

# 🔹 Load env
load_dotenv()
print("MONGO_URI:", os.getenv("MONGO_URI"))

app = Flask(__name__)
CORS(app)

# 🔐 Mongo config
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# ✅ EXPLICIT DATABASE (IMPORTANT FIX)
db = mongo.cx["focusflow_db"]

# 🔍 Test connection
try:
    mongo.cx.server_info()
    print("✅ MongoDB Connected Successfully")
    print("DB:", db)
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)


# 🔹 Helper
def format_task(task):
    return {
        "id": str(task["_id"]),
        "text": task.get("text"),
        "assignedDate": task.get("assignedDate"),
        "dueDate": task.get("dueDate"),
        "completed": task.get("completed", False),
        "pinned": task.get("pinned", False),
        "category": task.get("category", "General"),
        "priority": task.get("priority", "Medium"),
        "createdAt": task.get("createdAt")
    }


# 🔹 GET TASKS
@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        date = request.args.get('date')
        keyword = request.args.get('search')

        query = {}

        if date:
            query["assignedDate"] = date

        if keyword:
            query["text"] = {"$regex": keyword, "$options": "i"}

        tasks = list(
            db.tasks.find(query).sort([
                ("pinned", -1),
                ("completed", 1),
                ("createdAt", -1)
            ])
        )

        return jsonify([format_task(task) for task in tasks]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 ADD TASK
@app.route('/tasks', methods=['POST'])
def add_task():
    try:
        data = request.get_json()
        print("📥 Received data:", data)

        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        if not data.get('text'):
            return jsonify({"error": "Task text is required"}), 400

        task = {
            "text": data['text'],
            "assignedDate": data.get('assignedDate'),
            "completed": False,
            "pinned": False,
            "createdAt": datetime.now(timezone.utc)
        }

        print("📦 Task to insert:", task)

        result = db.tasks.insert_one(task)  # ✅ FIXED

        print("✅ Inserted ID:", result.inserted_id)

        return jsonify({
            "message": "Task created",
            "id": str(result.inserted_id)
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 🔹 UPDATE TASK
@app.route('/tasks/<id>', methods=['PATCH'])
def update_task(id):
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No update data provided"}), 400

        allowed_fields = [
            "text", "assignedDate", "dueDate",
            "completed", "pinned", "category", "priority"
        ]

        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        db.tasks.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        updated_task = db.tasks.find_one({"_id": ObjectId(id)})

        if not updated_task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({
            "message": "Task updated",
            "task": format_task(updated_task)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 DELETE TASK
@app.route('/tasks/<id>', methods=['DELETE'])
def delete_task(id):
    try:
        result = db.tasks.delete_one({"_id": ObjectId(id)})

        if result.deleted_count == 0:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"message": "Task deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 HEALTH CHECK
@app.route('/')
def home():
    return jsonify({"message": "To-Do Backend Running 🚀"})


if __name__ == '__main__':
    import os

app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
