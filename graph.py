from pydantic import BaseModel
from typing import List, Any
import json
import time

from langgraph.graph import StateGraph, END

from agent import Agent
from decomposer import Decomposer

class AgentState(BaseModel):
    original_task: str
    sub_tasks: List[str] = []
    results: List[Any] = []
    max_retries: int = 3
    retries: int = 0
    error: str | None = None

agent_instance = Agent()
decomposer_instance = Decomposer(agent=agent_instance)

def decompose_task(state: AgentState) -> dict:
    print("--- Node: Decompose Task ---")
    original_task = state.original_task
    if not original_task:
        raise ValueError("Original task is missing from the state.")
    
    sub_tasks = decomposer_instance.decompose(original_task)
    print(f"Decomposed into sub-tasks: {sub_tasks}")

    return {"sub_tasks": sub_tasks}

def execute_step(state: AgentState) -> dict:
    print("--- Node: Execute Step ---")
    sub_tasks = state.sub_tasks
    if not sub_tasks:
        print("No more sub-tasks to execute.")
        return {}
    
    current_task = sub_tasks[0]
    print(f"Executing sub-task: {current_task}")

    try:
        result = agent_instance.execute(current_task)
        print(f"Sub-task '{current_task}' executed successfully.")

        remaining_sub_tasks = sub_tasks[1:]
        return {
            "sub_tasks": remaining_sub_tasks,
            "results": state.results + [result],
            "error": None,
            "retries": 0
        }
    except Exception as e:
        print(f"Error executing sub-task '{current_task}': {e}")

        return {
            "error": str(e),
            "retries": state.retries + 1,
        }
    
def handle_error(state: AgentState) -> dict:
    print("--- Node: Handle Error ---")
    if state.retries >= state.max_retries:
        print(f"Task failed permanently after {state.retries} attempts.")
        return {}
    
    print(f"Attempt {state.retries}/{state.max_retries}. Retrying after a delay...")
    time.sleep(2)

    return {"error": None}

def should_continue(state: AgentState) -> str:
    print("--- Conditional Edge: Should Continue? ---")
    if state.error:
        print("Decision: Error detected, routing to handle_error.")
        return "handle_error"

    if not state.sub_tasks:
        print("Decision: No more tasks, ending the workflow.")
        return END

    print("Decision: Continue to execute_step.")
    return "execute_step"
    
workflow = StateGraph(AgentState)

workflow.add_node("decompose_task", decompose_task)
workflow.add_node("execute_step", execute_step)
workflow.add_node("handle_error", handle_error)

workflow.set_entry_point("decompose_task")

workflow.add_edge("decompose_task", "execute_step")
workflow.add_edge("handle_error", "execute_step")

workflow.add_conditional_edges(
    "execute_step",
    should_continue,
    {
        "execute_step": "execute_step",
        "handle_error": "handle_error",
        END: END
    }
)

app = workflow.compile()

if __name__ == "__main__":
    print("--- Testing Graph Execution ---")

    inputs = {"original_task": "What is the current time, and what are the latest developments in AI?"}

    final_state = app.invoke(inputs)

    print("\n--- Final Graph State ---")
    print(json.dumps(final_state, indent=2))