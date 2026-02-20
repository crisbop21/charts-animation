"""
Finance Slides Generator
========================
Researches daily trending topics in stocks and finance, generates
engaging slides based on configurable preferences, and iterates on
engagement quality using AI self-critique.

Usage:
    export ANTHROPIC_API_KEY=your-key
    python slides_generator.py

The script will:
  1. Fetch recent financial news from RSS feeds
  2. Use Claude to identify the most compelling trending topics
  3. Generate a slide deck tailored to your audience and platform
  4. Self-critique the engagement quality and iterate until it meets
     a configurable threshold (or hits the max iteration count)
  5. Output the final deck to the terminal and save as JSON
"""

import anthropic
import json
import os
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel
from typing import List


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

@dataclass
class SlidePreferences:
    """Configure how slides are researched, generated, and refined."""

    audience: str = "retail investors and finance enthusiasts"
    tone: str = "professional yet engaging — think Morning Brew meets Bloomberg"
    platform: str = "LinkedIn"  # LinkedIn, Instagram, Twitter/X, TikTok
    num_slides: int = 6
    focus_areas: list[str] = field(default_factory=lambda: [
        "stocks", "market trends", "economic indicators", "earnings",
    ])
    style_notes: str = (
        "Bold headlines, concise bullet points, and include specific "
        "data points or statistics when possible"
    )
    engagement_threshold: int = 8   # Min score (1-10) before accepting
    max_iterations: int = 3         # Max self-critique rounds


# ---------------------------------------------------------------------------
# Structured output models (Pydantic)
# ---------------------------------------------------------------------------

class Slide(BaseModel):
    slide_number: int
    title: str
    content: List[str]          # Bullet points or key messages
    speaker_notes: str          # Talking points for the presenter
    visual_suggestion: str      # Describes what chart/image to pair


class SlideDeck(BaseModel):
    topic: str
    hook: str                   # Attention-grabbing post caption
    slides: List[Slide]
    call_to_action: str
    hashtags: List[str]


class EngagementReview(BaseModel):
    score: int                  # 1-10
    strengths: List[str]
    weaknesses: List[str]
    specific_improvements: List[str]
    revised_hook: str           # Suggested improved hook


# ---------------------------------------------------------------------------
# News fetching via RSS
# ---------------------------------------------------------------------------

RSS_FEEDS = {
    "Yahoo Finance Top Stories": (
        "https://feeds.finance.yahoo.com/rss/2.0/headline"
        "?region=US&lang=en-US"
    ),
    "Yahoo Finance Markets": (
        "https://feeds.finance.yahoo.com/rss/2.0/headline"
        "?s=^GSPC&region=US&lang=en-US"
    ),
}


def fetch_finance_news() -> list[dict]:
    """Fetch recent headlines from financial RSS feeds."""
    articles: list[dict] = []

    for source, url in RSS_FEEDS.items():
        try:
            resp = requests.get(
                url, timeout=10,
                headers={"User-Agent": "FinanceSlideGenerator/1.0"},
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in root.iter("item"):
                title_el = item.find("title")
                desc_el = item.find("description")
                pub_el = item.find("pubDate")

                if title_el is not None and title_el.text:
                    articles.append({
                        "source": source,
                        "title": title_el.text.strip(),
                        "description": (
                            (desc_el.text or "").strip()
                            if desc_el is not None else ""
                        ),
                        "date": (
                            (pub_el.text or "").strip()
                            if pub_el is not None else ""
                        ),
                    })
        except Exception as exc:
            print(f"  [warn] Could not fetch {source}: {exc}")

    return articles


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-6"


def research_topics(
    client: anthropic.Anthropic,
    articles: list[dict],
    prefs: SlidePreferences,
) -> str:
    """Analyze news headlines and identify the most compelling topics."""

    if articles:
        news_block = "\n".join(
            f"- [{a['source']}] {a['title']}"
            + (f": {a['description'][:200]}" if a["description"] else "")
            for a in articles[:30]
        )
    else:
        news_block = (
            "(No articles could be fetched — use your knowledge of "
            "current market trends and recent events instead)"
        )

    today = datetime.now().strftime("%B %d, %Y")

    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{
            "role": "user",
            "content": (
                f"You are a financial content strategist. Today is {today}.\n\n"
                f"Analyze these recent finance/market headlines and identify the "
                f"TOP 3 most compelling trending topics that would make engaging "
                f"social media slide content for {prefs.audience} on "
                f"{prefs.platform}.\n\n"
                f"Focus areas: {', '.join(prefs.focus_areas)}\n\n"
                f"Recent headlines:\n{news_block}\n\n"
                f"For each topic, provide:\n"
                f"1. The topic/angle\n"
                f"2. Why it's trending or relevant right now\n"
                f"3. The key data points or narrative hooks\n"
                f"4. Why this audience would care\n\n"
                f"Be specific and actionable. These topics will be used to "
                f"generate slide decks."
            ),
        }],
    ) as stream:
        response = stream.get_final_message()

    return "\n".join(
        block.text for block in response.content if block.type == "text"
    )


