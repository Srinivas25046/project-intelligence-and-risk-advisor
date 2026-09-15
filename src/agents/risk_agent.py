from src.agents.base_agent import BaseAgent


class RiskForecastingAgent(BaseAgent):
    agent_name = "risk_agent"
    retrieval_query = "project risks delays schedule dependency vendor blocker challenges"
    system_instructions = """You are a project risk analyst. Identify risks and forecast delivery challenges from the provided project content.

Return JSON in exactly this shape:
{
  "risks": [
    {"description": "...", "likely_impact": "schedule|scope|quality|cost", "severity": "low|medium|high", "evidence_source": "..."}
  ],
  "delivery_forecast": "A short paragraph assessing whether the project is on-track, at-risk, or delayed, and why."
}"""