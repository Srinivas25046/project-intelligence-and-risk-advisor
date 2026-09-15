from src.agents.base_agent import BaseAgent


class BlockerActionItemAgent(BaseAgent):
    agent_name = "blocker_agent"
    retrieval_query = "blockers pending decisions unresolved issues action items meeting notes"
    additional_filters = [{"status": "Blocked"}]
    system_instructions = """You are a project coordinator. Extract blockers and action items from the provided project content.

IMPORTANT CLASSIFICATION RULE: any task or item with a status of "Blocked"
MUST be included in the "blockers" array (describing what it is blocking),
in addition to appearing in "action_items" with its actual status.

Return JSON in exactly this shape:
{
  "blockers": [{"description": "...", "blocking": "...", "source": "..."}],
  "action_items": [{"task": "...", "owner": "...", "status": "..."}]
}
Use the exact status value given in the source data when present (e.g. "Blocked", "In Progress", "Done", "Not Started"). Only use "Not specified" when no status is given at all."""