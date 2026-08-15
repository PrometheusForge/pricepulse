import os
import pandas as pd
from groq import Groq

def generate_executive_digest(summary_df: pd.DataFrame, wow_df: pd.DataFrame) -> str:
    """Feeds market data to Groq to generate a plain-English executive summary."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    top_spreads = summary_df.head(15).to_string(index=False)
    
    if not wow_df.empty:
        wow_trends = wow_df.sort_values("pct_change_7d", ascending=False).head(10).to_string(index=False)
    else:
        wow_trends = "No week-over-week data available yet (requires 7 days of history)."

    prompt = f"""
    You are an expert retail pricing analyst. I will provide you with the latest market comparison data and week-over-week price changes for a catalog of products.
    
    Write a 3 to 5 sentence executive summary of the market.
    Focus on:
    - Which competitors are consistently undercutting or overpricing the market.
    - Notable price spreads or significant week-over-week shifts.
    - A concluding strategic insight or recommendation.

    Do not use markdown tables. Keep it readable, punchy, and professional.

    Latest Market Summary (Top Spreads):
    {top_spreads}

    Week-over-Week Changes (Top Movers):
    {wow_trends}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    
    return response.choices[0].message.content