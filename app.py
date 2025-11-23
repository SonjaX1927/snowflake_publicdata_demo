import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from snowflake_query import run_query


STATUS_LABELS = {
    "F": "Filled",
    "O": "Open",
    "P": "Pending",
}


st.set_page_config(
    page_title="Snowflake Orders Analytics",
    layout="wide",
)


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Layout tweaks */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
            max-width: 1200px;
        }

        /* Card look for sections */
        .report-card {
            padding: 1.25rem 1.5rem;
            border-radius: 0.75rem;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            box-shadow: 0 10px 15px -10px rgba(15, 23, 42, 0.18);
        }

        .kpi-metric div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
        }

        .kpi-metric div[data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            color: #9ca3af;
        }

        .ekgvj880 { /* section header hack */
            font-weight: 600 !important;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def enrich_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Add human-readable labels and derived columns for analytics."""
    if df.empty:
        return df

    df = df.copy()
    df["STATUS_LABEL"] = df["STATUS"].map(STATUS_LABELS).fillna(df["STATUS"])
    return df


@st.cache_data(show_spinner=False, ttl=600)
def load_orders(start_date: str, end_date: str) -> pd.DataFrame:
    sql = """
        SELECT
            O_ORDERKEY            AS ORDER_KEY,
            O_ORDERDATE::date     AS ORDER_DATE,
            O_ORDERSTATUS         AS STATUS,
            O_ORDERPRIORITY       AS PRIORITY,
            O_TOTALPRICE          AS TOTAL_PRICE
        FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
        WHERE O_ORDERDATE BETWEEN %s AND %s
    """
    df = run_query(sql, params=[start_date, end_date])
    # Ensure correct dtypes
    df["ORDER_DATE"] = pd.to_datetime(df["ORDER_DATE"])
    df = enrich_orders(df)
    return df


def sidebar_filters(df: pd.DataFrame):
    st.sidebar.title("Control panel")

    min_date = df["ORDER_DATE"].min().date() if not df.empty else date(1992, 1, 1)
    max_date = df["ORDER_DATE"].max().date() if not df.empty else date(1998, 12, 31)

    start_date, end_date = st.sidebar.date_input(
        "Order date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(start_date, (list, tuple)):
        start_date = start_date[0]
    if isinstance(end_date, (list, tuple)):
        end_date = end_date[-1]

    status_options = sorted(df["STATUS"].dropna().unique().tolist()) if not df.empty else []
    selected_status = st.sidebar.multiselect(
        "Order status filter (F=Filled, O=Open, P=Pending)",
        options=status_options,
        default=status_options,
    )

    priority_options = sorted(df["PRIORITY"].dropna().unique().tolist()) if not df.empty else []
    selected_priority = st.sidebar.multiselect(
        "Order priority filter",
        options=priority_options,
        default=priority_options,
    )

    return (start_date, end_date, selected_status, selected_priority)


def apply_filters(df, start_date, end_date, status_list, priority_list):
    if df.empty:
        return df

    mask = (df["ORDER_DATE"] >= pd.to_datetime(start_date)) & (
        df["ORDER_DATE"] <= pd.to_datetime(end_date)
    )

    if status_list:
        mask &= df["STATUS"].isin(status_list)
    if priority_list:
        mask &= df["PRIORITY"].isin(priority_list)

    return df[mask].copy()


def kpi_section(df: pd.DataFrame):
    with st.container():
        col1, col2, col3 = st.columns(3)

        total_orders = int(len(df))
        total_amount = float(df["TOTAL_PRICE"].sum()) if not df.empty else 0.0
        avg_order_value = total_amount / total_orders if total_orders > 0 else 0.0

        distinct_days = df["ORDER_DATE"].nunique() if not df.empty else 0
        orders_per_day = total_orders / distinct_days if distinct_days > 0 else 0.0
        median_order_value = (
            float(df["TOTAL_PRICE"].median()) if not df.empty else 0.0
        )
        p90_order_value = (
            float(df["TOTAL_PRICE"].quantile(0.9)) if not df.empty else 0.0
        )

        with col1:
            st.container().markdown("<div class='report-card kpi-metric'>", unsafe_allow_html=True)
            st.metric("Total orders", f"{total_orders:,}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.container().markdown("<div class='report-card kpi-metric'>", unsafe_allow_html=True)
            st.metric("Total revenue", f"${total_amount:,.0f}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.container().markdown("<div class='report-card kpi-metric'>", unsafe_allow_html=True)
            st.metric("Average order value", f"${avg_order_value:,.0f}")
            st.markdown("</div>", unsafe_allow_html=True)

        col4, col5, col6 = st.columns(3)

        with col4:
            st.container().markdown("<div class='report-card kpi-metric'>", unsafe_allow_html=True)
            st.metric("Median order value", f"${median_order_value:,.0f}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col5:
            st.container().markdown("<div class='report-card kpi-metric'>", unsafe_allow_html=True)
            st.metric("90th percentile order value", f"${p90_order_value:,.0f}")
            st.markdown("</div>", unsafe_allow_html=True)
        with col6:
            st.container().markdown("<div class='report-card kpi-metric'>", unsafe_allow_html=True)
            st.metric("Orders per active day", f"{orders_per_day:,.1f}")
            st.markdown("</div>", unsafe_allow_html=True)


def time_series_section(df: pd.DataFrame):
    if df.empty:
        return

    df_month = (
        df.assign(month=df["ORDER_DATE"].dt.to_period("M").dt.to_timestamp())
        .groupby("month")
        .agg(order_cnt=("ORDER_KEY", "count"), total_amount=("TOTAL_PRICE", "sum"))
        .reset_index()
    )

    with st.container():
        st.markdown("### Time trends")
        col1, col2 = st.columns((2, 1))

        fig_amount = px.area(
            df_month,
            x="month",
            y="total_amount",
            title="Monthly revenue trend",
            labels={"month": "Month", "total_amount": "Revenue"},
        )
        fig_amount.update_traces(mode="lines", line=dict(width=2))

        fig_orders = px.bar(
            df_month,
            x="month",
            y="order_cnt",
            title="Monthly order volume",
            labels={"month": "Month", "order_cnt": "Order count"},
        )

        col1.plotly_chart(fig_amount, use_container_width=True)
        col1.caption("Shows how total revenue evolves within the selected period.")
        col2.plotly_chart(fig_orders, use_container_width=True)
        col2.caption("Shows how order volume evolves within the selected period.")


def yearly_trend_section(df: pd.DataFrame):
    """Show yearly revenue, volume and YoY growth across all years."""
    if df.empty:
        return

    df_year = (
        df.assign(year=df["ORDER_DATE"].dt.year)
        .groupby("year")
        .agg(order_cnt=("ORDER_KEY", "count"), total_amount=("TOTAL_PRICE", "sum"))
        .reset_index()
        .sort_values("year")
    )
    df_year["revenue_yoy"] = df_year["total_amount"].pct_change() * 100.0

    with st.container():
        st.markdown("### Yearly performance and growth")
        col1, col2 = st.columns((2, 1))

        with col1:
            fig_rev = px.bar(
                df_year,
                x="year",
                y="total_amount",
                title="Total revenue by year",
                labels={"year": "Year", "total_amount": "Revenue"},
                text_auto=".0f",
            )
            st.plotly_chart(fig_rev, use_container_width=True)
            st.caption(
                "Comparing total revenue by year highlights long-term growth patterns and structural shifts in demand."
            )

        with col2:
            df_yoy = df_year.dropna(subset=["revenue_yoy"])  # first year has no prior year
            if not df_yoy.empty:
                fig_yoy = px.line(
                    df_yoy,
                    x="year",
                    y="revenue_yoy",
                    markers=True,
                    title="Year-over-year revenue growth",
                    labels={"year": "Year", "revenue_yoy": "YoY growth (%)"},
                )
                st.plotly_chart(fig_yoy, use_container_width=True)
                st.caption(
                    "Year-over-year growth shows acceleration or slowdown that may be hidden in absolute revenue levels."
                )


def yearly_month_comparison_section(df: pd.DataFrame):
    """Compare the same calendar month across different years to analyze seasonality."""
    if df.empty:
        return

    df_my = (
        df.assign(
            year=df["ORDER_DATE"].dt.year,
            month=df["ORDER_DATE"].dt.month,
        )
        .groupby(["year", "month"])
        .agg(total_amount=("TOTAL_PRICE", "sum"))
        .reset_index()
    )

    with st.container():
        st.markdown("### Month-over-month comparison across years")
        fig = px.line(
            df_my,
            x="month",
            y="total_amount",
            color="year",
            markers=True,
            title="Seasonality: revenue by month and year",
            labels={
                "month": "Month",
                "total_amount": "Revenue",
                "year": "Year",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Comparing the same calendar month across years controls for seasonality and answers questions like "
            "'Is March this year stronger than March last year?'."
        )


def status_trend_section(df: pd.DataFrame):
    """Show how revenue composition by status evolves over time."""
    if df.empty:
        return

    df_status = (
        df.assign(month=df["ORDER_DATE"].dt.to_period("M").dt.to_timestamp())
        .groupby(["month", "STATUS_LABEL"])
        .agg(total_amount=("TOTAL_PRICE", "sum"))
        .reset_index()
    )

    with st.container():
        st.markdown("### Revenue by order status over time")
        fig = px.area(
            df_status,
            x="month",
            y="total_amount",
            color="STATUS_LABEL",
            title="Monthly revenue by status",
            labels={
                "month": "Month",
                "total_amount": "Revenue",
                "STATUS_LABEL": "Status",
            },
        )
        fig.update_traces(mode="lines", line=dict(width=1.5))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Shows how the revenue mix between Filled, Open, and Pending orders shifts over time."
        )


def distribution_section(df: pd.DataFrame):
    if df.empty:
        return

    with st.container():
        st.markdown("### Structural breakdown")
        col1, col2 = st.columns(2)

        status_cnt = (
            df.groupby("STATUS")["ORDER_KEY"].count().reset_index(name="cnt")
        )
        fig_status = px.bar(
            status_cnt,
            x="STATUS",
            y="cnt",
            title="Order count by status (F=Filled, O=Open, P=Pending)",
            labels={"STATUS": "Status", "cnt": "Order count"},
            text="cnt",
        )
        fig_status.update_traces(textposition="outside")

        priority_cnt = (
            df.groupby("PRIORITY")["ORDER_KEY"].count().reset_index(name="cnt")
        )
        fig_priority = px.bar(
            priority_cnt,
            x="PRIORITY",
            y="cnt",
            title="Order count by priority",
            labels={"PRIORITY": "Priority", "cnt": "Order count"},
            text="cnt",
        )
        fig_priority.update_traces(textposition="outside")

        col1.plotly_chart(fig_status, use_container_width=True)
        col1.caption(
            "Highlights how orders are distributed across status codes (Filled, Open, Pending)."
        )
        col2.plotly_chart(fig_priority, use_container_width=True)
        col2.caption("Shows whether certain priority levels dominate order volume.")


def status_priority_comparison_section(df: pd.DataFrame):
    """More analytical comparison views for status and priority."""
    if df.empty:
        return

    with st.container():
        st.markdown("### Status & priority comparison")
        col1, col2 = st.columns(2)

        status_stats = (
            df.groupby("STATUS_LABEL")
            .agg(
                avg_value=("TOTAL_PRICE", "mean"),
                order_cnt=("ORDER_KEY", "count"),
                total_amount=("TOTAL_PRICE", "sum"),
            )
            .reset_index()
        )

        fig_status_avg = px.bar(
            status_stats,
            x="STATUS_LABEL",
            y="avg_value",
            title="Average order value by status",
            labels={
                "STATUS_LABEL": "Status",
                "avg_value": "Average order value",
            },
            text_auto=".0f",
        )
        col1.plotly_chart(fig_status_avg, use_container_width=True)
        col1.caption(
            "Compares typical order size across statuses to see where higher-value orders concentrate."
        )

        priority_status = (
            df.groupby(["PRIORITY", "STATUS_LABEL"])["ORDER_KEY"]
            .count()
            .reset_index(name="order_cnt")
        )

        fig_priority_status = px.bar(
            priority_status,
            x="PRIORITY",
            y="order_cnt",
            color="STATUS_LABEL",
            barmode="stack",
            title="Order count by priority and status",
            labels={
                "PRIORITY": "Priority",
                "order_cnt": "Order count",
                "STATUS_LABEL": "Status",
            },
        )
        col2.plotly_chart(fig_priority_status, use_container_width=True)
        col2.caption(
            "Shows how each priority level splits into Filled, Open, and Pending orders."
        )


def value_distribution_section(df: pd.DataFrame):
    """Visualize the distribution of order values overall and by status."""
    if df.empty:
        return

    with st.container():
        st.markdown("### Order value distribution")
        col1, col2 = st.columns(2)

        fig_hist = px.histogram(
            df,
            x="TOTAL_PRICE",
            nbins=50,
            title="Overall order value distribution",
            labels={"TOTAL_PRICE": "Order value"},
        )
        fig_hist.update_yaxes(title="Number of orders")
        col1.plotly_chart(fig_hist, use_container_width=True)
        col1.caption("Provides an overview of the distribution and tail of order values.")

        fig_box = px.box(
            df,
            x="STATUS_LABEL",
            y="TOTAL_PRICE",
            title="Order value by status",
            labels={
                "STATUS_LABEL": "Status",
                "TOTAL_PRICE": "Order value",
            },
            points="outliers",
        )
        col2.plotly_chart(fig_box, use_container_width=True)
        col2.caption("Compares value distribution and outliers across statuses.")


def heatmap_section(df: pd.DataFrame):
    if df.empty:
        return

    df_heat = df.copy()
    df_heat["month"] = df_heat["ORDER_DATE"].dt.to_period("M").dt.to_timestamp()
    pivot = (
        df_heat.pivot_table(
            index="PRIORITY",
            columns="STATUS",
            values="TOTAL_PRICE",
            aggfunc="sum",
            fill_value=0,
        )
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            colorbar=dict(title="Revenue"),
        )
    )
    fig.update_layout(
        title="Revenue heatmap: status × priority",
        xaxis_title="Status",
        yaxis_title="Priority",
    )

    with st.container():
        st.markdown("### Order mix insights")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Highlights combinations of status and priority that contribute the most to revenue."
        )


def sample_table_section(df: pd.DataFrame):
    if df.empty:
        return

    with st.container():
        st.markdown("### Sample orders")
        st.caption("Random sample of orders to quickly inspect the raw structure.")
        sample = df.sample(min(1000, len(df)), random_state=42)
        st.dataframe(sample, use_container_width=True, height=360)


def sql_reference_section():
    with st.expander("View sample SQL"):
        st.code(
            """SQL
SELECT
  O_ORDERKEY,
  O_ORDERDATE::date AS ORDER_DATE,
  O_ORDERSTATUS     AS STATUS,
  O_ORDERPRIORITY   AS PRIORITY,
  O_TOTALPRICE      AS TOTAL_PRICE
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
WHERE O_ORDERDATE BETWEEN :start_date AND :end_date;
            """,
            language="sql",
        )


def main():
    inject_custom_css()

    st.title("Snowflake Orders Analytics Dashboard")
    st.write(
        "Interactive analytics dashboard built on SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS. "
        "Use the filters on the left to explore orders, revenue, and the status/priority mix."
    )
    st.caption("Order status codes: F = Filled, O = Open, P = Pending.")

    # 先加载一个较大的日期范围数据，方便侧边栏给出全局范围
    base_df = load_orders("1992-01-01", "1998-12-31")

    start_date, end_date, selected_status, selected_priority = sidebar_filters(base_df)

    df_filtered = apply_filters(
        base_df,
        start_date=start_date,
        end_date=end_date,
        status_list=selected_status,
        priority_list=selected_priority,
    )

    if df_filtered.empty:
        st.warning("No data for the current filters. Please adjust the date range or filters.")
        return

    years = sorted(df_filtered["ORDER_DATE"].dt.year.unique().tolist())
    tab_labels = ["Overview"] + [str(y) for y in years]
    tabs = st.tabs(tab_labels)

    # Overview: all years aggregated
    with tabs[0]:
        kpi_section(df_filtered)
        yearly_trend_section(df_filtered)
        yearly_month_comparison_section(df_filtered)
        status_trend_section(df_filtered)

        st.markdown("### Data & SQL")
        sample_table_section(df_filtered)
        sql_reference_section()

    # Year-specific detailed pages
    for idx, year in enumerate(years, start=1):
        df_year = df_filtered[df_filtered["ORDER_DATE"].dt.year == year]
        with tabs[idx]:
            st.subheader(f"Year {year} – detailed breakdown")
            kpi_section(df_year)
            time_series_section(df_year)
            distribution_section(df_year)
            status_priority_comparison_section(df_year)
            value_distribution_section(df_year)


if __name__ == "__main__":
    main()
