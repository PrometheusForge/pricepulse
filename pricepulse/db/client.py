import os
from supabase import create_client, Client

def get_service_client() -> Client:
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

def upsert_retailer(client: Client, name: str, base_url: str, adapter_key: str) -> int:
    res = client.table("retailers").upsert(
        {"name": name, "base_url": base_url, "adapter_key": adapter_key},
        on_conflict="name"
    ).execute()
    return res.data[0]["id"]

def upsert_product(client: Client, sku: str, display_name: str, category: str,
                    map_price: float | None) -> int:
    res = client.table("products").upsert(
        {"sku": sku, "display_name": display_name, "category": category,
         "map_price": map_price},
        on_conflict="sku"
    ).execute()
    return res.data[0]["id"]

def upsert_listing(client: Client, product_id: int, retailer_id: int, url: str,
                    matched_title: str, confidence: float, method: str) -> int:
    res = client.table("retailer_listings").upsert(
        {"product_id": product_id, "retailer_id": retailer_id, "listing_url": url,
         "matched_title": matched_title, "match_confidence": confidence,
         "match_method": method},
        on_conflict="product_id,retailer_id"
    ).execute()
    return res.data[0]["id"]

def record_price(client: Client, listing_id: int, price: float, currency: str,
                  in_stock: bool, shipping_cost: float = 0.0):
    client.table("price_observations").insert({
        "listing_id": listing_id, "price": price, "currency": currency,
        "in_stock": in_stock, "shipping_cost": shipping_cost
    }).execute()