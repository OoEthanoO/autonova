from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel
import json

from database import get_db_connection
from graph import app as graph_app, AgentState

app = FastAPI()

class TaskRequest(BaseModel):
    task: str

@app.get("/")
async def root():
    return {"message": "Autonova v0.3.0 Agent"}

@app.post("/agent/execute")
async def execute_task(request: TaskRequest):
    task_description = request.task
    graph_input = {"original_task": task_description}

    final_state = None
    task_id = None
    conn = None

    try:
        print(f"Invoking graph for task: {task_description}")
        final_state = graph_app.invoke(graph_input)
        print("Graph execution complete.")

        conn = get_db_connection()
        if conn is None:
            print("Warning: Could not connect to the database to log results.")
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (original_task, sub_tasks, status)
                    VALUES (%s, %s, %s) RETURNING id
                    """,
                    (
                        final_state.get('original_task'),
                        json.dumps(final_state.get('results', [])),
                        'SUCCESS'
                    )
                )
                task_id = cur.fetchone()[0]
                conn.commit()
                print(f"Task {task_id} and results logged to database.")

    except Exception as e:
        print(f"An error occurred during graph execution or database logging: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute task graph: {e}")
    finally:
        if conn:
            conn.close()

    response_data = {
        "task_id": task_id,
        "final_state": final_state
    }

    return Response(content=json.dumps(response_data, indent=2), media_type="application/json")