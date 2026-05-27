import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# -- Page config ---------------------------------------------------------------
st.set_page_config(
    page_title="AirQuality IQ – Beijing",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "AirQuality IQ Dashboard v2.0"},
)

# -- Constants -----------------------------------------------------------------
DATA_PATH  = "dashboard/air_quality_cleaned.csv"
POLLUTANTS = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]
METEO_COLS = ["TEMP", "PRES", "DEWP", "RAIN", "WSPM"]

POLLUTANT_COLORS = {
    "PM2.5": "#E53935",
    "PM10":  "#FB8C00",
    "SO2":   "#F9A825",
    "NO2":   "#43A047",
    "CO":    "#1E88E5",
    "O3":    "#8E24AA",
}

WHO_GUIDELINES = {
    "PM2.5": 5,
    "PM10":  15,
    "SO2":   40,
    "NO2":   10,
    "CO":    4000,
    "O3":    60,
}

CHART_TEMPLATE = "plotly_white"

# -- CSS -----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.stApp { background: #F5F7FA; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1B2A 0%, #1B2A3B 100%) !important;
}
/* Sidebar: light text for regular elements */
[data-testid="stSidebar"] * { color: #E8EDF2 !important; }
[data-testid="stSidebar"] .stRadio label { color: #CBD5E0 !important; }
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label { color: #A0AEC0 !important; font-size: 0.82rem !important; }
[data-testid="stSidebar"] hr { border-color: #2D3F52 !important; }

/* Sidebar: multiselect selected tags — dark bg so white text stays readable */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}
/* Sidebar: input boxes — keep a visible dark background */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] [data-baseweb="input"] {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.15) !important;
}
/* Sidebar: multiselect/date input containers */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stDateInput"] > div > div {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.15) !important;
}

