from app.graph.llm import llm, critic_llm
from app.graph.state import ResearchState, CriticOutput
from app.mcp_client import mcp_client
from app.graph.utils import invoke_with_retry, research_topic
import asyncio
import time

def planner(state: ResearchState) -> dict:
    """
    The planner node generates a research plan based on the research question.
    It populates the topics field in the ResearchState with relevant topics.
    """
    prompt = f"""A research question: '{state.question}' is provided, you're a researcher planning to report on the question.
Your task is to generate a set of 3-5 topics that are HIGHLY relevant and specific to the research question, avoiding general or vague terms.
Return ONLY the topics, separated by commas, with no numbering, no extra text, no explanation."""

    response = llm.invoke(prompt)
    topics = [t.strip() for t in response.content.split(",") if t.strip()]

    return {"topics": topics}

start = time.time()
async def researcher(state: ResearchState) -> dict:
    tools = await mcp_client.get_tools()
    llm_with_tools = llm.bind_tools(tools)

    semaphore = asyncio.Semaphore(1)

    search_context = await asyncio.gather(
        *(research_topic(topic, state.question, llm_with_tools, tools, semaphore) for topic in state.topics)
    )

    combined_context = "\n\n---\n\n".join(search_context)

    feedback_note = ""
    if state.critic_feedback:
        feedback_note = f"""

IMPORTANT — your previous attempt was rejected. Address this feedback specifically:
{state.critic_feedback}"""

    synthesis_prompt = f"""You are a seasoned researcher. Using the search results below, write a
well-organized, point-wise document (max 1000-1500 words) covering theories, principles, and
concepts relevant to each topic for the question: "{state.question}"

Group content clearly by topic. Cite sources (paper titles, URLs) where the search results provide them.{feedback_note}

Search results:
{combined_context}"""

    response = await invoke_with_retry(llm.ainvoke, synthesis_prompt)
    print(f"researcher took {time.time() - start:.1f}s")
    return {"answer": response.content, "loop_count": state.loop_count + 1}


def critic(state: ResearchState) -> dict:
    """
    Rates the researcher's answer out of 5 against the topics and question,
    and provides feedback to guide a retry if the rating is insufficient.
    """
    prompt = f"""You are a strict panelist reviewing a research report for a conference.

Question being addressed: {state.question}
Topics that should be covered: {state.topics}

Report to review:
{state.answer}

Rate this report from 0-5 based on:
- Coverage: does it address every topic listed?
- Accuracy: are the claims well-supported and plausible?
- Depth: is each topic explained with real substance, not just surface-level mentions?

Then give specific, actionable feedback. If the rating is below 3, the feedback must
clearly state what's missing or weak so the researcher can improve it on a retry.

Respond with ONLY a JSON object in exactly this format, no other text:
{{"rating": <integer 0-5>, "feedback": "<your feedback as a single string>"}}"""

    structured_llm = critic_llm.with_structured_output(CriticOutput, method="json_mode")
    result = structured_llm.invoke(prompt)

    return {
        "rating": result.rating,
        "critic_feedback": result.feedback,
    }

def writer(state: ResearchState) -> dict:
    """
    Synthesizes the researched answer into a polished, well-structured final report
    for the given research question.
    """

    prompt = f"""You are a professional report writer. Turn the raw research notes below into a
polished, well-structured final report for the question: "{state.question}"

Topics covered: {state.topics}

Raw research notes:
{state.answer}

Requirements:
- Write a clear title and a brief 2-3 sentence executive summary at the top
- Organize the body under clear headings, one per topic
- Keep the technical substance from the research notes — do not remove facts, do not oversimplify
- Rewrite for clarity and flow, but preserve all citations/sources mentioned in the notes
- Close with a short conclusion tying the topics back to the original question
- Target length: 800-1200 words

Return only the final report text, no preamble like "Here is the report"."""

    response = llm.invoke(prompt)

    return {
        "report": response.content
    }
