import datetime
import litellm

class Agent:
    def __init__(self):
        self.llm_model = "ollama/phi3"

    def get_current_time(self) -> str:
        return datetime.datetime.now().isoformat()
    
    def _invoke_llm(self, prompt: str) -> str:
        try:
            response = litellm.completion(
                model=self.llm_model,
                messages=[{"content": prompt, "role": "user"}]
            )
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                return response.choices[0].message.content
            return "Error: LLM response was empty or not in expected format."
        except Exception as e:
            print(f"LiteLLM Exception: {e}")
            return f"Error invoking LLM: {e}"
        
    def search_web(self, query: str) -> str:
        prompt = f"Please provide a concise, simulated web search result for the query: '{query}'. Imagine you are a search engine providing a top snippet."
        return self._invoke_llm(prompt)

    def execute(self, task: str) -> str:
        if task.lower() == "current time":
            return self.get_current_time()
        return f"Task received: {task}"
    
if __name__ == "__main__":
    agent = Agent()
    
    print(f"Current time test: {agent.execute('current time')}")

    test_task = "What is the weather today?"
    result = agent.execute(test_task)
    print(f"Agent execution result for '{test_task}': {result}")

    print("\nTesting LLM invocation...")
    llm_test_prompt = "What is the capital of France?"
    llm_response = agent._invoke_llm(llm_test_prompt)
    print(f"Prompt: {llm_test_prompt}")
    print(f"LLM Response: {llm_response}")

    llm_test_prompt_2 = "Explain the concept of a Large Language Model in one sentence."
    llm_response_2 = agent._invoke_llm(llm_test_prompt_2)
    print(f"Prompt: {llm_test_prompt_2}")
    print(f"LLM Response: {llm_response_2}")

    print("\nTesting simulated web search...")
    search_query = "latest news on AI advancements"
    search_result = agent.search_web(search_query)
    print(f"Search Query: {search_query}")
    print(f"Simulated Search Result: {search_result}")

    search_query_2 = "best Python web frameworks"
    search_result_2 = agent.search_web(search_query_2)
    print(f"Search Query: {search_query_2}")
    print(f"Simulated Search Result: {search_result_2}")