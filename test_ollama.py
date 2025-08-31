#!/usr/bin/env python3
"""
Quick test script for the Ollama model
Usage: python test_ollama.py
"""

import sys
from agent_executor import OllamaModel


def test_ollama_chat(user_input: str):
    """Test the Ollama model with chat interface"""
    print(f"🤖 Testing Ollama model with input: '{user_input}'")
    print("-" * 50)
    
    try:
        # Create Ollama model instance
        model = OllamaModel()
        
        # Test with chat interface
        messages = [{'role': 'user', 'content': user_input}]
        response = model.chat(messages)
        
        print("✅ Chat Response:")
        if 'message' in response and 'content' in response['message']:
            print(response['message']['content'])
        else:
            print(f"Unexpected response format: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def test_ollama_generate(user_input: str):
    """Test the Ollama model with generate interface"""
    print(f"\n🔄 Testing generate method...")
    print("-" * 50)
    
    try:
        # Create Ollama model instance
        model = OllamaModel()
        
        # Test with generate interface
        response = model.generate(user_input)
        
        print("✅ Generate Response:")
        if 'response' in response:
            print(response['response'])
        else:
            print(f"Unexpected response format: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


def main():
    print("🧪 Ollama Model Test Script")
    print("=" * 50)
    
    # Test cases for math problems
    test_cases = [
        "What is 15 + 27?",
        "If I have 100 apples and give away 35, how many do I have left?",
        "Calculate 12 * 8",
        "What is 144 divided by 12?",
        "A rectangular room is 12 feet long and 8 feet wide. What is the area?",
        "A rectangle is 8 cm long and 6 cm wide. What is its perimeter? (Answer with digits)"
    ]
    
    # Check if user provided input as command line argument
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        print(f"Using user input: '{user_input}'\n")
        test_cases = [user_input]
    else:
        print("No input provided. Using default test cases.\n")
        print("💡 To test with your own input: python test_ollama.py 'Your question here'")
        print("-" * 50)
    
    # Run tests
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}:")
        success = test_ollama_chat(test_input)
        
        if success:
            test_ollama_generate(test_input)
        
        if i < len(test_cases):
            input("\n⏸️  Press Enter to continue to next test...")
        
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()
