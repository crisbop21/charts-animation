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
from functools import partial
from export import (
    revenue_growth_to_mp4,
    market_share_to_mp4,
    employee_bubble_to_mp4,
    product_kpi_to_mp4,
    bar_race_to_mp4,
    funnel_to_mp4,
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

# High-contrast palette optimized for mobile/OLED screens
TIKTOK_COLORS = [
    "#FF3366",  # hot pink
    "#00D4FF",  # electric cyan
    "#FFD700",  # gold
    "#00FF88",  # neon green
    "#FF6B35",  # vivid orange
    "#B44DFF",  # vivid purple
    "#FF4757",  # coral red
    "#18DCFF",  # sky blue
]

CORPORATE_TEMPLATE = "plotly_white"


def apply_corporate_style(fig: go.Figure, tiktok: bool = False) -> go.Figure:
    """Apply consistent styling to a Plotly figure. TikTok mode uses larger text and bolder visuals."""
    colors = TIKTOK_COLORS if tiktok else CORPORATE_COLORS

    if tiktok:
        fig.update_layout(
            font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", size=18),
            plot_bgcolor="#0D0D0D",
            paper_bgcolor="#0D0D0D",
            title_font_size=28,
            title_font_color="#FFFFFF",
            legend=dict(
                bgcolor="rgba(0,0,0,0.6)",
                bordercolor="#333",
                borderwidth=1,
                font_size=16,
                font_color="#FFFFFF",
            ),
            margin=dict(l=60, r=30, t=80, b=60),
            colorway=colors,
            height=900,
        )
        fig.update_xaxes(
            gridcolor="#222", gridwidth=0.5,
            tickfont=dict(size=15, color="#AAAAAA"),
            title_font=dict(size=17, color="#CCCCCC"),
        )
        fig.update_yaxes(
            gridcolor="#222", gridwidth=0.5,
            tickfont=dict(size=15, color="#AAAAAA"),
            title_font=dict(size=17, color="#CCCCCC"),
        )
    else:
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
            colorway=colors,
        )
        fig.update_xaxes(gridcolor="#e9ecef", gridwidth=0.5)
        fig.update_yaxes(gridcolor="#e9ecef", gridwidth=0.5)
    return fig


