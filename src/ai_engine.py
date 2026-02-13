import os
from dotenv import load_dotenv
import google.generativeai as genai

ROOT = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(ROOT, ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

# def generate_hypotheses(topic: str, custom_query: str = None) -> str:
#     prompt = DETECTIVE_PROMPT.format(topic=topic, custom_query=custom_query or "N/A")
#     model = genai.GenerativeModel("gemini-2.5-flash")
#     response = model.generate_content(prompt)
#     return response.text 

def generate_hypotheses(topic: str, custom_query: str = None) -> str:
    prompt = DETECTIVE_PROMPT.format(
        topic=topic,
        custom_query=custom_query or "N/A"
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    # SAFE RESPONSE HANDLING
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


from livenews import fetch_latest_news
from db_manager import (
    get_last_fetch_time,
    update_confidence,
    get_hypothesis_by_id
)

def temporal_update_engine(hypothesis_id: int):
    """
    Uses live news + existing Gemini reasoning
    to TEMPORALLY update hypothesis confidence
    """

    hypothesis = get_hypothesis_by_id(hypothesis_id)

    topic = hypothesis["topic"]
    old_conf = hypothesis["confidence"]
    last_time = hypothesis["last_updated"]

    articles = fetch_latest_news(topic, last_time)

    if not articles:
        return old_conf

    support, contradict = 0, 0

    for art in articles:
        analysis = generate_hypotheses(
            topic,
            custom_query=art["content"]
        )

        text = analysis.lower()

        if "supports" in text or "strengthens" in text:
            support += 1
        elif "contradicts" in text or "weakens" in text:
            contradict += 1

    delta = (support - contradict) * 0.05
    new_conf = max(0, min(1, old_conf + delta))

    update_confidence(hypothesis_id, new_conf)

    return new_conf

