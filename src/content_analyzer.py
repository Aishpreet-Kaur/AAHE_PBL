"""
Content-based credibility analysis using pre-trained ML models.
Analyzes article text to score credibility beyond just domain reputation.
"""

import re
from textblob import TextBlob
import spacy
from transformers import pipeline

# Load pre-trained models once at module import
print("Loading ML models for content analysis...")
nlp = spacy.load("en_core_web_sm")  # For entity recognition
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("✓ Models loaded successfully")


def analyze_content_credibility(text: str, title: str) -> dict:
    """
    Analyze article content for credibility signals.
    
    Args:
        text: Article content (snippet or full text)
        title: Article title
        
    Returns:
        Dictionary with scores and explanations
    """
    
    if not text or len(text.strip()) < 50:
        # Too short to analyze meaningfully
        return {
            'content_score': 6.0,
            'hedging_score': 6.0,
            'citation_score': 6.0,
            'emotional_score': 6.0,
            'structure_score': 6.0,
            'explanation': 'Insufficient text for content analysis'
        }
    
    # Run all four analyses
    hedging_score = _analyze_hedging_language(text)
    citation_score = _analyze_citation_behavior(text)
    emotional_score = _analyze_emotional_tone(text, title)
    structure_score = _analyze_structure(text, title)
    
    # Combine scores (weighted average)
    content_score = (
        hedging_score * 0.30 +
        citation_score * 0.30 +
        emotional_score * 0.25 +
        structure_score * 0.15
    )
    
    # Generate explanation
    explanation = _generate_explanation(hedging_score, citation_score, emotional_score, structure_score)
    
    return {
        'content_score': round(content_score, 2),
        'hedging_score': round(hedging_score, 2),
        'citation_score': round(citation_score, 2),
        'emotional_score': round(emotional_score, 2),
        'structure_score': round(structure_score, 2),
        'explanation': explanation
    }


def _analyze_hedging_language(text: str) -> float:
    """
    Detect cautious vs over-confident language.
    Good journalism uses hedging words. Propaganda uses absolutes.
    """
    
    text_lower = text.lower()
    word_count = len(text.split())
    
    # Hedging words (cautious, responsible journalism)
    hedging_words = [
        'reportedly', 'allegedly', 'according to', 'appears to', 'seems to',
        'suggests', 'indicates', 'may', 'might', 'could', 'possibly',
        'likely', 'potentially', 'apparently', 'presumably', 'said to be',
        'claimed', 'purportedly', 'supposedly'
    ]
    
    # Over-confident words (red flags)
    confident_words = [
        'definitely', 'absolutely', 'certainly', 'undeniably', 'proves',
        'confirms', 'without doubt', 'guaranteed', 'always', 'never',
        'everyone knows', 'obviously', 'clearly shows'
    ]
    
    hedging_count = sum(1 for word in hedging_words if word in text_lower)
    confident_count = sum(1 for word in confident_words if word in text_lower)
    
    # Calculate score
    if word_count < 50:
        return 6.0  # Too short to judge
    
    # Normalize by text length (per 100 words)
    hedging_density = (hedging_count / word_count) * 100
    confident_density = (confident_count / word_count) * 100
    
    # Good journalism: high hedging, low confidence
    # Scale to 0-10
    if hedging_density > 2 and confident_density < 1:
        score = 9.0  # Excellent
    elif hedging_density > 1 and confident_density < 2:
        score = 7.5  # Good
    elif confident_density > 3:
        score = 4.0  # Too confident, red flag
    else:
        score = 6.0  # Neutral
    
    return score


def _analyze_citation_behavior(text: str) -> float:
    """
    Check if article cites sources, experts, organizations.
    Good journalism names sources. Bad journalism makes unsupported claims.
    """
    
    # Use spaCy to find named entities
    doc = nlp(text[:1000])  # Analyze first 1000 chars (model limit)
    
    # Count specific entity types
    person_count = sum(1 for ent in doc.ents if ent.label_ == "PERSON")
    org_count = sum(1 for ent in doc.ents if ent.label_ == "ORG")
    
    # Citation phrases
    citation_phrases = [
        'according to', 'said', 'told', 'reported', 'announced',
        'spokesperson', 'official', 'expert', 'researcher', 'professor',
        'study', 'research', 'data shows', 'analysis', 'survey'
    ]
    
    phrase_count = sum(1 for phrase in citation_phrases if phrase in text.lower())
    
    # Calculate score
    total_citations = person_count + org_count + phrase_count
    
    if total_citations >= 5:
        score = 9.0  # Well-sourced
    elif total_citations >= 3:
        score = 7.5  # Adequately sourced
    elif total_citations >= 1:
        score = 6.0  # Some sources
    else:
        score = 4.0  # No apparent sources
    
    return score


