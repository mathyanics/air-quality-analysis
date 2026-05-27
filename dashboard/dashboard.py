import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings

warnings.filterwarnings("ignore")

# -- Page config ---------------------------------------------------------------
st.set_page_config(
    page_title="Analisis Kualitas Udara Beijing",
    page_icon="🌬️",
    layout="wide",
)

# -- Constants -----------------------------------------------------------------
DATA_PATH   = "dashboard/air_quality_cleaned.csv"
WHO         = {"PM2.5": 5, "PM10": 15}
MONTH_NAMES = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr",  5:"Mei", 6:"Jun",
               7:"Jul", 8:"Agu", 9:"Sep", 10:"Okt", 11:"Nov", 12:"Des"}
MONTH_ORDER = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]

AQ_BINS   = [0, 12.0, 35.4, 55.4, 150.4, 250.4, float("inf")]
AQ_LABELS = ["Baik", "Sedang", "Tidak Sehat (Sensitif)",
             "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
AQ_COLORS = ["#00C853", "#FFD600", "#FF6D00", "#DD2C00", "#880E4F", "#4A0010"]

TEMP_ORDER = ["Sangat Dingin (<0°C)", "Dingin (0-10°C)", "Sejuk (10-20°C)",
              "Hangat (20-30°C)", "Panas (>30°C)"]
WIND_ORDER = ["Sangat Lemah (0-1)", "Lemah (1-2)", "Sedang (2-4)",
              "Kencang (4-6)", "Sangat Kencang (>6)"]

# -- Load data -----------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, index_col="datetime", parse_dates=True)
    df["month"] = df.index.month
    df["year"]  = df.index.year
    df["hour"]  = df.index.hour
    return df

df = load_data()

# -- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.title("Kualitas Udara Beijing")
    st.caption("Dashboard Analisis Data")
    st.markdown("---")

    st.subheader("Filter Data")

    min_d = df.index.min().date()
    max_d = df.index.max().date()
    start_d = st.date_input("Tanggal Mulai", min_d, min_value=min_d, max_value=max_d)
    end_d   = st.date_input("Tanggal Akhir", max_d, min_value=min_d, max_value=max_d)

    st.markdown("")
    all_stations = sorted(df["station"].unique())
    sel_stations = st.multiselect("Pilih Stasiun", all_stations, default=all_stations)

    st.markdown("---")
    st.caption(
        "Dataset: PRSA Air Quality\n"
        "12 stasiun pemantauan\n"
        "Maret 2013 - Februari 2017"
    )

# -- Guard clauses -------------------------------------------------------------
if not sel_stations:
    st.warning("Pilih minimal satu stasiun di sidebar.")
    st.stop()

if start_d > end_d:
    st.error("Tanggal mulai harus lebih awal dari tanggal akhir.")
    st.stop()

# -- Filter data ---------------------------------------------------------------
fdf = df.loc[
    (df.index.date >= start_d) &
    (df.index.date <= end_d) &
    (df["station"].isin(sel_stations))
].copy()

if fdf.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# -- Header --------------------------------------------------------------------
st.title("Dashboard Analisis Kualitas Udara Beijing")
st.caption(
    "Sumber Data: PRSA Air Quality Dataset  |  "
    "12 Stasiun Pemantauan  |  "
    "Maret 2013 - Februari 2017"
)
st.markdown("---")

# -- KPI Row -------------------------------------------------------------------
avg_pm25  = fdf["PM2.5"].mean()
avg_pm10  = fdf["PM10"].mean()
pct_who25 = (fdf["PM2.5"] > 5).mean() * 100
n_danger  = int((fdf["PM2.5"] > 75).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Rekaman",            f"{len(fdf):,}")
c2.metric("Rata-rata PM2.5",          f"{avg_pm25:.1f} ug/m3",
          f"{avg_pm25 / 5:.1f}x batas WHO", delta_color="inverse")
c3.metric("Rata-rata PM10",           f"{avg_pm10:.1f} ug/m3",
          f"{avg_pm10 / 15:.1f}x batas WHO", delta_color="inverse")
c4.metric("Jam Berbahaya (PM2.5>75)", f"{n_danger:,}",
          f"{n_danger / len(fdf) * 100:.1f}% dari total", delta_color="off")

st.markdown("---")

# -- Tabs ----------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "Pertanyaan 1: Pola Musiman",
    "Pertanyaan 2: Faktor Meteorologi",
    "Analisis Lanjutan",
])

