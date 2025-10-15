Smart Task Planner
Overview
Smart Task Planner employs AI to break down complex goals into structured, manageable tasks automatically. With the use of Groq's LLaMA 3.3 model, it parses your goals and devises in-depth plans with dependencies, timelines, and priorities.


Features

LLM Powered Task Breakdown - Automatically produces detailed task plans based on your goals
Dependency Tracking - Determines which tasks rely on others
Critical Paths - Identifies the most critical activities to ensure project success
Timeline Estimation - Gives realistic duration values for all activities
Priority Assignment - Automatically assigns tasks to high/medium/low priority classes
Plan Persistence - Save and reload existing plans from a local database
REST API - Backend API for integration with other tools
Simple Streamlit web interface

Architecture
The project has three main parts:

Frontend (main.py) - Streamlit web interface
Backend API (backend.py) - FastAPI REST service
Database (database.py) - SQLite storage layer

Getting Started/ Running the file
Clone the repository

Install the dependencies:
pip install -r requirements.txt

Create a .env file in the project root and set your Groq API key:
GROQ_API_KEY=your_api_key_here


Running the Application:
You have two choices for executing the application.
Option 1: Streamlit UI Only
Just execute:
streamlit run main.py

Option 2: With Backend API
Open two terminal windows. In the first terminal, execute the backend:
uvicorn backend:app --reload

In the second terminal, execute the frontend:
streamlit run main.py
The app will be opened in your browser at http://localhost:8501.

Usage
Using the Web Interface
The interface is simple. Type in your objective in the text field on the sidebar. For instance, you can type "Launch a mobile app within 3 months" or "Host a virtual conference with 500+ attendees."
You may optionally include a deadline such as "2 weeks" or "1 month" to enable the AI to plan accordingly.
Click "Generate Plan" and the AI will break down your goal into a structured task list. Each task has a description, estimated time, dependency on other tasks, and a priority level.
Tasks identified as "Critical Path" are the most critical tasks that might cause your whole project to be delayed if not finished on time.
All plans are saved automatically to the database. You can load saved plans from the dropdown in the sidebar.

Using the API
The application also exposes a REST API for programmatic access.
To create a plan:
curl -X POST "http://127.0.0.1:8000/generate-plan" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Launch a SaaS product", "deadline": "2 months"}'
To get all saved plans:
curl "http://127.0.0.1:8000/plans"
To get a particular plan by ID:
curl "http://127.0.0.1:8000/plans/1"
How It Works
When you enter a goal, the system forwards it to Groq's LLaMA 3.3 model with a request to decompose it into organized tasks. The AI processes the goal and creates tasks that have realistic timelines and interdependencies.
The program then analyzes this information to determine the critical path - the series of tasks that are most vital for project success. Tasks are divided into phases (planning, execution, review) and ranked based on priority.
All data is stored in a local SQLite database, so you can return to your plans later and monitor your progress.


Database
The app stores data in SQLite. The task_planner.db database file is automatically created when you run the app for the first time. No further setup is required.

Dependencies :
streamlit>=1.28.0
groq>=0.4.2
python-dotenv>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
requests>=2.31.0

All of these dependencies are in the requirements.txt file and can be easily installed via pip.


Understanding Task Phases

Planning - Preliminary research and preparation work
Execution - Active implementation work
Review - Quality control and review work

Priority Levels
High - Urgent tasks that need to be done first
Medium - Essential but not urgent tasks
Low - Nice-to-haves or follow-up tasks


Critical Path Tasks
These are tasks with the most dependencies or dependencies for numerous tasks. Critical path task delays will probably delay the project as a whole.