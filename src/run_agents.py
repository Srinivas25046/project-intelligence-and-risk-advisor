import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import json
from dotenv import load_dotenv

load_dotenv()

from src.agents.scope_agent import ScopeExtractionAgent
from src.agents.risk_agent import RiskForecastingAgent
from src.agents.blocker_agent import BlockerActionItemAgent
from src.insights_store import save_insight

if __name__ == "__main__":
    agents = {
        "scope": ScopeExtractionAgent(),
        "risks": RiskForecastingAgent(),
        "blockers": BlockerActionItemAgent(),
    }

    for name, agent in agents.items():
        print("=" * 80)
        print(f"AGENT: {agent.agent_name}")
        print("=" * 80)
        try:
            result = agent.run()
            print(json.dumps(result, indent=2))
            save_insight(name, result)
        except Exception as e:
            print(f"[{agent.agent_name}] All providers failed: {e}")
            print("(Continuing to next agent rather than stopping the whole run.)")
        print()