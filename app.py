import json
from pathlib import Path
import plotly.graph_objects as go

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Cream Cheese Dashboard",
    page_icon="🧀",
    layout="wide"
)

DATA_DIR = Path(__file__).resolve().parent / "dashboard_data"


# --------------------------------------------------
# Load helpers
# --------------------------------------------------
@st.cache_data
def load_parquet(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / f"{name}.parquet")


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{name}.csv")


@st.cache_data
def load_meta() -> dict:
    with open(DATA_DIR / "meta_info.json", "r", encoding="utf-8") as f:
        return json.load(f)


def to_dt(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c])
    return df


def fmt_int(x) -> str:
    try:
        return f"{int(round(x)):,}".replace(",", " ")
    except Exception:
        return str(x)


def fmt_float(x, nd=2) -> str:
    try:
        return f"{x:,.{nd}f}".replace(",", " ")
    except Exception:
        return str(x)


def show_metric_row(metrics: list[tuple[str, str]]):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


# --------------------------------------------------
# Load data
# --------------------------------------------------
meta_info = load_meta()

dataset_passport = load_csv("dataset_passport")
cc_passport = load_csv("cc_passport")

segment_metrics = load_parquet("segment_metrics")
monthly_segment = to_dt(load_parquet("monthly_segment"), ["month_start"])
channel_share = load_parquet("channel_share")
top_loyal_products_real = load_parquet("top_loyal_products_real")
top_never_products_real = load_parquet("top_never_products_real")

common_products = load_parquet("common_products")
overlap_summary = load_csv("overlap_summary") if (DATA_DIR / "overlap_summary.csv").exists() else load_parquet("overlap_summary")
common_products_short = load_parquet("common_products_short")
common_affinity_filtered = load_parquet("common_affinity_filtered")
common_affinity_mass = load_parquet("common_affinity_mass")

loyal_monthly = to_dt(load_parquet("loyal_monthly"), ["month_start"])
loyal_yearly = load_parquet("loyal_yearly")
loyal_brand_summary = load_parquet("loyal_brand_summary")
loyal_brand_yearly = load_parquet("loyal_brand_yearly")

loyal_price_monthly = to_dt(load_parquet("loyal_price_monthly"), ["month_start"])
brand_price_monthly = to_dt(load_parquet("brand_price_monthly"), ["month_start"])
brand_price_total = load_parquet("brand_price_total")

infl_analysis = to_dt(load_parquet("infl_analysis"), ["month_start"])
loyal_price_vs_infl = to_dt(load_parquet("loyal_price_vs_infl"), ["month_start"])
infl_key_points = to_dt(load_parquet("infl_key_points"), ["month_start"])

violette_channel = load_parquet("violette_channel")
violette_channel_monthly = to_dt(load_parquet("violette_channel_monthly"), ["month_start"])

pack_total_all = load_parquet("pack_total_all")
pack_yearly_all = load_parquet("pack_yearly_all")

dow_brand_all = load_parquet("dow_brand_all")
seasonality_month = load_parquet("seasonality_month")
daypart_brand_all = load_parquet("daypart_brand_all")

never_month_channel = load_parquet("never_month_channel")
never_dow_channel = load_parquet("never_dow_channel")
never_daypart_channel = load_parquet("never_daypart_channel")
ad_reco_channel = load_parquet("ad_reco_channel")

flavor_2025 = load_parquet("flavor_2025")
top3_flavors_final = load_parquet("top3_flavors_final")
brand_flavor_all = load_parquet("brand_flavor_all")
flavor_price_compare = load_parquet("flavor_price_compare")

competitor_brand_summary = load_parquet("competitor_brand_summary")
competitor_group_summary = load_parquet("competitor_group_summary")
final_table_presentation = load_parquet("final_table_presentation")


# --------------------------------------------------
# Title
# --------------------------------------------------
st.title("Dashboard по творожным сырам")
st.caption("Анализ loyal-когорты покупателей Violette, 2023-2025")

