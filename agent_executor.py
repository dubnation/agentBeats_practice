from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from typing import Dict, Any, List
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AgentBeatsPracticeAgent:
    """Agent Beats Practice Agent"""
    
    def __init__(self):
        self.claude = AnthropicModel()

    async def invoke(self, user_input: str) -> str:
        # Process the user input here
        try:
            resp = await self.claude.chat(messages=[{'role': 'user', 'content': user_input}])
            return resp
        except Exception as e:
            return f"Error processing request: {str(e)}"

class AnthropicModel:
    """Claude (Anthropic) Model for Mathematical Problem Solving"""
    def __init__(self):
        # Get API key from environment variables
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = 'claude-3-5-sonnet-20241022'  # Latest Claude model
        self.system_prompt = """You are a mathematical calculator. When given a math problem, solve it and return ONLY the numerical answer.

Rules:
- Solve the math problem immediately
- Return only the final number (with units if specified)
- Do not explain your work
- Do not ask questions

Examples:
- "Tom has 23 candies, and Anna gives him 17 more. How many candies does he have in total?" → "40"
- "A rabbit eats 6 carrots every 2 days. How many carrots will it eat in 6 days?" → "18"
- "How many 5-dollar bills can you get in exchange for a 20-dollar bill?" → "4"
- "What is 15 + 27?" → "42"
- "A rectangle is 8 cm long and 6 cm wide. What is its perimeter?" → "28 cm"

Give ONLY the answer."""

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Prepend system message if not already present
            if not messages or messages[0].get('role') != 'system':
                messages = [{'role': 'system', 'content': self.system_prompt}] + messages
            
            # Convert to Claude's message format (system prompt is separate)
            system_message = messages[0]['content'] if messages[0]['role'] == 'system' else self.system_prompt
            user_messages = [msg for msg in messages if msg['role'] != 'system']
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_message,
                messages=user_messages
            )
            
            return response.content[0].text
        except Exception as e:
            return f"Claude API error: {str(e)}"
    
    def generate(self, prompt: str) -> str:
        try:
            # Create a single user message
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            return f"Claude API error: {str(e)}"
    

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


