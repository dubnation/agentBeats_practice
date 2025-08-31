import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_executor import AgentBeatsPracticeAgent, OllamaModel, AgentBeatsPracticeAgentExecutor


class TestOllamaModel:
    """Test cases for OllamaModel class"""
    
    def test_init(self):
        """Test OllamaModel initialization"""
        with patch('agent_executor.ollama') as mock_ollama:
            model = OllamaModel()
            assert model.ollama == mock_ollama
            assert model.model == 'llama3.2'
    
    @patch('agent_executor.ollama')
    def test_chat_success(self, mock_ollama):
        """Test successful chat method"""
        # Mock successful ollama response
        mock_response = {
            "message": {
                "content": "Hello! How can I help you?"
            }
        }
        mock_ollama.chat.return_value = mock_response
        
        model = OllamaModel()
        messages = [{"role": "user", "content": "Hello"}]
        result = model.chat(messages)
        
        mock_ollama.chat.assert_called_once_with(model='llama3.2', messages=messages)
        assert result == mock_response
    
    @patch('agent_executor.ollama')
    def test_chat_error_handling(self, mock_ollama):
        """Test chat method error handling"""
        # Mock ollama exception
        mock_ollama.chat.side_effect = Exception("Connection error")
        
        model = OllamaModel()
        messages = [{"role": "user", "content": "Hello"}]
        result = model.chat(messages)
        
        assert "Ollama API error: Connection error" in result["message"]["content"]
    
    @patch('agent_executor.ollama')
    def test_generate_success(self, mock_ollama):
        """Test successful generate method"""
        # Mock successful ollama response
        mock_response = {
            "response": "This is a generated response."
        }
        mock_ollama.generate.return_value = mock_response
        
        model = OllamaModel()
        prompt = "Generate a response"
        result = model.generate(prompt)
        
        mock_ollama.generate.assert_called_once_with(model='llama3.2', prompt=prompt)
        assert result == mock_response
    
    @patch('agent_executor.ollama')
    def test_generate_error_handling(self, mock_ollama):
        """Test generate method error handling"""
        # Mock ollama exception
        mock_ollama.generate.side_effect = Exception("Model not found")
        
        model = OllamaModel()
        prompt = "Generate a response"
        result = model.generate(prompt)
        
        assert "Ollama API error: Model not found" in result["response"]


class TestAgentBeatsPracticeAgent:
    """Test cases for AgentBeatsPracticeAgent class"""
    
    def test_init(self):
        """Test agent initialization"""
        with patch('agent_executor.OllamaModel') as mock_ollama_model:
            agent = AgentBeatsPracticeAgent()
            mock_ollama_model.assert_called_once()
            assert hasattr(agent, 'ollama')
    
    @pytest.mark.asyncio
    async def test_invoke_success(self):
        """Test successful invoke method"""
        with patch('agent_executor.OllamaModel') as mock_ollama_model:
            # Mock the ollama model instance
            mock_ollama_instance = Mock()
            mock_ollama_instance.chat.return_value = {
                "message": {"content": "Hello! How can I help you?"}
            }
            mock_ollama_model.return_value = mock_ollama_instance
            
            agent = AgentBeatsPracticeAgent()
            result = await agent.invoke("Hello")
            
            mock_ollama_instance.chat.assert_called_once_with(
                messages=[{'role': 'user', 'content': 'Hello'}]
            )
            assert result == "Hello! How can I help you?"
    
    @pytest.mark.asyncio
    async def test_invoke_error_handling(self):
        """Test invoke method error handling"""
        with patch('agent_executor.OllamaModel') as mock_ollama_model:
            # Mock the ollama model instance to raise an exception
            mock_ollama_instance = Mock()
            mock_ollama_instance.chat.side_effect = Exception("API error")
            mock_ollama_model.return_value = mock_ollama_instance
            
            agent = AgentBeatsPracticeAgent()
            result = await agent.invoke("Hello")
            
            assert "Error processing request: API error" in result


