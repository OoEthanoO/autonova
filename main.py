from fastapi import FastAPI, Response
from pydantic import BaseModel
import json

from agent import Agent
from decomposer import Decomposer

app = FastAPI()

agent_instance = Agent()
decomposer_instance = Decomposer(agent=agent_instance)

class TaskRequest(BaseModel):
    task: str

@app.get("/")
async def root():
    return {"message": "Autonova v0.2.0 Agent"}

@app.post("/agent/execute")
async def execute_task(request: TaskRequest):
    task_description = request.task

    print(f"Received task for decomposition: {task_description}")
    sub_tasks = decomposer_instance.decompose(task_description)
    print(f"Decomposed sub-tasks: {sub_tasks}")

    response_data = {
        "original_task": task_description,
        "decomposed_sub_tasks": sub_tasks
    }

    return Response(content=json.dumps(response_data, indent=2), media_type="application/json")