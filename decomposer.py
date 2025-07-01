from agent import Agent

class Decomposer:
    def __init__(self, agent: Agent):
        self.agent = agent

    def decompose(self, task: str) -> list[str]:
        system_prompt = """You are a task decomposition expert. Your role is to break down a complex, high-level user request into a sequence of simple, executable sub-tasks that can be handled by an agent with the following tools:
- `current_time`: Gets the current time.
- `search_web`: Searches the web for a given query.
- `answer_directly`: Provides a direct answer to a simple question.

Your output MUST be a numbered list, with each step on a new line. Do not add any introductory or concluding text.

Example:
User Request: "Summarize the latest AI news and email me the top 3 stories."
Your Output:
1. Search the web for "latest AI news".
2. Analyze the search results to identify the top 3 most significant stories.
3. For each of the top 3 stories, read the content and generate a concise summary.
4. Compose an email draft containing the three summaries.
5. Send the email to me.

Example 2:
User Request: "What time is it and who is the US president?"
Your Output:
1. Get the current time.
2. Search the web for "current US president"."""

        user_prompt = f"User Request: \"{task}\"\nYour Output:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm_response = self.agent._invoke_llm(messages)

        print(f"Raw LLM response for decomposition:\n{llm_response}")

        sub_tasks = []
        lines = [line.strip() for line in llm_response.strip().split('\n') if line.strip()]

        for line in lines:
            parts = line.split('.', 1)
            if len(parts) == 2 and parts[0].isdigit():
                task_description = parts[1].strip()
            else:
                task_description = line
            
            if task_description:
                sub_tasks.append(task_description)
        
        return sub_tasks