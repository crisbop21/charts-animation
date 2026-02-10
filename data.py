"""Dummy corporate dataset generators for animated chart demos."""

import numpy as np
import pandas as pd


def generate_quarterly_revenue(seed: int = 42) -> pd.DataFrame:
    """Quarterly revenue by business unit over 5 years (2020-2024)."""
    rng = np.random.default_rng(seed)
    years = range(2020, 2025)
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    units = ["Cloud Services", "Enterprise Software", "Consulting", "Data Analytics"]

    base = {"Cloud Services": 120, "Enterprise Software": 200, "Consulting": 80, "Data Analytics": 60}
    growth = {"Cloud Services": 1.08, "Enterprise Software": 1.03, "Consulting": 1.04, "Data Analytics": 1.12}

    rows = []
    for unit in units:
        rev = base[unit]
        for year in years:
            for q in quarters:
                noise = rng.normal(1.0, 0.05)
                seasonal = 1.1 if q in ("Q3", "Q4") else 0.95
                rev = rev * growth[unit] ** 0.25 * seasonal * noise
                rows.append({
                    "Year": year,
                    "Quarter": q,
                    "Period": f"{year} {q}",
                    "Business Unit": unit,
                    "Revenue ($M)": round(max(rev, 10), 1),
                })
    return pd.DataFrame(rows)


def generate_market_share(seed: int = 42) -> pd.DataFrame:
    """Monthly market share evolution for competing products."""
    rng = np.random.default_rng(seed)
    months = pd.date_range("2022-01", periods=36, freq="MS")
    companies = ["Acme Corp", "GlobalTech", "NovaSoft", "PeakData", "Others"]
    shares_start = [32, 25, 18, 10, 15]

    rows = []
    shares = np.array(shares_start, dtype=float)
    for month in months:
        drift = rng.normal(0, 0.4, size=len(companies))
        drift[0] += 0.15  # Acme Corp trending up
        drift[1] -= 0.05
        shares = np.clip(shares + drift, 2, 50)
        shares = shares / shares.sum() * 100
        for company, share in zip(companies, shares):
            rows.append({
                "Date": month,
                "Month": month.strftime("%Y-%m"),
                "Company": company,
                "Market Share (%)": round(share, 1),
            })
    return pd.DataFrame(rows)


def generate_employee_metrics(seed: int = 42) -> pd.DataFrame:
    """Quarterly employee headcount and satisfaction by department."""
    rng = np.random.default_rng(seed)
    departments = ["Engineering", "Sales", "Marketing", "Operations", "HR", "Finance"]
    quarters = pd.date_range("2021-01", periods=16, freq="QS")
    base_hc = {"Engineering": 450, "Sales": 300, "Marketing": 120, "Operations": 200, "HR": 60, "Finance": 80}

    rows = []
    for dept in departments:
        hc = base_hc[dept]
        sat = rng.uniform(3.5, 4.2)
        for q in quarters:
            hc = int(hc * rng.uniform(1.00, 1.06))
            sat = np.clip(sat + rng.normal(0.02, 0.08), 2.5, 5.0)
            rows.append({
                "Quarter": q,
                "Quarter Label": q.strftime("%Y-Q") + str((q.month - 1) // 3 + 1),
                "Department": dept,
                "Headcount": hc,
                "Satisfaction (1-5)": round(sat, 2),
                "Attrition Rate (%)": round(rng.uniform(3, 18), 1),
            })
    return pd.DataFrame(rows)


def generate_product_kpis(seed: int = 42) -> pd.DataFrame:
    """Weekly product KPIs: DAU, conversion, latency for an animated scatter."""
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2024-01-01", periods=52, freq="W")
    products = ["Platform A", "Platform B", "Platform C"]
    sizes = {"Platform A": 80, "Platform B": 50, "Platform C": 30}

    rows = []
    for product in products:
        dau = rng.integers(10_000, 90_000)
        conv = rng.uniform(2, 8)
        for week in weeks:
            dau = int(np.clip(dau + rng.normal(500, 2000), 5000, 150_000))
            conv = np.clip(conv + rng.normal(0.05, 0.2), 1, 15)
            latency = np.clip(rng.normal(200, 40) - conv * 5, 50, 500)
            rows.append({
                "Week": week,
                "Week Label": week.strftime("%Y-W%U"),
                "Product": product,
                "DAU": dau,
                "Conversion Rate (%)": round(conv, 2),
                "Avg Latency (ms)": round(latency, 0),
                "Team Size": sizes[product],
            })
    return pd.DataFrame(rows)


def generate_regional_sales(seed: int = 42) -> pd.DataFrame:
    """Yearly regional sales for animated choropleth / bar race."""
    rng = np.random.default_rng(seed)
    regions = [
        "North America", "Europe", "Asia Pacific",
        "Latin America", "Middle East & Africa",
    ]
    years = list(range(2018, 2025))
    base = [500, 380, 290, 120, 80]

    rows = []
    for region, b in zip(regions, base):
        rev = b
        for year in years:
            rev = rev * rng.uniform(1.02, 1.15)
            rows.append({
                "Year": year,
                "Region": region,
                "Sales ($M)": round(rev, 1),
            })
    return pd.DataFrame(rows)


def generate_funnel_data(seed: int = 42) -> pd.DataFrame:
    """Monthly sales funnel stages."""
    rng = np.random.default_rng(seed)
    months = pd.date_range("2023-01", periods=24, freq="MS")
    stages = ["Leads", "Qualified", "Proposal", "Negotiation", "Closed Won"]
    drop_rates = [1.0, 0.45, 0.30, 0.18, 0.10]

    rows = []
    for month in months:
        base_leads = int(rng.integers(8000, 14000))
        for stage, dr in zip(stages, drop_rates):
            count = int(base_leads * dr * rng.uniform(0.85, 1.15))
            rows.append({
                "Month": month,
                "Month Label": month.strftime("%b %Y"),
                "Stage": stage,
                "Count": count,
                "Stage Order": stages.index(stage),
            })
    return pd.DataFrame(rows)
