import json
from dotenv import load_dotenv

load_dotenv()

from src.agents.scope_agent import ScopeExtractionAgent
from src.agents.risk_agent import RiskForecastingAgent
from src.agents.blocker_agent import BlockerActionItemAgent

if __name__ == "__main__":
    agents = [
        ScopeExtractionAgent(),
        RiskForecastingAgent(),
        BlockerActionItemAgent(),
    ]

    for agent in agents:
        print("=" * 80)
        print(f"AGENT: {agent.agent_name}")
        print("=" * 80)
        result = agent.run()
        print(json.dumps(result, indent=2))
        print()