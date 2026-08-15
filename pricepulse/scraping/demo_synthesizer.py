"""
DEMO-ONLY utility. Generates additional 'competitor' price feeds by applying
documented random variance to one real scraped catalog, so the full
multi-retailer pipeline (including product matching) can be safely and
reproducibly demonstrated without scraping named commercial competitors.
Replace with real, vetted retailer adapters for production use (see the
Go-Live Checklist below).
"""
import random
from .base_adapter import ScrapedListing

FILLER_WORDS = ["New", "Official", "Genuine", "2026 Edition", "Bundle"]

def _perturb_title(title: str, rng: random.Random) -> str:
    words = title.split()
    if rng.random() < 0.3 and words:
        words.insert(rng.randrange(len(words) + 1), rng.choice(FILLER_WORDS))
    if rng.random() < 0.2 and len(words) > 3:
        words = words[:-1]
    return " ".join(words)

def synthesize_competitor(base_listings: list[ScrapedListing], retailer_name: str,
                           seed: int, price_jitter=(-0.15, 0.12),
                           stockout_rate: float = 0.05) -> list[ScrapedListing]:
    rng = random.Random(seed)
    out = []
    for listing in base_listings:
        if rng.random() < stockout_rate:
            continue
        jitter = rng.uniform(*price_jitter)
        out.append(ScrapedListing(
            retailer_name=retailer_name,
            product_query=listing.product_query,
            title=_perturb_title(listing.title, rng),
            price=round(listing.price * (1 + jitter), 2),
            currency=listing.currency,
            url=listing.url,
            in_stock=True,
        ))
    return out