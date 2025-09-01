import hashlib
import base64
from typing import Dict, Any, List

# Tool definitions for the agent
def md5_digest(data: str) -> str:
    """Generate MD5 hash of the input data (as hex string)"""
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def sha512_digest(data: str) -> str:
    """Generate SHA512 hash of the input data (as hex string)"""
    return hashlib.sha512(data.encode('utf-8')).hexdigest()

def base64_encode(data: str) -> str:
    """Encode data to base64"""
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def base64_decode(data: str) -> str:
    """Decode base64 data"""
    try:
        return base64.b64decode(data).decode('utf-8')
    except Exception as e:
        return f"Error decoding base64: {str(e)}"
    
def execute_code(code: str) -> str:
    """Execute Python code safely and return the result"""
    try:
        import subprocess
        import tempfile
        import os
        
        # Create a temporary file to write the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code with timeout protection
            result = subprocess.run(
                ['python3', temp_file], 
                capture_output=True, 
                text=True, 
                timeout=30  # 30 second timeout
            )
            
            # Clean up temp file
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return result.stdout.strip() if result.stdout else "Code executed successfully (no output)"
            else:
                return f"Error: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            os.unlink(temp_file)
            return "Error: Code execution timed out (30 seconds limit)"
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            return f"Error executing code: {str(e)}"
            
    except Exception as e:
        return f"Error setting up code execution: {str(e)}"

# Tool schema definitions for Claude function calling
AVAILABLE_TOOLS = [
    {
        "name": "md5_digest",
        "description": "Generate MD5 hash of the input text",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "The text to hash"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "sha512_digest", 
        "description": "Generate SHA512 hash of the input text",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "The text to hash"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "base64_encode",
        "description": "Encode text to base64",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "The text to encode"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "base64_decode",
        "description": "Decode base64 encoded text",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "The base64 encoded text to decode"
                }
            },
            "required": ["data"]
        }
    },
    {
        "name": "execute_code",
        "description": "Execute Python code to solve complex computational problems. Use this when you need to perform calculations, algorithms, or data processing that goes beyond simple math.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The complete Python code to execute. Should be a full program with print statements to show results."
                }
            },
            "required": ["code"]
        }
    }
]

# Tool execution function
def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool by name with given arguments"""
    try:
        if tool_name == "md5_digest":
            return md5_digest(arguments["data"])
        elif tool_name == "sha512_digest":
            return sha512_digest(arguments["data"])
        elif tool_name == "base64_encode":
            return base64_encode(arguments["data"])
        elif tool_name == "base64_decode":
            return base64_decode(arguments["data"])
        elif tool_name == "execute_code":
            return execute_code(arguments["code"])
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"





