import pandas as pd
import numpy as np

def generate_forecast(history_df: pd.DataFrame, days_ahead: int = 5) -> dict:
    if len(history_df) < 3:
        return {"recommendation": "Not enough data to forecast.", "forecast_df": pd.DataFrame()}

    daily_avg = history_df.groupby(history_df['observed_at'].dt.date)['price'].mean().reset_index()
    daily_avg['observed_at'] = pd.to_datetime(daily_avg['observed_at'])
    daily_avg = daily_avg.sort_values('observed_at')

    if len(daily_avg) < 2:
        return {"recommendation": "Not enough data to forecast.", "forecast_df": pd.DataFrame()}

    daily_avg['date_ordinal'] = daily_avg['observed_at'].map(pd.Timestamp.toordinal)
    
    x = daily_avg['date_ordinal']
    y = daily_avg['price']
    
    m, c = np.polyfit(x, y, 1)
    
    last_date = daily_avg['observed_at'].max()
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days_ahead + 1)]
    future_ordinals = [d.toordinal() for d in future_dates]
    
    future_prices = [m * ord_val + c for ord_val in future_ordinals]
    
    forecast_df = pd.DataFrame({
        'observed_at': future_dates,
        'price': future_prices,
        'retailer_name': '🔮 Projected Average'
    })
    
    if m < -0.05:
        rec = "📉 **Wait.** The market trend is falling. Better deals are likely ahead."
    elif m > 0.05:
        rec = "📈 **Buy Now.** The market trend is rising. Lock in the current price."
    else:
        rec = "⚖️ **Stable.** Prices are holding steady. Safe to buy whenever."
        
    return {"recommendation": rec, "forecast_df": forecast_df}