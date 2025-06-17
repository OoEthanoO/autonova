from fastapi import FastAPI
from pydantic import BaseModel

from agent import Agent

app = FastAPI()

agent_instance = Agent()

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    result: str

@app.get("/")
async def root():
    return {"message": "Autonova v0.1.0 Agent"}

@app.post("/agent/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    task_description = request.task
    execution_result = agent_instance.execute(task_description)
    return {"result": execution_result}