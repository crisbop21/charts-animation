"""
Animated Corporate Dashboard - Exploring Python Animation Capabilities
======================================================================
A Streamlit app showcasing animated Plotly charts with dummy corporate data.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data import (
    generate_quarterly_revenue,
    generate_market_share,
    generate_employee_metrics,
    generate_product_kpis,
    generate_regional_sales,
    generate_funnel_data,
)

# ---------------------------------------------------------------------------
# Page config & corporate theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Corporate Analytics Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

CORPORATE_COLORS = [
    "#1B2A4A",  # dark navy
    "#2E86AB",  # teal
    "#A23B72",  # magenta
    "#F18F01",  # amber
    "#3C8D2F",  # green
    "#6C757D",  # grey
    "#C73E1D",  # red-orange
    "#5C4D7D",  # purple
]

CORPORATE_TEMPLATE = "plotly_white"


def apply_corporate_style(fig: go.Figure) -> go.Figure:
    """Apply consistent corporate styling to a Plotly figure."""
    fig.update_layout(
        font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", size=13),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_size=18,
        title_font_color="#1B2A4A",
        legend=dict(
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#dee2e6",
            borderwidth=1,
            font_size=11,
        ),
        margin=dict(l=50, r=30, t=60, b=50),
        colorway=CORPORATE_COLORS,
    )
    fig.update_xaxes(gridcolor="#e9ecef", gridwidth=0.5)
    fig.update_yaxes(gridcolor="#e9ecef", gridwidth=0.5)
    return fig


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    .block-container { padding-top: 1.5rem; }
    h1 { color: #1B2A4A; border-bottom: 3px solid #2E86AB; padding-bottom: 0.4rem; }
    h2 { color: #1B2A4A; }
    h3 { color: #2E86AB; }
    .stMetric { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 1rem; border-radius: 8px; border-left: 4px solid #2E86AB; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("---")
animation_speed = st.sidebar.slider("Animation speed (ms per frame)", 50, 500, 150, step=50)
st.sidebar.markdown("---")
sections = st.sidebar.multiselect(
    "Sections to display",
    [
        "Revenue Growth Animation",
        "Market Share Race",
        "Employee Bubble Chart",
        "Product KPI Scatter",
        "Regional Sales Bar Race",
        "Sales Funnel Animation",
    ],
    default=[
        "Revenue Growth Animation",
        "Market Share Race",
        "Employee Bubble Chart",
        "Product KPI Scatter",
        "Regional Sales Bar Race",
        "Sales Funnel Animation",
    ],
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Corporate Analytics Dashboard")
st.markdown(
    "Exploring **animated Python visualizations** with Plotly + Streamlit. "
    "Every chart below uses `animation_frame` or manual frame-based animation."
)

# Quick KPIs
rev_df = generate_quarterly_revenue()
latest_year = rev_df["Year"].max()
total_rev = rev_df[rev_df["Year"] == latest_year]["Revenue ($M)"].sum()
prev_rev = rev_df[rev_df["Year"] == latest_year - 1]["Revenue ($M)"].sum()
yoy = (total_rev - prev_rev) / prev_rev * 100

ms_df = generate_market_share()
latest_share = ms_df[ms_df["Company"] == "Acme Corp"]["Market Share (%)"].iloc[-1]

emp_df = generate_employee_metrics()
total_hc = emp_df.groupby("Quarter").last().groupby("Department")["Headcount"].last().sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("FY Revenue", f"${total_rev:,.0f}M", f"{yoy:+.1f}% YoY")
col2.metric("Market Share (Acme)", f"{latest_share:.1f}%", "+3.2pp vs 2022")
col3.metric("Total Headcount", f"{total_hc:,}")
col4.metric("Business Units", "4", "")

st.markdown("---")

# ===================================================================
# 1. ANIMATED AREA CHART - Quarterly Revenue Growth
# ===================================================================
if "Revenue Growth Animation" in sections:
    st.header("1 - Revenue Growth by Business Unit")
    st.caption("Animated area chart showing quarterly revenue evolution across business units. Press play to watch growth over time.")

    fig_rev = px.area(
        rev_df,
        x="Business Unit",
        y="Revenue ($M)",
        color="Business Unit",
        animation_frame="Period",
        range_y=[0, rev_df["Revenue ($M)"].max() * 1.15],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=CORPORATE_COLORS,
        title="Quarterly Revenue by Business Unit",
    )
    fig_rev.update_layout(
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=1.15,
            x=0.5,
            xanchor="center",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame": {"duration": animation_speed, "redraw": True},
                                  "fromcurrent": True}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    apply_corporate_style(fig_rev)
    st.plotly_chart(fig_rev, use_container_width=True)

    with st.expander("View revenue data"):
        st.dataframe(rev_df, use_container_width=True, hide_index=True)

    st.markdown("---")

# ===================================================================
# 2. ANIMATED LINE CHART - Market Share Race
# ===================================================================
if "Market Share Race" in sections:
    st.header("2 - Market Share Race")
    st.caption("Animated line chart showing how market share shifts month-over-month across competitors.")

    # Build frames manually for a cumulative line animation
    months = ms_df["Month"].unique()
    frames = []
    for i in range(1, len(months) + 1):
        subset = ms_df[ms_df["Month"].isin(months[:i])]
        frames.append(go.Frame(
            data=[
                go.Scatter(
                    x=subset[subset["Company"] == c]["Month"],
                    y=subset[subset["Company"] == c]["Market Share (%)"],
                    mode="lines+markers",
                    name=c,
                    line=dict(width=3),
                    marker=dict(size=4),
                )
                for c in ms_df["Company"].unique()
            ],
            name=months[i - 1],
        ))

    init = ms_df[ms_df["Month"] == months[0]]
    fig_ms = go.Figure(
        data=[
            go.Scatter(
                x=init[init["Company"] == c]["Month"],
                y=init[init["Company"] == c]["Market Share (%)"],
                mode="lines+markers",
                name=c,
                line=dict(width=3),
                marker=dict(size=4),
            )
            for c in ms_df["Company"].unique()
        ],
        frames=frames,
        layout=go.Layout(
            title="Monthly Market Share Evolution",
            xaxis=dict(title="Month", range=[months[0], months[-1]]),
            yaxis=dict(title="Market Share (%)", range=[0, 50]),
            updatemenus=[dict(
                type="buttons", showactive=False, y=1.15, x=0.5, xanchor="center",
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, {"frame": {"duration": animation_speed, "redraw": True},
                                      "fromcurrent": True, "transition": {"duration": 80}}]),
                    dict(label="Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False},
                                        "mode": "immediate"}]),
                ],
            )],
            sliders=[dict(
                active=0,
                steps=[dict(args=[[m], {"frame": {"duration": animation_speed, "redraw": True},
                                        "mode": "immediate"}],
                            method="animate", label=m)
                       for m in months],
                x=0.05, len=0.9, y=-0.05,
                currentvalue=dict(prefix="Month: ", font_size=12),
            )],
        ),
    )
    apply_corporate_style(fig_ms)
    fig_ms.update_layout(colorway=CORPORATE_COLORS)
    st.plotly_chart(fig_ms, use_container_width=True)
    st.markdown("---")

# ===================================================================
# 3. ANIMATED BUBBLE CHART - Employee Metrics
# ===================================================================
if "Employee Bubble Chart" in sections:
    st.header("3 - Employee Metrics Bubble Chart")
    st.caption("Animated scatter showing headcount vs satisfaction per department. Bubble size = attrition rate.")

    fig_emp = px.scatter(
        emp_df,
        x="Headcount",
        y="Satisfaction (1-5)",
        size="Attrition Rate (%)",
        color="Department",
        animation_frame="Quarter Label",
        hover_name="Department",
        size_max=45,
        range_x=[30, emp_df["Headcount"].max() * 1.15],
        range_y=[2.3, 5.2],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=CORPORATE_COLORS,
        title="Headcount vs Satisfaction (bubble = attrition rate)",
    )
    fig_emp.update_layout(
        updatemenus=[dict(
            type="buttons", showactive=False, y=1.15, x=0.5, xanchor="center",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame": {"duration": animation_speed, "redraw": True},
                                  "fromcurrent": True}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    apply_corporate_style(fig_emp)
    st.plotly_chart(fig_emp, use_container_width=True)
    st.markdown("---")

# ===================================================================
# 4. ANIMATED SCATTER - Product KPIs
# ===================================================================
if "Product KPI Scatter" in sections:
    st.header("4 - Product KPI Exploration")
    st.caption("Weekly animated scatter: DAU vs Conversion Rate. Bubble size = team size, color = product.")

    kpi_df = generate_product_kpis()
    fig_kpi = px.scatter(
        kpi_df,
        x="DAU",
        y="Conversion Rate (%)",
        size="Team Size",
        color="Product",
        animation_frame="Week Label",
        hover_data=["Avg Latency (ms)"],
        size_max=40,
        range_x=[0, kpi_df["DAU"].max() * 1.15],
        range_y=[0, kpi_df["Conversion Rate (%)"].max() * 1.25],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=CORPORATE_COLORS,
        title="DAU vs Conversion Rate Over Time",
    )
    fig_kpi.update_layout(
        updatemenus=[dict(
            type="buttons", showactive=False, y=1.15, x=0.5, xanchor="center",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame": {"duration": animation_speed, "redraw": True},
                                  "fromcurrent": True}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    apply_corporate_style(fig_kpi)
    st.plotly_chart(fig_kpi, use_container_width=True)
    st.markdown("---")

# ===================================================================
# 5. ANIMATED BAR RACE - Regional Sales
# ===================================================================
if "Regional Sales Bar Race" in sections:
    st.header("5 - Regional Sales Bar Race")
    st.caption("Animated horizontal bar chart racing through yearly regional sales.")

    reg_df = generate_regional_sales()
    reg_df = reg_df.sort_values(["Year", "Sales ($M)"], ascending=[True, True])

    fig_bar = px.bar(
        reg_df,
        x="Sales ($M)",
        y="Region",
        color="Region",
        animation_frame="Year",
        orientation="h",
        range_x=[0, reg_df["Sales ($M)"].max() * 1.15],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=CORPORATE_COLORS,
        title="Regional Sales Race ($M)",
        text="Sales ($M)",
    )
    fig_bar.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig_bar.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        showlegend=False,
        updatemenus=[dict(
            type="buttons", showactive=False, y=1.15, x=0.5, xanchor="center",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame": {"duration": animation_speed * 3, "redraw": True},
                                  "fromcurrent": True, "transition": {"duration": 400}}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    apply_corporate_style(fig_bar)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("---")

# ===================================================================
# 6. ANIMATED FUNNEL - Sales Pipeline
# ===================================================================
if "Sales Funnel Animation" in sections:
    st.header("6 - Sales Funnel Animation")
    st.caption("Animated bar chart showing the sales funnel stages evolving month-over-month.")

    funnel_df = generate_funnel_data()
    funnel_df = funnel_df.sort_values(["Month", "Stage Order"])

    fig_funnel = px.bar(
        funnel_df,
        x="Count",
        y="Stage",
        color="Stage",
        animation_frame="Month Label",
        orientation="h",
        range_x=[0, funnel_df["Count"].max() * 1.15],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=CORPORATE_COLORS,
        title="Sales Funnel Progression",
        text="Count",
    )
    fig_funnel.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_funnel.update_layout(
        yaxis=dict(categoryorder="array",
                   categoryarray=list(reversed(["Leads", "Qualified", "Proposal", "Negotiation", "Closed Won"]))),
        showlegend=False,
        updatemenus=[dict(
            type="buttons", showactive=False, y=1.15, x=0.5, xanchor="center",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame": {"duration": animation_speed * 2, "redraw": True},
                                  "fromcurrent": True, "transition": {"duration": 200}}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    apply_corporate_style(fig_funnel)
    st.plotly_chart(fig_funnel, use_container_width=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#6C757D; font-size:0.85rem;'>"
    "Built with Streamlit + Plotly | Dummy data for demonstration purposes"
    "</div>",
    unsafe_allow_html=True,
)
