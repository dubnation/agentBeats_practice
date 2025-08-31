from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from typing import Dict, Any, List
import ollama


class AgentBeatsPracticeAgent:
    """Agent Beats Practice Agent"""
    
    def __init__(self):
        self.ollama = OllamaModel()

    async def invoke(self, user_input: str) -> str:
        # Process the user input here
        try:
            resp = self.ollama.chat(messages=[{'role': 'user', 'content': user_input}])
            return resp['message']['content']
        except Exception as e:
            return f"Error processing request: {str(e)}"

class OllamaModel:
    """Ollama Llama 3.2 Model with Agent Context"""
    def __init__(self):
        self.ollama = ollama
        self.model = 'llama3.2'
        self.system_prompt = """You will solve mathematics-based word problems and arithmetic problems. Return ONLY the final numerical answer with the appropriate unit if specified in the problem. Do not show your work, calculations, or explanations.

Examples:
- For "What is 5 + 3?" → "8"
- For "A rectangle is 4m long and 3m wide. What is the perimeter?" → "14 m"
- For "Calculate 12 × 7" → "84"
- For "A rectangle is 8 cm long and 6 cm wide. What is its perimeter?" → "28 cm"

Format: [number] [unit] (if unit is mentioned in the problem)
"""

    def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            # Prepend system message if not already present
            if not messages or messages[0].get('role') != 'system':
                messages = [{'role': 'system', 'content': self.system_prompt}] + messages
            
            return self.ollama.chat(model=self.model, messages=messages)
        except Exception as e:
            return {"message": {"content": f"Ollama API error: {str(e)}"}}
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        try:
            # Add system context to the prompt
            full_prompt = f"{self.system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            return self.ollama.generate(model=self.model, prompt=full_prompt)
        except Exception as e:
            return {"response": f"Ollama API error: {str(e)}"}
    

class AgentBeatsPracticeAgentExecutor(AgentExecutor):
    
    def __init__(self):
        self.agent = AgentBeatsPracticeAgent()
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Extract user input from the request context
        user_input = context.message.content if hasattr(context, 'message') and hasattr(context.message, 'content') else "No input provided"
        
        # Pass the input to the agent
        result = await self.agent.invoke(user_input)
        await event_queue.enqueue_event(new_agent_text_message(result))

    # --8<-- [end:HelloWorldAgentExecutor_execute]

    # --8<-- [start:HelloWorldAgentExecutor_cancel]
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')


