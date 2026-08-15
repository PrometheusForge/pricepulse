import os
import json
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

_client = Groq(api_key=os.environ["GROQ_API_KEY"])

PROMPT = """You are an expert e-commerce data analyst matching a scraped retailer product title to a canonical catalog entry.

CRITICAL RULES:
1. Match ONLY if it is the exact same physical product/model.
2. Pay strict attention to attributes like size, color, weight, and quantity. (e.g., A "3-pack" does not match a single item).
3. An accessory is NOT the product (e.g., "Charmander Case" does not match "Charmander Figure").
4. If no candidate is a definitive match, you MUST set match_index to null.
5. Respond with ONLY valid JSON. Do not include markdown formatting (like ```json), and do not include conversational text.

EXPECTED JSON FORMAT:
{{
  "reasoning": "<1-2 short sentences explaining your logic before deciding>",
  "match_index": <int or null>,
  "confidence": <0.0 to 1.0>
}}

Scraped title: {scraped_title}
Candidates:
{candidates}
"""

def llm_tiebreak(scraped_title: str, candidate_names: list[str]) -> dict:
    candidate_block = "\n".join(f"{i}: {c}" for i, c in enumerate(candidate_names))
    
    try:
        resp = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": PROMPT.format(
                scraped_title=scraped_title, candidates=candidate_block)}],
            temperature=0,
        )

        raw_output = resp.choices[0].message.content.strip()

        if raw_output.startswith("```json"):
            raw_output = raw_output.replace("```json", "", 1)
        elif raw_output.startswith("```"):
            raw_output = raw_output.replace("```", "", 1)
            
        if raw_output.endswith("```"):
            raw_output = raw_output[::-1].replace("```", "", 1)[::-1]
            
        raw_output = raw_output.strip()
        
        result = json.loads(raw_output)
        
        return {
            "match_index": result.get("match_index"),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", "No reasoning provided.")
        }
        
    except json.JSONDecodeError:
        print(f"⚠️ JSON Parse Error for '{scraped_title}'. Raw AI Output:\n{raw_output}")
        return {"match_index": None, "confidence": 0.0, "reasoning": "JSON parse error."}
    except Exception as e:
        print(f"⚠️ Groq API Error for '{scraped_title}': {e}")
        return {"match_index": None, "confidence": 0.0, "reasoning": "API error."}