top_metrics = [
    ("Loyal buyers", fmt_int(meta_info["loyal_buyers_cnt"])),
    ("Строк категории", fmt_int(meta_info["df_loyal_cc_rows"])),
    ("Чеки категории", fmt_int(meta_info["df_loyal_cc_checks"])),
    ("Бренды", fmt_int(meta_info["df_loyal_cc_brands"])),
    ("Flavor groups", fmt_int(meta_info["df_loyal_cc_flavor_groups"])),
]

if "never_buyers_cnt" in meta_info:
    top_metrics.append(("Never buyers", fmt_int(meta_info["never_buyers_cnt"])))

show_metric_row(top_metrics)

st.info(
    "Фильтры применяются только внутри текущего блока или вкладки. "
    "Каждый раздел дэшборда управляется отдельно."
)

tab_overview, tab_seg, tab_price, tab_pack, tab_time, tab_comp = st.tabs([
    "Overview",
    "Segmentation",
    "Pricing",
    "Packs",
    "Time & Flavor",
    "Competitors"
])


# --------------------------------------------------
# TAB 1 - OVERVIEW
# --------------------------------------------------
with tab_overview:
    st.header("Overview")
    st.caption("Общая картина loyal-когорты и итоговые ключевые метрики.")

    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.subheader("Итоговая таблица для презентации")
        st.dataframe(final_table_presentation, use_container_width=True)

    with col2:
        st.subheader("Паспорт категории")
        st.dataframe(cc_passport, use_container_width=True)

    st.subheader("Доли брендов в loyal-когорте")
    brand_share_plot = loyal_brand_summary.sort_values("kg_share_pct", ascending=False).head(12)
    fig = px.bar(
        brand_share_plot,
        x="brand",
        y="kg_share_pct",
        title="Доля брендов в потреблении loyal-когорты, % кг"
    )
    fig.update_layout(xaxis_title="Бренд", yaxis_title="% кг")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Динамика доли брендов по годам")
    brand_year_options = sorted(loyal_brand_yearly["brand"].dropna().unique().tolist())
    selected_brands = st.multiselect(
        "Бренды для сравнения долей по годам",
        brand_year_options,
        default=[b for b in ["violette", "hochland", "ekomilk", "almette"] if b in brand_year_options],
        key="overview_brand_year"
    )

    df_plot = loyal_brand_yearly[loyal_brand_yearly["brand"].isin(selected_brands)]
    fig2 = px.line(
        df_plot,
        x="year",
        y="kg_share_pct",
        color="brand",
        markers=True,
        title="Доля бренда в loyal-когорте по годам"
    )
    fig2.update_layout(xaxis_title="Год", yaxis_title="% кг")
    st.plotly_chart(fig2, use_container_width=True)


