from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.graph.edges import route_after_critic
from app.graph.nodes import planner, researcher, critic, writer

builder = StateGraph(ResearchState)

builder.add_node('planner', planner)
builder.add_node('researcher', researcher)
builder.add_node('critic', critic)
builder.add_node('writer', writer)

builder.add_edge(START, 'planner')
builder.add_edge('planner', 'researcher')
builder.add_edge('researcher', 'critic')

builder.add_conditional_edges('critic', route_after_critic, {"writer": "writer", "researcher": "researcher"})
builder.add_edge('writer', END)

graph = builder.compile()