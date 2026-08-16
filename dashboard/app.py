import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from supabase import create_client
from pricepulse.analytics.compare import build_comparison_table, check_map_violations, get_buy_box_winners
from pricepulse.analytics.forecast import generate_forecast
from pricepulse.reporting.report import render_price_history_chart

st.set_page_config(page_title="PricePulse Dashboard", page_icon="📡", layout="wide")

def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

client = get_client()

if "session" not in st.session_state:
    st.session_state.session = None

if not st.session_state.session:
    st.title("📡 PricePulse SaaS")
    st.caption("Secure Client Portal Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In"):
        try:
            res = client.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.session = res.session
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
            
    st.divider()
    
    st.info("💡 **Evaluating for hiring or freelance inquiries?** Click below to inspect a live sandbox tenant without creating an account.")
    if st.button("🚀 Explore Live Demo (Guest Access)", use_container_width=True):
        try:
            res = client.auth.sign_in_with_password({
                "email": "demo@pricepulse.app", 
                "password": "DemoAccess2026!"
            })
            st.session_state.session = res.session
            st.rerun()
        except Exception as e:
            st.error(f"Demo environment is currently unavailable: {e}")
            
    st.stop()

if st.session_state.session:
    client.postgrest.auth(st.session_state.session.access_token)

st.sidebar.markdown(f"**Logged in as:**\n`{st.session_state.session.user.email}`")
if st.sidebar.button("Log Out"):
    try:
        client.auth.sign_out()
    except Exception:
        pass
    st.session_state.session = None
    st.rerun()

st.title("📡 PricePulse — Competitive Price Intelligence")
st.caption("Live market monitoring engine and price analytics.")

def load_observations() -> pd.DataFrame:
    rows = (client.table("price_observations")
            .select("price, shipping_cost, currency, in_stock, observed_at, "
                    "retailer_listings(matched_title, products(id, display_name, map_price), "
                    "retailers(name))")
            .execute().data)
    records = []
    for r in rows:
        listing = r.get("retailer_listings") or {}
        product = (listing or {}).get("products") or {}
        retailer = (listing or {}).get("retailers") or {}
        records.append({
            "product_id": product.get("id"),
            "product_name": product.get("display_name"),
            "retailer_name": retailer.get("name"),
            "price": r["price"],
            "shipping_cost": r.get("shipping_cost", 0.0),
            "map_price": product.get("map_price"),
            "in_stock": r.get("in_stock", True),
            "observed_at": r["observed_at"],
        })
    return pd.DataFrame(records)

df = load_observations()

if df.empty:
    st.info("No pricing observations found. Run the main pipeline to populate data.")
    st.stop()

summary = build_comparison_table(df)
map_violations = check_map_violations(df)
buy_box_winners = get_buy_box_winners(df)

tab1, tab2, tab3 = st.tabs(["📊 Market Summary", "🚨 MAP Compliance", "🏆 True Value (Buy-Box)"])

with tab1:
    st.subheader("Market position summary")
    st.dataframe(
        summary[["product_name", "cheapest_retailer", "cheapest_price",
                 "priciest_retailer", "priciest_price", "avg_price", "price_spread_pct"]],
        use_container_width=True, hide_index=True,
    )

    st.subheader("Price History & Forecast")
    product_choice = st.selectbox("Product", summary["product_name"].tolist())
    history = df[df.product_name == product_choice].copy()
    history['observed_at'] = pd.to_datetime(history['observed_at'])

    forecast_data = generate_forecast(history)

    if not forecast_data["forecast_df"].empty:
        st.markdown(f"**🤖 AI Advisor:** {forecast_data['recommendation']}")
        plot_df = pd.concat([history, forecast_data["forecast_df"]], ignore_index=True)
    else:
        st.markdown("**🤖 AI Advisor:** Gathering more data to generate forecast...")
        plot_df = history

    st.plotly_chart(render_price_history_chart(plot_df, product_choice), use_container_width=True)

with tab2:
    st.subheader("MAP (Minimum Advertised Price) Violations")
    if map_violations.empty:
        st.success("All retailers are fully compliant with MAP policies.")
    else:
        st.error(f"Detected {len(map_violations)} MAP policy violations!")
        st.dataframe(
            map_violations[["product_name", "retailer_name", "price", "map_price", "observed_at"]],
            use_container_width=True, hide_index=True,
        )

with tab3:
    st.subheader("Composite 'True Value' Ranking")
    st.caption("Calculates the overall best deal by weighting Price (70%), Shipping Cost (20%), and Stock Availability (10%).")
    st.dataframe(
        buy_box_winners,
        use_container_width=True, hide_index=True,
    )