# --------------------------------------------------
# TAB 2 - SEGMENTATION
# --------------------------------------------------
with tab_seg:
    st.header("Segmentation")
    st.caption("Размер сегментов, активность, каналы и сопутствующие товары.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Размер и метрики сегментов")
        st.dataframe(segment_metrics, use_container_width=True)

    with col2:
        fig = px.bar(
            segment_metrics.sort_values("buyers_cnt", ascending=False),
            x="segment",
            y="buyers_cnt",
            title="Количество покупателей по сегментам"
        )
        fig.update_layout(xaxis_title="Сегмент", yaxis_title="Покупатели")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Частота и интенсивность покупок по месяцам")
    metric_option = st.selectbox(
        "Метрика месячной динамики сегментов",
        ["checks_per_buyer", "kg_per_buyer", "rub_per_buyer"],
        key="seg_metric"
    )

    fig2 = px.line(
        monthly_segment,
        x="month_start",
        y=metric_option,
        color="segment",
        title=f"{metric_option} по сегментам"
    )
    fig2.update_layout(xaxis_title="Месяц", yaxis_title=metric_option)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Канальная структура сегментов")
    channel_plot = channel_share.copy()
    channel_plot["channel"] = channel_plot["is_marketplace"].map({
        True: "Маркетплейс",
        False: "Не маркетплейс"
    })

    share_option = st.selectbox(
        "Показатель канальной структуры",
        ["checks_share_pct", "rub_share_pct", "kg_share_pct"],
        key="seg_channel_metric"
    )

    fig3 = px.bar(
        channel_plot,
        x="segment",
        y=share_option,
        color="channel",
        barmode="group",
        title=f"{share_option} по сегментам"
    )
    fig3.update_layout(xaxis_title="Сегмент", yaxis_title="%")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Сопутствующие товары: top-списки")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Loyal Violette**")
        st.dataframe(top_loyal_products_real.head(15), use_container_width=True)

    with col2:
        st.markdown("**Never Violette**")
        st.dataframe(top_never_products_real.head(15), use_container_width=True)

    st.subheader("Пересечение сопутствующих товаров")
    col1, col2 = st.columns([0.9, 1.4])
    with col1:
        st.markdown("**Overlap summary**")
        st.dataframe(overlap_summary, use_container_width=True)

    with col2:
        st.markdown("**Общие товары из коротких витрин**")
        st.dataframe(common_products, use_container_width=True)

    st.subheader("Общие товары: массовый слой и affinity")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Массовые общие товары**")
        st.dataframe(common_affinity_mass.head(20), use_container_width=True)

    with col2:
        st.markdown("**Товары с повышенной относительной представленностью у Loyal**")
        st.dataframe(common_affinity_filtered.head(20), use_container_width=True)

    st.subheader("Канальные рекомендации для сегмента Never Violette")
    st.caption("Когда лучше показывать рекламу Violette для тех, кто бренд не покупает.")

    st.dataframe(ad_reco_channel, use_container_width=True)


