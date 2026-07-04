"""
shrauandsartu
03_charts.py
------------
Generates the visuals for the report. Kept to matplotlib/seaborn defaults
with minor styling - the goal is clarity, not decoration.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 120

OUT = '/home/claude/analysis/outputs'
CLASS_ORDER = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']
BUCKET_ORDER = ['Fear', 'Neutral', 'Greed']
COLORS = {'Extreme Fear': '#7f1d1d', 'Fear': '#dc2626', 'Neutral': '#6b7280',
          'Greed': '#16a34a', 'Extreme Greed': '#14532d'}
BUCKET_COLORS = {'Fear': '#dc2626', 'Neutral': '#6b7280', 'Greed': '#16a34a'}

merged = pd.read_csv(f'{OUT}/merged_trades.csv')
daily = pd.read_csv(f'{OUT}/daily_aggregated.csv')
daily['date'] = pd.to_datetime(daily['date'])
closes = merged[merged['is_close']].copy()

# ---------- Chart 1: Win rate by sentiment class ----------
fig, ax = plt.subplots(figsize=(8, 5))
win_rates = closes.groupby('sentiment')['Closed PnL'].apply(lambda x: (x > 0).mean()).reindex(CLASS_ORDER)
bars = ax.bar(win_rates.index, win_rates.values * 100, color=[COLORS[c] for c in CLASS_ORDER])
ax.set_ylabel('Win Rate (%)')
ax.set_title('Trader Win Rate by Market Sentiment')
ax.set_ylim(0, max(win_rates.values * 100) + 10)
for bar, val in zip(bars, win_rates.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val*100:.1f}%', ha='center', fontsize=10)
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(f'{OUT}/chart1_winrate_by_sentiment.png')
plt.close()

# ---------- Chart 2: Avg PnL per trade by sentiment class ----------
fig, ax = plt.subplots(figsize=(8, 5))
avg_pnl = closes.groupby('sentiment')['Closed PnL'].mean().reindex(CLASS_ORDER)
bars = ax.bar(avg_pnl.index, avg_pnl.values, color=[COLORS[c] for c in CLASS_ORDER])
ax.set_ylabel('Average Closed PnL per Trade (USD)')
ax.set_title('Average Trade Profitability by Market Sentiment')
for bar, val in zip(bars, avg_pnl.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'${val:.0f}', ha='center', fontsize=10)
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(f'{OUT}/chart2_avgpnl_by_sentiment.png')
plt.close()

# ---------- Chart 3: Long vs Short share by bucket ----------
opens = merged[merged['Direction'].isin(['Open Long', 'Open Short'])].copy()
ls = pd.crosstab(opens['sentiment_bucket'], opens['Direction'], normalize='index').reindex(BUCKET_ORDER) * 100
fig, ax = plt.subplots(figsize=(8, 5))
ls.plot(kind='bar', stacked=True, ax=ax, color=['#2563eb', '#f97316'])
ax.set_ylabel('% of Position Opens')
ax.set_title('Long vs Short Positioning by Market Sentiment')
ax.legend(title='', labels=['Long', 'Short'])
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f'{OUT}/chart3_long_short_by_sentiment.png')
plt.close()

# ---------- Chart 4: Time series - FG index vs daily PnL ----------
fig, ax1 = plt.subplots(figsize=(13, 5.5))
ax1.plot(daily['date'], daily['fg_value'], color='#9333ea', label='Fear/Greed Index', linewidth=1.2)
ax1.set_ylabel('Fear/Greed Index (0-100)', color='#9333ea')
ax1.tick_params(axis='y', labelcolor='#9333ea')

ax2 = ax1.twinx()
ax2.bar(daily['date'], daily['total_pnl'], color='#16a34a', alpha=0.4, width=1.5, label='Daily Total PnL')
ax2.set_ylabel('Daily Total Closed PnL (USD)', color='#16a34a')
ax2.tick_params(axis='y', labelcolor='#16a34a')
ax2.axhline(0, color='gray', linewidth=0.6)

ax1.set_title('Market Sentiment vs Daily Trader PnL Over Time')
fig.tight_layout()
plt.savefig(f'{OUT}/chart4_timeseries_sentiment_vs_pnl.png')
plt.close()

# ---------- Chart 5: Avg position size by sentiment ----------
fig, ax = plt.subplots(figsize=(8, 5))
size_by = merged.groupby('sentiment_bucket')['Size USD'].median().reindex(BUCKET_ORDER)
bars = ax.bar(size_by.index, size_by.values, color=[BUCKET_COLORS[b] for b in BUCKET_ORDER])
ax.set_ylabel('Median Position Size (USD)')
ax.set_title('Median Trade Size by Market Sentiment')
for bar, val in zip(bars, size_by.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, f'${val:.0f}', ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(f'{OUT}/chart5_size_by_sentiment.png')
plt.close()

# ---------- Chart 6: Top-10 vs All accounts win rate by bucket ----------
top_accounts = closes.groupby('Account')['Closed PnL'].sum().sort_values(ascending=False).head(10).index
top_perf = closes[closes['Account'].isin(top_accounts)]
top_wr = top_perf.groupby('sentiment_bucket')['Closed PnL'].apply(lambda x: (x > 0).mean()).reindex(BUCKET_ORDER)
all_wr = closes.groupby('sentiment_bucket')['Closed PnL'].apply(lambda x: (x > 0).mean()).reindex(BUCKET_ORDER)

fig, ax = plt.subplots(figsize=(8, 5))
x = range(len(BUCKET_ORDER))
width = 0.35
ax.bar([i - width/2 for i in x], all_wr.values * 100, width, label='All Traders', color='#94a3b8')
ax.bar([i + width/2 for i in x], top_wr.values * 100, width, label='Top 10 Traders', color='#16a34a')
ax.set_xticks(list(x))
ax.set_xticklabels(BUCKET_ORDER)
ax.set_ylabel('Win Rate (%)')
ax.set_title('Win Rate by Sentiment: Top Traders vs All Traders')
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUT}/chart6_top_vs_all_winrate.png')
plt.close()

print("6 charts saved to outputs/")
