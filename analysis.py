"""
Montreal Housing Market Analysis
================================
A data analysis project exploring rental and housing price trends
across Montreal boroughs using synthetic data modeled on real market ranges.

Author: Yumo Xu
Portfolio: yumorepos.github.io
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 150,
    "font.family": "sans-serif",
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})

SEED = 42
np.random.seed(SEED)


# ── Data Generation ─────────────────────────────────────────────
# Synthetic data modeled on real Montreal rental/housing market ranges (2020-2025)
# Sources referenced: CMHC Rental Market Reports, Centris Quebec, StatCan

BOROUGHS = [
    "Plateau-Mont-Royal", "Ville-Marie", "Rosemont", "Outremont",
    "Verdun", "Côte-des-Neiges", "Saint-Laurent", "Mercier",
    "Villeray", "Le Sud-Ouest", "Ahuntsic", "Lachine",
]

# Base monthly rent by unit type (CAD, 2020 baseline)
BASE_RENT = {"Studio": 850, "1BR": 1150, "2BR": 1450, "3BR": 1800, "4BR+": 2200}

# Borough premium multiplier (1.0 = average)
BOROUGH_MULT = {
    "Plateau-Mont-Royal": 1.20, "Ville-Marie": 1.35, "Rosemont": 1.05,
    "Outremont": 1.25, "Verdun": 0.95, "Côte-des-Neiges": 0.90,
    "Saint-Laurent": 0.88, "Mercier": 0.85, "Villeray": 1.00,
    "Le Sud-Ouest": 1.10, "Ahuntsic": 0.92, "Lachine": 0.87,
}

# Annual rent increase rate (compounding, varies by year)
ANNUAL_INCREASES = {2020: 0.02, 2021: 0.03, 2022: 0.05, 2023: 0.06, 2024: 0.04, 2025: 0.035}


def generate_rental_data(n_per_combo: int = 40) -> pd.DataFrame:
    """Generate synthetic Montreal rental listings."""
    rows = []
    for year in range(2020, 2026):
        cumulative = 1.0
        for y in range(2020, year + 1):
            cumulative *= (1 + ANNUAL_INCREASES.get(y, 0.03))

        for borough in BOROUGHS:
            for unit_type, base in BASE_RENT.items():
                for _ in range(n_per_combo):
                    price = base * BOROUGH_MULT[borough] * cumulative
                    noise = np.random.normal(1.0, 0.08)
                    rent = round(price * noise, 0)

                    # Random listing date within the year
                    start = datetime(year, 1, 1)
                    offset = np.random.randint(0, 365)
                    date = start + timedelta(days=offset)

                    # Vacancy: lower in expensive boroughs
                    vacancy_rate = max(0.01, 0.05 - BOROUGH_MULT[borough] * 0.02 + np.random.normal(0, 0.01))

                    rows.append({
                        "date": date,
                        "year": year,
                        "borough": borough,
                        "unit_type": unit_type,
                        "monthly_rent": rent,
                        "vacancy_rate": round(vacancy_rate, 4),
                    })

    df = pd.DataFrame(rows)
    return df


def generate_sales_data(n_per_combo: int = 20) -> pd.DataFrame:
    """Generate synthetic Montreal home sales data."""
    # Median sale prices by property type (2020 baseline, CAD)
    BASE_PRICE = {"Condo": 350_000, "Duplex": 550_000, "Single-Family": 480_000, "Triplex": 700_000}
    ANNUAL_PRICE_GROWTH = {2020: 0.05, 2021: 0.12, 2022: 0.08, 2023: -0.02, 2024: 0.03, 2025: 0.04}

    rows = []
    for year in range(2020, 2026):
        cumulative = 1.0
        for y in range(2020, year + 1):
            cumulative *= (1 + ANNUAL_PRICE_GROWTH.get(y, 0.03))

        for borough in BOROUGHS:
            for prop_type, base in BASE_PRICE.items():
                for _ in range(n_per_combo):
                    price = base * BOROUGH_MULT[borough] * cumulative
                    noise = np.random.normal(1.0, 0.12)
                    sale_price = round(price * noise, -3)  # round to nearest $1K

                    start = datetime(year, 1, 1)
                    offset = np.random.randint(0, 365)
                    date = start + timedelta(days=offset)

                    # Days on market: inversely correlated with demand
                    dom = max(5, int(np.random.normal(45 / BOROUGH_MULT[borough], 15)))

                    rows.append({
                        "date": date,
                        "year": year,
                        "borough": borough,
                        "property_type": prop_type,
                        "sale_price": sale_price,
                        "days_on_market": dom,
                    })

    return pd.DataFrame(rows)


# ── Analysis Functions ──────────────────────────────────────────

def analyze_rental_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Compute yearly rental stats by borough and unit type."""
    stats = (
        df.groupby(["year", "borough", "unit_type"])["monthly_rent"]
        .agg(["median", "mean", "std", "count"])
        .reset_index()
    )
    stats.columns = ["year", "borough", "unit_type", "median_rent", "mean_rent", "std_rent", "listings"]
    return stats


