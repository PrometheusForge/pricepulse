import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from pricepulse.db.client import get_service_client
from pricepulse.analytics.compare import build_comparison_table, week_over_week_change
from pricepulse.reporting.ai_digest import generate_executive_digest
from pricepulse.alerts.notify import send_discord_alert

def run_digest():
    client = get_service_client()

    rows = (client.table("price_observations")
            .select("price, observed_at, retailer_listings(matched_title, "
                    "products(id, display_name), retailers(name))")
            .execute().data)
    
    records = []
    for r in rows:
        listing = r.get("retailer_listings") or {}
        prod = (listing or {}).get("products") or {}
        ret = (listing or {}).get("retailers") or {}
        records.append({"product_id": prod.get("id"), "product_name": prod.get("display_name"),
                         "retailer_name": ret.get("name"), "price": r["price"],
                         "observed_at": r["observed_at"]})
    
    df = pd.DataFrame(records)
    if df.empty:
        print("No observations recorded yet. Digest aborted.")
        return

    summary = build_comparison_table(df)
    wow = week_over_week_change(df)

    print("Generating AI digest via Groq...")
    digest_text = generate_executive_digest(summary, wow)
    
    print("\n--- AI EXECUTIVE DIGEST ---")
    print(digest_text)

    formatted_alert = f"🧠 **Weekly PricePulse Executive Insight**\n\n{digest_text}"
    send_discord_alert(formatted_alert)
    print("\nDigest sent to Discord successfully.")

if __name__ == "__main__":
    run_digest()