def _download_section(key: str, filename: str, export_fn, tiktok: bool):
    """Show 'Generate MP4' button and, once ready, a download button.

    *export_fn* must accept a ``progress_cb`` keyword argument and return
    MP4 bytes.  Use ``functools.partial`` to bind the data arguments.
    """
    with st.container(border=True):
        col_label, col_btn = st.columns([3, 1])
        col_label.markdown("**Export this animation as MP4 video**")

        if col_btn.button("Generate MP4", key=f"gen_{key}", use_container_width=True):
            bar = st.progress(0, text="Rendering frames...")
            try:
                mp4_data = export_fn(
                    progress_cb=lambda p: bar.progress(
                        p, text=f"Rendering frames... {int(p * 100)}%",
                    ),
                )
                st.session_state[f"mp4_{key}"] = mp4_data
            except Exception as e:
                st.error(f"MP4 generation failed: {e}")
            finally:
                bar.empty()

        if st.session_state.get(f"mp4_{key}"):
            st.download_button(
                "Download MP4",
                st.session_state[f"mp4_{key}"],
                file_name=filename,
                mime="video/mp4",
                key=f"dl_{key}",
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Dashboard Controls")
st.sidebar.markdown("---")
tiktok_mode = st.sidebar.toggle("TikTok Mode (9:16 vertical)", value=False)
if tiktok_mode:
    st.sidebar.caption(
        "Optimized for screen recording: dark background, bold colors, "
        "large text, vertical layout. Shows one chart at a time."
    )
animation_speed = st.sidebar.slider(
    "Animation speed (ms per frame)", 50, 500,
    200 if tiktok_mode else 150, step=50,
)
st.sidebar.markdown("---")

all_sections = [
    "Revenue Growth Animation",
    "Market Share Race",
    "Employee Bubble Chart",
    "Product KPI Scatter",
    "Regional Sales Bar Race",
    "Sales Funnel Animation",
]

if tiktok_mode:
    selected_section = st.sidebar.radio("Chart to display", all_sections, index=4)
    sections = [selected_section]
else:
    sections = st.sidebar.multiselect(
        "Sections to display",
        all_sections,
        default=all_sections,
    )

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
if tiktok_mode:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="st-"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
        .block-container { padding-top: 1rem; max-width: 540px !important; margin: 0 auto; }
        .stApp { background-color: #0D0D0D; }
        h1, h2, h3, p, span, label { color: #FFFFFF !important; }
        h1 { border-bottom: 3px solid #FF3366; padding-bottom: 0.4rem; font-size: 1.6rem !important; }
        h2 { font-size: 1.4rem !important; }
        .stMetric { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    padding: 1rem; border-radius: 8px; border-left: 4px solid #FF3366; }
        .stMetric label, .stMetric [data-testid="stMetricValue"],
        .stMetric [data-testid="stMetricDelta"] { color: #FFFFFF !important; }
        [data-testid="stSidebar"] { background-color: #111111; }
        [data-testid="stSidebar"] * { color: #EEEEEE !important; }
    </style>
    """, unsafe_allow_html=True)
else:
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
# Header
# ---------------------------------------------------------------------------
if tiktok_mode:
    st.title("Analytics Dashboard")
else:
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

if tiktok_mode:
    col1, col2 = st.columns(2)
    col1.metric("FY Revenue", f"${total_rev:,.0f}M", f"{yoy:+.1f}% YoY")
    col2.metric("Market Share", f"{latest_share:.1f}%", "+3.2pp")
else:
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
    if not tiktok_mode:
        st.caption("Animated area chart showing quarterly revenue evolution across business units. Press play to watch growth over time.")

    _colors = TIKTOK_COLORS if tiktok_mode else CORPORATE_COLORS
    fig_rev = px.area(
        rev_df,
        x="Business Unit",
        y="Revenue ($M)",
        color="Business Unit",
        animation_frame="Period",
        range_y=[0, rev_df["Revenue ($M)"].max() * 1.15],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=_colors,
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
    apply_corporate_style(fig_rev, tiktok=tiktok_mode)
    st.plotly_chart(fig_rev, use_container_width=True)
    _download_section("revenue", "revenue_growth.mp4",
                      partial(revenue_growth_to_mp4, rev_df, animation_speed, tiktok_mode),
                      tiktok_mode)

    if not tiktok_mode:
        with st.expander("View revenue data"):
            st.dataframe(rev_df, use_container_width=True, hide_index=True)

    st.markdown("---")

# ===================================================================
# 2. ANIMATED LINE CHART - Market Share Race
# ===================================================================
if "Market Share Race" in sections:
    st.header("2 - Market Share Race")
    if not tiktok_mode:
        st.caption("Animated line chart showing how market share shifts month-over-month across competitors.")

    _colors = TIKTOK_COLORS if tiktok_mode else CORPORATE_COLORS
    _line_w = 5 if tiktok_mode else 3
    _marker_s = 7 if tiktok_mode else 4

    # Build frames manually for a cumulative line animation
    months = ms_df["Month"].unique()
    companies = ms_df["Company"].unique()
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
                    line=dict(width=_line_w, color=_colors[j % len(_colors)]),
                    marker=dict(size=_marker_s),
                )
                for j, c in enumerate(companies)
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
                line=dict(width=_line_w, color=_colors[j % len(_colors)]),
                marker=dict(size=_marker_s),
            )
            for j, c in enumerate(companies)
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
                currentvalue=dict(prefix="Month: ", font_size=14 if tiktok_mode else 12),
            )],
        ),
    )
    apply_corporate_style(fig_ms, tiktok=tiktok_mode)
    fig_ms.update_layout(colorway=_colors)
    st.plotly_chart(fig_ms, use_container_width=True)
    _download_section("market_share", "market_share_race.mp4",
                      partial(market_share_to_mp4, ms_df, animation_speed, tiktok_mode),
                      tiktok_mode)
    st.markdown("---")

# ===================================================================
# 3. ANIMATED BUBBLE CHART - Employee Metrics
# ===================================================================
if "Employee Bubble Chart" in sections:
    st.header("3 - Employee Metrics Bubble Chart")
    if not tiktok_mode:
        st.caption("Animated scatter showing headcount vs satisfaction per department. Bubble size = attrition rate.")

    _colors = TIKTOK_COLORS if tiktok_mode else CORPORATE_COLORS
    fig_emp = px.scatter(
        emp_df,
        x="Headcount",
        y="Satisfaction (1-5)",
        size="Attrition Rate (%)",
        color="Department",
        animation_frame="Quarter Label",
        hover_name="Department",
        size_max=55 if tiktok_mode else 45,
        range_x=[30, emp_df["Headcount"].max() * 1.15],
        range_y=[2.3, 5.2],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=_colors,
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
    apply_corporate_style(fig_emp, tiktok=tiktok_mode)
    st.plotly_chart(fig_emp, use_container_width=True)
    _download_section("employee", "employee_bubble.mp4",
                      partial(employee_bubble_to_mp4, emp_df, animation_speed, tiktok_mode),
                      tiktok_mode)
    st.markdown("---")

# ===================================================================
# 4. ANIMATED SCATTER - Product KPIs
# ===================================================================
if "Product KPI Scatter" in sections:
    st.header("4 - Product KPI Exploration")
    if not tiktok_mode:
        st.caption("Weekly animated scatter: DAU vs Conversion Rate. Bubble size = team size, color = product.")

    _colors = TIKTOK_COLORS if tiktok_mode else CORPORATE_COLORS
    kpi_df = generate_product_kpis()
    fig_kpi = px.scatter(
        kpi_df,
        x="DAU",
        y="Conversion Rate (%)",
        size="Team Size",
        color="Product",
        animation_frame="Week Label",
        hover_data=["Avg Latency (ms)"],
        size_max=50 if tiktok_mode else 40,
        range_x=[0, kpi_df["DAU"].max() * 1.15],
        range_y=[0, kpi_df["Conversion Rate (%)"].max() * 1.25],
        template=CORPORATE_TEMPLATE,
        color_discrete_sequence=_colors,
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
    apply_corporate_style(fig_kpi, tiktok=tiktok_mode)
    st.plotly_chart(fig_kpi, use_container_width=True)
    _download_section("product_kpi", "product_kpi.mp4",
                      partial(product_kpi_to_mp4, kpi_df, animation_speed, tiktok_mode),
                      tiktok_mode)
    st.markdown("---")

# ===================================================================
# 5. ANIMATED BAR RACE - Regional Sales
# ===================================================================
if "Regional Sales Bar Race" in sections:
    st.header("5 - Regional Sales Bar Race")
    if not tiktok_mode:
        st.caption("Animated horizontal bar chart racing through yearly regional sales.")

    _colors = TIKTOK_COLORS if tiktok_mode else CORPORATE_COLORS
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
        color_discrete_sequence=_colors,
        title="Regional Sales Race ($M)",
        text="Sales ($M)",
    )
    _text_size = 18 if tiktok_mode else None
    fig_bar.update_traces(
        texttemplate="%{text:.0f}", textposition="outside",
        textfont=dict(size=_text_size) if tiktok_mode else {},
    )
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
    apply_corporate_style(fig_bar, tiktok=tiktok_mode)
    st.plotly_chart(fig_bar, use_container_width=True)
    _download_section("bar_race", "regional_bar_race.mp4",
                      partial(bar_race_to_mp4, reg_df, animation_speed * 3, tiktok_mode),
                      tiktok_mode)
    st.markdown("---")

# ===================================================================
# 6. ANIMATED FUNNEL - Sales Pipeline
# ===================================================================
if "Sales Funnel Animation" in sections:
    st.header("6 - Sales Funnel Animation")
    if not tiktok_mode:
        st.caption("Animated bar chart showing the sales funnel stages evolving month-over-month.")

    _colors = TIKTOK_COLORS if tiktok_mode else CORPORATE_COLORS
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
        color_discrete_sequence=_colors,
        title="Sales Funnel Progression",
        text="Count",
    )
    _text_size = 18 if tiktok_mode else None
    fig_funnel.update_traces(
        texttemplate="%{text:,.0f}", textposition="outside",
        textfont=dict(size=_text_size) if tiktok_mode else {},
    )
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
    apply_corporate_style(fig_funnel, tiktok=tiktok_mode)
    st.plotly_chart(fig_funnel, use_container_width=True)
    _download_section("funnel", "sales_funnel.mp4",
                      partial(funnel_to_mp4, funnel_df, animation_speed * 2, tiktok_mode),
                      tiktok_mode)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
_footer_color = "#555" if tiktok_mode else "#6C757D"
st.markdown(
    f"<div style='text-align:center; color:{_footer_color}; font-size:0.85rem;'>"
    "Built with Streamlit + Plotly | Dummy data for demonstration purposes"
    "</div>",
    unsafe_allow_html=True,
)
