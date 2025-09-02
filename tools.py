import hashlib
import base64
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import tic-tac-toe functions
from tictactoe_tool import press_cell, getCurrGameStatus, getWinningNumber

# Selenium driver for persistent tic-tac-toe sessions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class TicTacToeDriverManager:
    """Manages a persistent Chrome driver for tic-tac-toe games"""
    
    def __init__(self):
        self.driver = None
        self.game_url = "https://ttt.puppy9.com/"
    
    def get_driver(self):
        """Get or create the persistent driver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # CRITICAL: Force Pacific timezone for tic-tac-toe validation
            chrome_options.add_argument("--timezone=America/Los_Angeles")
            
            # Disable cache to prevent stale winning numbers
            chrome_options.add_argument("--disable-application-cache")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            
            # Add headless mode for faster performance (comment out to see browser)
            # chrome_options.add_argument("--headless")  # COMMENTED OUT - browser will be visible!
            
            # Set page load timeout
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(15)  # 15 second timeout
            self.driver.implicitly_wait(15)  # 15 second implicit wait
            print("🌐 Created new Chrome driver for tic-tac-toe (PST timezone, cache disabled)")
        
        return self.driver
    
    def close_driver(self):
        """Close the persistent driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("🔒 Closed tic-tac-toe Chrome driver")

# Global driver manager instance
ttt_driver_manager = TicTacToeDriverManager()

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