# --------------------------------------------------
# TAB 3 - PRICING
# --------------------------------------------------
with tab_price:
    st.header("Pricing")
    st.caption("Динамика цены loyal-когорты, брендов, каналов и сопоставление с официальной инфляцией.")

    st.subheader("Цена loyal-когорты")
    price_mode = st.selectbox(
        "Основной график loyal-когорты",
        ["price_per_kg_weighted", "price_index_jan2023_100"],
        key="price_main_mode"
    )

    title_map = {
        "price_per_kg_weighted": "Средневзвешенная цена за кг",
        "price_index_jan2023_100": "Индекс цены, январь 2023 = 100"
    }

    fig = px.line(
        loyal_price_monthly,
        x="month_start",
        y=price_mode,
        title=title_map[price_mode]
    )
    fig.update_layout(
        xaxis_title="Месяц",
        yaxis_title="Руб/кг" if price_mode == "price_per_kg_weighted" else "Январь 2023 = 100"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------
    # Подготовка индекса инфляции
    # ----------------------------------------------
    loyal_price_vs_infl_local = loyal_price_vs_infl.sort_values("month_start").reset_index(drop=True).copy()

    pi = loyal_price_vs_infl_local["official_inflation_yoy"] / 100
    monthly_factor = (1 + pi) ** (1 / 12)

    infl_index = [100.0]
    for i in range(1, len(loyal_price_vs_infl_local)):
        infl_index.append(infl_index[-1] * monthly_factor.iloc[i])

    loyal_price_vs_infl_local["inflation_index_jan2023_100"] = infl_index

    # ----------------------------------------------
    # Индекс цены категории vs индекс инфляции
    # ----------------------------------------------
    st.subheader("Индекс цены категории vs индекс официальной инфляции")
    st.caption(
        "Обе линии приведены к базе январь 2023 = 100. "
        "Индекс инфляции восстановлен приближённо из официальной инфляции, заданной в % годовых по месяцам, "
        "через месячный множитель (1 + π)^(1/12)."
    )

    infl_compare = loyal_price_vs_infl_local[
        ["month_start", "category_price_index_jan2023_100", "inflation_index_jan2023_100"]
    ].copy()

    infl_compare_long = infl_compare.melt(
        id_vars=["month_start"],
        value_vars=["category_price_index_jan2023_100", "inflation_index_jan2023_100"],
        var_name="series",
        value_name="value"
    )

    infl_compare_long["series"] = infl_compare_long["series"].map({
        "category_price_index_jan2023_100": "Индекс цены категории",
        "inflation_index_jan2023_100": "Индекс официальной инфляции"
    })

    fig_infl_index = px.line(
        infl_compare_long,
        x="month_start",
        y="value",
        color="series",
        title="Индекс цены категории vs индекс официальной инфляции"
    )
    fig_infl_index.update_layout(
        xaxis_title="Месяц",
        yaxis_title="Январь 2023 = 100"
    )
    st.plotly_chart(fig_infl_index, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ключевые точки**")
        st.dataframe(infl_key_points, use_container_width=True)

    with col2:
        st.markdown("**Средняя цена по брендам за весь период**")
        st.dataframe(
            brand_price_total.sort_values("price_per_kg_weighted", ascending=False),
            use_container_width=True
        )

    st.subheader("Цена по брендам")
    brand_options = sorted(brand_price_monthly["brand"].dropna().unique().tolist())
    selected_price_brands = st.multiselect(
        "Бренды для сравнения цены",
        brand_options,
        default=[b for b in ["violette", "hochland", "ekomilk", "almette", "no_brand"] if b in brand_options],
        key="price_brands"
    )

    df_price = brand_price_monthly[brand_price_monthly["brand"].isin(selected_price_brands)]
    fig2 = px.line(
        df_price,
        x="month_start",
        y="price_per_kg_weighted",
        color="brand",
        title="Средневзвешенная цена за кг по брендам"
    )
    fig2.update_layout(xaxis_title="Месяц", yaxis_title="Руб/кг")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Violette по каналам")
    col1, col2 = st.columns([0.9, 1.2])
    with col1:
        violette_channel_show = violette_channel.copy()
        violette_channel_show["Канал"] = violette_channel_show["is_marketplace"].map({
            True: "Маркетплейс",
            False: "Не маркетплейс"
        })
        st.dataframe(violette_channel_show, use_container_width=True)

    with col2:
        temp = violette_channel_monthly.copy()
        temp["channel"] = temp["is_marketplace"].map({
            True: "Маркетплейс",
            False: "Не маркетплейс"
        })
        fig3 = px.line(
            temp,
            x="month_start",
            y="price_per_kg_weighted",
            color="channel",
            title="Цена Violette по каналам"
        )
        fig3.update_layout(xaxis_title="Месяц", yaxis_title="Руб/кг")
        st.plotly_chart(fig3, use_container_width=True)


# --------------------------------------------------
# TAB 4 - PACKS
# --------------------------------------------------
with tab_pack:
    st.header("Packs")
    st.caption("Фасовки, их структура, цены и миграция по годам.")

    pack_brand_options = sorted(pack_total_all["brand"].dropna().unique().tolist())
    selected_pack_brand = st.selectbox(
        "Бренд для анализа фасовок",
        pack_brand_options,
        index=pack_brand_options.index("violette") if "violette" in pack_brand_options else 0,
        key="pack_brand"
    )

    pack_total_brand = pack_total_all[pack_total_all["brand"] == selected_pack_brand].copy()
    pack_year_brand = pack_yearly_all[pack_yearly_all["brand"] == selected_pack_brand].copy()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Фасовки бренда {selected_pack_brand}")
        st.dataframe(
            pack_total_brand.sort_values("total_kg", ascending=False).head(15),
            use_container_width=True
        )

    with col2:
        fig = px.bar(
            pack_total_brand.sort_values("total_kg", ascending=False).head(12),
            x="pack_size_g",
            y="total_kg",
            title=f"Топ фасовок бренда {selected_pack_brand}"
        )
        fig.update_layout(xaxis_title="Фасовка, г", yaxis_title="Кг")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Миграция фасовок по годам")
    fig2 = px.bar(
        pack_year_brand,
        x="year",
        y="kg_share_within_brand_year_pct",
        color="pack_size_g",
        title=f"Доля фасовок внутри бренда {selected_pack_brand}"
    )
    fig2.update_layout(xaxis_title="Год", yaxis_title="% кг внутри бренда")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Цена по фасовкам")
    pack_metric = st.selectbox(
        "Метрика фасовок",
        ["price_per_kg_weighted", "avg_pack_price"],
        key="pack_metric"
    )
    fig3 = px.bar(
        pack_total_brand.sort_values("total_kg", ascending=False).head(12),
        x="pack_size_g",
        y=pack_metric,
        title=f"{pack_metric} по фасовкам бренда {selected_pack_brand}"
    )
    fig3.update_layout(xaxis_title="Фасовка, г", yaxis_title=pack_metric)
    st.plotly_chart(fig3, use_container_width=True)


# --------------------------------------------------
# TAB 5 - TIME & FLAVOR
# --------------------------------------------------
with tab_time:
    st.header("Time & Flavor")
    st.caption("Дни недели, сезонность, время суток, flavor_group и рекомендации по каналам.")

    st.subheader("Временные паттерны по брендам")
    time_brand_options = sorted(dow_brand_all["brand"].dropna().unique().tolist())
    selected_time_brands = st.multiselect(
        "Бренды для временных паттернов",
        time_brand_options,
        default=[b for b in ["violette", "hochland", "ekomilk", "no_brand"] if b in time_brand_options],
        key="time_brands"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Дни недели**")
        df_dow = dow_brand_all[dow_brand_all["brand"].isin(selected_time_brands)].copy()
        fig = px.bar(
            df_dow,
            x="dow_name",
            y="kg_share_pct",
            color="brand",
            barmode="group",
            title="Доля объема по дням недели"
        )
        fig.update_layout(xaxis_title="День недели", yaxis_title="% кг")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Время суток**")
        df_daypart = daypart_brand_all[daypart_brand_all["brand"].isin(selected_time_brands)].copy()
        fig2 = px.bar(
            df_daypart,
            x="daypart",
            y="kg_share_pct",
            color="brand",
            barmode="group",
            title="Доля объема по времени суток"
        )
        fig2.update_layout(xaxis_title="Время суток", yaxis_title="% кг")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Сезонность loyal-когорты")
    fig3 = px.bar(
        seasonality_month.sort_values("month"),
        x="month",
        y="kg_per_buyer",
        title="Кг на покупателя по месяцам"
    )
    fig3.update_layout(xaxis_title="Месяц", yaxis_title="Кг на покупателя")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Канальные рекомендации для Never Violette")
    st.dataframe(ad_reco_channel, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fig_nm = px.line(
            never_month_channel,
            x="month",
            y="kg_per_buyer",
            color="channel",
            markers=True,
            title="Never Violette: кг на покупателя по месяцам"
        )
        fig_nm.update_layout(xaxis_title="Месяц", yaxis_title="Кг на покупателя")
        st.plotly_chart(fig_nm, use_container_width=True)

    with col2:
        fig_nd = px.line(
            never_dow_channel,
            x="dow_name",
            y="kg_per_buyer",
            color="channel",
            markers=True,
            title="Never Violette: кг на покупателя по дням недели"
        )
        fig_nd.update_layout(xaxis_title="День недели", yaxis_title="Кг на покупателя")
        st.plotly_chart(fig_nd, use_container_width=True)

    with col3:
        fig_np = px.line(
            never_daypart_channel,
            x="daypart",
            y="kg_per_buyer",
            color="channel",
            markers=True,
            title="Never Violette: кг на покупателя по времени суток"
        )
        fig_np.update_layout(xaxis_title="Время суток", yaxis_title="Кг на покупателя")
        st.plotly_chart(fig_np, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Топ flavor_group в 2025 году")
        st.dataframe(flavor_2025.head(10), use_container_width=True)

    with col2:
        st.subheader("Топ-3 flavor_group по годам")
        st.dataframe(top3_flavors_final, use_container_width=True)

    st.subheader("Flavor_group по брендам")
    flavor_brand_options = sorted(brand_flavor_all["brand"].dropna().unique().tolist())
    selected_flavor_brands = st.multiselect(
        "Бренды для flavor_group",
        flavor_brand_options,
        default=[b for b in ["violette", "hochland", "almette", "ekomilk"] if b in flavor_brand_options],
        key="flavor_brands"
    )

    flavor_metric = st.selectbox(
        "Метрика flavor_group",
        ["total_rub", "total_kg", "checks_nunique"],
        index=0,
        key="flavor_metric"
    )

    metric_title_map = {
        "total_rub": "Выручка, руб",
        "total_kg": "Объём, кг",
        "checks_nunique": "Число чеков"
    }

    temp_flavor = brand_flavor_all[brand_flavor_all["brand"].isin(selected_flavor_brands)].copy()

    use_log_scale = st.toggle(
        "Логарифмическая шкала для полного графика",
        value=True,
        key="flavor_log_scale"
    )

    fig4 = px.bar(
        temp_flavor.sort_values(flavor_metric, ascending=False),
        x="flavor_group",
        y=flavor_metric,
        color="brand",
        barmode="group",
        title=f"{metric_title_map[flavor_metric]} по flavor_group"
    )
    fig4.update_layout(
        xaxis_title="Flavor group",
        yaxis_title=metric_title_map[flavor_metric],
        yaxis_type="log" if use_log_scale else "linear"
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Flavor_group по брендам без plain")
    temp_flavor_no_plain = temp_flavor[temp_flavor["flavor_group"] != "plain"].copy()

    fig5 = px.bar(
        temp_flavor_no_plain.sort_values(flavor_metric, ascending=False),
        x="flavor_group",
        y=flavor_metric,
        color="brand",
        barmode="group",
        title=f"{metric_title_map[flavor_metric]} по flavor_group без plain"
    )
    fig5.update_layout(
        xaxis_title="Flavor group",
        yaxis_title=metric_title_map[flavor_metric]
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Экономика plain vs non-plain")
    st.dataframe(flavor_price_compare, use_container_width=True)


# --------------------------------------------------
# TAB 6 - COMPETITORS
# --------------------------------------------------
with tab_comp:
    st.header("Competitors")
    st.caption("Конкуренты внутри loyal-когорты, включая brand и no_brand.")

    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        st.subheader("Все бренды-конкуренты")
        st.dataframe(competitor_brand_summary, use_container_width=True)

    with col2:
        st.subheader("Группировка конкурентов")
        st.dataframe(competitor_group_summary, use_container_width=True)

    st.subheader("Сравнение выбранных конкурентов")
    competitor_options = competitor_brand_summary["brand"].dropna().tolist()
    selected_competitors = st.multiselect(
        "Выберите конкурентов",
        competitor_options,
        default=[b for b in ["hochland", "almette", "ekomilk", "no_brand"] if b in competitor_options],
        key="competitors_select"
    )

    comp_df = competitor_brand_summary[competitor_brand_summary["brand"].isin(selected_competitors)].copy()

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            comp_df.sort_values("total_kg", ascending=False),
            x="brand",
            y="total_kg",
            title="Конкуренты по объему, кг"
        )
        fig.update_layout(xaxis_title="Бренд", yaxis_title="Кг")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            comp_df.sort_values("buyers_nunique", ascending=False),
            x="brand",
            y="buyers_nunique",
            title="Конкуренты по числу покупателей"
        )
        fig2.update_layout(xaxis_title="Бренд", yaxis_title="Покупатели")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Фасовки выбранных конкурентов")
    comp_pack = pack_total_all[pack_total_all["brand"].isin(selected_competitors)].copy()
    fig3 = px.bar(
        comp_pack.sort_values("total_kg", ascending=False).head(25),
        x="pack_size_g",
        y="total_kg",
        color="brand",
        barmode="group",
        title="Фасовки выбранных конкурентов"
    )
    fig3.update_layout(xaxis_title="Фасовка, г", yaxis_title="Кг")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Flavor_group выбранных конкурентов")
    comp_flavor = brand_flavor_all[brand_flavor_all["brand"].isin(selected_competitors)].copy()
    fig4 = px.bar(
        comp_flavor.sort_values("total_rub", ascending=False).head(25),
        x="flavor_group",
        y="total_rub",
        color="brand",
        barmode="group",
        title="Flavor_group выбранных конкурентов"
    )
    fig4.update_layout(xaxis_title="Flavor group", yaxis_title="Руб")
    st.plotly_chart(fig4, use_container_width=True)