# =============================================================================
# TAB 1 - Seasonal Pattern (Q1)
# =============================================================================
with tab1:
    st.subheader("Pola Musiman PM2.5 & PM10 vs Standar WHO")
    st.caption(
        "Rata-rata bulanan PM2.5 dan PM10 dibandingkan dengan standar tahunan WHO "
        "(PM2.5: 5 ug/m3 - PM10: 15 ug/m3)"
    )

    seas = fdf.groupby("month")[["PM2.5", "PM10"]].mean().round(2)
    seas.index = [MONTH_NAMES[m] for m in seas.index]
    seas = seas.reindex([m for m in MONTH_ORDER if m in seas.index])

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_bar(
            x=seas.index, y=seas["PM2.5"],
            marker_color="#E53935", name="PM2.5",
            text=seas["PM2.5"].round(0).astype(int), textposition="outside",
        )
        fig.add_hline(
            y=5, line_dash="dash", line_color="navy",
            annotation_text="WHO 5 ug/m3", annotation_position="top right",
        )
        fig.update_layout(
            title="Visualisasi 1a: Rata-rata PM2.5 per Bulan",
            xaxis_title="Bulan", yaxis_title="Konsentrasi (ug/m3)",
            height=420, showlegend=False, template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_bar(
            x=seas.index, y=seas["PM10"],
            marker_color="#FB8C00", name="PM10",
            text=seas["PM10"].round(0).astype(int), textposition="outside",
        )
        fig2.add_hline(
            y=15, line_dash="dash", line_color="navy",
            annotation_text="WHO 15 ug/m3", annotation_position="top right",
        )
        fig2.update_layout(
            title="Visualisasi 1b: Rata-rata PM10 per Bulan",
            xaxis_title="Bulan", yaxis_title="Konsentrasi (ug/m3)",
            height=420, showlegend=False, template="plotly_white",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Persentase Jam Melampaui Standar WHO per Bulan")

    ex25 = fdf.groupby("month")["PM2.5"].apply(lambda x: (x > 5).mean() * 100).round(1)
    ex10 = fdf.groupby("month")["PM10"].apply(lambda x: (x > 15).mean() * 100).round(1)
    ex_df = pd.DataFrame({"PM2.5 > 5 ug/m3": ex25, "PM10 > 15 ug/m3": ex10})
    ex_df.index = [MONTH_NAMES[m] for m in ex_df.index]
    ex_df = ex_df.reindex([m for m in MONTH_ORDER if m in ex_df.index])
    ex_df.index.name = "month"

    ex_m = ex_df.reset_index().melt(id_vars="month", var_name="Polutan", value_name="Persen")

    fig3 = px.bar(
        ex_m, x="month", y="Persen", color="Polutan", barmode="group",
        color_discrete_map={"PM2.5 > 5 ug/m3": "#E53935", "PM10 > 15 ug/m3": "#FB8C00"},
        labels={"month": "Bulan", "Persen": "% Jam Melampaui WHO"},
        title="Visualisasi 2: Persentase Jam Melampaui Standar WHO per Bulan",
        text_auto=".0f",
        template="plotly_white",
    )
    fig3.update_layout(height=420, yaxis_range=[0, 115], legend_title="Polutan")
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

    pct_pm25 = (fdf["PM2.5"] > 5).mean() * 100
    pct_pm10 = (fdf["PM10"] > 15).mean() * 100
    st.info(
        "**Kesimpulan Pertanyaan 1:**\n\n"
        f"- PM2.5 tertinggi pada bulan **{seas['PM2.5'].idxmax()}** "
        f"({seas['PM2.5'].max():.0f} ug/m3, {seas['PM2.5'].max()/5:.0f}x batas WHO) "
        f"dan terendah pada **{seas['PM2.5'].idxmin()}** ({seas['PM2.5'].min():.0f} ug/m3).\n"
        f"- PM10 tertinggi pada bulan **{seas['PM10'].idxmax()}** "
        f"({seas['PM10'].max():.0f} ug/m3) — dipengaruhi badai debu musim semi.\n"
        f"- **{pct_pm25:.1f}%** jam PM2.5 dan **{pct_pm10:.1f}%** jam PM10 melampaui "
        f"standar WHO — krisis kualitas udara yang sistemik sepanjang tahun."
    )

# =============================================================================
# TAB 2 - Meteorological Factors (Q2)
# =============================================================================
with tab2:
    st.subheader("Pengaruh Suhu & Kecepatan Angin terhadap Konsentrasi PM2.5")
    st.caption(
        "Korelasi Pearson dan rata-rata PM2.5 berdasarkan kategori suhu dan kecepatan angin"
    )

    corr_wspm  = fdf[["PM2.5", "WSPM"]].corr().iloc[0, 1]
    corr_temp  = fdf[["PM2.5", "TEMP"]].corr().iloc[0, 1]
    pct_danger = (fdf["PM2.5"] > 75).mean() * 100

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Korelasi PM2.5 & WSPM", f"{corr_wspm:.2f}",
               "Negatif — angin dispersi polutan", delta_color="off")
    mc2.metric("Korelasi PM2.5 & TEMP", f"{corr_temp:.2f}",
               "Negatif — dingin memperparah polusi", delta_color="off")
    mc3.metric("Jam Berbahaya (PM2.5>75)", f"{int((fdf['PM2.5'] > 75).sum()):,}",
               f"{pct_danger:.1f}% dari total rekaman", delta_color="off")

    st.markdown("---")

    fdf["TEMP_cat"] = pd.cut(
        fdf["TEMP"], bins=[-50, 0, 10, 20, 30, 60],
        labels=TEMP_ORDER, include_lowest=True,
    )
    fdf["WSPM_cat"] = pd.cut(
        fdf["WSPM"], bins=[-0.01, 1, 2, 4, 6, 100],
        labels=WIND_ORDER, include_lowest=True,
    )

    temp_avg = fdf.groupby("TEMP_cat")["PM2.5"].mean().reindex(TEMP_ORDER).reset_index()
    wind_avg = fdf.groupby("WSPM_cat")["PM2.5"].mean().reindex(WIND_ORDER).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        COLORS_T = ["#1A237E", "#1976D2", "#FDD835", "#F57C00", "#B71C1C"]
        fig = px.bar(
            temp_avg, x="TEMP_cat", y="PM2.5",
            color="TEMP_cat", color_discrete_sequence=COLORS_T,
            title="Visualisasi 3: Rata-rata PM2.5 per Kategori Suhu",
            labels={"TEMP_cat": "Kategori Suhu", "PM2.5": "Rata-rata PM2.5 (ug/m3)"},
            text=temp_avg["PM2.5"].fillna(0).round(0).astype(int),
            template="plotly_white",
        )
        fig.update_layout(showlegend=False, height=440, xaxis_tickangle=-20)
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        COLORS_W = ["#B71C1C", "#E53935", "#FF7043", "#42A5F5", "#1565C0"]
        fig2 = px.bar(
            wind_avg, x="WSPM_cat", y="PM2.5",
            color="WSPM_cat", color_discrete_sequence=COLORS_W,
            title="Visualisasi 4: Rata-rata PM2.5 per Kategori Kecepatan Angin",
            labels={"WSPM_cat": "Kategori Kecepatan Angin",
                    "PM2.5": "Rata-rata PM2.5 (ug/m3)"},
            text=wind_avg["PM2.5"].fillna(0).round(0).astype(int),
            template="plotly_white",
        )
        fig2.update_layout(showlegend=False, height=440, xaxis_tickangle=-20)
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.info(
        "**Kesimpulan Pertanyaan 2:**\n\n"
        f"- Kecepatan angin (r = **{corr_wspm:.2f}**) dan suhu (r = **{corr_temp:.2f}**) "
        f"berkorelasi negatif dengan PM2.5 — angin lemah dan udara dingin memperburuk kualitas udara.\n"
        f"- Kondisi berbahaya (PM2.5 > 75 ug/m3) terjadi pada **{pct_danger:.1f}%** "
        f"dari total jam pengukuran.\n"
        f"- Kombinasi suhu sangat dingin (<0°C) + angin sangat lemah (0-1 m/s) "
        f"adalah kondisi paling berisiko untuk paparan PM2.5 tinggi."
    )

# =============================================================================
# TAB 3 - Advanced Analytics
# =============================================================================
with tab3:
    st.subheader("Klasifikasi Kualitas Udara & Pengelompokan Stasiun")
    st.caption(
        "Binning PM2.5 berdasarkan breakpoints US EPA - "
        "Manual clustering 12 stasiun berdasarkan rata-rata PM2.5"
    )

    fdf_adv = fdf.copy()
    fdf_adv["AQ_Level"] = pd.cut(fdf_adv["PM2.5"], bins=AQ_BINS, labels=AQ_LABELS)
    aq_dist = fdf_adv["AQ_Level"].value_counts().sort_index()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Distribusi Tingkat Kualitas Udara PM2.5 (US EPA)**")
        present = [
            (lbl, clr)
            for lbl, clr in zip(AQ_LABELS, AQ_COLORS)
            if lbl in aq_dist.index and aq_dist[lbl] > 0
        ]
        fig = go.Figure(go.Pie(
            labels=[l for l, _ in present],
            values=[aq_dist[l] for l, _ in present],
            marker_colors=[c for _, c in present],
            hole=0.5,
            textinfo="percent+label",
            textfont_size=10,
        ))
        fig.update_layout(
            title="Visualisasi 5: Distribusi Kualitas Udara PM2.5",
            height=480, template="plotly_white", showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Manual Clustering Stasiun Berdasarkan Rata-rata PM2.5**")
        pm25_sta = fdf.groupby("station")["PM2.5"].mean().sort_values()
        q33_v    = pm25_sta.quantile(0.33)
        q67_v    = pm25_sta.quantile(0.67)

        def cluster_label(v):
            if v <= q33_v:
                return "Polusi Rendah"
            if v <= q67_v:
                return "Polusi Sedang"
            return "Polusi Tinggi"

        cl_df = pd.DataFrame({
            "Stasiun": pm25_sta.index,
            "PM2.5":   pm25_sta.values,
            "Kluster": [cluster_label(v) for v in pm25_sta.values],
        })
        color_map = {
            "Polusi Rendah": "#43A047",
            "Polusi Sedang": "#FDD835",
            "Polusi Tinggi": "#E53935",
        }
        fig2 = px.bar(
            cl_df, x="Stasiun", y="PM2.5", color="Kluster",
            color_discrete_map=color_map,
            title="Visualisasi 6: Manual Clustering 12 Stasiun Beijing",
            labels={"PM2.5": "Rata-rata PM2.5 (ug/m3)"},
            text=cl_df["PM2.5"].round(1),
            template="plotly_white",
        )
        fig2.add_hline(y=5, line_dash="dash", line_color="navy",
                       annotation_text="WHO 5 ug/m3")
        fig2.update_layout(height=480, xaxis_tickangle=-45, legend_title="Kluster")
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Distribusi Kualitas Udara per Bulan (%)")

    monthly_aq = (
        fdf_adv.groupby("month")["AQ_Level"]
               .value_counts(normalize=True)
               .unstack(fill_value=0) * 100
    )
    monthly_aq.index = [MONTH_NAMES[m] for m in monthly_aq.index]
    monthly_aq = monthly_aq.reindex([m for m in MONTH_ORDER if m in monthly_aq.index])

    fig3 = go.Figure()
    for label, color in zip(AQ_LABELS, AQ_COLORS):
        if label in monthly_aq.columns:
            fig3.add_trace(go.Bar(
                name=label,
                x=monthly_aq.index,
                y=monthly_aq[label].round(1),
                marker_color=color,
            ))
    fig3.update_layout(
        barmode="stack",
        title="Visualisasi 7: Distribusi Kualitas Udara per Bulan (%)",
        xaxis_title="Bulan", yaxis_title="Persentase (%)",
        height=440, template="plotly_white",
        legend_title="Tingkat Kualitas Udara",
    )
    st.plotly_chart(fig3, use_container_width=True)

    unhealthy_pct = (
        fdf_adv["AQ_Level"]
        .isin(["Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"])
        .mean() * 100
    )
    top_cat = aq_dist.idxmax()
    top_pct = aq_dist.max() / len(fdf_adv) * 100
    rendah  = cl_df[cl_df["Kluster"] == "Polusi Rendah"]["Stasiun"].tolist()
    tinggi  = cl_df[cl_df["Kluster"] == "Polusi Tinggi"]["Stasiun"].tolist()

    st.info(
        "**Kesimpulan Analisis Lanjutan:**\n\n"
        f"- Kategori terbanyak: **{top_cat}** ({top_pct:.1f}% waktu). "
        f"Total **{unhealthy_pct:.1f}%** jam tergolong Tidak Sehat atau lebih buruk.\n"
        f"- Kluster Polusi Rendah: {', '.join(rendah)} "
        f"— stasiun pinggiran/suburban dengan ventilasi lebih baik.\n"
        f"- Kluster Polusi Tinggi: {', '.join(tinggi)} "
        f"— stasiun urban padat, diprioritaskan untuk intervensi kebijakan."
    )

# -- Footer --------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Dibuat oleh **Yahya Putra Pradana** · "
    "Proyek Analisis Data Dicoding · 2026"
)
