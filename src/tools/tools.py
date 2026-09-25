from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS
import arxiv
import requests

mcp = FastMCP("research-tools")

@mcp.tool()
def web_search(query: str, max_results: int = 5)->str:
    """Search the web for a query and return summarized results."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results = max_results))

    if not results:
        return "No result found."

    formatted = []
    for r in results:
        formatted.append(f"Title: {r['title']} \n Snippet: {r['body']}\n URL: {r['href']}")

    return "\n\n".join(formatted)


@mcp.tool()
def arxiv_search(query: str, max_results: int = 5) -> str:
    """Search arXiv for academic papers relevant to a query. Returns title, authors, abstract, and PDF Links"""
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    results = list(client.results(search))
    if not results:
        return "No Papers Found."

    formatted = []
    for r in results:
        authors = ", ".join(a.name for a in r.authors[:3])
        formatted.append(
            f"Title: {r.title}\n"
            f"Authors: {authors}\n"
            f"Published: {r.published.strftime('%Y-%m-%d')}\n"
            f"Abstract: {r.summary[:400]}...\n"
            f"PDF: {r.pdf_url}"
        )

    return "\n\n".join(formatted)

@mcp.tool()
def semantic_scholar_search(query: str, max_results: int=5)->str:
    """Search Semantic Scholar for academic papers. Returns title, authors, year, abstract, and citation count."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,year,abstract,citationCount,url",
    }

    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        return f"Semantic Scholar search failed: {response.status_code}"

    data = response.json().get("data", [])
    if not data:
        return "No papers found."

    formatted = []
    for p in data:
        authors = ", ".join(a["name"] for a in p.get("authors", [])[:3])
        abstract = (p.get("abstract") or "No abstract available.")[:400]
        formatted.append(
            f"Title: {p.get('title')}\n"
            f"Authors: {authors}\n"
            f"Year: {p.get('year')}\n"
            f"Citations: {p.get('citationCount')}\n"
            f"Abstract: {abstract}...\n"
            f"URL: {p.get('url')}"
        )
    return "\n\n".join(formatted)