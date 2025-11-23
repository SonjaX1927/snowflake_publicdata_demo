# Snowflake Public Data Demo: Orders Analytics Dashboard

一个基于 Snowflake 公共样例数据 **SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS** 的交互式可视化 Demo，使用：

- Snowflake 作为数据源
- Python + Streamlit 构建 Web Dashboard
- Plotly 进行可视化

支持：

- 自定义订单日期范围过滤
- 按订单状态、订单优先级过滤
- 多张可视化图表（时间趋势、分布、热力图等）
- KPI 卡片样式、深色主题、简洁布局

---

## 1. 环境准备

### 1.1 Python & 虚拟环境

建议使用 Python 3.9+。

```bash
cd snowflake_demo
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1.2 Snowflake 账号 & 公共数据

1. 注册并登录 Snowflake（Free Trial 即可）。
2. 在 Web UI 中确保可以访问 sample 数据：

```sql
USE WAREHOUSE WH_DEMO;           -- 或你自己的 warehouse
USE DATABASE SNOWFLAKE_SAMPLE_DATA;
USE SCHEMA TPCH_SF1;

SELECT *
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
LIMIT 10;
```

确认查询正常后，再进行本地连接配置。

---

## 2. 配置 Snowflake 凭据

项目支持两种方式配置 Snowflake 连接信息：

### 2.1 使用 Streamlit secrets（推荐，用于部署 / 本地）

在项目根目录创建 `.streamlit/secrets.toml` 文件：

```toml
[snowflake]
user = "YOUR_USER"
password = "YOUR_PASSWORD"
account = "YOUR_ACCOUNT"          # 例如 abcd-xy12345
warehouse = "WH_DEMO"
database = "SNOWFLAKE_SAMPLE_DATA"
schema = "TPCH_SF1"
role = "ACCOUNTADMIN"
```

> 你也可以复制 `.streamlit/secrets.toml.example` 后修改内容。

### 2.2 使用环境变量（本地开发）

设置以下环境变量：

```bash
export SNOWFLAKE_USER="YOUR_USER"
export SNOWFLAKE_PASSWORD="YOUR_PASSWORD"
export SNOWFLAKE_ACCOUNT="YOUR_ACCOUNT"
export SNOWFLAKE_WAREHOUSE="WH_DEMO"
export SNOWFLAKE_DATABASE="SNOWFLAKE_SAMPLE_DATA"
export SNOWFLAKE_SCHEMA="TPCH_SF1"
export SNOWFLAKE_ROLE="ACCOUNTADMIN"
```

`snowflake_query.py` 会优先读取 `st.secrets["snowflake"]`，如果不存在就回退到环境变量。

---

## 3. 本地运行

在项目根目录执行：

```bash
streamlit run app.py
```

浏览器中打开终端输出的本地地址（通常是 `http://localhost:8501`），即可看到 Dashboard：

- 顶部 KPI：订单数量、订单总金额、平均订单金额
- 多张可视化图：
  - 每月订单金额趋势（面积图）
  - 每月订单数量（柱状图）
  - 按订单状态分布（柱状图）
  - 按订单优先级分布（柱状图）
  - 状态 × 优先级 订单金额热力图
- 订单明细样例表
- 展示使用的 SQL 示例（折叠面板中）

---

## 4. 部署建议（可选）

如果要做 Project Demo 对外展示，推荐使用 **Streamlit Community Cloud**：

1. 将本项目推送到 GitHub 公开仓库。
2. 在 https://streamlit.io/ 上登录并创建新应用，选择：
   - 你的 GitHub 仓库
   - 分支（如 `main`）
   - 入口脚本：`app.py`
3. 在应用设置的 `Secrets` 中粘贴与本地 `.streamlit/secrets.toml` 相同的配置。
4. 部署完成后即可获得一个公开可访问的 URL，适合作为项目展示链接。

---

## 5. 结构概览

```text
snowflake_demo/
  app.py                 # Streamlit Web App（多张可视化 + 布局设计）
  snowflake_query.py     # Snowflake 查询封装
  requirements.txt       # 依赖
  README.md
  .streamlit/
    config.toml          # 主题配置（深色风格）
    secrets.toml.example # Snowflake 配置示例（不包含真实密钥）
```

你可以在此基础上继续扩展：增加更多维度分析、加入其他 Snowflake 公共数据集、或接入你自己的业务数据。
