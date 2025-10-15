from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from database import TaskPlannerDB
from datetime import datetime
from dotenv import load_dotenv
import os
import json

from main import TaskPlannerAPI  # Reuse your logic class

load_dotenv()
app = FastAPI(title="Smart Task Planner API")

# Initialize database
db = TaskPlannerDB()

# Initialize Groq client
def init_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not found in environment")
    return Groq(api_key=api_key)

client = init_groq_client()
api = TaskPlannerAPI(client)

# Input model
class GoalInput(BaseModel):
    goal: str
    deadline: str | None = None

@app.post("/generate-plan")
def generate_plan(data: GoalInput):
    """
    Generate a task plan for a given goal and optional deadline.
    """
    try:
        plan = api.generate_plan(data.goal, data.deadline)
        
        if "error" in plan:
            raise HTTPException(status_code=500, detail=plan["error"])
        
        plan_id = db.save_plan(data.goal, data.deadline, plan)
        return {
            "message": "Plan generated successfully",
            "plan_id": plan_id,
            "plan": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/plans")
def get_all_plans():
    """Fetch all saved plans"""
    return db.get_all_plans()


@app.get("/plans/{plan_id}")
def get_plan(plan_id: int):
    """Fetch a single plan by ID"""
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan
