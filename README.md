# Agent Beats Practice 🤖

A versatile AI agent built with Claude (Anthropic) that can perform mathematical calculations, cryptographic operations, code execution, and autonomously play tic-tac-toe games to extract winning numbers.

This agent is designed to work with the **[Agent Programming Exercise (APE)](https://ape.llm.phd/)** evaluation toolkit, which tests AI agents across 6 different capabilities including math, tool use, image understanding, web browsing, code execution, and memory tasks.

## 🚀 Features

### Core Capabilities
- **Arithmetic & Math**: Complex mathematical calculations and problem solving
- **Cryptographic Tools**: MD5 and SHA512 hash generation
- **Base64 Encoding/Decoding**: Text encoding and decoding operations
- **Python Code Execution**: Execute Python code for computational problems
- **Conversation History**: SQLite database for storing and retrieving chat history
- **Image Analysis**: Analyze and describe images using Claude's vision capabilities

### 🎮 Tic-Tac-Toe Gaming
- **Autonomous Gameplay**: AI agent plays tic-tac-toe strategically on https://ttt.puppy9.com/
- **Strategic Decision Making**: Implements optimal tic-tac-toe strategy with priority-based moves
- **Winning Number Extraction**: Automatically extracts 14-digit winning codes after victories
- **Enhanced Board Visualization**: Clear 3x3 grid display with position numbers and strategic analysis
- **Browser Automation**: Uses Selenium WebDriver for game interaction

## 🛠️ Technology Stack

- **AI Model**: Claude 3.5 Sonnet (Anthropic)
- **Framework**: a2a-sdk (Agent-to-Agent communication)
- **Web Framework**: Starlette with CORS support
- **Database**: SQLite3 for conversation history
- **Browser Automation**: Selenium WebDriver (Chrome)
- **Testing**: pytest with comprehensive test coverage

## 📦 Installation

### Prerequisites
- Python 3.11+
- Google Chrome browser
- ChromeDriver (automatically managed by Selenium)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd agentBeats_practice
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. **Run the server**
   ```bash
   python __main__.py
   ```

The server will start on `http://0.0.0.0:3000`

## 🎯 Usage

### Starting the Agent
```bash
python __main__.py
```

### Available Tools

#### Mathematical Operations
- Basic arithmetic and complex calculations
- Prime number generation
- Mathematical sequences (Fibonacci, etc.)

#### Cryptographic Operations
```python
# Example requests:
"Generate MD5 hash of 'hello world'"
"Create SHA512 hash for my password"
```

#### Encoding/Decoding
```python
# Example requests:
"Encode 'Hello World' to base64"
"Decode SGVsbG8gV29ybGQ= from base64"
```

#### Code Execution
```python
# Example request:
"Calculate the first 10 prime numbers using Python"
# The agent will write and execute Python code to solve this
```

#### Tic-Tac-Toe Gaming
```python
# Example request:
"Play tic-tac-toe and get me a winning number"
```

The agent will:
1. Navigate to https://ttt.puppy9.com/
2. Play strategically using optimal tic-tac-toe strategy
3. Win the game
4. Extract the 14-digit winning number
5. Return the number in format: "🏆 Victory! Winning number: 20250902104856"

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Tic-Tac-Toe Specific Tests
```bash
python test_tictactoe_tool.py
```

### Run Focused Tic-Tac-Toe Tests
```bash
python test_tictactoe_tool.py focus
```

## 🔧 Configuration

### Timezone Settings
The agent is configured for **Pacific Standard Time (PST)** to ensure proper tic-tac-toe winning number validation:

```python
# Automatically set in __main__.py and agent_executor.py
os.environ['TZ'] = 'US/Pacific'
```

### Browser Settings
- **Headless Mode**: Disabled by default (browser visible for debugging)
- **Cache**: Disabled to prevent stale winning numbers
- **Timezone**: Forced to America/Los_Angeles for consistent validation

### Performance Settings
- **Max Iterations**: 15 (prevents infinite loops)
- **Context Messages**: 20 (balances memory vs performance)
- **Code Execution Timeout**: 30 seconds
- **Browser Timeouts**: 15 seconds

## 📁 Project Structure

```
agentBeats_practice/
├── __main__.py              # Server entry point and configuration
├── agent_executor.py        # Core AI agent logic and Claude integration
├── tools.py                # Tool definitions and execution functions
├── tictactoe_tool.py       # Tic-tac-toe game automation functions
├── test_tictactoe_tool.py  # Comprehensive tic-tac-toe tests
├── test_anthropic.py       # Claude API integration tests
├── view_history.py         # Database history viewer utility
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🎮 Tic-Tac-Toe Strategy

The agent implements optimal tic-tac-toe strategy with the following priority order:

1. **🏆 Immediate Win**: Complete 3 X's in a line
2. **🚨 Block Threat**: Block opponent from winning  
3. **🎯 Create Fork**: Create multiple winning opportunities
4. **🛡️ Block Fork**: Prevent opponent forks
5. **🎯 Center**: Take center position (strongest)
6. **🏗️ Opposite Corner**: Take opposite corner if opponent has corner
7. **🏗️ Empty Corner**: Take any corner (strong positions)
8. **🏗️ Side**: Take sides as last resort

### Board Layout
```
Position numbers:
 0 | 1 | 2 
-----------
 3 | 4 | 5 
-----------
 6 | 7 | 8 
```

## 🧪 APE Evaluation Compatibility

This agent is fully compatible with the **[Agent Programming Exercise (APE)](https://ape.llm.phd/)** evaluation platform and handles all 6 test categories:

### Test Coverage
1. **🧮 Elementary Math Problems**: Uses built-in arithmetic capabilities and code execution
2. **🔧 Tool Use (SHA512/MD5)**: Implements cryptographic hash generation tools
3. **👁️ Image Understanding**: Leverages Claude's vision capabilities for image analysis
4. **🎮 Web Browsing (Tic-Tac-Toe)**: Autonomous tic-tac-toe gameplay with winning number extraction
5. **💻 Code Generation**: Python code execution for algorithm implementation
6. **🧠 Memory Tasks**: SQLite-based conversation history for cross-session persistence

### APE Integration
- **A2A Protocol**: Full support for agent-to-agent communication
- **Evaluation Endpoints**: Compatible with APE's testing infrastructure
- **Performance Optimized**: Configured for APE's 3-minute evaluation timeframe

## 🤝 API Integration

The agent supports **a2a (Agent-to-Agent)** protocol for communication with other AI agents and the APE evaluation platform:

- **Agent Card**: `/.well-known/agent-card.json`
- **RPC Endpoint**: `/a2a`
- **Homepage**: `/` (server status and endpoints)

## 🔍 Troubleshooting

### Common Issues

1. **"No module named 'selenium'"**
   ```bash
   pip install selenium
   ```

2. **ChromeDriver issues**
   - Selenium automatically manages ChromeDriver
   - Ensure Chrome browser is installed

3. **Anthropic API issues**
   - Verify `ANTHROPIC_API_KEY` is set correctly
   - Check API key has sufficient credits

4. **Tic-tac-toe timing issues**
   - System must be in Pacific timezone
   - Winning numbers must be validated within 5 minutes

### Debug Mode
- Browser runs in **visible mode** by default for debugging
- Enable headless mode by uncommenting in `tools.py`:
  ```python
  chrome_options.add_argument("--headless")
  ```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Commit your changes: `git commit -m 'Add some feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **Anthropic** for Claude AI model
- **a2a-sdk** for agent communication framework
- **Selenium** for browser automation
- **https://ttt.puppy9.com/** for the tic-tac-toe testing platform

---

**Built with ❤️ for AI agent experimentation and learning**