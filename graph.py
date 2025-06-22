from pydantic import BaseModel
from typing import List, Any
import json

from langgraph.graph import StateGraph, END

from agent import Agent
from decomposer import Decomposer

class AgentState(BaseModel):
    original_task: str
    sub_tasks: List[str] = []
    results: List[Any] = []

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
    
    remaining_sub_tasks = sub_tasks.copy()
    current_task = remaining_sub_tasks.pop(0)
    print(f"Executing sub-task: {current_task}")

    result = agent_instance.execute(current_task)

    return {
        "sub_tasks": remaining_sub_tasks,
        "results": state.results + [result]
    }

def should_continue(state: AgentState) -> str:
    print("--- Conditional Edge: Should Continue? ---")
    if state.sub_tasks:
        print("Decision: Yes, continue to execute_step.")
        return "execute_step"
    else:
        print("Decision: No, end the workflow.")
        return END
    
workflow = StateGraph(AgentState)

workflow.add_node("decompose_task", decompose_task)
workflow.add_node("execute_step", execute_step)

workflow.set_entry_point("decompose_task")

workflow.add_edge("decompose_task", "execute_step")
workflow.add_conditional_edges(
    "execute_step",
    should_continue,
    {
        "execute_step": "execute_step",
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