def generate_slides(
    client: anthropic.Anthropic,
    topics: str,
    prefs: SlidePreferences,
) -> SlideDeck:
    """Generate a slide deck based on researched topics and preferences."""

    today = datetime.now().strftime("%B %d, %Y")

    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_format=SlideDeck,
        messages=[{
            "role": "user",
            "content": (
                f"Create a {prefs.num_slides}-slide deck for {prefs.platform} "
                f"about the most compelling topic from this research. "
                f"Today is {today}.\n\n"
                f"RESEARCH:\n{topics}\n\n"
                f"REQUIREMENTS:\n"
                f"- Audience: {prefs.audience}\n"
                f"- Tone: {prefs.tone}\n"
                f"- Platform: {prefs.platform}\n"
                f"- Number of slides: {prefs.num_slides}\n"
                f"- Style: {prefs.style_notes}\n\n"
                f"SLIDE GUIDELINES:\n"
                f"- Slide 1 should be a hook/title slide that grabs attention\n"
                f"- Each slide should have 2-4 concise bullet points\n"
                f"- Include specific numbers, percentages, or data points\n"
                f"- Last slide should have a clear call-to-action\n"
                f"- The hook should be an attention-grabbing one-liner for the "
                f"post caption\n"
                f"- Include relevant hashtags for {prefs.platform}\n"
                f"- Visual suggestions should describe what chart, image, or "
                f"graphic would work best\n"
                f"- Make it feel timely and urgent — people should want to "
                f"share this\n\n"
                f"Write for maximum engagement: bold claims backed by data, "
                f"contrarian takes, or surprising insights that make people "
                f"stop scrolling."
            ),
        }],
    )

    if response.parsed_output is None:
        raise RuntimeError(
            "Claude refused to generate slides. "
            f"Stop reason: {response.stop_reason}"
        )
    return response.parsed_output


def review_engagement(
    client: anthropic.Anthropic,
    deck: SlideDeck,
    prefs: SlidePreferences,
) -> EngagementReview:
    """Critically evaluate the engagement quality of a slide deck."""

    deck_json = deck.model_dump_json(indent=2)

    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        output_format=EngagementReview,
        messages=[{
            "role": "user",
            "content": (
                f"You are a social media engagement expert and harsh critic. "
                f"Rate this {prefs.platform} slide deck on a scale of 1-10 "
                f"for engagement potential.\n\n"
                f"Target audience: {prefs.audience}\n"
                f"Platform: {prefs.platform}\n\n"
                f"SLIDE DECK:\n{deck_json}\n\n"
                f"Evaluate critically on these dimensions:\n"
                f"- Hook strength: Would someone stop scrolling?\n"
                f"- Information density: Is each slide earning its place?\n"
                f"- Specificity: Are there concrete numbers and data, or "
                f"just vague claims?\n"
                f"- Shareability: Would someone repost or save this?\n"
                f"- Flow: Does it build to a satisfying conclusion?\n"
                f"- Call-to-action: Does it drive engagement?\n"
                f"- Visual potential: Can these be made visually compelling?\n"
                f"- Timeliness: Does it feel urgent and current?\n\n"
                f"Be brutally honest. A score of 8+ means this is genuinely "
                f"ready to post and would perform well.\n\n"
                f"Provide SPECIFIC, ACTIONABLE improvements — not vague "
                f"suggestions like 'make it more engaging'. Say exactly what "
                f"to change and how."
            ),
        }],
    )

    if response.parsed_output is None:
        raise RuntimeError(
            "Claude refused to review engagement. "
            f"Stop reason: {response.stop_reason}"
        )
    return response.parsed_output


