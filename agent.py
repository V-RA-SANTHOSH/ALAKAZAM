import os
import re
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()

# --- 1. State Definition ---
class AgentState(TypedDict):
    query: str
    plan: str
    research: str
    verdict: str

# --- 2. Tools & Model ---
# We use the 2026-standard Llama 3.3 70B for high-reasoning forensic tasks
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
search = DuckDuckGoSearchRun()

# Helper: Local Regex DOI Check
def get_doi_status(text: str):
    doi_pattern = r'10.\d{4,9}/[-._;()/:A-Z0-9]+'
    dois = re.findall(doi_pattern, text, re.IGNORECASE)
    return f"DOIs_FOUND: {', '.join(dois)}" if dois else "NO_DOI_FOUND"

# --- 3. Node Definitions ---

def plan_research(state: AgentState):
    """
    Forensic Planner: Creates both Exact and Broad queries to prevent 
    false positives for famous papers while catching fakes.
    """
    prompt = f"""
    The user provided these citations/claims: {state['query']}
    
    TASK: Generate search queries to verify existence.
    For each item, generate:
    1. An EXACT query in quotes: "Full Title of Paper"
    2. A BROAD query: Author Name + Journal + Year
    
    Output ONLY the queries, one per line. Do not add numbers or bullets.
    """
    res = llm.invoke(prompt)
    return {"plan": res.content}

def web_search(state: AgentState):
    """
    Researcher: Executes queries. If the query is long, it truncates to 
    fit search engine limits.
    """
    # We take the first 4 queries from the plan to keep it fast
    queries = state["plan"].strip().split("\n")[:5]
    search_results = ""
    for q in queries:
        try:
            search_results += f"\n--- Search for: {q} ---\n"
            search_results += search.run(q)
        except:
            continue
            
    doi_info = get_doi_status(state['query'])
    return {"research": f"{search_results}\n\n[System_Internal_Check]: {doi_info}"}

def finalize(state: AgentState):
    """
    Adjudicator: The 'Judge' with 2026 context. 
    Uses a strict table format for line-by-line accountability.
    """
    prompt = f"""
    ROLE: Forensic Citation Auditor (Strict Mode)
    CURRENT DATE: January 4, 2026
    
    INPUT LIST: {state['query']}
    SEARCH EVIDENCE: {state['research']}
    
    STRICT VERDICT RULES:
    1. If a citation's EXACT TITLE is not found in the search evidence, check if the Author/Journal is real.
    2. If the Author is real but the Title is missing, mark as HALLUCINATION (likely a 'fake title' attributed to a real person).
    3. Famous papers (e.g., Vaswani 2017 'Attention is All You Need') must be marked REAL.
    4. 2025/2026 data must be verified against current events (e.g., 2025 OBBB Tax Act, 2024 Nobel Prizes).

    OUTPUT FORMAT:
    | # | Citation/Claim | Verdict | Specific Reason |
    |---|----------------|---------|-----------------|
    (Audit every single line)

    OVERALL SUMMARY: [Short summary of findings]
    """
    res = llm.invoke(prompt)
    return {"verdict": res.content}

# --- 4. Graph Construction ---
builder = StateGraph(AgentState)
builder.add_node("planner", plan_research)
builder.add_node("researcher", web_search)
builder.add_node("adjudicator", finalize)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "adjudicator")
builder.add_edge("adjudicator", END)

fact_checker_app = builder.compile()