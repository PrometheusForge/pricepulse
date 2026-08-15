from playwright.sync_api import sync_playwright
from .base_adapter import RetailerAdapter, ScrapedListing
from .robots import is_allowed
from .throttle import polite_delay

BASE_URL = "https://scrapeme.live/shop/"

class ScrapemeAdapter(RetailerAdapter):
    name = "scrapeme_direct"

    def fetch(self, search_term: str) -> list[ScrapedListing]:
        if not is_allowed(BASE_URL):
            return []
        polite_delay("scrapeme.live")

        listings = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="PricePulseBot/1.0 (portfolio project; contact: you@example.com)"
            )
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=90000)
            cards = page.query_selector_all("li.product")
            for card in cards:
                title_el = card.query_selector(".woocommerce-loop-product__title")
                price_el = card.query_selector(".price")
                link_el = card.query_selector("a")
                if not (title_el and price_el and link_el):
                    continue
                title = title_el.inner_text().strip()
                if search_term.lower() not in title.lower():
                    continue
                price_text = price_el.inner_text().replace("£", "").split("–")[0].strip()
                try:
                    price = float(price_text)
                except ValueError:
                    continue
                listings.append(ScrapedListing(
                    retailer_name=self.name,
                    product_query=search_term,
                    title=title,
                    price=price,
                    currency="GBP",
                    url=link_el.get_attribute("href") or BASE_URL,
                    in_stock=True,
                ))
            browser.close()
        return listings