import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict

class TaskPlannerDB:
    """Simple SQLite database for storing task plans"""
    
    def __init__(self, db_path: str = "task_planner.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                deadline TEXT,
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_plan(self, goal: str, deadline: Optional[str], plan: Dict) -> int:
        """Save a generated plan and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO plans (goal, deadline, plan_json, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            goal,
            deadline,
            json.dumps(plan),
            datetime.now().isoformat()
        ))
        
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return plan_id
    
    def get_plan(self, plan_id: int) -> Optional[Dict]:
        """Retrieve a plan by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, goal, deadline, plan_json, created_at
            FROM plans WHERE id = ?
        """, (plan_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "goal": row[1],
                "deadline": row[2],
                "plan": json.loads(row[3]),
                "created_at": row[4]
            }
        return None
    
    def get_all_plans(self) -> List[Dict]:
        """Get all saved plans"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, goal, deadline, created_at
            FROM plans
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "goal": row[1],
                "deadline": row[2],
                "created_at": row[3]
            }
            for row in rows
        ]
    
    def delete_plan(self, plan_id: int) -> bool:
        """Delete a plan by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted