import asyncio
from groq import APIConnectionError, APIStatusError

"""
Retry logic if some error comes up
"""
async def invoke_with_retry(llm_call, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return await llm_call(*args, **kwargs)
        except (APIConnectionError, APIStatusError) as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"Groq call failed ({e}), retrying in {wait}s...")
            await asyncio.sleep(wait)


"""
For parallel processing of the workflow.
"""
MCP_CONCURRENCY_LIMIT = 2

async def research_topic(topic: str, question: str, llm_with_tools, tools, semaphore: asyncio.Semaphore) -> str:
    async with semaphore:
        tool_prompt = f"""You are researching the topic: "{topic}" for the question: "{question}"

You have three tools available:
- web_search: general web results, good for current events, practical/applied info
- arxiv_search: academic papers, good for technical/theoretical concepts
- semantic_scholar_search: academic papers with citation counts, good for established/foundational theory

Pick the most appropriate tool(s) for this topic and call them to gather information."""

        response = await invoke_with_retry(llm_with_tools.ainvoke, tool_prompt)

        if not response.tool_calls:
            return f"Topic: {topic}\nNo tool was called - model responded directly:\n{response.content}"

        parts = [f"Topic: {topic}"]
        for call in response.tool_calls:
            tool = next((t for t in tools if t.name == call["name"]), None)
            if tool is None:
                continue
            try:
                result = await tool.ainvoke(call["args"])
                parts.append(f"Source: {call['name']}\n{result}")
            except Exception as e:
                parts.append(f"Source: {call['name']}\nError: {e}")

        return "\n".join(parts)