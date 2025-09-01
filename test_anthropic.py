#!/usr/bin/env python3
"""
Test script for Anthropic Claude integration.
This allows you to directly test the AnthropicModel without going through the full agent pipeline.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_executor import AnthropicModel


async def test_anthropic_direct():
    """Test the AnthropicModel directly with various inputs"""
    print("=== Testing Anthropic Model Directly ===\n")
    
    try:
        # Initialize the model
        claude = AnthropicModel()
        print("✅ AnthropicModel initialized successfully")
        print(f"Model: {claude.model}")
        print(f"API Key present: {'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'No'}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to initialize AnthropicModel: {e}")
        return
    
    # Test cases
    test_cases = [
        "What is 5 + 3?",
        "Tom has 23 candies, and Anna gives him 17 more. How many candies does he have in total?",
        "There are 56 apples in a basket. Children eat 19 of them. How many apples are left?",
        "What is 15 * 7?",
        "Hello, how are you?"  # Non-math question to see how it responds
    ]
    
    print("=== Running Test Cases ===")
    for i, question in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"Question: {question}")
        
        try:
            response = await claude.chat([{"role": "user", "content": question}])
            print(f"Raw Response: '{response}'")
            print(f"Response Type: {type(response)}")
            print(f"Response Length: {len(response)} characters")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def interactive_test():
    """Interactive testing - allows you to type questions and see responses"""
    print("\n=== Interactive Testing Mode ===")
    print("Type your questions and see Claude's responses.")
    print("Type 'quit', 'exit', or 'q' to stop.\n")
    
    try:
        claude = AnthropicModel()
    except Exception as e:
        print(f"❌ Failed to initialize AnthropicModel: {e}")
        return
    
    while True:
        try:
            question = input("Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not question:
                continue
                
            print("Processing...")
            response = await claude.chat([{"role": "user", "content": question}])
            print(f"Claude: {response}")
            print(f"(Raw response type: {type(response)}, length: {len(response)})\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


async def test_system_prompt():
    """Test if the system prompt is working correctly"""
    print("\n=== Testing System Prompt Effectiveness ===")
    
    try:
        claude = AnthropicModel()
        
        # Test a math question to see if it follows the "numbers only" instruction
        question = "What is 25 + 17? Please explain your work."
        print(f"Question (with request for explanation): {question}")
        
        response = await claude.chat([{"role": "user", "content": question}])
        print(f"Response: '{response}'")
        
        # Analyze if it followed instructions
        if response.strip().isdigit():
            print("✅ System prompt working - returned only number")
        elif any(word in response.lower() for word in ['because', 'first', 'then', 'explanation']):
            print("⚠️  System prompt partially ignored - included explanation")
        else:
            print("🤔 Unclear if system prompt is working properly")
            
    except Exception as e:
        print(f"❌ Error testing system prompt: {e}")


def check_environment():
    """Check if environment is set up correctly"""
    print("=== Environment Check ===")
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✅ ANTHROPIC_API_KEY is set (length: {len(api_key)} characters)")
    else:
        print("❌ ANTHROPIC_API_KEY is not set!")
        print("   Please set it in your .env file or environment variables")
    
    # Check if anthropic package is installed
    try:
        import anthropic
        print(f"✅ anthropic package installed (version: {anthropic.__version__})")
    except ImportError:
        print("❌ anthropic package not installed!")
        print("   Run: pip install anthropic")
    except AttributeError:
        print("✅ anthropic package installed")
    
    # Check dotenv
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv package available")
    except ImportError:
        print("❌ python-dotenv package not installed!")
    
    print()


async def main():
    """Main test function"""
    print("Anthropic Claude Integration Test")
    print("=" * 40)
    
    # Check environment first
    check_environment()
    
    # Menu
    while True:
        print("\nSelect test mode:")
        print("1. Run predefined test cases")
        print("2. Interactive testing (type your own questions)")
        print("3. Test system prompt effectiveness")
        print("4. Run all tests")
        print("5. Exit")
        
        choice = input("\nYour choice (1-5): ").strip()
        
        if choice == '1':
            await test_anthropic_direct()
        elif choice == '2':
            await interactive_test()
        elif choice == '3':
            await test_system_prompt()
        elif choice == '4':
            await test_anthropic_direct()
            await test_system_prompt()
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please select 1-5.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
