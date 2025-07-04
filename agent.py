import datetime
import litellm
import json
from duckduckgo_search import DDGS

class Agent:
    def __init__(self):
        self.llm_model = "ollama/gemma3:12b-it-q4_K_M"

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
        
    def synthesize_final_answer(self, original_task: str, history: list) -> str:
        context_str = "You have access to the results of the steps executed to address the original user request. Your task is to synthesize these results into a single, coherent final answer for the user.\n\n"
        context_str += f"ORIGINAL REQUEST: \"{original_task}\"\n\n"
        context_str += "RESULTS OF EXECUTED STEPS:\n"
        formatted_history = "\n---\n".join([json.dumps(item, indent=2) for item in history])
        context_str += formatted_history + "\n\n--\n"

        system_prompt = "You are a helpful assistant. Based on the original request and the collected results from a series of steps, provide a comprehensive and user-friendly final answer."
        user_prompt = f"{context_str}Please provide the final, synthesized answer to the user."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self._invoke_llm(messages)
        
    def search_web(self, query: str) -> str:
        print(f"Performing web search for: '{query}'")
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=3)]
                if not results:
                    return "No results found."
                return "\n\n".join([f"Title: {res['title']}\nURL: {res['href']}\nSnippet: {res['body']}" for res in results])
        except Exception as e:
            print(f"Error during web search: {e}")
            return f"Error performing web search: {e}"

    def execute(self, task: str, history: list = None) -> dict:
        log_data = {
            "task": task,
            "llm_decision_raw": None,
            "tool_used": None,
            "tool_input": None,
            "tool_output": None,
            "final_response": None
        }

        context_str = ""
        if history:
            context_str = "You have access to the results of previous steps. Use this information to answer the current task if possible before searching the web again.\n\nPREVIOUS RESULTS:\n"
            formatted_history = "\n---\n".join([json.dumps(item, indent=2) for item in history])
            context_str += formatted_history + "\n\n--\n"

        system_prompt = f"""{context_str}You are an agent that must decide which tool to use to respond to a task.
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


        
        return log_data
    
if __name__ == "__main__":
    agent = Agent()
    
    print("--- Test Case 1: Current Time ---")
    time_task = "What time is it?"
    result_dict = agent.execute(time_task)
    print(json.dumps(result_dict, indent=2))

    print("\n--- Test Case 2: Web Search ---")
    search_task = "What are the latest developments in AI?"
    result_dict = agent.execute(search_task)
    print(json.dumps(result_dict, indent=2))

    print("\n--- Test Case 3: Direct Answer ---")
    direct_task = "What is the capital of France?"
    result_dict = agent.execute(direct_task)
    print(json.dumps(result_dict, indent=2))

    print("\n--- Test Case 4: Fallback (potentially) ---")
    unknown_task = "Explain quantum entanglement simply."
    result_dict = agent.execute(unknown_task)
    print(json.dumps(result_dict, indent=2))