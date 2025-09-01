from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from typing import Dict, Any, List
import anthropic
import os
from dotenv import load_dotenv
import re
import json
from tools import AVAILABLE_TOOLS, execute_tool, store_client_input

# Load environment variables from .env file
load_dotenv()


class AgentBeatsPracticeAgent:
    """Agent Beats Practice Agent"""
    
    def __init__(self):
        self.claude = AnthropicModel()

    async def invoke(self, user_input: str) -> str:
        """Process user input and return only the string response."""
        try:
            print(user_input)
            resp = await self.claude.chat(messages=[{'role': 'user', 'content': user_input}])
            print(resp)
            # Extract just the numerical answer
            #answer = self.extract_numerical_answer(resp)
            #print(f"DEBUG: Extracted answer: {answer}")
            return resp
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def extract_numerical_answer(self, response: str) -> str:
        """Extract just the numerical answer from Claude's response"""
        # Remove any leading/trailing whitespace
        response = response.strip()
        
        # Try to find a number at the start of the response
        number_match = re.match(r'^(\d+(?:\.\d+)?)', response)
        if number_match:
            return number_match.group(1)
        
        # Try to find the last number in the response
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', response)
        if numbers:
            return numbers[-1]
        
        # If no clear number found, return the original response
        return response

class AnthropicModel:
    """Claude (Anthropic) Model with Tool Support"""
    def __init__(self):
        # Get API key from environment variables
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = 'claude-3-5-sonnet-20241022'  # Latest Claude model
        self.system_prompt = """You are a helpful AI assistant with access to various tools for mathematical calculations, text processing, data encoding/decoding, code execution, and conversation history tracking.

You can:
1. Solve mathematical problems and return numerical answers
2. Generate MD5 and SHA512 hashes of text
3. Encode and decode base64 data
4. Write and execute Python code to solve complex computational problems
5. Access previous client inputs from the conversation history database

IMPORTANT: You can make multiple tool calls in sequence when needed. For example:
- If asked to hash something multiple times, use the output of one hash as input to the next
- If asked to encode then hash, or hash then encode, chain the operations
- Always use the actual tool results as input for subsequent operations

CODE EXECUTION GUIDELINES:
- For complex mathematical problems, algorithms, or data processing, write and execute Python code
- Always write complete, runnable Python programs with print statements to show results
- Include proper imports and error handling in your code
- Use the execute_code tool for problems that require:
  * Complex calculations or algorithms
  * Prime number calculations
  * Data processing or analysis
  * Mathematical sequences or series
  * Any computation beyond simple arithmetic

CONVERSATION HISTORY CAPABILITIES:
- All client inputs are automatically stored in a SQLite database
- Use get_recent_client_inputs(k) to retrieve the last k client inputs from the database
- This is useful for:
  * Reviewing what was discussed earlier in the session
  * Finding patterns in previous requests
  * Referencing information from past conversations
  * Understanding context when a user refers to "earlier" or "before"
- The database stores inputs with timestamps and session information
- You can retrieve up to 100 recent inputs at once (parameter k between 1-100)

When given a simple math problem, solve it step by step and provide the final numerical answer.
When asked to hash text or encode/decode data, use the appropriate tools.
When asked to solve complex computational problems, write and execute Python code.
When a user refers to previous conversations or asks about "what we discussed before", use get_recent_client_inputs to check the history.
When asked to perform multiple operations in sequence, use multiple tool calls with the output of each operation as input to the next.

Always be helpful and provide clear responses, showing your work when performing multiple steps."""

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Convert to Claude's message format (system prompt is separate)
            conversation_messages = [msg for msg in messages if msg['role'] != 'system']
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                print(f"🔄 Conversation iteration {iteration}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0,
                    system=self.system_prompt,
                    messages=conversation_messages,
                    tools=AVAILABLE_TOOLS
                )
                
                # Check if there are any tool calls in this response
                has_tool_calls = any(block.type == "tool_use" for block in response.content)
                
                if not has_tool_calls:
                    # No tool calls, this is the final response
                    final_text = ""
                    for content_block in response.content:
                        if content_block.type == "text":
                            final_text += content_block.text
                    
                    return final_text.strip() if final_text else "I apologize, but I couldn't generate a proper response."
                
                # Process tool calls
                assistant_message_content = []
                tool_results = []
                
                for content_block in response.content:
                    if content_block.type == "text":
                        assistant_message_content.append({
                            "type": "text",
                            "text": content_block.text
                        })
                    elif content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_id = content_block.id
                        
                        print(f"🔧 Using tool: {tool_name} with input: {tool_input}")
                        
                        # Execute the tool
                        tool_result = execute_tool(tool_name, tool_input)
                        print(f"📤 Tool result: {tool_result}")
                        
                        # Add tool use to assistant message
                        assistant_message_content.append({
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": tool_input
                        })
                        
                        # Prepare tool result for user message
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": tool_result
                        })
                
                # Add assistant message with tool calls
                conversation_messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })
                
                # Add user message with tool results
                if tool_results:
                    conversation_messages.append({
                        "role": "user",
                        "content": tool_results
                    })
            
            # If we've hit max iterations, return what we have
            return "I've completed the available tool calls but reached the maximum iteration limit."
            
        except Exception as e:
            print(f"Claude API error: {str(e)}")
            return f"Claude API error: {str(e)}"


class AgentBeatsPracticeAgentExecutor(AgentExecutor):
    
    def __init__(self):
        self.agent = AgentBeatsPracticeAgent()
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Extract user input from A2A message parts structure
        user_input = "No input provided"
        session_id = None
        user_id = "default"
        
        try:
            # A2A uses message.parts[0].root.text structure
            if (hasattr(context, 'message') and 
                hasattr(context.message, 'parts') and 
                context.message.parts and
                hasattr(context.message.parts[0], 'root') and
                hasattr(context.message.parts[0].root, 'text')):
                
                user_input = context.message.parts[0].root.text
                print(f"✅ Successfully extracted user input: '{user_input}'")
                
                # Try to extract session/user ID from context if available
                if hasattr(context, 'session_id'):
                    session_id = str(context.session_id)
                if hasattr(context, 'user_id'):
                    user_id = str(context.user_id)
                elif hasattr(context, 'message') and hasattr(context.message, 'user_id'):
                    user_id = str(context.message.user_id)
                
            else:
                print("❌ Could not extract user input from A2A message structure")
                
        except Exception as e:
            print(f"❌ Error extracting user input: {e}")
            user_input = "Error extracting input"
        
        # Store the client input in the database (if it's not empty or error message)
        if user_input and user_input != "No input provided" and not user_input.startswith("Error extracting"):
            try:
                store_result = store_client_input(user_input, session_id, user_id)
                print(f"📝 {store_result}")
            except Exception as e:
                print(f"❌ Failed to store input in database: {e}")
        
        # Pass the input to the agent
        result = await self.agent.invoke(user_input)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')