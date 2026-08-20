from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.graph.edges import Edge

builder = StateGraph(ResearchState)

builder.add_node('planner', planner)
builder.add_node('researcher', researcher)
builder.add_node('critic', critic)
builder.add_node('writer', writer)
builder.add_node('evaluator', evaluator)

builder.add_edge(START, 'planner')
builder.add_edge('planner', 'researcher')
builder.add_edge('researcher', 'critic')

builder.add_conditional_edges('critic', Edge.route_after_critic, {"writer": "writer", "researcher": "researcher"})
builder.add_edge('writer', 'evaluator')
builder.add_edge('evaluator', END)

graph = builder.compile()