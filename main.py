import streamlit as st
from groq import Groq
import json
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional
from database import TaskPlannerDB
import os

# CRITICAL: set_page_config must be the FIRST Streamlit command
st.set_page_config(
    page_title="Smart Task Planner",
    layout="wide"
)

# Load environment variables after page config
load_dotenv()
db = TaskPlannerDB()

# Initialize Groq client with error handling
def init_groq_client():
    """Initialize Groq client with proper error handling"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None, "GROQ_API_KEY not found in environment variables"
        
        # Initialize with minimal parameters for groq==0.4.2
        client = Groq(api_key=api_key)
        return client, None
    except TypeError as e:
        # Handle version-specific issues
        if "proxies" in str(e):
            return None, "Groq client version mismatch. Please run: pip install --upgrade groq"
        return None, f"TypeError: {str(e)}"
    except Exception as e:
        return None, f"Failed to initialize: {str(e)}"

client, init_error = init_groq_client()

class TaskPlannerAPI:
    """Core API for task planning logic"""
    
    def __init__(self, groq_client: Groq):
        self.client = groq_client
        self.model = "llama-3.3-70b-versatile"
    
    def generate_plan(self, goal: str, deadline: Optional[str] = None) -> Dict:
        """
        Generate a task breakdown for a given goal.
        
        Args:
            goal: The user's goal description
            deadline: Optional deadline string (e.g., "2 weeks", "1 month")
        
        Returns:
            Dict containing tasks, dependencies, and timelines
        """
        prompt = self._build_prompt(goal, deadline)
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert project manager and task planner. Break down goals into actionable tasks with realistic timelines and dependencies. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            return self._validate_and_format_plan(plan, goal)
            
        except Exception as e:
            return {
                "error": str(e),
                "goal": goal,
                "tasks": []
            }
    
    def _build_prompt(self, goal: str, deadline: Optional[str]) -> str:
        """Build the LLM prompt"""
        deadline_text = f" with a deadline of {deadline}" if deadline else ""
        
        return f"""Break down the following goal into actionable tasks{deadline_text}.

Goal: {goal}

Provide a JSON response with this structure:
{{
    "goal": "the original goal",
    "total_estimated_duration": "estimated time to complete (e.g., '2 weeks', '1 month')",
    "tasks": [
        {{
            "id": 1,
            "title": "task title",
            "description": "detailed description",
            "duration": "estimated duration (e.g., '2 days', '1 week')",
            "dependencies": [list of task IDs that must be completed first],
            "priority": "high|medium|low",
            "phase": "planning|execution|review"
        }}
    ]
}}