def _analyze_emotional_tone(text: str, title: str) -> float:
    """
    Detect emotional/sensational language vs neutral reporting.
    Good journalism is neutral. Clickbait/propaganda is emotional.
    """
    
    # Analyze title separately (titles are often more sensational)
    title_blob = TextBlob(title)
    title_polarity = abs(title_blob.sentiment.polarity)  # 0 = neutral, 1 = extreme
    
    # Analyze content
    text_blob = TextBlob(text[:500])  # First 500 chars
    text_polarity = abs(text_blob.sentiment.polarity)
    
    # Check for ALL CAPS (sensationalism indicator)
    caps_ratio = sum(1 for c in title if c.isupper()) / max(len(title), 1)
    
    # Check for exclamation marks
    exclamation_count = text.count('!') + title.count('!')
    
    # Calculate neutrality score
    # Lower polarity = more neutral = higher score
    base_score = (1 - (title_polarity * 0.6 + text_polarity * 0.4)) * 10
    
    # Penalties
    if caps_ratio > 0.5:  # More than 50% caps in title
        base_score -= 2.0
    if exclamation_count > 2:
        base_score -= 1.0
    
    # Clamp to 0-10 range
    score = max(0, min(10, base_score))
    
    return score


def _analyze_structure(text: str, title: str) -> float:
    """
    Check for professional article structure.
    """
    
    score = 5.0  # Start at baseline
    
    # Check 1: Reasonable paragraph length
    sentences = text.split('.')
    if 3 <= len(sentences) <= 20:
        score += 1.5  # Good structure
    
    # Check 2: Not all caps
    if not title.isupper():
        score += 1.5
    
    # Check 3: Proper punctuation (not excessive)
    question_marks = text.count('?')
    exclamations = text.count('!')
    if question_marks <= 2 and exclamations <= 2:
        score += 1.5
    
    # Check 4: Reasonable title length
    if 10 <= len(title.split()) <= 20:
        score += 0.5
    
    return min(10, score)


def _generate_explanation(hedging, citation, emotional, structure) -> str:
    """Generate human-readable explanation of scores"""
    
    explanations = []
    
    # Hedging
    if hedging >= 7.5:
        explanations.append("✓ Cautious language")
    elif hedging < 5:
        explanations.append("⚠ Over-confident claims")
    
    # Citations
    if citation >= 7.5:
        explanations.append("✓ Well-sourced")
    elif citation < 5:
        explanations.append("⚠ Few citations")
    
    # Emotional tone
    if emotional >= 7.5:
        explanations.append("✓ Neutral tone")
    elif emotional < 5:
        explanations.append("⚠ Emotional language")
    
    # Structure
    if structure >= 7:
        explanations.append("✓ Professional format")
    
    if not explanations:
        return "Standard content quality"
    
    return " | ".join(explanations)


# Test function
if __name__ == "__main__":
    # Test with good article
    good_text = """
    According to a study published in Nature journal, researchers at 
    Stanford University found significant results. Dr. Jane Smith, 
    the lead researcher, told reporters that the findings suggest 
    a correlation. The research team analyzed data from 1,200 participants.
    """
    
    result = analyze_content_credibility(good_text, "Study Shows Correlation in New Research")
    print("Good Article Analysis:")
    print(f"  Content Score: {result['content_score']}/10")
    print(f"  Explanation: {result['explanation']}")
    print()
    
    # Test with bad article
    bad_text = """
    SHOCKING discovery PROVES everything we knew was WRONG! 
    This will blow your mind! Everyone is talking about this 
    incredible breakthrough that changes EVERYTHING! You won't 
    believe what happened next! Absolutely amazing!
    """
    
    result = analyze_content_credibility(bad_text, "SHOCKING DISCOVERY WILL BLOW YOUR MIND!!!")
    print("Bad Article Analysis:")
    print(f"  Content Score: {result['content_score']}/10")
    print(f"  Explanation: {result['explanation']}")