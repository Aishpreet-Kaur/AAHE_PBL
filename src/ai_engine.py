# from db_manager import (
    get_last_fetch_time,
    update_confidence,
    get_hypothesis_by_id
)
from livenews import fetch_latest_news
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from datetime import datetime, date

from typing import List, Dict, Tuple
import json

ROOT = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(ROOT, ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))



def search_web_sources(topic: str, max_results: int = 5) -> Tuple[List[Dict], str]:
    """
    Search the web for evidence and sources related to the topic.

    Returns:
        - List of source dictionaries
        - Formatted evidence text for the AI prompt
    """

    # Option 1: Using Serper API (recommended - $0.001 per search)
    serper_api_key = os.getenv("SERPER_API_KEY")

    if serper_api_key:
        return _search_with_serper(topic, serper_api_key, max_results)

    # Option 2: Using Google Custom Search (backup)
    google_cse_key = os.getenv("GOOGLE_CSE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")

    if google_cse_key and google_cse_id:
        return _search_with_google_cse(topic, google_cse_key, google_cse_id, max_results)

    # Option 3: Fallback to NewsAPI for news-based topics
    news_api_key = os.getenv("NEWS_API_KEY")

    if news_api_key:
        return _search_with_newsapi(topic, news_api_key, max_results)

    # No API keys available
    return [], "⚠️ No web search API configured. Please add SERPER_API_KEY, GOOGLE_CSE_API_KEY, or NEWS_API_KEY to .env file."


def _search_with_serper(topic: str, api_key: str, max_results: int) -> Tuple[List[Dict], str]:
    """Search using Serper API (Best option - fast and comprehensive)"""

    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": topic,
        "num": max_results
    })

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers,
                                 data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        sources = []
        evidence_text = "📚 **Verified Web Sources:**\n\n"

        # Process organic results
        for idx, result in enumerate(data.get('organic', [])[:max_results], 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', '')
            url = result.get('link', '')

            # ML-based credibility analysis
            cred_result = _calculate_credibility(url, title, snippet)

            source = {
                'id': idx,
                'title': title,
                'url': url,
                'snippet': snippet,
                'date': result.get('date', 'N/A'),
                'position': result.get('position', idx),
                'credibility_score': cred_result['score'],
                'credibility_explanation': cred_result['explanation'],
                'credibility_components': cred_result['components']
            }

            sources.append(source)

            evidence_text += f"**[{idx}] {source['title']}**\n"
            evidence_text += f"   📍 Source: {source['url']}\n"
            evidence_text += f"   📅 Date: {source['date']}\n"
            evidence_text += f"   ⭐ Credibility: {source['credibility_score']:.2f}/10\n"
            evidence_text += f"   📝 Snippet: {source['snippet']}\n\n"

        return sources, evidence_text

    except Exception as e:
        return [], f"⚠️ Serper API error: {str(e)}"


def _search_with_google_cse(topic: str, api_key: str, cse_id: str, max_results: int) -> Tuple[List[Dict], str]:
    """Search using Google Custom Search Engine"""

    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        'key': api_key,
        'cx': cse_id,
        'q': topic,
        'num': min(max_results, 10)  # Google CSE max is 10
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        sources = []
        evidence_text = "📚 **Verified Web Sources:**\n\n"

        for idx, item in enumerate(data.get('items', []), 1):
            title = item.get('title', 'No title')
            snippet = item.get('snippet', '')
            url = item.get('link', '')

            # ML-based credibility analysis
            cred_result = _calculate_credibility(url, title, snippet)

            source = {
                'id': idx,
                'title': title,
                'url': url,
                'snippet': snippet,
                'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', 'N/A'),
                'credibility_score': cred_result['score'],
                'credibility_explanation': cred_result['explanation'],
                'credibility_components': cred_result['components']
            }

            sources.append(source)

            evidence_text += f"**[{idx}] {source['title']}**\n"
            evidence_text += f"   📍 Source: {source['url']}\n"
            evidence_text += f"   ⭐ Credibility: {source['credibility_score']:.2f}/10\n"
            evidence_text += f"   📝 Snippet: {source['snippet']}\n\n"

        return sources, evidence_text

    except Exception as e:
        return [], f"⚠️ Google CSE error: {str(e)}"


