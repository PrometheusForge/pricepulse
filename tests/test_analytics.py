import pandas as pd
from pricepulse.analytics.compare import build_comparison_table

def test_cheapest_retailer_identified():
    df = pd.DataFrame([
        {"product_id": 1, "product_name": "Widget", "retailer_name": "A",
         "price": 10.0, "observed_at": "2026-01-01"},
        {"product_id": 1, "product_name": "Widget", "retailer_name": "B",
         "price": 8.0, "observed_at": "2026-01-01"},
    ])
    result = build_comparison_table(df)
    assert result.iloc[0]["cheapest_retailer"] == "B"
    assert result.iloc[0]["priciest_retailer"] == "A"

def test_price_spread_calculation():
    df = pd.DataFrame([
        {"product_id": 1, "product_name": "Widget", "retailer_name": "A",
         "price": 10.0, "observed_at": "2026-01-01"},
        {"product_id": 1, "product_name": "Widget", "retailer_name": "B",
         "price": 20.0, "observed_at": "2026-01-01"},
    ])
    result = build_comparison_table(df)
    assert result.iloc[0]["price_spread_pct"] == 100.0