def improve_slides(
    client: anthropic.Anthropic,
    deck: SlideDeck,
    review: EngagementReview,
    prefs: SlidePreferences,
) -> SlideDeck:
    """Revise the slide deck based on engagement review feedback."""

    deck_json = deck.model_dump_json(indent=2)
    review_json = review.model_dump_json(indent=2)

    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_format=SlideDeck,
        messages=[{
            "role": "user",
            "content": (
                f"Revise this slide deck to address ALL the engagement "
                f"feedback below. Make it significantly more engaging, "
                f"specific, and shareable.\n\n"
                f"CURRENT SLIDES:\n{deck_json}\n\n"
                f"ENGAGEMENT REVIEW (score: {review.score}/10):\n"
                f"{review_json}\n\n"
                f"REQUIREMENTS:\n"
                f"- Audience: {prefs.audience}\n"
                f"- Platform: {prefs.platform}\n"
                f"- Number of slides: {prefs.num_slides}\n"
                f"- Tone: {prefs.tone}\n\n"
                f"Address every weakness and implement every specific "
                f"improvement suggestion. If the reviewer suggested a better "
                f"hook, use it or improve on it further.\n\n"
                f"Make each slide punchier, more data-driven, and more "
                f"shareable."
            ),
        }],
    )

    if response.parsed_output is None:
        raise RuntimeError(
            "Claude refused to improve slides. "
            f"Stop reason: {response.stop_reason}"
        )
    return response.parsed_output


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_deck(deck: SlideDeck) -> str:
    """Format a slide deck for terminal display."""
    sep = "=" * 60
    lines = [
        "",
        sep,
        f"  TOPIC:  {deck.topic}",
        f"  HOOK:   {deck.hook}",
        sep,
    ]

    for slide in deck.slides:
        lines.append(f"\n  ┌─ Slide {slide.slide_number}: {slide.title}")
        lines.append("  │")
        for bullet in slide.content:
            lines.append(f"  │  • {bullet}")
        lines.append("  │")
        lines.append(f"  │  Visual: {slide.visual_suggestion}")
        lines.append(f"  │  Notes:  {slide.speaker_notes}")
        lines.append("  └" + "─" * 50)

    lines.append(f"\n  CTA:      {deck.call_to_action}")
    lines.append(f"  Hashtags: {' '.join(deck.hashtags)}")
    lines.append(sep)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(prefs: SlidePreferences | None = None) -> SlideDeck:
    """
    Full pipeline: research → generate → iterate → output.

    Returns the final SlideDeck.
    """
    if prefs is None:
        prefs = SlidePreferences()

    # Validate API key early
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Error: ANTHROPIC_API_KEY environment variable is not set.\n"
            "  export ANTHROPIC_API_KEY=your-key-here"
        )
        raise SystemExit(1)

    client = anthropic.Anthropic()

    print(f"\nFinance Slides Generator")
    print(f"  Platform:  {prefs.platform}")
    print(f"  Audience:  {prefs.audience}")
    print(f"  Slides:    {prefs.num_slides}")
    print(f"  Threshold: {prefs.engagement_threshold}/10")

    # Step 1: Fetch news
    print("\n[1/4] Fetching financial news...")
    articles = fetch_finance_news()
    print(f"  Found {len(articles)} recent articles")

    # Step 2: Research trending topics
    print("\n[2/4] Analyzing trending topics with Claude...")
    topics = research_topics(client, articles, prefs)
    print("  Identified top trending topics")

    # Step 3: Generate initial slides
    print("\n[3/4] Generating slide deck...")
    deck = generate_slides(client, topics, prefs)
    print(f"  Generated {len(deck.slides)} slides on: {deck.topic}")

    # Step 4: Iterate on engagement quality
    print(
        f"\n[4/4] Reviewing engagement "
        f"(target: {prefs.engagement_threshold}/10, "
        f"max iterations: {prefs.max_iterations})..."
    )

    for iteration in range(prefs.max_iterations):
        review = review_engagement(client, deck, prefs)
        print(f"\n  Iteration {iteration + 1}/{prefs.max_iterations}: "
              f"Score {review.score}/10")

        if review.strengths:
            print(f"    Strengths:  {review.strengths[0]}")
        if review.weaknesses:
            print(f"    Weaknesses: {review.weaknesses[0]}")

        if review.score >= prefs.engagement_threshold:
            print(f"  ✓ Engagement target met!")
            break

        # Don't improve after the last iteration
        if iteration < prefs.max_iterations - 1:
            print(f"  → Improving slides based on feedback...")
            deck = improve_slides(client, deck, review, prefs)
        else:
            print(f"  Max iterations reached. Using current version.")

    # Output to terminal
    print(format_deck(deck))

    # Save as JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"slides_{timestamp}.json",
    )
    with open(output_path, "w") as f:
        json.dump(deck.model_dump(), f, indent=2)
    print(f"\nSaved to {output_path}")

    return deck


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    prefs = SlidePreferences(
        audience="retail investors and finance enthusiasts",
        tone="professional yet engaging — think Morning Brew meets Bloomberg",
        platform="LinkedIn",
        num_slides=6,
        focus_areas=[
            "stocks", "market trends", "economic indicators", "earnings",
        ],
        style_notes=(
            "Bold headlines, concise bullets, specific data points "
            "and percentages"
        ),
        engagement_threshold=8,
        max_iterations=3,
    )

    run_pipeline(prefs)
