"""
01_build_merged_dataset.py
---------------------------
Loads both raw datasets, cleans them, joins each trade to that day's
Fear/Greed classification, and saves a merged trade-level file plus a
daily-aggregated file for the rest of the analysis to build on.
"""

import pandas as pd

# ---------- Load ----------
fg = pd.read_csv('/mnt/user-data/uploads/fear_greed_index.csv')
tr = pd.read_csv('/mnt/user-data/uploads/historical_data.csv')

# ---------- Clean sentiment data ----------
fg['date'] = pd.to_datetime(fg['date']).dt.date
fg = fg[['date', 'value', 'classification']].rename(
    columns={'value': 'fg_value', 'classification': 'sentiment'}
)

# Collapse the 5-way classification into a simpler 2-way bucket too,
# useful for cleaner comparisons later.
def bucket(s):
    if s in ('Fear', 'Extreme Fear'):
        return 'Fear'
    if s in ('Greed', 'Extreme Greed'):
        return 'Greed'
    return 'Neutral'

fg['sentiment_bucket'] = fg['sentiment'].apply(bucket)

# ---------- Clean trader data ----------
tr['dt'] = pd.to_datetime(tr['Timestamp IST'], format='%d-%m-%Y %H:%M')
tr['date'] = tr['dt'].dt.date

# Only keep trades where PnL is actually being realised (closing/reducing
# trades). Opens have Closed PnL = 0 by definition on Hyperliquid, so
# including them would water down PnL-based stats without adding info.
tr['is_close'] = tr['Direction'].str.contains('Close', na=False) | tr['Direction'].isin(['Buy', 'Sell'])

# ---------- Merge ----------
merged = tr.merge(fg, on='date', how='inner')

print(f"Trades total: {len(tr):,}")
print(f"Trades matched to a sentiment day: {len(merged):,} ({len(merged)/len(tr)*100:.1f}%)")
print(f"Date range covered by sentiment data that overlaps trades: "
      f"{merged['date'].min()} to {merged['date'].max()}")

merged.to_csv('/home/claude/analysis/outputs/merged_trades.csv', index=False)

# ---------- Daily aggregation ----------
daily = merged.groupby('date').agg(
    total_pnl=('Closed PnL', 'sum'),
    avg_pnl_per_trade=('Closed PnL', 'mean'),
    trade_count=('Closed PnL', 'count'),
    total_volume_usd=('Size USD', 'sum'),
    avg_size_usd=('Size USD', 'mean'),
    unique_accounts=('Account', 'nunique'),
    sentiment=('sentiment', 'first'),
    sentiment_bucket=('sentiment_bucket', 'first'),
    fg_value=('fg_value', 'first'),
).reset_index()

daily['win_rate'] = merged.groupby('date').apply(
    lambda g: (g['Closed PnL'] > 0).sum() / len(g) if len(g) > 0 else None
).values

daily.to_csv('/home/claude/analysis/outputs/daily_aggregated.csv', index=False)

print("\nSaved:")
print(" - outputs/merged_trades.csv")
print(" - outputs/daily_aggregated.csv")
print(f"\nDaily records: {len(daily)}")
print(daily.head())
