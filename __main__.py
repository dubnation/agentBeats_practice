import uvicorn
import os
import time

# Force Pacific Standard Time timezone (CRITICAL for tic-tac-toe validation)
os.environ['TZ'] = 'US/Pacific'
if hasattr(time, 'tzset'):
    time.tzset()
    print("✓ System timezone set to US/Pacific")

# Verify timezone is correctly set
import datetime
current_time = datetime.datetime.now()
print(f"✓ Current system time: {current_time} (should be Pacific time)")

# Additional environment variables for timezone consistency
os.environ['LC_TIME'] = 'en_US.UTF-8'
os.environ['LANG'] = 'en_US.UTF-8'

try:
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentSkill,
    )
    from starlette.middleware.cors import CORSMiddleware
    print("✓ a2a modules and CORS middleware imported")
except ImportError as e:
    print(f"✗ Failed to import a2a modules: {e}")
    exit(1)

try:
    from agent_executor import (
        AgentBeatsPracticeAgentExecutor,  # type: ignore[import-untyped]
    )
    print("✓ agent_executor imported")
except ImportError as e:
    print(f"✗ Failed to import agent_executor: {e}")
    exit(1)

if __name__ == '__main__':
    print("Creating agent configuration...")
    
    try:
        # --8<-- [start:AgentSkill]
        arithmetic_skill = AgentSkill(
            id='basic_arithmetic_operations',
            name='Arithmetic Skill',
            description='Returns answers to basic arithmetic operations',
            tags=['arithmetic', 'basic'],
            examples=['6', '-3', '0', '452', '12344'],
        )
        
        crypto_skill = AgentSkill(
            id='cryptographic_operations',
            name='Cryptographic Tools',
            description='Generate MD5 and SHA512 hashes of text',
            tags=['hash', 'crypto', 'md5', 'sha512'],
            examples=['d41d8cd98f00b204e9800998ecf8427e', 'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e'],
        )
        
        encoding_skill = AgentSkill(
            id='encoding_operations',
            name='Encoding Tools',
            description='Encode and decode base64 data',
            tags=['encoding', 'base64', 'decode'],
            examples=['SGVsbG8gV29ybGQ=', 'Hello World'],
        )
        
        code_execution_skill = AgentSkill(
            id='code_execution',
            name='Code Execution',
            description='Write and execute Python code to solve complex computational problems, algorithms, and mathematical calculations',
            tags=['python', 'code', 'algorithms', 'computation', 'prime', 'math'],
            examples=['Finding prime numbers up to 100', 'Computing factorial of 50', 'Sum of squares modulo 1000', 'Fibonacci sequence'],
        )
        
        conversation_history_skill = AgentSkill(
            id='conversation_history',
            name='Conversation History',
            description='Access and review previous client inputs stored in a local SQLite database for context and reference',
            tags=['history', 'database', 'memory', 'context', 'previous', 'sqlite'],
            examples=['Show me the last 5 things I asked', 'What did we discuss earlier?', 'Review previous requests', 'Check conversation history'],
        )

        image_understanding_skill = AgentSkill(
            id='image_understanding',
            name='Image Understanding',
            description='Analyze and describe images, identify objects, text, scenes, and answer questions about image content',
            tags=['image', 'vision', 'recognition', 'analysis', 'OCR'],
            examples=['What is in this image?', 'Describe this picture', 'Read the text in this image', 'Identify objects in the photo'],
        )
        
        tictactoe_skill = AgentSkill(
            id='tictactoe_game',
            name='Tic-Tac-Toe Gaming',
            description='Play tic-tac-toe games on https://ttt.puppy9.com/, win games strategically, and extract 14-digit winning numbers',
            tags=['gaming', 'tictactoe', 'strategy', 'winning', 'automation'],
            examples=['20250902101461', 'Play tic-tac-toe and get winning number', 'Win the game at ttt.puppy9.com'],
        )
        print("✓ Agent skills created")

        # --8<-- [start:AgentCard]
        # This will be the public-facing agent card
        public_agent_card = AgentCard(
            name='Agent Beats Practice Agent',
            description='A versatile AI assistant that can perform arithmetic calculations, generate cryptographic hashes (MD5, SHA512), handle base64 encoding/decoding operations, execute Python code to solve complex computational problems, access conversation history from a local database, analyze images and provide descriptions, and play tic-tac-toe games to win 14-digit numbers',
            url='http://localhost:3000/',
            version='1.0.0',
            default_input_modes=['text', 'image'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[arithmetic_skill, crypto_skill, encoding_skill, code_execution_skill, conversation_history_skill, image_understanding_skill, tictactoe_skill],
            supports_authenticated_extended_card=True,
        )
        print("✓ Agent card created")
        # --8<-- [end:AgentCard]

        # This will be the authenticated extended agent card
        # It includes the additional 'extended_skill'

        request_handler = DefaultRequestHandler(
            agent_executor=AgentBeatsPracticeAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        print("✓ Request handler created")

        server = A2AStarletteApplication(
            agent_card=public_agent_card,
            http_handler=request_handler,
        )
        print("✓ A2A server application created")
        
        # Add CORS middleware to handle cross-origin requests
        # Build the server application
        app = server.build()
        
        # Add CORS (Cross-Origin Resource Sharing) middleware
        # This allows web browsers from different domains/origins to access our API
        # The "*" means we're allowing all domains to access it (good for development, but should be restricted in production)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for development
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods including OPTIONS
            allow_headers=["*"],  # Allow all headers
        )
        print("✓ CORS middleware added")
        
        # Import what we need to create a basic homepage endpoint
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        
        # Create a handler function for the homepage that returns basic server info
        async def root_handler(request):
            return JSONResponse({
                "message": "Agent Beats Practice Agent is running!",
                "status": "online",
                "endpoints": {
                    "agent_card": "/.well-known/agent-card.json",  # Endpoint that describes the agent's capabilities
                    "a2a_rpc": "/a2a",  # Main endpoint for agent-to-agent communication
                }
            })
        
        # Add the homepage route as the first route
        app.routes.insert(0, Route("/", root_handler, methods=["GET"]))
        print("✓ Root handler added")
        
        # Start the server using uvicorn
        # 0.0.0.0 means accept connections from any IP address
        # Port 3000 is where the server will listen for requests
        print("Starting server on http://0.0.0.0:3000...")
        uvicorn.run(app, host='0.0.0.0', port=3000)
        
    except Exception as e:
        print(f"✗ Error creating server: {e}")
        import traceback
        traceback.print_exc()