class TestAgentBeatsPracticeAgentExecutor:
    """Test cases for AgentBeatsPracticeAgentExecutor class"""
    
    def test_init(self):
        """Test executor initialization"""
        with patch('agent_executor.AgentBeatsPracticeAgent') as mock_agent:
            executor = AgentBeatsPracticeAgentExecutor()
            mock_agent.assert_called_once()
            assert hasattr(executor, 'agent')
    
    @pytest.mark.asyncio
    async def test_execute_with_message_content(self):
        """Test execute method with valid message content"""
        with patch('agent_executor.AgentBeatsPracticeAgent') as mock_agent_class:
            with patch('agent_executor.new_agent_text_message') as mock_new_message:
                # Setup mocks
                mock_agent_instance = AsyncMock()
                mock_agent_instance.invoke.return_value = "Agent response"
                mock_agent_class.return_value = mock_agent_instance
                
                mock_context = Mock()
                mock_context.message.content = "User input"
                mock_event_queue = AsyncMock()
                mock_new_message.return_value = "formatted_message"
                
                # Test execution
                executor = AgentBeatsPracticeAgentExecutor()
                await executor.execute(mock_context, mock_event_queue)
                
                # Verify calls
                mock_agent_instance.invoke.assert_called_once_with("User input")
                mock_new_message.assert_called_once_with("Agent response")
                mock_event_queue.enqueue_event.assert_called_once_with("formatted_message")
    
    @pytest.mark.asyncio
    async def test_execute_without_message_content(self):
        """Test execute method without message content"""
        with patch('agent_executor.AgentBeatsPracticeAgent') as mock_agent_class:
            with patch('agent_executor.new_agent_text_message') as mock_new_message:
                # Setup mocks
                mock_agent_instance = AsyncMock()
                mock_agent_instance.invoke.return_value = "Agent response"
                mock_agent_class.return_value = mock_agent_instance
                
                mock_context = Mock(spec=[])  # Mock without message attribute
                mock_event_queue = AsyncMock()
                mock_new_message.return_value = "formatted_message"
                
                # Test execution
                executor = AgentBeatsPracticeAgentExecutor()
                await executor.execute(mock_context, mock_event_queue)
                
                # Verify calls with fallback input
                mock_agent_instance.invoke.assert_called_once_with("No input provided")
                mock_new_message.assert_called_once_with("Agent response")
                mock_event_queue.enqueue_event.assert_called_once_with("formatted_message")
    
    @pytest.mark.asyncio
    async def test_cancel_raises_exception(self):
        """Test cancel method raises exception"""
        with patch('agent_executor.AgentBeatsPracticeAgent'):
            executor = AgentBeatsPracticeAgentExecutor()
            mock_context = Mock()
            mock_event_queue = Mock()
            
            with pytest.raises(Exception, match="cancel not supported"):
                await executor.cancel(mock_context, mock_event_queue)


class TestIntegration:
    """Integration tests for the complete flow"""
    
    @pytest.mark.asyncio
    async def test_full_flow_success(self):
        """Test the complete flow from executor to ollama and back"""
        with patch('agent_executor.ollama') as mock_ollama:
            # Mock ollama response
            mock_ollama.chat.return_value = {
                "message": {"content": "Integrated response"}
            }
            
            with patch('agent_executor.new_agent_text_message') as mock_new_message:
                mock_new_message.return_value = "formatted_message"
                
                # Setup context and event queue
                mock_context = Mock()
                mock_context.message.content = "Hello, how are you?"
                mock_event_queue = AsyncMock()
                
                # Execute the flow
                executor = AgentBeatsPracticeAgentExecutor()
                await executor.execute(mock_context, mock_event_queue)
                
                # Verify the complete flow
                mock_ollama.chat.assert_called_once_with(
                    model='llama3.2',
                    messages=[{'role': 'user', 'content': 'Hello, how are you?'}]
                )
                mock_new_message.assert_called_once_with("Integrated response")
                mock_event_queue.enqueue_event.assert_called_once_with("formatted_message")


# Manual test functions for interactive testing
async def manual_test_ollama_model():
    """Manual test for OllamaModel - requires actual Ollama installation"""
    print("\n=== Manual OllamaModel Test ===")
    try:
        model = OllamaModel()
        
        # Test chat
        print("Testing chat method...")
        chat_result = model.chat([{"role": "user", "content": "Say hello in one word"}])
        print(f"Chat result: {chat_result}")
        
        # Test generate
        print("Testing generate method...")
        generate_result = model.generate("Say goodbye in one word")
        print(f"Generate result: {generate_result}")
        
    except Exception as e:
        print(f"Manual test error (expected if Ollama not installed): {e}")


async def manual_test_agent():
    """Manual test for AgentBeatsPracticeAgent - requires actual Ollama installation"""
    print("\n=== Manual Agent Test ===")
    try:
        agent = AgentBeatsPracticeAgent()
        result = await agent.invoke("Tell me a short joke")
        print(f"Agent response: {result}")
    except Exception as e:
        print(f"Manual test error (expected if Ollama not installed): {e}")


def run_manual_tests():
    """Run manual tests that require actual Ollama installation"""
    print("Running manual tests (requires Ollama to be installed and running)...")
    asyncio.run(manual_test_ollama_model())
    asyncio.run(manual_test_agent())


if __name__ == "__main__":
    # Run automated tests
    print("To run automated tests, use: pytest test_agent_executor.py -v")
    print("To run tests with coverage: pytest test_agent_executor.py --cov=agent_executor --cov-report=html")
    
    # Optionally run manual tests
    choice = input("\nDo you want to run manual tests? (requires Ollama) [y/N]: ").lower()
    if choice == 'y':
        run_manual_tests()
    else:
        print("Skipping manual tests. Use pytest to run automated unit tests.")