def compute_affordability(rental_df: pd.DataFrame) -> pd.DataFrame:
    """Compute rent-to-income ratio assuming Montreal median household income."""
    # Montreal median household income (approx, from StatCan)
    MEDIAN_INCOME = {2020: 52000, 2021: 54000, 2022: 56500, 2023: 58000, 2024: 60000, 2025: 62000}

    yearly = rental_df.groupby("year")["monthly_rent"].median().reset_index()
    yearly.columns = ["year", "median_rent"]
    yearly["annual_rent"] = yearly["median_rent"] * 12
    yearly["median_income"] = yearly["year"].map(MEDIAN_INCOME)
    yearly["rent_to_income"] = (yearly["annual_rent"] / yearly["median_income"] * 100).round(1)
    return yearly


# ── Visualization Functions ─────────────────────────────────────

def plot_rent_trends(stats: pd.DataFrame) -> None:
    """Plot median rent over time by unit type (city-wide)."""
    city_wide = stats.groupby(["year", "unit_type"])["median_rent"].median().reset_index()

    fig, ax = plt.subplots()
    for unit_type in BASE_RENT.keys():
        subset = city_wide[city_wide["unit_type"] == unit_type]
        ax.plot(subset["year"], subset["median_rent"], marker="o", linewidth=2, label=unit_type)

    ax.set_title("Montreal Median Monthly Rent by Unit Type (2020–2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Monthly Rent (CAD)")
    ax.legend(title="Unit Type")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/01_rent_trends.png")
    plt.close()
    print("  ✓ Saved 01_rent_trends.png")


def plot_borough_comparison(stats: pd.DataFrame) -> None:
    """Heatmap of median 2BR rent by borough and year."""
    two_br = stats[stats["unit_type"] == "2BR"]
    pivot = two_br.pivot_table(index="borough", columns="year", values="median_rent", aggfunc="median")
    pivot = pivot.sort_values(by=pivot.columns[-1], ascending=False)

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="YlOrRd", linewidths=0.5, ax=ax)
    ax.set_title("Median 2BR Rent by Borough (CAD/month)")
    ax.set_xlabel("Year")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/02_borough_heatmap.png")
    plt.close()
    print("  ✓ Saved 02_borough_heatmap.png")


