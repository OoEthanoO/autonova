import datetime
import litellm
import json

class Agent:
    def __init__(self):
        self.llm_model = "ollama/gemma3:12b"

    def get_current_time(self) -> str:
        return datetime.datetime.now().isoformat()
    
    def _invoke_llm(self, messages: list) -> str:
        try:
            response = litellm.completion(
                model=self.llm_model,
                messages=messages,
                temperature=0.0
            )
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return "Error: LLM response was empty or not in expected format."
        except Exception as e:
            print(f"LiteLLM Exception: {e}")
            return f"Error invoking LLM: {e}"
        
    def search_web(self, query: str) -> str:
        prompt = f"Please provide a concise, simulated web search result for the query: '{query}'. Imagine you are a search engine providing a top snippet."
        return self._invoke_llm([{"content": prompt, "role": "user"}])

    def execute(self, task: str) -> str:
        log_data = {
            "task": task,
            "llm_decision_raw": None,
            "tool_used": None,
            "tool_input": None,
            "tool_output": None,
            "final_response": None
        }

        system_prompt = """You are an agent that must decide which tool to use to respond to a task.
Your response MUST be a single line in one of the following formats, and nothing else:
1. For current time: ACTION: current_time
2. For web searches: ACTION: search_web | QUERY: [your search query]
3. For direct answers: ACTION: answer_directly | ANSWER: [your direct answer]"""

        user_prompt = f"""Here are some examples:

TASK: "what time is it?"
Your single-line response: ACTION: current_time

TASK: "who is the president of the united states?"
Your single-line response: ACTION: search_web | QUERY: current president of the united states

TASK: "what is 2+2?"
Your single-line response: ACTION: answer_directly | ANSWER: 4

---
TASK: "{task}"
---

Your single-line response:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        llm_decision_str = self._invoke_llm(messages)
        log_data["llm_decision_raw"] = llm_decision_str

        if llm_decision_str.startswith("Error invoking LLM:") or llm_decision_str.startswith("Error: LLM response was empty"):
            log_data["tool_used"] = "llm_error_during_decision"
            log_data["final_response"] = llm_decision_str
            log_data["tool_output"] = llm_decision_str
        elif llm_decision_str.startswith("ACTION: current_time"):
            log_data["tool_used"] = "current_time"
            tool_result = self.get_current_time()
            log_data["tool_output"] = tool_result
            log_data["final_response"] = tool_result
        elif llm_decision_str.startswith("ACTION: search_web | QUERY:"):
            log_data["tool_used"] = "search_web"
            try:
                query = llm_decision_str.split("| QUERY:", 1)[1].strip()
                if not query:
                    query = task
            except IndexError:
                query = task
            log_data["tool_input"] = query
            tool_result = self.search_web(query)
            log_data["tool_output"] = tool_result
            log_data["final_response"] = tool_result
        elif llm_decision_str.startswith("ACTION: answer_directly | ANSWER:"):
            log_data["tool_used"] = "answer_directly"
            try:
                answer = llm_decision_str.split("| ANSWER:", 1)[1].strip()
                if not answer:
                    answer = self._invoke_llm([{"content": f"Please provide an answer to the task: {task}", "role": "user"}])
            except IndexError:
                answer = self._invoke_llm([{"content": f"Please provide an answer to the task: {task}", "role": "user"}])
            log_data["tool_output"] = answer
            log_data["final_response"] = answer
        else:
            log_data["tool_used"] = "fallback_direct_answer"
            print(f"Unexpected LLM decision format: {llm_decision_str}")
            direct_answer = self._invoke_llm([{"content": f"Please provide a response to the task: {task}", "role": "user"}])
            log_data["tool_output"] = direct_answer
            log_data["final_response"] = direct_answer
            if not log_data["llm_decision_raw"]:
                log_data["llm_decision_raw"] = llm_decision_str


        
        return json.dumps(log_data, indent=2)
    
if __name__ == "__main__":
    agent = Agent()
    
    print("--- Test Case 1: Current Time ---")
    time_task = "What time is it?"
    result_json_str = agent.execute(time_task)
    print(result_json_str)

    print("\n--- Test Case 2: Web Search ---")
    search_task = "What are the latest developments in AI?"
    result_json_str = agent.execute(search_task)
    print(result_json_str)

    print("\n--- Test Case 3: Direct Answer ---")
    direct_task = "What is the capital of France?"
    result_json_str = agent.execute(direct_task)
    print(result_json_str)

    print("\n--- Test Case 4: Fallback (potentially) ---")
    unknown_task = "Explain quantum entanglement simply."
    result_json_str = agent.execute(unknown_task)
    print(result_json_str)