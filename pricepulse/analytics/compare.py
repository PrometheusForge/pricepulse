import pandas as pd
import yaml

def get_buy_box_winners(observations_df: pd.DataFrame) -> pd.DataFrame:
    if observations_df.empty:
        return pd.DataFrame()

    with open("config/scoring.yaml") as f:
        weights = yaml.safe_load(f)["weights"]
        
    latest = observations_df.sort_values("observed_at").groupby(["product_id", "retailer_name"]).tail(1).copy()
    
    if "shipping_cost" not in latest.columns:
        latest["shipping_cost"] = 0.0

    latest["price_norm"] = latest.groupby("product_id")["price"].transform(
        lambda x: 1 - ((x - x.min()) / (x.max() - x.min() + 0.001))
    )
    latest["ship_norm"] = latest.groupby("product_id")["shipping_cost"].transform(
        lambda x: 1 - ((x - x.min()) / (x.max() - x.min() + 0.001))
    )
    latest["stock_norm"] = latest["in_stock"].astype(float)
    
    latest["true_value_score"] = (
        (latest["price_norm"] * weights["price"]) +
        (latest["ship_norm"] * weights["shipping"]) +
        (latest["stock_norm"] * weights["stock"])
    )
    
    idx = latest.groupby("product_id")["true_value_score"].idxmax()
    winners = latest.loc[idx, ["product_name", "retailer_name", "price", "shipping_cost", "true_value_score"]]
    
    winners.rename(columns={"retailer_name": "best_value_retailer"}, inplace=True)
    winners["true_value_score"] = (winners["true_value_score"] * 100).round(1)
    
    return winners.sort_values("true_value_score", ascending=False)

def build_comparison_table(observations_df: pd.DataFrame) -> pd.DataFrame:
    latest = (observations_df
              .sort_values("observed_at")
              .groupby(["product_id", "retailer_name"])
              .tail(1))

    summary = latest.groupby(["product_id", "product_name"]).agg(
        cheapest_price=("price", "min"),
        priciest_price=("price", "max"),
        avg_price=("price", "mean"),
        n_retailers=("retailer_name", "nunique"),
    ).reset_index()

    summary["price_spread_pct"] = (
        (summary["priciest_price"] - summary["cheapest_price"])
        / summary["cheapest_price"] * 100
    ).round(1)

    def _retailer_at_extreme(pid: int, which: str) -> str:
        rows = latest[latest.product_id == pid]
        idx = rows.price.idxmin() if which == "min" else rows.price.idxmax()
        return rows.loc[idx, "retailer_name"]

    summary["cheapest_retailer"] = summary["product_id"].apply(lambda pid: _retailer_at_extreme(pid, "min"))
    summary["priciest_retailer"] = summary["product_id"].apply(lambda pid: _retailer_at_extreme(pid, "max"))
    return summary.sort_values("price_spread_pct", ascending=False)


def week_over_week_change(history_df: pd.DataFrame) -> pd.DataFrame:
    history_df = history_df.copy()
    history_df["observed_at"] = pd.to_datetime(history_df["observed_at"])
    out_rows = []
    for (pid, retailer), grp in history_df.groupby(["product_id", "retailer_name"]):
        grp = grp.sort_values("observed_at")
        if len(grp) < 2:
            continue
        latest_row = grp.iloc[-1]
        cutoff = latest_row["observed_at"] - pd.Timedelta(days=7)
        past = grp[grp["observed_at"] <= cutoff]
        if past.empty:
            continue
        past_price = past.iloc[-1]["price"]
        pct_change = round((latest_row["price"] - past_price) / past_price * 100, 1)
        out_rows.append({
            "product_id": pid, "retailer_name": retailer,
            "current_price": latest_row["price"], "price_7d_ago": past_price,
            "pct_change_7d": pct_change,
        })
    return pd.DataFrame(out_rows)

def check_map_violations(observations_df: pd.DataFrame) -> pd.DataFrame:
    if "map_price" not in observations_df.columns:
        return pd.DataFrame()

    latest = (observations_df
              .sort_values("observed_at")
              .groupby(["product_id", "retailer_name"])
              .tail(1))
    
    violations = latest[
        latest["map_price"].notna() & 
        (latest["price"] < latest["map_price"])
    ]
    
    return violations