class InputHistoryDB:
    """SQLite3 database for storing client input history"""
    
    def __init__(self, db_path: str = "./client_history.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create client_inputs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                user_id TEXT
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON client_inputs(timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def store_input(self, input_text: str, session_id: str = None, user_id: str = "default") -> bool:
        """Store a client input in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO client_inputs (input_text, session_id, user_id) 
                VALUES (?, ?, ?)
            ''', (input_text, session_id, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error storing input: {e}")
            return False
    
    def get_recent_inputs(self, k: int = 5, user_id: str = "default") -> List[Dict[str, Any]]:
        """Retrieve the last k client inputs from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, input_text, timestamp, session_id 
                FROM client_inputs 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, k))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": row[0],
                    "input": row[1],
                    "timestamp": row[2],
                    "session_id": row[3]
                } 
                for row in results
            ]
            
        except Exception as e:
            print(f"Error retrieving recent inputs: {e}")
            return []
    
    def get_input_count(self, user_id: str = "default") -> int:
        """Get total count of stored inputs for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM client_inputs WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            print(f"Error counting inputs: {e}")
            return 0


# Initialize the database
history_db = InputHistoryDB()

def store_client_input(input_text: str, session_id: str = None, user_id: str = "default") -> str:
    """Store client input in the history database"""
    success = history_db.store_input(input_text, session_id, user_id)
    if success:
        return f"✅ Stored client input in history database"
    else:
        return f"❌ Failed to store client input"

def get_recent_client_inputs(k: int = 10, user_id: str = "default") -> str:
    """Retrieve the last k client inputs from the history database (optimized for context efficiency)"""
    try:
        k = int(k)  # Ensure k is an integer
        if k <= 0:
            return "❌ Number of records must be greater than 0"
        if k > 5:  # Reduced to 5 to prevent context overload
            k = 5
            output_prefix = "⚠️ Limited to 5 records to manage context size. "
        else:
            output_prefix = ""
            
        inputs = history_db.get_recent_inputs(k, user_id)
        total_count = history_db.get_input_count(user_id)
        
        if not inputs:
            return f"❌ No client inputs found in database (total stored: {total_count})"
        
        # Compact format to save tokens
        output = f"{output_prefix}📋 Last {len(inputs)} inputs ({total_count} total):\n"
        
        for i, record in enumerate(inputs, 1):
            # More compact timestamp
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')) if record['timestamp'] else None
            time_str = timestamp.strftime("%m/%d %H:%M") if timestamp else "?"
            
            # Show more characters for number pairs and important data
            input_text = record['input']
            if len(input_text) > 120:  # Increased from 60 to 120 to show full number pairs
                input_text = input_text[:117] + "..."
            
            output += f"{i}. [{time_str}] {input_text}\n"
        
        # Add summary if there are many more inputs
        if total_count > len(inputs):
            output += f"... and {total_count - len(inputs)} more inputs in history\n"
        
        return output.strip()
        
    except ValueError:
        return "❌ Invalid number format for k parameter"
    except Exception as e:
        return f"❌ Error retrieving client inputs: {str(e)}"

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
    },
    {
        "name": "get_recent_client_inputs",
        "description": "Retrieve recent client inputs from history database (context-optimized, max 5 entries)",
        "input_schema": {
            "type": "object",
            "properties": {
                "k": {
                    "type": "integer",
                    "description": "Number of recent inputs to retrieve (1-5, auto-capped for context efficiency)",
                    "minimum": 1,
                    "maximum": 5
                },
                "user_id": {
                    "type": "string",
                    "description": "User identifier (optional, defaults to 'default')",
                    "default": "default"
                }
            },
            "required": ["k"]
        }
    },
    {
        "name": "press_cell",
        "description": "Press a cell on the tic-tac-toe game board at https://ttt.puppy9.com/",
        "input_schema": {
            "type": "object",
            "properties": {
                "num": {
                    "type": "integer",
                    "description": "Cell position to press (0-8). Layout: 0|1|2, 3|4|5, 6|7|8",
                    "minimum": 0,
                    "maximum": 8
                }
            },
            "required": ["num"]
        }
    },
    {
        "name": "getCurrGameStatus",
        "description": "Get current tic-tac-toe game state from https://ttt.puppy9.com/ - returns board as 2D array and game status",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "getWinningNumber",
        "description": "Extract the 14-digit winning number from tic-tac-toe game after winning",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "start_new_tictactoe_game",
        "description": "Start a fresh tic-tac-toe game (navigates to new game page)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "close_tictactoe_browser", 
        "description": "Close the tic-tac-toe browser when done playing (cleanup)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
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
        elif tool_name == "get_recent_client_inputs":
            return get_recent_client_inputs(
                k=arguments["k"], 
                user_id=arguments.get("user_id", "default")
            )
        elif tool_name == "press_cell":
            driver = ttt_driver_manager.get_driver()
            result = press_cell(arguments["num"], driver=driver)
            return f"✅ Cell {arguments['num']} pressed successfully" if result else f"❌ Failed to press cell {arguments['num']}"
        elif tool_name == "getCurrGameStatus":
            try:
                driver = ttt_driver_manager.get_driver()
                result = getCurrGameStatus(driver=driver)
                if result:
                    board = result['currentGameBoard']
                    status = result['gameStatus']
                    
                    # Create enhanced board visualization with positions and clear grid
                    def format_cell(row, col, cell):
                        pos = row * 3 + col
                        if cell:
                            return f" {cell.upper()} "
                        else:
                            return f" {pos} "
                    
                    board_display = "📋 GAME BOARD (You are X, Computer is O):\n"
                    board_display += "   Positions: 0|1|2, 3|4|5, 6|7|8\n"
                    board_display += "   ┌───┬───┬───┐\n"
                    
                    for row in range(3):
                        board_display += "   │"
                        for col in range(3):
                            board_display += format_cell(row, col, board[row][col]) + "│"
                        board_display += "\n"
                        if row < 2:
                            board_display += "   ├───┼───┼───┤\n"
                    
                    board_display += "   └───┴───┴───┘\n"
                    board_display += f"🎯 Status: {status.upper()}"
                    
                    # Add strategic analysis
                    if status == "still playing":
                        empty_cells = []
                        for row in range(3):
                            for col in range(3):
                                if board[row][col] == '':
                                    empty_cells.append(row * 3 + col)
                        board_display += f"\n🎲 Available moves: {empty_cells}"
                        
                        # Check for immediate threats/opportunities
                        threats = []
                        opportunities = []
                        
                        # Quick analysis for wins/blocks (simplified)
                        lines = [
                            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],  # rows
                            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],  # cols  
                            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)]  # diagonals
                        ]
                        
                        for line in lines:
                            x_count = sum(1 for r,c in line if board[r][c] == 'x')
                            o_count = sum(1 for r,c in line if board[r][c] == 'o')
                            empty_count = sum(1 for r,c in line if board[r][c] == '')
                            
                            if x_count == 2 and empty_count == 1:  # Can win
                                for r,c in line:
                                    if board[r][c] == '':
                                        opportunities.append(r*3+c)
                            elif o_count == 2 and empty_count == 1:  # Must block
                                for r,c in line:
                                    if board[r][c] == '':
                                        threats.append(r*3+c)
                        
                        if opportunities:
                            board_display += f"\n🎯 WIN OPPORTUNITIES: {list(set(opportunities))}"
                        if threats:
                            board_display += f"\n🚨 BLOCK THREATS: {list(set(threats))}"
                    
                    return board_display
                else:
                    return "❌ Failed to get game status"
            except Exception as e:
                if "timeout" in str(e).lower() or "timeoutexception" in str(e):
                    ttt_driver_manager.close_driver()  # Reset driver on timeout
                    return "⏱️ Website loading timeout - try again or check connection"
                else:
                    return f"❌ Error getting game status: {str(e)}"
        elif tool_name == "getWinningNumber":
            driver = ttt_driver_manager.get_driver()
            result = getWinningNumber(driver=driver)
            return f"🏆 Winning number: {result}" if result else "❌ No winning number found"
        elif tool_name == "start_new_tictactoe_game":
            # Force a completely fresh game by refreshing and clearing cache
            driver = ttt_driver_manager.get_driver()
            driver.delete_all_cookies()  # Clear cookies
            driver.refresh()  # Refresh to clear DOM state
            driver.get("https://ttt.puppy9.com/")  # Navigate to fresh game
            return "🎮 Started fresh tic-tac-toe game (cleared cache)"
        elif tool_name == "close_tictactoe_browser":
            ttt_driver_manager.close_driver()
            return "🔒 Closed tic-tac-toe browser"
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"





