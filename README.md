🚀 FocusFlow AI – Smart Task Management System

FocusFlow AI is a modern, full-stack productivity application designed to help users efficiently manage daily tasks with an intelligent, minimal, and visually engaging interface.

It combines task tracking, calendar-based planning, and basic AI-driven insights to enhance productivity and focus.

📌 Features
✅ Create, update, delete tasks
📅 Assign tasks to specific dates
📌 Pin important tasks
✔️ Mark tasks as completed
🧠 AI-based productivity insights (basic logic-driven)
📊 Real-time task statistics (Total / Pending / Completed)
🗓️ Interactive calendar and timeline navigation
🎨 Modern glassmorphism UI design
🔄 Drag-and-drop task reordering
🏷️ Tag-based task categorization (e.g., #work, #study)
🛠️ Tech Stack
Frontend
HTML5, CSS3 (Custom UI)
JavaScript (Vanilla JS)
SortableJS (Drag & Drop)
Lucide Icons (Icons)
Backend
Python
Flask (REST API)
Flask-PyMongo
Database
MongoDB
Other Tools
Git
GitHub
dotenv
🏗️ Project Architecture
Frontend (HTML/CSS/JS)
        ↓
 REST API (Flask Backend)
        ↓
 MongoDB Database
⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/focusflow-ai.git
cd focusflow-ai
2️⃣ Create virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
3️⃣ Install dependencies
pip install -r requirements.txt
4️⃣ Setup environment variables

Create a .env file:

MONGO_URI=your_mongodb_connection_string
5️⃣ Run backend server
python app.py

Server runs on:

http://127.0.0.1:5000
6️⃣ Run frontend

Open index.html using Live Server (VS Code) or:

python -m http.server 5500

Then open:

http://localhost:5500
🔌 API Endpoints
Method	Endpoint	Description
GET	/tasks	Get all tasks
POST	/tasks	Add new task
PATCH	/tasks/<id>	Update task
DELETE	/tasks/<id>	Delete task
🧠 AI Insight Feature

FocusFlow AI includes a lightweight rule-based AI system that:

Analyzes daily task completion
Tracks productivity patterns
Generates motivational insights dynamically
🔐 Security Note
.env file is excluded using .gitignore
MongoDB credentials are not exposed publicly
Environment variables are used for secure configuration
📸 UI Preview

Add screenshots here (recommended for GitHub)

🚀 Future Enhancements
🤖 Advanced AI recommendations (ML-based)
📱 Mobile responsive improvements
🔔 Notifications & reminders
👤 User authentication (JWT)
☁️ Cloud deployment (Render / Vercel)
📈 Productivity analytics dashboard
👨‍💻 Author

Ankith Raj
B.Tech Final Year Student
Aspiring AI/ML Engineer

⭐ Contribution

Contributions are welcome! Feel free to fork this repository and submit pull requests.

📜 License

This project is open-source and available under the MIT License.

💡 Final Note

This project demonstrates full-stack development skills including:

Frontend UI/UX design
Backend API development
Database integration
Debugging and real-world problem solving