.sidebar-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 0.25rem 0 1.25rem;
    border-bottom: 1px solid #2D3F52;
    margin-bottom: 1.25rem;
}
.sidebar-brand-icon { font-size: 2rem; line-height: 1; }
.sidebar-brand-name { font-size: 1rem; font-weight: 700; color: #E8EDF2; line-height: 1.2; }
.sidebar-brand-sub  { font-size: 0.7rem; color: #A0AEC0; }
.nav-section {
    font-size: 0.68rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px;
    color: #4A6785 !important; margin: 0.9rem 0 0.4rem;
}

.hero-banner {
    background: linear-gradient(135deg, #0D1B2A 0%, #1B3A5C 55%, #1565C0 100%);
    border-radius: 16px;
    padding: 2.2rem 2.5rem 1.8rem;
    margin-bottom: 1.5rem;
    position: relative; overflow: hidden;
}
.hero-banner::after {
    content: "";
    position: absolute; top: -70px; right: -70px;
    width: 220px; height: 220px;
    background: rgba(255,255,255,0.04); border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.14); color: #E8F0FE;
    font-size: 0.7rem; font-weight: 700;
    padding: 3px 11px; border-radius: 20px;
    margin-bottom: 0.65rem; letter-spacing: 0.8px;
    text-transform: uppercase;
}
.hero-title    { font-size: 2.1rem; font-weight: 700; color: #fff; margin: 0 0 0.35rem; line-height: 1.2; }
.hero-subtitle { font-size: 0.95rem; color: #A8C0D6; margin: 0; }

.kpi-card {
    background: #FFFFFF; border-radius: 12px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
    border-left: 4px solid var(--accent);
}
.kpi-label {
    font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.7px;
    color: #718096; margin-bottom: 0.3rem;
}
.kpi-value { font-size: 1.85rem; font-weight: 700; color: #1A202C; line-height: 1; margin-bottom: 0.2rem; }
.kpi-unit  { font-size: 0.75rem; color: #A0AEC0; }
.kpi-delta       { font-size: 0.78rem; margin-top: 0.3rem; }
.kpi-delta.over  { color: #E53E3E; }
.kpi-delta.ok    { color: #38A169; }

.section-title    { font-size: 1.4rem; font-weight: 700; color: #1A202C; margin: 0.3rem 0 0.15rem; }
.section-subtitle { font-size: 0.88rem; color: #718096; margin-bottom: 1rem; }
.divider {
    height: 3px;
    background: linear-gradient(90deg, #1565C0 0%, transparent 100%);
    border: none; margin: 0.3rem 0 1.2rem; border-radius: 2px;
}

.insight-card {
    background: #EBF4FF; border: 1px solid #BEE3F8;
    border-radius: 10px; padding: 0.9rem 1.15rem; margin-top: 0.6rem;
}
.insight-card h4 { color: #2B6CB0; font-size: 0.87rem; font-weight: 700; margin: 0 0 0.45rem; }
.insight-card ul  { margin: 0; padding-left: 1.2rem; }
.insight-card li  { color: #2C5282; font-size: 0.85rem; margin-bottom: 0.2rem; }

.stTabs [data-baseweb="tab-list"] {
    gap: 3px; background: #EDF2F7; border-radius: 10px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px; padding: 7px 18px;
    font-weight: 600; font-size: 0.86rem;
    color: #4A5568; background: transparent; border: none;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF; color: #1565C0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }

[data-testid="metric-container"] {
    background: #FFFFFF; border-radius: 10px;
    padding: 0.9rem 1.1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07);
}
</style>
""", unsafe_allow_html=True)


# -- Helpers -------------------------------------------------------------------
def avail(df, cols):
    return [c for c in cols if c in df.columns]


def pcols(pollutants):
    return [POLLUTANT_COLORS.get(p, "#1E88E5") for p in pollutants]


def style_fig(fig, height=460):
    fig.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        height=height,
        font=dict(family="Inter, sans-serif", size=12, color="#2D3748"),
        title_font=dict(size=14, color="#1A202C", family="Inter, sans-serif"),
        legend=dict(
            bgcolor="#FFFFFF", bordercolor="#CBD5E0", borderwidth=1,
            font=dict(color="#2D3748"),
        ),
        margin=dict(l=10, r=10, t=46, b=10),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="#E2E8F0", zeroline=False,
        linecolor="#CBD5E0", linewidth=1, showline=True,
        tickfont=dict(color="#2D3748"), title_font=dict(color="#2D3748"),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#E2E8F0", zeroline=False,
        linecolor="#CBD5E0", linewidth=1, showline=True,
        tickfont=dict(color="#2D3748"), title_font=dict(color="#2D3748"),
    )
    return fig


def insight(bullets):
    items = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(
        f'<div class="insight-card"><h4>💡 Key Insights</h4><ul>{items}</ul></div>',
        unsafe_allow_html=True,
    )


def hero(title, subtitle):
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-badge">Air Quality Intelligence</div>
        <div class="hero-title">{title}</div>
        <p class="hero-subtitle">{subtitle}</p>
    </div>""", unsafe_allow_html=True)


def section(title, subtitle=""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)


# -- Data ----------------------------------------------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_PATH, index_col="datetime", parse_dates=True)
        return df
    except FileNotFoundError:
        st.error(f"Data file not found at **{DATA_PATH}**.")
        return None


# -- Sidebar -------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <span class="sidebar-brand-icon">🌬️</span>
            <div>
                <div class="sidebar-brand-name">AirQuality IQ</div>
                <div class="sidebar-brand-sub">Beijing · 2013 – 2017</div>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)
        page = st.radio(
            "",
            ["📊  Overview",
             "📈  Temporal Trends",
             "🔗  Pollutant Relationships",
             "🗺️  Station Comparison",
             "ℹ️  About"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown('<div class="nav-section">Dataset</div>', unsafe_allow_html=True)
        st.caption("12 monitoring stations\nMarch 2013 – February 2017\n6 pollutants · 5 met. factors")

    return page.split("  ", 1)[-1]


# -- KPI row -------------------------------------------------------------------
def render_kpi_row(df):
    ap = avail(df, POLLUTANTS)
    if not ap:
        return
    cols = st.columns(len(ap))
    for col, p in zip(cols, ap):
        avg   = df[p].mean()
        who   = WHO_GUIDELINES.get(p)
        ratio = avg / who if who else None
        if ratio and ratio > 1:
            dcls, dtxt = "over", f"↑ {ratio:.1f}× WHO guideline"
        else:
            dcls, dtxt = "ok", "✓ Within WHO guideline"
        accent = POLLUTANT_COLORS.get(p, "#1E88E5")
        col.markdown(f"""
        <div class="kpi-card" style="--accent:{accent}">
            <div class="kpi-label">{p}</div>
            <div class="kpi-value">{avg:.1f}</div>
            <div class="kpi-unit">μg/m³ — avg all stations</div>
            <div class="kpi-delta {dcls}">{dtxt}</div>
        </div>""", unsafe_allow_html=True)


# -- Overview ------------------------------------------------------------------
def render_overview(df):
    hero(
        "Air Quality Overview",
        "High-level summary of pollutant concentrations across all 12 Beijing stations (2013–2017).",
    )

    section("Pollutant Averages vs. WHO Guidelines",
            "Dataset-wide mean concentrations compared to WHO annual mean guidelines.")
    render_kpi_row(df)
    st.markdown("<br>", unsafe_allow_html=True)

    ap = avail(df, POLLUTANTS)
    c1, c2 = st.columns(2)

    with c1:
        section("Monthly Trends", "All pollutants — monthly mean")
        monthly = df[ap].resample("ME").mean().reset_index()
        monthly_m = monthly.melt(id_vars="datetime", value_vars=ap,
                                  var_name="Pollutant", value_name="Concentration")
        fig = px.line(monthly_m, x="datetime", y="Concentration", color="Pollutant",
                      color_discrete_map={p: POLLUTANT_COLORS.get(p, "#1E88E5") for p in ap})
        style_fig(fig, 350)
        fig.update_layout(xaxis_title="", yaxis_title="μg/m³",
                          legend_title="Pollutant", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Seasonal Heatmap", "Average concentration — month × pollutant")
        tmp = df[ap].copy()
        tmp["Month"] = tmp.index.month
        pivot = tmp.groupby("Month")[ap].mean()
        pivot.index = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        fig2 = px.imshow(pivot.T, color_continuous_scale="YlOrRd",
                         text_auto=".0f", aspect="auto")
        style_fig(fig2, 350)
        fig2.update_layout(xaxis_title="Month", yaxis_title="",
                           coloraxis_colorbar_title="μg/m³")
        st.plotly_chart(fig2, use_container_width=True)

    if "station" in df.columns:
        section("Station Rankings", "Average PM2.5 by monitoring station (all years)")
        p = "PM2.5" if "PM2.5" in df.columns else ap[0]
        sta = df.groupby("station")[p].mean().sort_values()
        fig3 = go.Figure(go.Bar(
            x=sta.values, y=sta.index, orientation="h",
            marker=dict(color=sta.values, colorscale="RdYlGn_r",
                        showscale=True, colorbar=dict(title="μg/m³")),
            text=[f"{v:.1f}" for v in sta.values], textposition="outside",
        ))
        style_fig(fig3, 380)
        fig3.update_layout(xaxis_title=f"{p} (μg/m³)", yaxis_title="", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)


# -- Temporal Trends -----------------------------------------------------------
def render_temporal_trends(df):
    hero(
        "Temporal Trends",
        "Explore how pollutant concentrations evolve over time at daily, monthly, seasonal, and hourly scales.",
    )

    ap = avail(df, POLLUTANTS)

    with st.sidebar:
        st.markdown('<div class="nav-section">Filters</div>', unsafe_allow_html=True)
        selected = st.multiselect("Pollutants", ap, default=ap[:3])
        min_d, max_d = df.index.min().date(), df.index.max().date()
        date_range = st.date_input("Date range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d)

    if not selected:
        st.warning("Select at least one pollutant in the sidebar.")
        return

    start, end = (date_range if isinstance(date_range, tuple) and len(date_range) == 2
                  else (date_range, date_range))
    fdf = df.loc[(df.index.date >= start) & (df.index.date <= end)]

    stat_cols = st.columns(len(selected))
    for col, p in zip(stat_cols, selected):
        col.metric(p, f"{fdf[p].mean():.1f} μg/m³",
                   delta=f"max {fdf[p].max():.0f} μg/m³", delta_color="off")
    st.markdown("<br>", unsafe_allow_html=True)

    tabs = st.tabs(["📅 Daily", "📆 Monthly", "🌡️ Seasonal", "⌚ Diurnal"])

    with tabs[0]:
        daily = fdf[selected].resample("D").mean().reset_index()
        cmap = {p: POLLUTANT_COLORS.get(p, "#1E88E5") for p in selected}
        daily_m = daily.melt(id_vars="datetime", value_vars=selected,
                              var_name="Pollutant", value_name="Concentration")
        fig = px.line(daily_m, x="datetime", y="Concentration", color="Pollutant",
                      color_discrete_map=cmap)
        style_fig(fig)
        fig.update_layout(xaxis_title="Date", yaxis_title="μg/m³",
                          legend_title="Pollutant", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        insight([
            "Short-term spikes indicate specific pollution events or adverse weather.",
            "Traffic-related pollutants (NO₂, CO) show weekday–weekend differences.",
            "Use the date-range filter in the sidebar to zoom into a specific period.",
        ])

    with tabs[1]:
        monthly = fdf[selected].resample("ME").mean().reset_index()
        monthly_m = monthly.melt(id_vars="datetime", value_vars=selected,
                                  var_name="Pollutant", value_name="Concentration")
        fig = px.line(monthly_m, x="datetime", y="Concentration", color="Pollutant",
                      markers=True,
                      color_discrete_map={p: POLLUTANT_COLORS.get(p, "#1E88E5") for p in selected})
        style_fig(fig)
        fig.update_layout(xaxis_title="Month", yaxis_title="μg/m³",
                          legend_title="Pollutant", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        insight([
            "Monthly averages smooth daily noise and reveal seasonal cycles.",
            "Annual patterns repeat consistently across the 4-year dataset.",
        ])

    with tabs[2]:
        tmp = fdf.copy()
        tmp["month"] = tmp.index.month
        seas = tmp.groupby("month")[selected].mean()
        seas.index = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        seas.index.name = "Month"
        seas_reset = seas.reset_index()
        seas_m = seas_reset.melt(id_vars="Month", value_vars=selected,
                                  var_name="Pollutant", value_name="Concentration")
        fig = px.bar(seas_m, x="Month", y="Concentration", color="Pollutant",
                     barmode="group",
                     color_discrete_map={p: POLLUTANT_COLORS.get(p, "#1E88E5") for p in selected})
        style_fig(fig)
        fig.update_layout(xaxis_title="Month", yaxis_title="μg/m³",
                          legend_title="Pollutant", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        insight([
            "PM2.5 and PM10 peak in winter — heating emissions and thermal inversions.",
            "O₃ peaks in summer due to photochemical reactions with sunlight.",
            "SO₂ spikes correlate with coal-burning heating seasons.",
        ])

    with tabs[3]:
        tmp2 = fdf.copy()
        tmp2["hour"] = tmp2.index.hour
        diurnal = tmp2.groupby("hour")[selected].mean().reset_index()
        diurnal_m = diurnal.melt(id_vars="hour", value_vars=selected,
                                  var_name="Pollutant", value_name="Concentration")
        fig = px.line(diurnal_m, x="hour", y="Concentration", color="Pollutant",
                      markers=True,
                      color_discrete_map={p: POLLUTANT_COLORS.get(p, "#1E88E5") for p in selected})
        style_fig(fig)
        fig.update_layout(
            xaxis_title="Hour of Day", yaxis_title="μg/m³",
            legend_title="Pollutant", hovermode="x unified",
            xaxis=dict(tickmode="linear", tick0=0, dtick=3),
        )
        st.plotly_chart(fig, use_container_width=True)
        insight([
            "Morning (07–09h) and evening (18–20h) rush hours drive NO₂ and CO peaks.",
            "O₃ peaks in the early afternoon when solar radiation is at its highest.",
            "PM concentrations build overnight due to reduced atmospheric mixing.",
        ])


# -- Pollutant Relationships ---------------------------------------------------
def render_pollutant_relationships(df):
    hero(
        "Pollutant Relationships",
        "Examine correlations between pollutants and explore the influence of meteorological factors.",
    )

    ap = avail(df, POLLUTANTS)
    am = avail(df, METEO_COLS)

    tabs = st.tabs(["🗂️ Correlation Matrix", "⚡ Scatter Explorer", "🌤️ Meteorological Factors"])

    with tabs[0]:
        with st.sidebar:
            st.markdown('<div class="nav-section">Correlation Options</div>', unsafe_allow_html=True)
            corr_vars = st.multiselect("Variables", ap + am, default=ap)
        if len(corr_vars) < 2:
            st.warning("Select at least two variables.")
        else:
            corr_mat = df[corr_vars].corr()
            fig = px.imshow(corr_mat, text_auto=".2f",
                            color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            style_fig(fig, 560)
            fig.update_layout(coloraxis_colorbar_title="Pearson r")
            st.plotly_chart(fig, use_container_width=True)
            insight([
                "PM2.5 ↔ PM10: strong positive correlation (shared emission sources).",
                "O₃ ↔ NO₂: negative correlation (photochemical titration).",
                "Temperature often negatively correlates with PM due to improved atmospheric mixing.",
            ])

    with tabs[1]:
        c1, c2, c3 = st.columns([1, 1, 1])
        x_var = c1.selectbox("X axis", ap, index=min(1, len(ap) - 1))
        y_var = c2.selectbox("Y axis", ap, index=0)
        n_pts = c3.slider("Sample size", 500, min(15000, len(df)), min(5000, len(df)), 500)
        color_by = st.selectbox("Color by (optional)", ["None"] + ap + am, index=0)

        if x_var == y_var:
            st.warning("Choose different variables for X and Y axes.")
        else:
            sdf = df.dropna(subset=[x_var, y_var]).sample(n=n_pts, random_state=42)
            color_col = None if color_by == "None" else color_by
            fig = px.scatter(
                sdf, x=x_var, y=y_var,
                color=color_col, opacity=0.55,
                color_continuous_scale="Viridis" if color_col else None,
            )
            style_fig(fig, 500)
            fig.update_layout(
                xaxis_title=f"{x_var} (μg/m³)",
                yaxis_title=f"{y_var} (μg/m³)",
                hovermode="closest",
            )
            st.plotly_chart(fig, use_container_width=True)

            corr = df[[x_var, y_var]].corr().iloc[0, 1]
            strength  = "Strong" if abs(corr) > 0.7 else ("Moderate" if abs(corr) > 0.3 else "Weak")
            direction = "positive" if corr > 0 else "negative"
            m1, m2, m3 = st.columns(3)
            m1.metric("Pearson r", f"{corr:.3f}")
            m2.metric("R²", f"{corr**2:.3f}")
            m3.metric("Relationship", f"{strength} {direction}")

    with tabs[2]:
        if not am:
            st.info("No meteorological data found in the dataset.")
        else:
            c1, c2, c3 = st.columns([1, 1, 1])
            meteo_var = c1.selectbox("Meteorological factor", am)
            poll_var  = c2.selectbox("Pollutant", ap)
            n_pts2    = c3.slider("Sample size", 500, min(15000, len(df)),
                                  min(5000, len(df)), 500, key="meteo_n")

            sdf2 = df.dropna(subset=[meteo_var, poll_var]).sample(n=n_pts2, random_state=42)
            fig  = px.scatter(sdf2, x=meteo_var, y=poll_var,
                              color=poll_var, opacity=0.5,
                              color_continuous_scale="RdYlGn_r")
            style_fig(fig, 500)
            x_lbl = {"TEMP": "Temperature (°C)", "PRES": "Pressure (hPa)",
                     "WSPM": "Wind Speed (m/s)", "DEWP": "Dew Point (°C)",
                     "RAIN": "Rainfall (mm)"}.get(meteo_var, meteo_var)
            fig.update_layout(xaxis_title=x_lbl,
                              yaxis_title=f"{poll_var} (μg/m³)")
            st.plotly_chart(fig, use_container_width=True)

            corr2 = df[[meteo_var, poll_var]].corr().iloc[0, 1]
            m1, m2 = st.columns(2)
            m1.metric("Pearson r", f"{corr2:.3f}")
            m2.metric("R²", f"{corr2**2:.3f}")
            insight([
                "Higher wind speed (WSPM) generally disperses pollutants — expect negative r.",
                "Lower temperature (TEMP) can trap pollutants via thermal inversions.",
                "Dew point (DEWP) correlates with humidity — affects secondary particle formation.",
            ])


# -- Station Comparison --------------------------------------------------------
def render_station_comparison(df):
    if "station" not in df.columns:
        st.info("Station information not available in the dataset.")
        return

    hero(
        "Station Comparison",
        "Compare air quality profiles across all 12 monitoring stations in Beijing.",
    )

    ap       = avail(df, POLLUTANTS)
    stations = sorted(df["station"].unique())

    with st.sidebar:
        st.markdown('<div class="nav-section">Filters</div>', unsafe_allow_html=True)
        sel_poll = st.selectbox("Pollutant", ap)
        sel_sta  = st.multiselect("Stations (trend & radar)", stations, default=stations[:4])

    section("Station Rankings", f"Average {sel_poll} — sorted highest to lowest")
    sta_avg = df.groupby("station")[sel_poll].mean().sort_values(ascending=False)
    accent  = POLLUTANT_COLORS.get(sel_poll, "#1E88E5")

    fig = go.Figure(go.Bar(
        x=sta_avg.index, y=sta_avg.values,
        marker_color=accent,
        text=[f"{v:.1f}" for v in sta_avg.values], textposition="outside",
    ))
    style_fig(fig, 400)
    fig.update_layout(xaxis_title="Station", yaxis_title=f"{sel_poll} (μg/m³)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Highest station", sta_avg.index[0],  f"{sta_avg.values[0]:.1f} μg/m³")
    m2.metric("Lowest station",  sta_avg.index[-1], f"{sta_avg.values[-1]:.1f} μg/m³")
    m3.metric("Range",           f"{sta_avg.values[0] - sta_avg.values[-1]:.1f} μg/m³")

    if sel_sta:
        st.markdown("<br>", unsafe_allow_html=True)
        section("Station Trends", f"Daily average {sel_poll} — selected stations")
        sta_data  = df[df["station"].isin(sel_sta)]
        daily_sta = (sta_data
                     .groupby(["station", pd.Grouper(freq="D")])[sel_poll]
                     .mean().reset_index())
        fig2 = px.line(daily_sta, x="datetime", y=sel_poll, color="station")
        style_fig(fig2, 440)
        fig2.update_layout(xaxis_title="Date",
                           yaxis_title=f"{sel_poll} (μg/m³)",
                           legend_title="Station", hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section("Pollutant Profiles", "Annual mean per station — radar chart")
        profile = df[df["station"].isin(sel_sta)].groupby("station")[ap].mean()
        fig3 = go.Figure()
        for sta in profile.index:
            vals = profile.loc[sta].tolist()
            fig3.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=ap + [ap[0]],
                fill="toself", name=sta, opacity=0.6,
            ))
        style_fig(fig3, 460)
        fig3.update_layout(polar=dict(radialaxis=dict(visible=True)),
                           legend_title="Station")
        st.plotly_chart(fig3, use_container_width=True)


# -- About ---------------------------------------------------------------------
def render_about(df=None):
    hero("About This Dashboard", "Data sources, methodology, and technology stack.")

    c1, c2 = st.columns(2)

    with c1:
        section("Data Source")
        st.markdown("""
| Attribute  | Detail |
|------------|--------|
| Stations   | 12 locations in Beijing |
| Period     | March 2013 – February 2017 |
| Frequency  | Hourly measurements |
| Source     | [HTI GitHub Repository](https://github.com/marceloreis/HTI.git) |

**Pollutants measured**
- **PM2.5** — Fine particles < 2.5 μm
- **PM10** — Coarse particles < 10 μm
- **SO₂** — Sulfur dioxide
- **NO₂** — Nitrogen dioxide
- **CO** — Carbon monoxide
- **O₃** — Ozone
""")

    with c2:
        section("Methodology")
        st.markdown("""
**Pipeline**
1. Raw CSVs cleaned — missing values forward-filled
2. Datetime index built from year/month/day/hour columns
3. Station labels merged into a single combined CSV
4. Outliers flagged using the IQR method

**WHO Annual Mean Guidelines**

| Pollutant | Guideline |
|-----------|-----------|
| PM2.5 | 5 μg/m³ |
| PM10  | 15 μg/m³ |
| NO₂   | 10 μg/m³ |
| O₃    | 60 μg/m³ |
""")

    section("Technology Stack")
    cols = st.columns(4)
    tools = [
        ("🐍 Python 3.11",    "Core language"),
        ("🐼 Pandas 2.2",     "Data wrangling"),
        ("📊 Plotly 6",       "Interactive charts"),
        ("🎈 Streamlit 1.45", "Dashboard framework"),
    ]
    for col, (name, desc) in zip(cols, tools):
        col.markdown(f"**{name}**  \n{desc}")


# -- Main ----------------------------------------------------------------------
def main():
    df = load_data()
    if df is None:
        return

    page = render_sidebar()

    dispatch = {
        "Overview":                render_overview,
        "Temporal Trends":         render_temporal_trends,
        "Pollutant Relationships":  render_pollutant_relationships,
        "Station Comparison":      render_station_comparison,
        "About":                   render_about,
    }
    dispatch.get(page, render_overview)(df)

    st.markdown("""
    <div style="text-align:center;padding:2.5rem 0 0.75rem;color:#A0AEC0;font-size:0.76rem;">
        AirQuality IQ &nbsp;&middot;&nbsp; Beijing 2013–2017 &nbsp;&middot;&nbsp; Built with Streamlit &amp; Plotly
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
