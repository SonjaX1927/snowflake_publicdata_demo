import os
from typing import Any, Dict, Optional

import pandas as pd
import snowflake.connector
import streamlit as st


def _get_connection_params() -> Dict[str, Any]:
    """Read Snowflake connection configuration from Streamlit secrets or env vars."""

    # Preferred: Streamlit Cloud / local .streamlit/secrets.toml
    if "snowflake" in st.secrets:
        s = st.secrets["snowflake"]
        return dict(
            user=s["user"],
            password=s["password"],
            account=s["account"],
            warehouse=s.get("warehouse", "WH_DEMO"),
            database=s.get("database", "SNOWFLAKE_SAMPLE_DATA"),
            schema=s.get("schema", "TPCH_SF1"),
            role=s.get("role", "ACCOUNTADMIN"),
        )

    # Fallback: environment variables (local development)
    try:
        return dict(
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_DEMO"),
            database=os.getenv("SNOWFLAKE_DATABASE", "SNOWFLAKE_SAMPLE_DATA"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "TPCH_SF1"),
            role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        )
    except KeyError as exc:
        missing = exc.args[0]
        raise RuntimeError(
            f"Missing Snowflake configuration for '{missing}'. "
            "Provide it via st.secrets['snowflake'] or environment variables."
        ) from exc


def run_query(sql: str, params: Optional[list] = None) -> pd.DataFrame:
    """Execute a SQL query against Snowflake and return the result as DataFrame."""
    conn_params = _get_connection_params()
    conn = snowflake.connector.connect(**conn_params)

    try:
        cur = conn.cursor()
        try:
            warehouse = conn_params.get("warehouse")
            if warehouse:
                cur.execute(f'USE WAREHOUSE "{warehouse}"')

            database = conn_params.get("database")
            if database:
                cur.execute(f'USE DATABASE "{database}"')

            schema = conn_params.get("schema")
            if schema:
                cur.execute(f'USE SCHEMA "{schema}"')
        finally:
            cur.close()

        df = pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

    return df