Guidelines:
- Create 5-15 tasks depending on goal complexity
- Be specific and actionable
- Consider realistic timelines
- Identify clear dependencies
- Group tasks into logical phases
- Prioritize tasks appropriately"""
    
    def _validate_and_format_plan(self, plan: Dict, goal: str) -> Dict:
        """Validate and format the plan response"""
        if not plan.get("tasks"):
            plan["tasks"] = []
        
        if not plan.get("goal"):
            plan["goal"] = goal
        
        # Ensure all tasks have required fields
        for i, task in enumerate(plan["tasks"]):
            task.setdefault("id", i + 1)
            task.setdefault("dependencies", [])
            task.setdefault("priority", "medium")
            task.setdefault("phase", "execution")
            task.setdefault("duration", "1-2 days")
        
        plan["generated_at"] = datetime.now().isoformat()
        return plan
    
    def analyze_critical_path(self, plan: Dict) -> List[int]:
        """Identify the critical path of task dependencies"""
        tasks = plan.get("tasks", [])
        if not tasks:
            return []
        
        # Simple critical path: tasks with most dependencies
        task_depths = {}
        
        def get_depth(task_id):
            if task_id in task_depths:
                return task_depths[task_id]
            
            task = next((t for t in tasks if t["id"] == task_id), None)
            if not task or not task.get("dependencies"):
                task_depths[task_id] = 0
                return 0
            
            max_dep_depth = max((get_depth(dep) for dep in task["dependencies"]), default=0)
            task_depths[task_id] = max_dep_depth + 1
            return task_depths[task_id]
        
        for task in tasks:
            get_depth(task["id"])
        
        # Return tasks sorted by depth (critical path)
        critical = sorted(task_depths.items(), key=lambda x: x[1], reverse=True)
        return [task_id for task_id, _ in critical[:5]]  # Top 5 critical tasks


def render_task_card(task: Dict, is_critical: bool = False):
    """Render a single task card"""
    priority_colors = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            priority_icon = priority_colors.get(task.get("priority", "medium"), "⚪")
            st.markdown(f"### {priority_icon} {task.get('title', 'Untitled Task')}")
            
            if is_critical:
                st.markdown("**critical Path Task**")
            
            st.markdown(f"*{task.get('description', 'No description')}*")
            
        with col2:
            st.markdown(f"**Duration:** {task.get('duration', 'N/A')}")
            st.markdown(f"**Phase:** {task.get('phase', 'N/A')}")
        
        if task.get("dependencies"):
            st.markdown(f"**Dependencies:** Tasks {', '.join(map(str, task['dependencies']))}")
        
        st.markdown("---")


def main():
    st.title("Smart Task Planner")
    st.markdown("Break down your goals into actionable tasks with AI-powered planning")
    
    # Check for initialization errors
    if init_error:
        st.error(f"⚠️ {init_error}")
        if "version mismatch" in init_error.lower() or "upgrade" in init_error.lower():
            st.code("pip install --upgrade groq", language="bash")
        st.info("Get your API key from: https://console.groq.com")
        st.info("Create a `.env` file in your project directory with: GROQ_API_KEY=your_key_here")
        return
    
    if client is None:
        st.error("⚠️ Failed to initialize Groq client. Please check your API key.")
        return
    
    # Initialize API
    api = TaskPlannerAPI(client)
    
    # Sidebar for input
    with st.sidebar:
        st.header("Goal Input")
        
        goal = st.text_area(
            "Describe your goal:",
            placeholder="e.g., Launch a SaaS product in 2 weeks",
            height=100
        )
        
        deadline = st.text_input(
            "Deadline (optional):",
            placeholder="e.g., 2 weeks, 1 month, 3 months"
        )
        
        generate_btn = st.button("Generate Plan", type="primary", use_container_width=True)
        
        # Saved plans section in sidebar
        st.markdown("---")
        st.subheader("Saved Plans")
        
        saved_plans = db.get_all_plans()
        if saved_plans:
            selected_plan_id = st.selectbox(
                "Load a previous plan:",
                options=[None] + [p["id"] for p in saved_plans],
                format_func=lambda x: "-- Select --" if x is None else f"ID {x}: {saved_plans[x-1]['goal'][:30]}..."
            )
            
            if selected_plan_id:
                if st.button(" Load Plan"):
                    st.session_state['current_plan_id'] = selected_plan_id
                    st.rerun()
        else:
            st.info("No saved plans yet")
        
        
    # Load plan from database if selected
    if 'current_plan_id' in st.session_state and not generate_btn:
        loaded_data = db.get_plan(st.session_state['current_plan_id'])
        if loaded_data:
            plan = loaded_data['plan']
            st.info(f"Loaded Plan ID: {loaded_data['id']} | Created: {loaded_data['created_at'][:10]}")
            
            # Display the plan (reuse the existing display code)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tasks", len(plan.get("tasks", [])))
            with col2:
                st.metric("Estimated Duration", plan.get("total_estimated_duration", "N/A"))
            with col3:
                high_priority = sum(1 for t in plan.get("tasks", []) if t.get("priority") == "high")
                st.metric("High Priority Tasks", high_priority)
            
            critical_path = api.analyze_critical_path(plan)
            
            tab1, tab2 = st.tabs(["All Tasks", "JSON View"])
            
            with tab1:
                st.subheader("Task Breakdown")
                for task in plan.get("tasks", []):
                    render_task_card(task, task.get("id") in critical_path)
            
            
           
                
    # Main content area
    if generate_btn and goal:
        with st.spinner(" Analyzing your goal and creating a plan..."):
            plan = api.generate_plan(goal, deadline if deadline else None)
    
        if plan.get("error"):
            st.error(f"Error generating plan: {plan['error']}")
            return
        
        # Save to database
        plan_id = db.save_plan(goal, deadline, plan)
        st.session_state['current_plan_id'] = plan_id
        st.success(f"Plan saved! ID: {plan_id}")

        # Display plan summary
        st.success("Plan generated successfully!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tasks", len(plan.get("tasks", [])))
        with col2:
            st.metric("Estimated Duration", plan.get("total_estimated_duration", "N/A"))
        with col3:
            high_priority = sum(1 for t in plan.get("tasks", []) if t.get("priority") == "high")
            st.metric("High Priority Tasks", high_priority)
        
        # Analyze critical path
        critical_path = api.analyze_critical_path(plan)
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["All Tasks", "JSON View"])
        
        with tab1:
            st.subheader("Task Breakdown")
            for task in plan.get("tasks", []):
                render_task_card(task, task.get("id") in critical_path)
        
        
        with tab2:
            st.json(plan)
            
            # Download button
            json_str = json.dumps(plan, indent=2)
            st.download_button(
                label="📥 Download Plan as JSON",
                data=json_str,
                file_name=f"task_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    elif generate_btn:
        st.warning("Please enter a goal to generate a plan.")
    
    else:
        
        st.markdown("### Example Goals:")
        examples = [
            "Launch a SaaS product in 2 weeks",
            "Organize a wedding in 6 months",
            "Learn machine learning in 3 months",
            "Build a mobile app MVP in 1 month",
            "Write and publish a book in 1 year"
        ]
        
        for example in examples:
            st.markdown(f"- {example}")


if __name__ == "__main__":
    main()