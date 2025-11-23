## 📊 Snowflake Public Orders Analytics Demo

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-ff4b4b?logo=streamlit)](https://streamlit.io/)
[![Snowflake](https://img.shields.io/badge/Snowflake-TPCH__SF1-29b5e8?logo=snowflake)](https://www.snowflake.com/)

This repository contains a lightweight analytics demo built on top of Snowflake public sample data. It is intended as an introductory example for working with Snowflake as a data warehouse and building simple BI-style dashboards.

- **Data source**: `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS`
- **Tech stack**: Python, Streamlit, Plotly, Snowflake Python connector
- **Use case**: Explore historical orders, revenue and order mix by status/priority

The main app (`app.py`) connects to Snowflake, queries the TPCH orders table, and exposes an interactive dashboard that lets you:

- Filter by order date range, status (F = Filled, O = Open, P = Pending) and priority
- Inspect **overview KPIs** (total revenue, order volume, AOV, median, P90, orders per day)
- Analyze **yearly trends** and **year-over-year growth**
- Compare **seasonality** by looking at the same month across multiple years
- Break down the **status / priority mix** and typical order size by segment
- Explore the **distribution of order values** and outliers

Each chart includes a short caption explaining why that view is useful from an analytics perspective, making the project suitable as a small portfolio piece or internal demo for Snowflake-based reporting.
