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
    """Ollama Llama 3.2 Model"""
    def __init__(self):
        self.ollama = ollama
        self.model = 'llama3.2'

    def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            return self.ollama.chat(model=self.model, messages=messages)
        except Exception as e:
            return {"message": {"content": f"Ollama API error: {str(e)}"}}
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        try:
            return self.ollama.generate(model=self.model, prompt=prompt)
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


