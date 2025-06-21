from pydantic import BaseModel
from typing import List, Any

class AgentState(BaseModel):
    original_task: str
    sub_tasks: List[str]
    results: List[Any] = []