def _search_with_newsapi(topic: str, api_key: str, max_results: int) -> Tuple[List[Dict], str]:
    """Search using NewsAPI (news articles only)"""

    url = "https://newsapi.org/v2/everything"

    params = {
        'q': topic,
        'apiKey': api_key,
        'sortBy': 'relevancy',
        'pageSize': max_results,
        'language': 'en'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        sources = []
        evidence_text = "📰 **News Sources:**\n\n"

        for idx, article in enumerate(data.get('articles', []), 1):
            title = article.get('title', 'No title')
            snippet = article.get('description', '')
            url = article.get('url', '')

            # ML-based credibility analysis
            cred_result = _calculate_credibility(url, title, snippet)

            source = {
                'id': idx,
                'title': title,
                'url': url,
                'snippet': snippet,
                'date': article.get('publishedAt', 'N/A'),
                'source_name': article.get('source', {}).get('name', 'Unknown'),
                'credibility_score': cred_result['score'],
                'credibility_explanation': cred_result['explanation'],
                'credibility_components': cred_result['components']
            }

            sources.append(source)

            evidence_text += f"**[{idx}] {source['title']}**\n"
            evidence_text += f"   📰 Publisher: {source['source_name']}\n"
            evidence_text += f"   📅 Published: {source['date']}\n"
            evidence_text += f"   📍 URL: {source['url']}\n"
            evidence_text += f"   📝 Snippet: {source['snippet']}\n\n"

        return sources, evidence_text

    except Exception as e:
        return [], f"⚠️ NewsAPI error: {str(e)}"



def _calculate_credibility(url: str, title: str = "", snippet: str = "") -> dict:
    """
    ML-based credibility analysis using content features.
    Returns detailed scoring breakdown.
    """

    # Import ML analyzer
    try:
        from content_analyzer import analyze_content_credibility
    except ImportError:
        # Fallback if ML module not available
        return {
            'score': 6.0,
            'explanation': 'ML module not available',
            'components': {}
        }

    # If we don't have enough content, return baseline
    if not snippet or len(snippet.strip()) < 50:
        return {
            'score': 6.0,
            'explanation': 'Insufficient content for ML analysis',
            'components': {
                'hedging': 6.0,
                'citations': 6.0,
                'emotional': 6.0,
                'structure': 6.0
            }
        }

    # Run ML analysis
    ml_result = analyze_content_credibility(snippet, title)

    return {
        'score': ml_result['content_score'],
        'explanation': ml_result['explanation'],
        'components': {
            'hedging': ml_result['hedging_score'],
            'citations': ml_result['citation_score'],
            'emotional': ml_result['emotional_score'],
            'structure': ml_result['structure_score']
        }
    }

# ============================================================================
# ENHANCED AI PROMPT WITH CITATIONS
# ============================================================================


DETECTIVE_PROMPT_WITH_CITATIONS = """
Act as a relentless, methodical investigative detective analyzing verified evidence from multiple sources.

**CRITICAL INSTRUCTION:** For EVERY factual claim you make, you MUST cite the source using [1], [2], [3] etc. 
matching the source numbers provided below. Do NOT make claims without citations.

Your analysis must:
1. Separate VERIFIED FACTS (with citations) from HYPOTHESES (clearly labeled as speculation)
2. Provide confidence scores (0-100%) for each major claim
3. Cross-reference claims across multiple sources
4. Flag contradictions between sources
5. Identify information gaps that need further investigation

**EVIDENCE QUALITY ASSESSMENT:**
- Sources with credibility score 8.0+ are highly reliable
- Sources with credibility score 6.0-7.9 are moderately reliable
- Multiple independent sources confirming the same fact increases confidence
- Single-source claims should have lower confidence scores

**OUTPUT STRUCTURE:**
Write in clear narrative prose (NO tables, NO bullet lists). Structure your report as:

1. Executive Summary (2-3 paragraphs with key findings and citations)
2. Verified Facts (cite every claim with [source number])
3. Cross-Source Analysis (where sources agree/disagree)
4. Hypotheses & Speculation (clearly labeled, with reasoning)
5. Confidence Assessment (overall confidence in the analysis)
6. Investigation Gaps (what additional evidence is needed)
7. Write a comprehensive, detailed analysis with at least 800-1000 words. Be thorough and explain each point in depth while maintaining citations.

Case/Investigation Topic: {topic}

Custom Investigation Query: {custom_query}

{evidence_sources}

Remember: CITE EVERY FACT with [number]. Example: "According to recent reports [1][3], the policy was implemented..."
"""


def generate_hypotheses_with_evidence(topic: str, custom_query: str = None, max_sources: int = 5) -> Tuple[str, List[Dict]]:
    """
    Generate hypotheses with web-sourced evidence and citations.

    Returns:
        - Generated report text with citations
        - List of source dictionaries
    """

    # Step 1: Search for evidence
    sources, evidence_text = search_web_sources(topic, max_sources)

    # Step 2: Create enhanced prompt with evidence
    prompt = DETECTIVE_PROMPT_WITH_CITATIONS.format(
        topic=topic,
        custom_query=custom_query or "N/A",
        evidence_sources=evidence_text
    )

    # Step 3: Generate with Gemini
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    # Step 4: Safe response handling
    if not response.candidates:
        return "No response generated.", sources

    candidate = response.candidates[0]

    if not candidate.content or not candidate.content.parts:
        return "No textual content returned by the model.", sources

    text_parts = []
    for part in candidate.content.parts:
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

    if not text_parts:
        return "Model returned empty content.", sources

    report_text = "\n".join(text_parts)

    return report_text, sources


# ============================================================================
# BACKWARD COMPATIBILITY (Original function)
# ============================================================================

DETECTIVE_PROMPT = """
Act as a relentless, methodical investigative detective: ingest and index fresh reporting and primary records,
extract and canonicalize all relevant entities,
trace and quantify links across Money, Power, Influence, Lobbying, Corruption, Conspiracy, and Alleged Crimes,
produce provable facts with evidence and confidence scores,
and produce clearly-labelled hypotheses and prioritized leads for human review.

Executive summary: pages summarizing key findings, highest-priority hypotheses.

For the following case topic, write a detailed investigative analytic report.
Separate and label verifiable facts (with evidence and confidence scores) and speculative hypotheses.
Prioritize clarity, logical flow, depth, and separation of fact vs. hypothesis.
Do NOT use tables or bullet lists. Write as readable, structured narrative text.

Case/Investigation Topic: {topic}

If any user query or request is supplied, treat it as high priority: {custom_query}
"""


def generate_hypotheses(topic: str, custom_query: str = None) -> str:
    """Original function without web search - kept for backward compatibility"""

    prompt = DETECTIVE_PROMPT.format(
        topic=topic,
        custom_query=custom_query or "N/A"
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    if not response.candidates:
        return "No response generated."

    candidate = response.candidates[0]

    if not candidate.content or not candidate.content.parts:
        return "No textual content returned by the model."

    text_parts = []
    for part in candidate.content.parts:
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

    if not text_parts:
        return "Model returned empty content."

    return "\n".join(text_parts)



def temporal_update_engine(hypothesis_id: int):
    """
    Uses live news + web sources + existing Gemini reasoning
    to TEMPORALLY update hypothesis confidence
    """

    hypothesis = get_hypothesis_by_id(hypothesis_id)

    topic = hypothesis["topic"]
    old_conf = hypothesis["confidence"]
    last_time = hypothesis["last_updated"]

    # Fetch latest news
    articles = fetch_latest_news(topic, last_time)

    if not articles:
        return old_conf

    support, contradict = 0, 0

    for art in articles:
        # Use evidence-based analysis
        analysis, _ = generate_hypotheses_with_evidence(
            topic,
            custom_query=f"Does this new information support or contradict the hypothesis? Article: {art['content']}"
        )

        text = analysis.lower()

        if "supports" in text or "strengthens" in text or "confirms" in text:
            support += 1
        elif "contradicts" in text or "weakens" in text or "refutes" in text:
            contradict += 1

    delta = (support - contradict) * 0.05
    new_conf = max(0, min(1, old_conf + delta))

    update_confidence(hypothesis_id, new_conf)

    return new_conf