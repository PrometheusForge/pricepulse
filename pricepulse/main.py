import yaml
import pandas as pd
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
load_dotenv()
from pricepulse.scraping.scrapeme_adapter import ScrapemeAdapter
from pricepulse.scraping.demo_synthesizer import synthesize_competitor
from pricepulse.matching.fuzzy import match_listing_to_product
from pricepulse.db.client import (get_service_client, upsert_retailer, upsert_product, upsert_listing, record_price)
from pricepulse.analytics.compare import build_comparison_table
from pricepulse.reporting.report import render_markdown_report
from pricepulse.alerts.notify import check_and_alert
from pricepulse.analytics.compare import build_comparison_table, check_map_violations
from pricepulse.alerts.notify import check_and_alert, alert_map_violations

def load_config():
    products = yaml.safe_load(open("config/products.yaml"))
    retailers = yaml.safe_load(open("config/retailers.yaml"))
    return products, retailers

def run():
    products, retailers = load_config()
    client = get_service_client()

    product_ids = {p["sku"]: upsert_product(client, p["sku"], p["display_name"],
                                             p["category"], p.get("map_price"))
                   for p in products}

    all_listings = []
    base_adapter = ScrapemeAdapter()
    for product in products:
        for term in product["search_terms"]:
            all_listings += base_adapter.fetch(term)

    for retailer_cfg in retailers:
        rid = upsert_retailer(client, retailer_cfg["name"],
                               retailer_cfg.get("base_url", ""),
                               retailer_cfg["adapter_key"])
        if retailer_cfg["mode"] == "live":
            listings = all_listings if retailer_cfg["name"] == "scrapeme_direct" else []
        else:
            listings = synthesize_competitor(
                all_listings, retailer_cfg["name"], retailer_cfg["seed"],
                tuple(retailer_cfg["price_jitter"]),
            )

        for listing in listings:
            match = match_listing_to_product(listing.title, products, accept_threshold=0.6)
            if not match or not match.get("product"):
                continue
            pid = product_ids[match["product"]["sku"]]
            listing_id = upsert_listing(client, pid, rid, listing.url, listing.title,
                                         match["confidence"], match["method"])
            record_price(client, listing_id, listing.price, listing.currency, listing.in_stock, getattr(listing, "shipping_cost", 0.0))

    rows = (client.table("price_observations")
         .select("price, observed_at, retailer_listings(matched_title, "
                 "products(id, display_name, map_price), retailers(name))")
         .execute().data)
    records = []
    for r in rows:
        listing = r.get("retailer_listings") or {}
        prod = (listing or {}).get("products") or {}
        ret = (listing or {}).get("retailers") or {}
        records.append({"product_id": prod.get("id"), "product_name": prod.get("display_name"),
                        "retailer_name": ret.get("name"), "price": r["price"],
                        "map_price": prod.get("map_price"),
                        "observed_at": r["observed_at"]})
    df = pd.DataFrame(records)
    if df.empty:
        print("No observations recorded this run.")
        return

    summary = build_comparison_table(df)
    report_md = render_markdown_report(summary)
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    from pathlib import Path
    Path("reports").mkdir(exist_ok=True)
    Path(f"reports/{run_date}.md").write_text(report_md, encoding="utf-8")
    print("--- DAILY REPORT GENERATED ---")
    print(report_md)
    return df

if __name__ == "__main__":
    df = run()    
    if df is not None and not df.empty:
        map_violations = check_map_violations(df)
        if not map_violations.empty:
            alert_map_violations(map_violations)