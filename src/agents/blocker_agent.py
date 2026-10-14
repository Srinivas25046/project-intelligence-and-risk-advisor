from src.agents.base_agent import BaseAgent


class BlockerActionItemAgent(BaseAgent):
    agent_name = "blocker_agent"
    retrieval_query = "blockers pending decisions unresolved issues action items meeting notes"
    additional_queries = ["newly reported issues or defects from the latest progress update"]
    additional_filters = [{"status": "Blocked"}]
    system_instructions = """You are a project coordinator. Extract blockers and action items from the provided project content.

IMPORTANT CLASSIFICATION RULES
1. Any task or item with a status of "Blocked" MUST be included in the "blockers" array
   (describing what it is blocking), in addition to appearing in "action_items" with its actual status.
2. Only list blockers that are STILL ACTIVE. Documents may carry dates; when documents disagree,
   trust the most recently dated one. If a later update says a blocker has been resolved or lifted,
   do NOT list it in "blockers" (you may still list the related action item with a "Done" status).
3. Merge duplicates: the same blocker mentioned in several documents is ONE entry.

Return JSON in exactly this shape:
{
  "blockers": [{"description": "...", "blocking": "...", "source": "..."}],
  "action_items": [{"task": "...", "owner": "...", "status": "..."}]
}
Use the exact status value given in the source data when present (e.g. "Blocked", "In Progress", "Done", "Not Started"). Only use "Not specified" when no status is given at all."""