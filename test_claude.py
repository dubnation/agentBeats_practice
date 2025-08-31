#!/usr/bin/env python3
"""
Quick test script for the Claude model
Usage: python test_claude.py
"""

import sys
import asyncio
from agent_executor import AnthropicModel


async def test_claude_chat(user_input: str):
    """Test the Claude model with chat interface"""
    print(f"🤖 Testing Claude model with input: '{user_input}'")
    print("-" * 50)
    
    try:
        # Create Claude model instance
        model = AnthropicModel()
        
        # Test with chat interface
        messages = [{'role': 'user', 'content': user_input}]
        response = await model.chat(messages)
        
        print("✅ Chat Response:")
        print(response)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


async def test_claude_generate(user_input: str):
    """Test the Claude model with generate interface"""
    print(f"\n🔄 Testing generate method...")
    print("-" * 50)
    
    try:
        # Create Claude model instance
        model = AnthropicModel()
        
        # Test with generate interface
        response = model.generate(user_input)
        
        print("✅ Generate Response:")
        print(response)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


async def main():
    print("🧪 Claude Model Test Script")
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
        print("💡 To test with your own input: python test_claude.py 'Your question here'")
        print("-" * 50)
    
    # Run tests
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}:")
        success = await test_claude_chat(test_input)
        
        if success:
            await test_claude_generate(test_input)
        
        if i < len(test_cases):
            input("\n⏸️  Press Enter to continue to next test...")
        
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
