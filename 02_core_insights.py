"""
02_core_insights.py
--------------------
The actual "explore the relationship" part. Computes trader performance
metrics broken down by sentiment class/bucket, and prints everything in a
readable form. Numbers here feed directly into the written insights doc.
"""

import pandas as pd
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')

merged = pd.read_csv('/home/claude/analysis/outputs/merged_trades.csv')
daily = pd.read_csv('/home/claude/analysis/outputs/daily_aggregated.csv')

CLASS_ORDER = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']
BUCKET_ORDER = ['Fear', 'Neutral', 'Greed']

# Only rows where a PnL was actually realised are meaningful for win-rate /
# PnL-based comparisons.
closes = merged[merged['is_close']].copy()

print("="*70)
print("1. TRADE-LEVEL PERFORMANCE BY SENTIMENT CLASS (5-way)")
print("="*70)
by_class = closes.groupby('sentiment').agg(
    trades=('Closed PnL', 'count'),
    total_pnl=('Closed PnL', 'sum'),
    avg_pnl=('Closed PnL', 'mean'),
    median_pnl=('Closed PnL', 'median'),
    win_rate=('Closed PnL', lambda x: (x > 0).mean()),
    avg_size_usd=('Size USD', 'mean'),
).reindex(CLASS_ORDER)
print(by_class)

print("\n" + "="*70)
print("2. TRADE-LEVEL PERFORMANCE BY SENTIMENT BUCKET (Fear/Neutral/Greed)")
print("="*70)
by_bucket = closes.groupby('sentiment_bucket').agg(
    trades=('Closed PnL', 'count'),
    total_pnl=('Closed PnL', 'sum'),
    avg_pnl=('Closed PnL', 'mean'),
    median_pnl=('Closed PnL', 'median'),
    win_rate=('Closed PnL', lambda x: (x > 0).mean()),
    avg_size_usd=('Size USD', 'mean'),
).reindex(BUCKET_ORDER)
print(by_bucket)

print("\n" + "="*70)
print("3. LONG vs SHORT BIAS BY SENTIMENT")
print("="*70)
opens = merged[merged['Direction'].isin(['Open Long', 'Open Short'])].copy()
long_short = pd.crosstab(opens['sentiment_bucket'], opens['Direction'], normalize='index') * 100
print(long_short.reindex(BUCKET_ORDER).round(1))

print("\n" + "="*70)
print("4. POSITION SIZE (USD) BY SENTIMENT")
print("="*70)
size_by_sentiment = merged.groupby('sentiment_bucket')['Size USD'].agg(
    ['mean', 'median', 'std']
).reindex(BUCKET_ORDER)
print(size_by_sentiment)

print("\n" + "="*70)
print("5. TOP 10 ACCOUNTS - DO THEY BEHAVE DIFFERENTLY ACROSS SENTIMENT?")
print("="*70)
top_accounts = closes.groupby('Account')['Closed PnL'].sum().sort_values(ascending=False).head(10)
print("Top 10 accounts by total realised PnL:")
print(top_accounts)

top_ids = top_accounts.index
top_perf = closes[closes['Account'].isin(top_ids)]
print("\nTop-10 accounts' win rate by sentiment bucket:")
print(top_perf.groupby('sentiment_bucket')['Closed PnL'].agg(
    win_rate=lambda x: (x > 0).mean(), avg_pnl='mean'
).reindex(BUCKET_ORDER))

all_perf_by_bucket = closes.groupby('sentiment_bucket')['Closed PnL'].agg(
    win_rate=lambda x: (x > 0).mean(), avg_pnl='mean'
).reindex(BUCKET_ORDER)
print("\nAll accounts' win rate by sentiment bucket (for comparison):")
print(all_perf_by_bucket)

print("\n" + "="*70)
print("6. CORRELATION: DAILY FEAR/GREED VALUE vs DAILY TOTAL PNL")
print("="*70)
corr = daily[['fg_value', 'total_pnl', 'win_rate', 'total_volume_usd']].corr()
print(corr)

print("\n" + "="*70)
print("7. SENTIMENT REGIME TRANSITIONS - DOES BEHAVIOR SHIFT THE DAY AFTER?")
print("="*70)
daily_sorted = daily.sort_values('date').reset_index(drop=True)
daily_sorted['prev_bucket'] = daily_sorted['sentiment_bucket'].shift(1)
daily_sorted['bucket_changed'] = daily_sorted['sentiment_bucket'] != daily_sorted['prev_bucket']
transition = daily_sorted[daily_sorted['bucket_changed']].groupby(
    ['prev_bucket', 'sentiment_bucket']
)['total_pnl'].agg(['mean', 'count'])
print(transition)

# Save summary tables for the report
by_class.to_csv('/home/claude/analysis/outputs/summary_by_class.csv')
by_bucket.to_csv('/home/claude/analysis/outputs/summary_by_bucket.csv')
long_short.to_csv('/home/claude/analysis/outputs/long_short_by_sentiment.csv')
print("\nSummary CSVs saved to outputs/")
