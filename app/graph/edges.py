from app.graph.state import ResearchState

"""
To re route back if critic is not satisfied
"""

MAX_LOOPS = 3
def route_after_critic(state: ResearchState) -> str:
    """
    Routes from the critic node: back to researcher if the answer quality
    is insufficient, otherwise forward to writer. Caps retries at MAX_LOOPS
    so a persistently low rating can't loop forever.
    """
    if state.rating > 3 or state.loop_count >= MAX_LOOPS:
        return "writer"
    return "researcher"