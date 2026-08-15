from dataclasses import dataclass

@dataclass
class ScrapedListing:
    retailer_name: str
    product_query: str
    title: str
    price: float
    currency: str
    url: str
    in_stock: bool
    shipping_cost: float = 0.0

class RetailerAdapter:
    """Every retailer integration implements this one method."""
    name: str = "base"

    def fetch(self, search_term: str) -> list[ScrapedListing]:
        raise NotImplementedError