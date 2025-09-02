from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message, new_task
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
    """Agent Beats Practice Agent with Image Support"""
    
    def __init__(self):
        self.claude = AnthropicModel()

    async def invoke(self, user_input: str, images: List[Dict[str, Any]] = None) -> str:
        """Process user input and images, return only the string response."""
        try:
            print(f"User input: {user_input}")
            if images:
                print(f"Images provided: {len(images)} image(s)")
                for i, img in enumerate(images):
                    print(f"  Image {i+1}: {img['media_type']}, data length: {len(img['data'])} chars")
            
            # Create message with both text and images
            messages = [{'role': 'user', 'content': user_input}]
            
            # Pass images to Claude
            resp = await self.claude.chat(messages=messages, images=images)
            print(f"Claude response: {resp}")
            return resp
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg)
            return error_msg
    
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
    """Claude (Anthropic) Model with Tool Support and Vision"""
    def __init__(self):
        # Get API key from environment variables
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = 'claude-3-5-sonnet-20241022'  # Latest Claude model with vision
        self.max_context_messages = 20  # Reduced for efficiency - focus on recent context only
        self.max_tokens_estimate = 150000  # Conservative estimate for context limit
        self.system_prompt = """You are a helpful AI assistant with tools for math, hashing (MD5/SHA512), base64 encoding/decoding, Python code execution, conversation history access, image analysis, and tic-tac-toe gaming.

TOOLS USAGE:
- Math: Solve step by step, provide numerical answers
- Hashing/Encoding: Chain operations when needed (e.g., encode then hash)
- Code: Use execute_code for complex calculations, algorithms, prime numbers, sequences
- History: When users ask about previous conversations, use get_recent_client_inputs(k=2 or k=3) ONCE to get recent entries, then directly answer from that data. DO NOT make multiple history calls.
- Images: Analyze, identify objects/text/scenes, perform OCR when needed
- Tic-Tac-Toe: Play strategically to win games and extract 14-digit winning numbers

TIC-TAC-TOE GAMING:
- Game board is a 2D array: [[row0], [row1], [row2]] where each cell can be 'x', 'o', or '' (empty)
- Cell positions are numbered 0-8 in this layout: 0|1|2, 3|4|5, 6|7|8
- ALWAYS use getCurrGameStatus after every move to check the current board state and game status
- You are 'X' (goes first), computer is 'O'
- Game status can be: 'win', 'lose', or 'still playing'
- When you win, immediately use getWinningNumber to extract the 14-digit code

TIC-TAC-TOE STRATEGY (PRIORITY ORDER - ALWAYS FOLLOW THIS SEQUENCE):
1. 🏆 IMMEDIATE WIN: If you can complete 3 X's in a line (row/column/diagonal), DO IT NOW
2. 🚨 BLOCK THREAT: If computer can win next turn (2 O's + empty), BLOCK IT NOW  
3. 🎯 CREATE FORK: Try to create multiple winning threats (two ways to win)
4. 🛡️ BLOCK FORK: If computer can create a fork, block it
5. 🎯 CENTER: Take center (position 4) if available - strongest position
6. 🏗️ OPPOSITE CORNER: If computer has a corner, take the opposite corner
7. 🏗️ EMPTY CORNER: Take any corner (0,2,6,8) - second strongest positions  
8. 🏗️ SIDE: Take any side (1,3,5,7) - weakest positions, use as last resort

DECISION MAKING:
- ALWAYS check the board analysis in getCurrGameStatus output
- Look for "WIN OPPORTUNITIES" and "BLOCK THREATS" hints
- If you see WIN OPPORTUNITIES: [5], immediately press cell 5  
- If you see BLOCK THREATS: [2], immediately press cell 2
- Never make random moves - always have a strategic reason
- Think one move ahead: "If I play here, what can the computer do?"

CRITICAL: TIC-TAC-TOE WINNING NUMBER RETURN:
- After successfully extracting a winning number (14-digit code), you MUST return it as your final response
- Format: "🏆 Victory! Winning number: [14-digit-code]"
- Example: "🏆 Victory! Winning number: 20250902104856"
- ALWAYS use close_tictactoe_browser after getting the winning number, then provide the final response
- This 14-digit number is the primary goal and must be returned to the user

HISTORY RETRIEVAL EFFICIENCY:
- For memory questions: Use get_recent_client_inputs(k=3) ONCE, find the answer in the results, state it directly
- DO NOT call get_recent_client_inputs multiple times - one call with k=2 or k=3 is sufficient
- If you can't find the answer in the first retrieval, tell the user it's not in recent history

Be concise and efficient. Avoid unnecessary tool calls."""

    def _estimate_message_tokens(self, message: Dict[str, Any]) -> int:
        """Rough estimate of tokens in a message"""
        content = message.get('content', '')
        if isinstance(content, str):
            # Rough estimate: 1 token per 4 characters
            return len(content) // 4
        elif isinstance(content, list):
            # For multimodal content, estimate each part
            total = 0
            for part in content:
                if part.get('type') == 'text':
                    total += len(part.get('text', '')) // 4
                elif part.get('type') == 'image':
                    total += 1000  # Rough estimate for image tokens
                elif part.get('type') == 'tool_use':
                    total += 50  # Tool use overhead
                elif part.get('type') == 'tool_result':
                    total += len(str(part.get('content', ''))) // 4
            return total
        return 0

    def _trim_conversation_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trim conversation history to stay within context limits"""
        if len(messages) <= 3:  # Always keep at least initial messages
            return messages
            
        # Calculate total estimated tokens
        total_tokens = sum(self._estimate_message_tokens(msg) for msg in messages)
        total_tokens += len(self.system_prompt) // 4  # Add system prompt tokens
        
        # If within limits, return as is
        if total_tokens <= self.max_tokens_estimate and len(messages) <= self.max_context_messages:
            return messages
        
        print(f"🔄 Trimming conversation: {len(messages)} messages, ~{total_tokens} tokens")
        
        # Keep first user message (with potential images) and recent messages
        first_user_msg = messages[0] if messages and messages[0]['role'] == 'user' else None
        
        # Keep the most recent messages up to our limit
        recent_messages = messages[-(self.max_context_messages-1):] if first_user_msg else messages[-self.max_context_messages:]
        
        # Reconstruct with first message + recent messages
        if first_user_msg and first_user_msg not in recent_messages:
            trimmed_messages = [first_user_msg] + recent_messages
        else:
            trimmed_messages = recent_messages
            
        # Add a summary message if we trimmed significantly
        if len(messages) - len(trimmed_messages) > 5:
            # Create summary of removed messages
            removed_messages = messages[:len(messages) - len(trimmed_messages)]
            summary_content = self._summarize_messages(removed_messages)
            summary_msg = {
                "role": "user", 
                "content": summary_content
            }
            trimmed_messages.insert(-3 if len(trimmed_messages) > 3 else 0, summary_msg)
        
        new_total = sum(self._estimate_message_tokens(msg) for msg in trimmed_messages)
        print(f"✅ Trimmed to {len(trimmed_messages)} messages, ~{new_total} tokens")
        
        return trimmed_messages

    def _compact_tool_sequences(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compact consecutive tool call sequences to reduce message count"""
        if len(messages) < 4:  # Need at least user -> assistant -> user -> assistant to compact
            return messages
        
        compacted = []
        i = 0
        
        while i < len(messages):
            current_msg = messages[i]
            
            # Check if this starts a tool call sequence
            if (i < len(messages) - 2 and 
                current_msg['role'] == 'assistant' and
                isinstance(current_msg.get('content'), list) and
                any(block.get('type') == 'tool_use' for block in current_msg['content']) and
                i + 1 < len(messages) and
                messages[i + 1]['role'] == 'user' and
                isinstance(messages[i + 1].get('content'), list) and
                any(block.get('type') == 'tool_result' for block in messages[i + 1]['content'])):
                
                # Found a tool sequence, check if results are simple
                tool_result_msg = messages[i + 1]
                
                # If tool results are short, compact them
                total_result_length = sum(len(str(block.get('content', ''))) 
                                        for block in tool_result_msg['content'] 
                                        if block.get('type') == 'tool_result')
                
                if total_result_length < 500:  # Compact short tool results
                    # Create a summary of tool calls
                    tool_names = []
                    for block in current_msg['content']:
                        if block.get('type') == 'tool_use':
                            tool_names.append(block.get('name'))
                    
                    # Replace with compact summary
                    compact_msg = {
                        "role": "user",
                        "content": f"[Tool calls executed: {', '.join(tool_names)} - results processed]"
                    }
                    compacted.append(compact_msg)
                    i += 2  # Skip both the assistant tool call and user tool result messages
                else:
                    # Keep as-is if results are long
                    compacted.append(current_msg)
                    i += 1
            else:
                compacted.append(current_msg)
                i += 1
        
        return compacted

    def _summarize_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Create a concise summary of a sequence of messages"""
        if not messages:
            return "[No messages to summarize]"
            
        # Extract key information
        user_queries = []
        tool_calls = []
        key_results = []
        
        for msg in messages:
            if msg['role'] == 'user':
                content = msg.get('content', '')
                if isinstance(content, str) and not content.startswith('['):
                    user_queries.append(content[:100] + ('...' if len(content) > 100 else ''))
            elif msg['role'] == 'assistant':
                content = msg.get('content', [])
                if isinstance(content, list):
                    for block in content:
                        if block.get('type') == 'tool_use':
                            tool_calls.append(block.get('name'))
                        elif block.get('type') == 'text' and len(block.get('text', '')) > 20:
                            key_results.append(block.get('text')[:80] + ('...' if len(block.get('text')) > 80 else ''))
        
        # Build summary
        summary_parts = []
        if user_queries:
            summary_parts.append(f"User asked about: {'; '.join(user_queries[:3])}")
        if tool_calls:
            tool_counts = {}
            for tool in tool_calls:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            tools_summary = ', '.join([f"{tool}({count})" for tool, count in tool_counts.items()])
            summary_parts.append(f"Tools used: {tools_summary}")
        if key_results and not tool_calls:  # Only include results if no tools (to avoid duplication)
            summary_parts.append(f"Responses: {'; '.join(key_results[:2])}")
        
        return '[SUMMARY: ' + ' | '.join(summary_parts) + ']' if summary_parts else '[Previous conversation - no key details]'

    async def chat(self, messages: List[Dict[str, Any]], images: List[Dict[str, Any]] = None) -> str:
        try:
            # Convert to Claude's message format (system prompt is separate)
            conversation_messages = [msg for msg in messages if msg['role'] != 'system']
            
            # If images are provided, add them to the first user message
            if images and conversation_messages:
                first_user_msg = None
                for i, msg in enumerate(conversation_messages):
                    if msg['role'] == 'user':
                        first_user_msg = msg
                        first_user_msg_index = i
                        break
                
                if first_user_msg:
                    # Convert message content to list format for multimodal
                    if isinstance(first_user_msg['content'], str):
                        # Convert text content to proper format and add images
                        content_blocks = [{"type": "text", "text": first_user_msg['content']}]
                        
                        # Add each image
                        for image in images:
                            content_blocks.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image['media_type'],
                                    "data": image['data']
                                }
                            })
                        
                        conversation_messages[first_user_msg_index]['content'] = content_blocks
                        print(f"🖼️ Added {len(images)} images to conversation")
            
            max_iterations = 15  # Prevent infinite loops - increased for complex tic-tac-toe games
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                print(f"🔄 Conversation iteration {iteration}")
                
                # Optimize conversation history to prevent context overload
                conversation_messages = self._compact_tool_sequences(conversation_messages)
                conversation_messages = self._trim_conversation_history(conversation_messages)
                
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
                    
                    print(f"🎯 Final response from Claude: '{final_text[:200]}{'...' if len(final_text) > 200 else ''}'")
                    
                    if final_text.strip():
                        return final_text.strip()
                    else:
                        print("⚠️ Claude returned empty response, using fallback message")
                        return "I apologize, but I couldn't generate a proper response."
                
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
            print(f"⚠️ Reached maximum iterations ({max_iterations}), returning partial result")
            return "I've completed the available tool calls but reached the maximum iteration limit."
            
        except Exception as e:
            print(f"❌ Claude API error: {str(e)}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return f"Claude API error: {str(e)}"


class AgentBeatsPracticeAgentExecutor(AgentExecutor):
    
    def __init__(self):
        self.agent = AgentBeatsPracticeAgent()
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Extract user input and images from A2A message parts structure
        user_input = "No input provided"
        images = []
        session_id = None
        user_id = "default"
        
        try:
            # A2A uses message.parts structure
            if (hasattr(context, 'message') and 
                hasattr(context.message, 'parts') and 
                context.message.parts):
                
                print(f"🔍 Processing {len(context.message.parts)} message parts")
                
                for i, part in enumerate(context.message.parts):
                    print(f"🔍 Processing part {i}: {type(part)}")
                    
                    if hasattr(part, 'root'):
                        root_type = type(part.root).__name__
                        print(f"🔍 Part {i} root type: {root_type}")
                        
                        # Handle text parts
                        if hasattr(part.root, 'text') and part.root.text:
                            user_input = part.root.text
                            print(f"✅ Successfully extracted user input: '{user_input}'")
                        
                        # Handle file parts (images)
                        elif root_type == 'FilePart':
                            print(f"🔍 Found FilePart, examining attributes...")
                            
                            # Check if this is an image file
                            file_obj = getattr(part.root, 'file', None)
                            if file_obj:
                                print(f"🔍 File object type: {type(file_obj)}")
                                print(f"🔍 File object attributes: {[attr for attr in dir(file_obj) if not attr.startswith('_')]}")
                                
                                # Extract file properties
                                file_data = None
                                media_type = None
                                
                                # Try to get the file data
                                if hasattr(file_obj, 'data'):
                                    file_data = file_obj.data
                                elif hasattr(file_obj, 'content'):
                                    file_data = file_obj.content
                                elif hasattr(file_obj, 'bytes'):
                                    file_data = file_obj.bytes
                                
                                # Try to get the media type
                                if hasattr(file_obj, 'media_type'):
                                    media_type = file_obj.media_type
                                elif hasattr(file_obj, 'mime_type'):
                                    media_type = file_obj.mime_type
                                elif hasattr(file_obj, 'content_type'):
                                    media_type = file_obj.content_type
                                elif hasattr(file_obj, 'type'):
                                    media_type = file_obj.type
                                
                                print(f"🔍 File data present: {file_data is not None}")
                                print(f"🔍 Media type: {media_type}")
                                
                                # If we have file data but no media type, try to infer from metadata
                                if file_data and not media_type:
                                    metadata = getattr(part.root, 'metadata', None)
                                    if metadata:
                                        print(f"🔍 Checking metadata: {type(metadata)}, {dir(metadata)}")
                                        # Try different ways to get media type from metadata
                                        if hasattr(metadata, 'media_type'):
                                            media_type = metadata.media_type
                                        elif hasattr(metadata, 'content_type'):
                                            media_type = metadata.content_type
                                        elif hasattr(metadata, 'mime_type'):
                                            media_type = metadata.mime_type
                                
                                # Check if this is an image based on media type or file extension
                                is_image = False
                                if media_type:
                                    is_image = media_type.startswith('image/')
                                
                                if file_data and is_image:
                                    # Convert bytes to base64 if needed
                                    if isinstance(file_data, bytes):
                                        import base64
                                        file_data = base64.b64encode(file_data).decode('utf-8')
                                    
                                    images.append({
                                        'data': file_data,
                                        'media_type': media_type
                                    })
                                    print(f"✅ Successfully extracted image: {media_type}")
                                    print(f"   Data length: {len(file_data)} characters")
                                elif file_data:
                                    print(f"⚠️ Found file data but not recognized as image (media_type: {media_type})")
                                else:
                                    print(f"❌ No file data found in FilePart")
                            else:
                                print(f"❌ FilePart has no 'file' attribute")
                
                # Try to extract session/user ID from context if available
                if hasattr(context, 'session_id'):
                    session_id = str(context.session_id)
                if hasattr(context, 'user_id'):
                    user_id = str(context.user_id)
                elif hasattr(context, 'message') and hasattr(context.message, 'user_id'):
                    user_id = str(context.message.user_id)
                
            else:
                print("❌ Could not extract input from A2A message structure")
                
        except Exception as e:
            print(f"❌ Error extracting input: {e}")
            import traceback
            traceback.print_exc()
            user_input = "Error extracting input"
        
        print(f"🎯 FINAL EXTRACTION RESULTS:")
        print(f"   Text input: '{user_input}'")
        print(f"   Images found: {len(images)}")
        for i, img in enumerate(images):
            print(f"     Image {i+1}: {img['media_type']}, data length: {len(img['data'])}")
        
        # Store the client input in the database (if it's not empty or error message)
        if user_input and user_input != "No input provided" and not user_input.startswith("Error extracting"):
            try:
                # Include note about images if present
                input_to_store = user_input
                if images:
                    input_to_store += f" [with {len(images)} image(s)]"
                    
                store_result = store_client_input(input_to_store, session_id, user_id)
                print(f"📝 {store_result}")
            except Exception as e:
                print(f"❌ Failed to store input in database: {e}")
        
        # Pass the input and images to the agent
        print(f"🚀 Invoking agent with input: '{user_input}' and {len(images)} images")
        
        try:
            result = await self.agent.invoke(user_input, images)
            print(f"✅ Agent invoke successful, result type: {type(result)}, length: {len(str(result)) if result else 0}")
            print(f"📋 Agent result preview: '{str(result)[:200]}{'...' if result and len(str(result)) > 200 else ''}'")
        except Exception as e:
            print(f"❌ Agent invoke failed: {e}")
            import traceback
            traceback.print_exc()
            result = f"Error processing request: {str(e)}"
        
        # Determine if this requires task creation (only for image understanding)
        is_image_task = len(images) > 0
        
        # Only create Tasks for image understanding - everything else uses Messages like before
        if is_image_task:
            print(f"🎯 Creating task for image processing")
            try:
                # Create initial task from user message 
                created_task = new_task(context.message)
                print(f"✅ Initial task created with ID: {created_task.id}")
                
                # Create response message and add it to the task history
                if result and result.strip() and result.strip() != "None":
                    print(f"📤 Adding response to task history: '{result[:100]}{'...' if len(result) > 100 else ''}'")
                    response_message = new_agent_text_message(
                        result.strip(), 
                        context_id=created_task.context_id, 
                        task_id=created_task.id
                    )
                else:
                    print(f"⚠️ Invalid result from agent (result='{result}'), using fallback message")
                    fallback_msg = "I apologize, I was unable to process your image."
                    response_message = new_agent_text_message(
                        fallback_msg,
                        context_id=created_task.context_id,
                        task_id=created_task.id
                    )
                
                # Add response to task history and update status
                if created_task.history is None:
                    created_task.history = []
                created_task.history.append(response_message)
                
                # Update task status to completed
                created_task.status.state = "completed"
                created_task.status.message = "Task completed successfully"
                
                print(f"🎯 Task updated with response, history length: {len(created_task.history)}")
                print(f"🔗 Final task - context_id: {created_task.context_id}, task_id: {created_task.id}")
                
                # Send the completed task (for image understanding)
                await event_queue.enqueue_event(created_task)
                
            except Exception as e:
                print(f"❌ Failed to create/update task: {e}")
                import traceback
                traceback.print_exc()
                # Fallback - send a simple message if task creation fails
                fallback_msg = f"Error processing image: {str(e)}"
                await event_queue.enqueue_event(new_agent_text_message(fallback_msg))
        else:
            # For non-image requests, send Message objects like before
            print(f"📤 Sending regular message response")
            if result and result.strip() and result.strip() != "None":
                print(f"✅ Sending text message: '{result[:100]}{'...' if len(result) > 100 else ''}'")
                await event_queue.enqueue_event(new_agent_text_message(result.strip()))
            else:
                print(f"⚠️ Invalid result from agent (result='{result}'), sending fallback message")
                fallback_msg = "I apologize, I was unable to process that request."
                await event_queue.enqueue_event(new_agent_text_message(fallback_msg))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')