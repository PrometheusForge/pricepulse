from rapidfuzz import fuzz

def fuzzy_match_score(query_title: str, candidate_title: str) -> float:
    return fuzz.token_sort_ratio(query_title, candidate_title) / 100.0

def match_listing_to_product(scraped_title: str, product_catalog: list[dict], accept_threshold: float = 0.72, ambiguous_floor: float = 0.45) -> dict | None:
    scored = sorted(
        ((p, fuzzy_match_score(p["display_name"], scraped_title)) for p in product_catalog),
        key=lambda x: x[1], reverse=True
    )
    if not scored:
        return None
    best_product, best_score = scored[0]
    if best_score >= accept_threshold:
        return {"product": best_product, "confidence": best_score, "method": "fuzzy"}
    if best_score >= ambiguous_floor:
        return {"product": None, "confidence": best_score, "method": "ambiguous", "candidates": [p for p, _ in scored[:3]]}
    return None