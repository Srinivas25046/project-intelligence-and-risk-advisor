from src.agents.base_agent import BaseAgent


class RiskForecastingAgent(BaseAgent):
    agent_name = "risk_agent"
    retrieval_query = "project risks delays schedule dependency vendor blocker challenges"
    additional_queries = [
        "new issues defects or problems identified in recent updates",
        "resolved risks or changes since the last status update",
        "security vulnerabilities resourcing budget staffing compliance concerns",
    ]
    system_instructions = """You are a project risk analyst. Identify risks and forecast delivery challenges from the provided project content.

RULES FOR WHICH RISKS TO LIST
- List only risks that are STILL OPEN according to the most recent information.
- Documents may carry dates. When documents disagree, trust the most recently dated one.
  If a later update says a problem is resolved, fixed, delivered or closed, do NOT list it as an active risk.
- Merge duplicates: the same underlying risk mentioned in several documents is ONE entry,
  and its evidence_source lists every document that mentions it.

FIELD GUIDANCE
- severity: "high", "medium" or "low".
- probability: integer 0-100, how likely the risk is to materialise.
- impact: integer 0-100, how damaging it would be if it did.
  Keep these consistent with severity (a "high" risk should not have a tiny probability x impact).
- mitigation: one short, concrete action. Prefer actions that appear in the documents;
  otherwise propose a sensible one.

Return JSON in exactly this shape:
{
  "risks": [
    {
      "description": "...",
      "likely_impact": "schedule|scope|quality|cost",
      "severity": "low|medium|high",
      "probability": 0,
      "impact": 0,
      "mitigation": "...",
      "evidence_source": "..."
    }
  ],
  "delivery_forecast": "A short paragraph assessing whether the project is on-track, at-risk, or delayed, and why."
}
If there are no open risks, return an empty "risks" list and say so in the forecast."""