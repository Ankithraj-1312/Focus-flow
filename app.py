from datetime import datetime, timezone, timedelta
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

# ✅ EXPLICIT DATABASE
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

        # Ensure assignedDate is always set and in YYYY-MM-DD format
        assigned_date = data.get('assignedDate')
        if not assigned_date:
            assigned_date = datetime.now().strftime('%Y-%m-%d')
        else:
            # If assigned_date is a datetime, convert to string
            if isinstance(assigned_date, datetime):
                assigned_date = assigned_date.strftime('%Y-%m-%d')

        task = {
            "text": data['text'],
            "assignedDate": assigned_date,
            "completed": False,
            "pinned": False,
            "category": data.get('category', 'General'),
            "priority": data.get('priority', 'Medium'),
            "createdAt": datetime.now(timezone.utc)
        }

        print("📦 Task to insert:", task)

        result = db.tasks.insert_one(task)

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


# 🔹 AI ANALYZE ENDPOINT - Week/Month/Year Reports
@app.route('/ai/analyze', methods=['POST'])
def analyze_tasks():
    try:
        data = request.get_json()
        time_range = data.get('timeRange', 'week')  # week, month, or year

        if not time_range in ['week', 'month', 'year']:
            return jsonify({"error": "Invalid timeRange. Use: week, month, or year"}), 400

        # Calculate date range
        today = datetime.now()

        if time_range == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif time_range == 'month':
            start_date = datetime(today.year, today.month, 1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(
                    today.year, today.month + 1, 1) - timedelta(days=1)
        else:  # year
            start_date = datetime(today.year, 1, 1)
            end_date = datetime(today.year, 12, 31)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        # Query tasks in date range
        tasks = list(db.tasks.find({
            "assignedDate": {
                "$gte": start_str,
                "$lte": end_str
            }
        }))

        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('completed', False)])
        pending_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks *
                           100) if total_tasks > 0 else 0

        # Count tasks by category
        work_tasks = len(
            [t for t in tasks if '#work' in t.get('text', '').lower()])
        study_tasks = len(
            [t for t in tasks if '#study' in t.get('text', '').lower()])

        # Generate AI insights
        insights = generate_insights(
            completion_rate, total_tasks, work_tasks, study_tasks)

        return jsonify({
            "timeRange": time_range,
            "dateRange": {
                "start": start_str,
                "end": end_str
            },
            "statistics": {
                "totalTasks": total_tasks,
                "completedTasks": completed_tasks,
                "pendingTasks": pending_tasks,
                "completionRate": round(completion_rate, 2)
            },
            "categoryBreakdown": {
                "work": {
                    "count": work_tasks,
                    "percentage": round((work_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0
                },
                "study": {
                    "count": study_tasks,
                    "percentage": round((study_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0
                }
            },
            "insights": insights
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# 🔹 AI INSIGHTS GENERATOR
def generate_insights(completion_rate, total_tasks, work_tasks, study_tasks):
    """Generate AI-powered insights based on task data"""
    insights = []

    # Completion rate insights
    if completion_rate >= 80:
        insights.append(
            "🎯 Excellent productivity! You're crushing your goals!")
    elif completion_rate >= 60:
        insights.append("💪 Good progress! Keep the momentum going.")
    elif completion_rate >= 40:
        insights.append("📍 Moderate performance. Time to focus on priorities.")
    else:
        insights.append(
            "⚠️ Low completion rate. Break tasks into smaller chunks.")

    # Workload analysis
    avg_daily = total_tasks / 7 if total_tasks > 0 else 0
    if avg_daily > 10:
        insights.append(
            "📌 You're taking on a lot. Consider if all tasks are essential.")
    elif avg_daily < 3 and total_tasks > 0:
        insights.append(
            "💡 You have capacity. Push yourself to add more meaningful goals.")

    # Category analysis
    total = work_tasks + study_tasks
    if total > 0:
        if work_tasks > 0:
            work_pct = (work_tasks / total) * 100
            insights.append(f"💼 Work tasks: {work_tasks} ({round(work_pct)}%)")
        if study_tasks > 0:
            study_pct = (study_tasks / total) * 100
            insights.append(
                f"📚 Study tasks: {study_tasks} ({round(study_pct)}%)")

    return insights


# 🔹 AI SUGGEST TASKS ENDPOINT
@app.route('/ai/suggest', methods=['POST'])
def suggest_tasks():
    try:
        data = request.get_json()
        date = data.get('date')

        if not date:
            return jsonify({"error": "Date is required"}), 400

        # Get previous 7 days tasks
        target_date = datetime.strptime(date, '%Y-%m-%d')
        week_ago = (target_date - timedelta(days=7)).strftime('%Y-%m-%d')

        prev_tasks = list(db.tasks.find({
            "assignedDate": {
                "$gte": week_ago,
                "$lt": date
            }
        }))

        # Analyze recurring patterns
        task_texts = [t.get('text', '') for t in prev_tasks]
        work_tasks = [t for t in task_texts if '#work' in t.lower()]
        study_tasks = [t for t in task_texts if '#study' in t.lower()]

        suggestions = []

        # Generate suggestions based on patterns
        if len(work_tasks) > 0:
            suggestions.append("📋 Review pending work items")
            suggestions.append("💼 Schedule important meetings")

        if len(study_tasks) > 0:
            suggestions.append("📚 Continue chapter reading")
            suggestions.append("✍️ Review notes")

        if len(prev_tasks) > 0:
            suggestions.append("🔄 Check off-hold tasks")

        return jsonify({
            "date": date,
            "suggestions": suggestions[:3],
            "reasoning": "Based on your recurring task patterns"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 GET ALL TASKS (For optimization - frontend reports)
@app.route('/tasks/all', methods=['GET'])
def get_all_tasks():
    try:
        tasks = list(db.tasks.find().sort([
            ("pinned", -1),
            ("completed", 1),
            ("createdAt", -1)
        ]))

        return jsonify([format_task(task) for task in tasks]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 GET TASKS BY DATE RANGE (For optimization)
@app.route('/tasks/range', methods=['GET'])
def get_tasks_by_range():
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')

        if not start_date or not end_date:
            return jsonify({"error": "start and end dates are required"}), 400

        tasks = list(db.tasks.find({
            "assignedDate": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort([
            ("pinned", -1),
            ("completed", 1),
            ("createdAt", -1)
        ]))

        return jsonify([format_task(task) for task in tasks]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 TASK STATISTICS
@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        date = request.args.get('date')

        if date:
            tasks = list(db.tasks.find({"assignedDate": date}))
        else:
            tasks = list(db.tasks.find())

        total = len(tasks)
        completed = len([t for t in tasks if t.get('completed', False)])
        pending = total - completed

        return jsonify({
            "date": date,
            "totalTasks": total,
            "completedTasks": completed,
            "pendingTasks": pending,
            "completionRate": round((completed / total * 100), 2) if total > 0 else 0
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 HEALTH CHECK
@app.route('/')
def home():
    return jsonify({"message": "FocusFlow AI Backend Running 🚀"})


if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
