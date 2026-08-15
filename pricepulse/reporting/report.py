import plotly.express as px
import pandas as pd

def render_markdown_report(summary_df: pd.DataFrame) -> str:
    lines = ["# PricePulse Daily Price Comparison Report", ""]
    for _, row in summary_df.iterrows():
        lines += [
            f"## {row.product_name}",
            f"- 🟢 Cheapest: **{row.cheapest_retailer}** — {row.cheapest_price}",
            f"- 🔴 Priciest: **{row.priciest_retailer}** — {row.priciest_price}",
            f"- Average market price: {row.avg_price:.2f}",
            f"- Price spread: {row.price_spread_pct}%",
            f"- Retailers tracked: {row.n_retailers}",
            "",
        ]
    return "\n".join(lines)

def render_price_history_chart(history_df: pd.DataFrame, product_name: str):
    fig = px.line(
        history_df, x="observed_at", y="price", color="retailer_name",
        title=f"Price history — {product_name}", markers=True,
    )
    fig.update_layout(template="plotly_white")
    return fig