"""Recreate animated charts with matplotlib and export as MP4.

Each chart is rebuilt from the source DataFrame using matplotlib, rendered
frame-by-frame to PNG, and stitched into an H.264 MP4 via imageio-ffmpeg.
"""

from __future__ import annotations

import io
import os
import tempfile

import imageio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

CORPORATE_COLORS = [
    "#1B2A4A", "#2E86AB", "#A23B72", "#F18F01",
    "#3C8D2F", "#6C757D", "#C73E1D", "#5C4D7D",
]
TIKTOK_COLORS = [
    "#FF3366", "#00D4FF", "#FFD700", "#00FF88",
    "#FF6B35", "#B44DFF", "#FF4757", "#18DCFF",
]

# ── shared helpers ──────────────────────────────────────────────────

def _theme(tiktok: bool):
    """Return (colors, bg, text_color, grid_color) for the active mode."""
    if tiktok:
        return TIKTOK_COLORS, "#0D0D0D", "#FFFFFF", "#333333"
    return CORPORATE_COLORS, "#FFFFFF", "#1B2A4A", "#e0e0e0"


def _new_fig(tiktok: bool):
    """Create a figure + axes pair with correct size and background."""
    colors, bg, text_c, grid_c = _theme(tiktok)
    dpi = 100
    w, h = (10.8, 19.2) if tiktok else (12.8, 7.2)
    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi)
    fig.set_facecolor(bg)
    fig.subplots_adjust(left=0.14, right=0.92, top=0.90, bottom=0.13)
    return fig, ax


