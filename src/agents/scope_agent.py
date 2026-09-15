from src.agents.base_agent import BaseAgent


class ScopeExtractionAgent(BaseAgent):
    agent_name = "scope_agent"
    retrieval_query = "project scope deliverables goals objectives overview purpose milestones timeline"
    additional_queries = ["team member responsibilities task owners assigned action items"]
    system_instructions = """You are a project scope analyst. Extract structured scope information from the provided project content.

Return JSON in exactly this shape:
{
  "project_goals": ["..."],
  "deliverables": ["..."],
  "milestones": [{"name": "...", "timeframe": "..."}],
  "responsibilities": [{"owner": "...", "responsibility": "..."}]
}
If a field cannot be determined from the content, return an empty list for it."""