def plot_affordability(afford_df: pd.DataFrame) -> None:
    """Bar chart: rent-to-income ratio over time."""
    fig, ax = plt.subplots()
    colors = ["#2ecc71" if r < 30 else "#f39c12" if r < 35 else "#e74c3c" for r in afford_df["rent_to_income"]]
    bars = ax.bar(afford_df["year"], afford_df["rent_to_income"], color=colors, edgecolor="white", linewidth=0.8)

    ax.axhline(y=30, color="#e74c3c", linestyle="--", linewidth=1, label="30% affordability threshold")
    ax.set_title("Montreal Rent-to-Income Ratio (2020–2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Rent as % of Median Income")
    ax.legend()

    for bar, val in zip(bars, afford_df["rent_to_income"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylim(0, max(afford_df["rent_to_income"]) + 5)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/03_affordability.png")
    plt.close()
    print("  ✓ Saved 03_affordability.png")


def plot_sales_distribution(sales_df: pd.DataFrame) -> None:
    """Violin plot of sale prices by property type (2025)."""
    recent = sales_df[sales_df["year"] == 2025]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=recent, x="property_type", y="sale_price", palette="Set2", inner="box", ax=ax)
    ax.set_title("Montreal Sale Price Distribution by Property Type (2025)")
    ax.set_xlabel("Property Type")
    ax.set_ylabel("Sale Price (CAD)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/04_sales_distribution.png")
    plt.close()
    print("  ✓ Saved 04_sales_distribution.png")


def plot_days_on_market(sales_df: pd.DataFrame) -> None:
    """Line chart: average days on market by year."""
    dom = sales_df.groupby("year")["days_on_market"].mean().reset_index()

    fig, ax = plt.subplots()
    ax.plot(dom["year"], dom["days_on_market"], marker="s", linewidth=2.5, color="#3498db", markersize=8)
    ax.fill_between(dom["year"], dom["days_on_market"], alpha=0.15, color="#3498db")
    ax.set_title("Average Days on Market — Montreal (2020–2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Days on Market")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/05_days_on_market.png")
    plt.close()
    print("  ✓ Saved 05_days_on_market.png")


# ── Main ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Montreal Housing Market Analysis")
    print("=" * 60)

    # Generate data
    print("\n📊 Generating synthetic dataset...")
    rentals = generate_rental_data()
    sales = generate_sales_data()
    print(f"  Rental listings: {len(rentals):,}")
    print(f"  Sales records:   {len(sales):,}")

    # Save raw data
    rentals.to_csv(f"{OUTPUT_DIR}/rentals.csv", index=False)
    sales.to_csv(f"{OUTPUT_DIR}/sales.csv", index=False)
    print(f"  ✓ Raw data saved to {OUTPUT_DIR}/")

    # Rental analysis
    print("\n📈 Analyzing rental trends...")
    rental_stats = analyze_rental_trends(rentals)

    city_median = rentals.groupby("year")["monthly_rent"].median()
    yoy_change = city_median.pct_change() * 100
    print(f"\n  City-wide median rent (2025): ${city_median.iloc[-1]:,.0f}/mo")
    print(f"  5-year rent increase: {((city_median.iloc[-1] / city_median.iloc[0]) - 1) * 100:.1f}%")
    print(f"  2025 YoY change: {yoy_change.iloc[-1]:+.1f}%")

    # Most/least expensive boroughs
    borough_2025 = (
        rentals[rentals["year"] == 2025]
        .groupby("borough")["monthly_rent"]
        .median()
        .sort_values(ascending=False)
    )
    print(f"\n  Most expensive borough:  {borough_2025.index[0]} (${borough_2025.iloc[0]:,.0f}/mo)")
    print(f"  Least expensive borough: {borough_2025.index[-1]} (${borough_2025.iloc[-1]:,.0f}/mo)")
    print(f"  Spread: ${borough_2025.iloc[0] - borough_2025.iloc[-1]:,.0f}/mo")

    # Affordability
    print("\n💰 Computing affordability metrics...")
    affordability = compute_affordability(rentals)
    latest = affordability.iloc[-1]
    print(f"  2025 rent-to-income ratio: {latest['rent_to_income']}%")
    if latest["rent_to_income"] > 30:
        print("  ⚠️  Above 30% threshold — housing stress territory")

    # Sales summary
    print("\n🏠 Sales market summary (2025)...")
    sales_2025 = sales[sales["year"] == 2025]
    for prop_type in ["Condo", "Duplex", "Single-Family", "Triplex"]:
        med = sales_2025[sales_2025["property_type"] == prop_type]["sale_price"].median()
        print(f"  {prop_type:15s} median: ${med:>12,.0f}")

    avg_dom = sales_2025["days_on_market"].mean()
    print(f"\n  Average days on market: {avg_dom:.0f}")

    # Generate visualizations
    print("\n🎨 Generating visualizations...")
    plot_rent_trends(rental_stats)
    plot_borough_comparison(rental_stats)
    plot_affordability(affordability)
    plot_sales_distribution(sales)
    plot_days_on_market(sales)

    print("\n" + "=" * 60)
    print("  Analysis complete! See output/ for charts and data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
