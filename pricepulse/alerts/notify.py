import os
import requests
from pricepulse.alerts.notify import alert_map_violations

def send_discord_alert(message: str):
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    requests.post(webhook_url, json={"content": message}, timeout=10)

def send_telegram_alert(message: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message}, timeout=10,
    )

def check_and_alert(summary_df, drop_threshold_pct: float = 8.0):
    for _, row in summary_df.iterrows():
        if row.price_spread_pct >= drop_threshold_pct:
            msg = (f"🔻 **{row.product_name}**: {row.cheapest_retailer} is "
                   f"undercutting the market by {row.price_spread_pct}% "
                   f"({row.cheapest_price} vs avg {row.avg_price:.2f})")
            send_discord_alert(msg)
            
def alert_map_violations(violations_df):
    if violations_df.empty:
        return
        
    for _, row in violations_df.iterrows():
        msg = (f"🚨 **MAP VIOLATION**: {row['retailer_name']} is selling "
               f"**{row['product_name']}** at {row['price']}, which is below "
               f"the legal minimum of {row['map_price']}!")
        send_discord_alert(msg)