def _style_ax(ax, tiktok: bool, title: str = ""):
    """Apply consistent axis styling."""
    _, bg, text_c, grid_c = _theme(tiktok)
    ax.set_facecolor(bg)
    if title:
        ax.set_title(title, color=text_c, fontsize=20 if tiktok else 15,
                     fontweight="bold", pad=12)
    ax.tick_params(colors=text_c, labelsize=13 if tiktok else 10)
    ax.yaxis.grid(True, color=grid_c, linewidth=0.5, alpha=0.7)
    ax.xaxis.grid(True, color=grid_c, linewidth=0.5, alpha=0.3)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _render_to_mp4(fig, update_fn, num_frames, fps, progress_cb=None):
    """Render *num_frames* by calling *update_fn(i)* and stitch into MP4."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        writer = imageio.get_writer(
            tmp_path, fps=fps, codec="libx264",
            output_params=["-pix_fmt", "yuv420p"],
        )
        for i in range(num_frames):
            update_fn(i)
            buf = io.BytesIO()
            fig.savefig(buf, format="png",
                        facecolor=fig.get_facecolor(), edgecolor="none")
            buf.seek(0)
            img = imageio.imread(buf)
            if img.ndim == 3 and img.shape[2] == 4:
                img = img[:, :, :3]
            writer.append_data(img)
            if progress_cb is not None:
                progress_cb((i + 1) / num_frames)
        writer.close()
        with open(tmp_path, "rb") as fh:
            return fh.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── 1. Revenue Growth (bar chart) ──────────────────────────────────

def revenue_growth_to_mp4(df, frame_duration_ms, tiktok, progress_cb=None):
    colors, bg, text_c, grid_c = _theme(tiktok)
    periods = df["Period"].unique()
    units = df["Business Unit"].unique()
    max_y = df["Revenue ($M)"].max() * 1.15
    fps = max(1, round(1000 / frame_duration_ms))

    fig, ax = _new_fig(tiktok)

    def update(i):
        ax.clear()
        _style_ax(ax, tiktok, f"Quarterly Revenue by Business Unit\n{periods[i]}")
        frame = df[df["Period"] == periods[i]]
        for j, unit in enumerate(units):
            vals = frame[frame["Business Unit"] == unit]["Revenue ($M)"].values
            val = vals[0] if len(vals) else 0
            ax.bar(j, val, color=colors[j % len(colors)], width=0.55)
        ax.set_xticks(range(len(units)))
        ax.set_xticklabels(units, rotation=25, ha="right", color=text_c)
        ax.set_ylim(0, max_y)
        ax.set_ylabel("Revenue ($M)", color=text_c, fontsize=12)

    result = _render_to_mp4(fig, update, len(periods), fps, progress_cb)
    plt.close(fig)
    return result

# ── 2. Market Share Race (cumulative lines) ────────────────────────

def market_share_to_mp4(df, frame_duration_ms, tiktok, progress_cb=None):
    colors, bg, text_c, grid_c = _theme(tiktok)
    months = df["Month"].unique()
    companies = df["Company"].unique()
    fps = max(1, round(1000 / frame_duration_ms))
    lw = 3.5 if tiktok else 2.5

    fig, ax = _new_fig(tiktok)

    def update(i):
        ax.clear()
        _style_ax(ax, tiktok, f"Monthly Market Share Evolution\n{months[i]}")
        visible = months[: i + 1]
        for j, company in enumerate(companies):
            c = df[(df["Company"] == company) & (df["Month"].isin(visible))]
            ax.plot(c["Month"], c["Market Share (%)"],
                    color=colors[j % len(colors)], linewidth=lw,
                    marker="o", markersize=5 if tiktok else 3, label=company)
        ax.set_xlim(months[0], months[-1])
        ax.set_ylim(0, 50)
        step = max(1, len(months) // 8)
        ax.set_xticks([months[k] for k in range(0, len(months), step)])
        ax.tick_params(axis="x", rotation=45)
        ax.set_ylabel("Market Share (%)", color=text_c, fontsize=12)
        ax.legend(fontsize=11 if tiktok else 9, facecolor=bg,
                  edgecolor=grid_c, labelcolor=text_c, loc="upper left")

    result = _render_to_mp4(fig, update, len(months), fps, progress_cb)
    plt.close(fig)
    return result

# ── 3. Employee Bubble Chart (scatter) ─────────────────────────────

def employee_bubble_to_mp4(df, frame_duration_ms, tiktok, progress_cb=None):
    colors, bg, text_c, grid_c = _theme(tiktok)
    quarters = df["Quarter Label"].unique()
    departments = df["Department"].unique()
    max_hc = df["Headcount"].max() * 1.15
    fps = max(1, round(1000 / frame_duration_ms))

    fig, ax = _new_fig(tiktok)

    def update(i):
        ax.clear()
        _style_ax(ax, tiktok,
                  f"Headcount vs Satisfaction (bubble = attrition)\n{quarters[i]}")
        frame = df[df["Quarter Label"] == quarters[i]]
        for j, dept in enumerate(departments):
            d = frame[frame["Department"] == dept]
            if d.empty:
                continue
            ax.scatter(d["Headcount"], d["Satisfaction (1-5)"],
                       s=d["Attrition Rate (%)"] * (35 if tiktok else 25),
                       color=colors[j % len(colors)], label=dept,
                       alpha=0.85, edgecolors="white", linewidth=0.5)
        ax.set_xlim(30, max_hc)
        ax.set_ylim(2.3, 5.2)
        ax.set_xlabel("Headcount", color=text_c, fontsize=12)
        ax.set_ylabel("Satisfaction (1-5)", color=text_c, fontsize=12)
        ax.legend(fontsize=10 if tiktok else 8, facecolor=bg,
                  edgecolor=grid_c, labelcolor=text_c, loc="upper left")

    result = _render_to_mp4(fig, update, len(quarters), fps, progress_cb)
    plt.close(fig)
    return result

# ── 4. Product KPI Scatter ─────────────────────────────────────────

def product_kpi_to_mp4(df, frame_duration_ms, tiktok, progress_cb=None):
    colors, bg, text_c, grid_c = _theme(tiktok)
    weeks = df["Week Label"].unique()
    products = df["Product"].unique()
    max_dau = df["DAU"].max() * 1.15
    max_conv = df["Conversion Rate (%)"].max() * 1.25
    fps = max(1, round(1000 / frame_duration_ms))

    fig, ax = _new_fig(tiktok)

    def update(i):
        ax.clear()
        _style_ax(ax, tiktok, f"DAU vs Conversion Rate\n{weeks[i]}")
        frame = df[df["Week Label"] == weeks[i]]
        for j, prod in enumerate(products):
            d = frame[frame["Product"] == prod]
            if d.empty:
                continue
            ax.scatter(d["DAU"], d["Conversion Rate (%)"],
                       s=d["Team Size"] * (8 if tiktok else 5),
                       color=colors[j % len(colors)], label=prod,
                       alpha=0.85, edgecolors="white", linewidth=0.5)
        ax.set_xlim(0, max_dau)
        ax.set_ylim(0, max_conv)
        ax.set_xlabel("DAU", color=text_c, fontsize=12)
        ax.set_ylabel("Conversion Rate (%)", color=text_c, fontsize=12)
        ax.legend(fontsize=10 if tiktok else 8, facecolor=bg,
                  edgecolor=grid_c, labelcolor=text_c, loc="upper right")

    result = _render_to_mp4(fig, update, len(weeks), fps, progress_cb)
    plt.close(fig)
    return result

# ── 5. Regional Sales Bar Race ─────────────────────────────────────

def bar_race_to_mp4(df, frame_duration_ms, tiktok, progress_cb=None):
    colors, bg, text_c, grid_c = _theme(tiktok)
    years = sorted(df["Year"].unique())
    regions = df["Region"].unique()
    region_colors = {r: colors[i % len(colors)] for i, r in enumerate(regions)}
    max_x = df["Sales ($M)"].max() * 1.2
    fps = max(1, round(1000 / frame_duration_ms))

    fig, ax = _new_fig(tiktok)
    fig.subplots_adjust(left=0.25, right=0.88)

    def update(i):
        ax.clear()
        _style_ax(ax, tiktok, f"Regional Sales Race ($M)\n{years[i]}")
        frame = df[df["Year"] == years[i]].sort_values("Sales ($M)")
        bars = ax.barh(frame["Region"], frame["Sales ($M)"],
                       color=[region_colors[r] for r in frame["Region"]],
                       height=0.55)
        for bar, val in zip(bars, frame["Sales ($M)"]):
            ax.text(bar.get_width() + max_x * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}", va="center", color=text_c,
                    fontsize=14 if tiktok else 11)
        ax.set_xlim(0, max_x)
        ax.set_xlabel("Sales ($M)", color=text_c, fontsize=12)
        ax.xaxis.grid(True, color=grid_c, linewidth=0.5, alpha=0.5)

    result = _render_to_mp4(fig, update, len(years), fps, progress_cb)
    plt.close(fig)
    return result

# ── 6. Sales Funnel Animation ──────────────────────────────────────

def funnel_to_mp4(df, frame_duration_ms, tiktok, progress_cb=None):
    colors, bg, text_c, grid_c = _theme(tiktok)
    month_labels = df["Month Label"].unique()
    stage_order = ["Closed Won", "Negotiation", "Proposal", "Qualified", "Leads"]
    stage_colors = {s: colors[i % len(colors)] for i, s in enumerate(stage_order)}
    max_x = df["Count"].max() * 1.2
    fps = max(1, round(1000 / frame_duration_ms))

    fig, ax = _new_fig(tiktok)
    fig.subplots_adjust(left=0.22, right=0.88)

    def update(i):
        ax.clear()
        _style_ax(ax, tiktok, f"Sales Funnel Progression\n{month_labels[i]}")
        frame = df[df["Month Label"] == month_labels[i]]
        # Sort by the fixed funnel order
        frame = frame.set_index("Stage").reindex(stage_order).reset_index()
        bars = ax.barh(frame["Stage"], frame["Count"],
                       color=[stage_colors[s] for s in frame["Stage"]],
                       height=0.55)
        for bar, val in zip(bars, frame["Count"]):
            ax.text(bar.get_width() + max_x * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:,.0f}", va="center", color=text_c,
                    fontsize=14 if tiktok else 11)
        ax.set_xlim(0, max_x)
        ax.set_xlabel("Count", color=text_c, fontsize=12)
        ax.xaxis.grid(True, color=grid_c, linewidth=0.5, alpha=0.5)

    result = _render_to_mp4(fig, update, len(month_labels), fps, progress_cb)
    plt.close(fig)
    return result

# ── 7. Generic export for user-uploaded template data ─────────────

def user_chart_to_mp4(df, chart_type, config, frame_duration_ms, tiktok,
                      progress_cb=None):
    """Render an animated chart from user-uploaded template data as MP4.

    *chart_type* is one of ``"bar"``, ``"line"``, ``"area"``, ``"scatter"``.
    *config* is a column-mapping dict produced by ``_config_for_chart_type``.
    """
    colors, bg, text_c, grid_c = _theme(tiktok)
    anim_col = config["animation"]
    frame_vals = list(df[anim_col].unique())
    fps = max(1, round(1000 / frame_duration_ms))

    fig, ax = _new_fig(tiktok)

    # Ensure string columns are truly strings (pandas may parse "NA" as NaN)
    for col in [anim_col, config.get("category"), config.get("color")]:
        if col and col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str)

    if chart_type == "bar":
        cat_col, val_col = config["category"], config["value"]
        categories = df[cat_col].unique()
        cat_colors = {c: colors[i % len(colors)] for i, c in enumerate(categories)}
        max_x = df[val_col].max() * 1.2
        fig.subplots_adjust(left=0.25, right=0.88)

        def update(i):
            ax.clear()
            _style_ax(ax, tiktok, f"{val_col} by {cat_col}\n{frame_vals[i]}")
            frame = df[df[anim_col] == frame_vals[i]].sort_values(val_col)
            bars = ax.barh(frame[cat_col], frame[val_col],
                           color=[cat_colors.get(c, colors[0]) for c in frame[cat_col]],
                           height=0.55)
            for bar, val in zip(bars, frame[val_col]):
                ax.text(bar.get_width() + max_x * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f"{val:,.0f}", va="center", color=text_c,
                        fontsize=14 if tiktok else 11)
            ax.set_xlim(0, max_x)
            ax.set_xlabel(val_col, color=text_c, fontsize=12)
            ax.xaxis.grid(True, color=grid_c, linewidth=0.5, alpha=0.5)

    elif chart_type in ("line", "area"):
        x_col, y_col, color_col = config["x"], config["y"], config["color"]
        groups = df[color_col].unique()
        group_colors = {g: colors[i % len(colors)] for i, g in enumerate(groups)}
        max_y = df[y_col].max() * 1.15
        lw = 3.5 if tiktok else 2.5

        def update(i):
            ax.clear()
            _style_ax(ax, tiktok, f"{y_col} over {x_col}\n{frame_vals[i]}")
            frame = df[df[anim_col] == frame_vals[i]]
            for g in groups:
                gdata = frame[frame[color_col] == g]
                x_pos = list(range(len(gdata)))
                y_vals = gdata[y_col].values
                x_labels = gdata[x_col].values
                if chart_type == "area":
                    ax.fill_between(x_pos, y_vals,
                                    color=group_colors[g], alpha=0.3)
                ax.plot(x_pos, y_vals,
                        color=group_colors[g], linewidth=lw,
                        marker="o", markersize=5 if tiktok else 3, label=g)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(x_labels, rotation=45, ha="right",
                                   color=text_c)
            ax.set_ylim(0, max_y)
            ax.set_ylabel(y_col, color=text_c, fontsize=12)
            ax.legend(fontsize=11 if tiktok else 9, facecolor=bg,
                      edgecolor=grid_c, labelcolor=text_c, loc="upper left")

    else:  # scatter
        x_col, y_col, color_col = config["x"], config["y"], config["color"]
        size_col = config.get("size")
        groups = df[color_col].unique()
        group_colors = {g: colors[i % len(colors)] for i, g in enumerate(groups)}
        max_x = df[x_col].max() * 1.15
        max_y = df[y_col].max() * 1.15

        def update(i):
            ax.clear()
            _style_ax(ax, tiktok, f"{y_col} vs {x_col}\n{frame_vals[i]}")
            frame = df[df[anim_col] == frame_vals[i]]
            for g in groups:
                gdata = frame[frame[color_col] == g]
                if gdata.empty:
                    continue
                s = (gdata[size_col] * (8 if tiktok else 5)
                     if size_col else (100 if tiktok else 60))
                ax.scatter(gdata[x_col], gdata[y_col], s=s,
                           color=group_colors[g], label=g,
                           alpha=0.85, edgecolors="white", linewidth=0.5)
            ax.set_xlim(0, max_x)
            ax.set_ylim(0, max_y)
            ax.set_xlabel(x_col, color=text_c, fontsize=12)
            ax.set_ylabel(y_col, color=text_c, fontsize=12)
            ax.legend(fontsize=10 if tiktok else 8, facecolor=bg,
                      edgecolor=grid_c, labelcolor=text_c, loc="upper right")

    result = _render_to_mp4(fig, update, len(frame_vals), fps, progress_cb)
    plt.close(fig)
    return result
