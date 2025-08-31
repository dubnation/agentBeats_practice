import uvicorn

try:
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentSkill,
    )
    print("✓ a2a modules imported")
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
        skill = AgentSkill(
            id='basic_arithmetic_operations',
            name='Arithmetic Skill',
            description='Returns answers to basic arithmetic operations',
            tags=['airthmetic', 'basic'],
            examples=['6', '-3', '0', '452', '12344'],
        )
        print("✓ Agent skill created")

        # --8<-- [start:AgentCard]
        # This will be the public-facing agent card
        public_agent_card = AgentCard(
            name='Agent Beats Practice Agent',
            description='Completes various practice tasks',
            url='http://localhost:3000/.well-known/agent-card.json',
            version='1.0.0',
            default_input_modes=['text'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],  # Only the basic skill for the public card
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
        
        print("Starting server on http://0.0.0.0:3000...")
        uvicorn.run(server.build(), host='0.0.0.0', port=3000)
        
    except Exception as e:
        print(f"✗ Error creating server: {e}")
        import traceback
        traceback.print_exc()