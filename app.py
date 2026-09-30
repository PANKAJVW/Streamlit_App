import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import snowflake.connector


load_dotenv()

APP_DIR = Path(__file__).resolve().parent
LOCAL_DATA_PATH = APP_DIR / "data" / "intake_requests.csv"
STREAMLIT_TITLE = "Intake Request Hub"
STATUS_ORDER = ["New", "Onhold", "Inprocess", "Completed"]


st.set_page_config(
    page_title=STREAMLIT_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0f172a;
            --panel: #111827;
            --card: #1f2937;
            --primary: #38bdf8;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text: #e2e8f0;
            --muted: #94a3b8;
        }

        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #111827 40%, #1e293b 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3, h4 {
            color: #f8fafc !important;
        }

        div[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.95);
        }

        .stMetric {
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 0.8rem;
            padding: 0.8rem 1rem;
        }

        .status-badge {
            display: inline-block;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            color: white;
            text-align: center;
        }

        .roadmap-card {
            background: rgba(31, 41, 55, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 1rem;
            padding: 1rem;
            min-height: 160px;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.2);
        }

        .roadmap-card h4 {
            margin-top: 0;
            margin-bottom: 0.75rem;
        }

        .dataframe-container {
            background: rgba(15, 23, 42, 0.7);
            border-radius: 0.8rem;
            padding: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_snowflake_config() -> dict | None:
    required_fields = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
    ]

    config = {field: os.getenv(field) for field in required_fields}
    if all(config.values()):
        config.update(
            {
                "database": os.getenv("SNOWFLAKE_DATABASE", "DEMO_DB"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                "table": os.getenv("SNOWFLAKE_TABLE", "INTAKE_REQUESTS"),
                "role": os.getenv("SNOWFLAKE_ROLE"),
            }
        )
        return config
    return None


def ensure_local_storage() -> None:
    LOCAL_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOCAL_DATA_PATH.exists():
        pd.DataFrame(columns=[
            "process_name",
            "description",
            "team_name",
            "request_date",
            "benefit",
            "ask",
            "efforts_required",
            "assigned_to",
            "stakeholder_name",
            "ba_name",
            "tech_stack",
            "developer_name",
            "manager_name",
            "status",
        ]).to_csv(LOCAL_DATA_PATH, index=False)


def normalize_status(value: str) -> str:
    if value is None:
        return "New"
    normalized = str(value).strip().lower().replace(" ", "")
    mapping = {
        "new": "New",
        "onhold": "Onhold",
        "inprocess": "Inprocess",
        "completed": "Completed",
        "in_progress": "Inprocess",
        "in-progress": "Inprocess",
        "in progress": "Inprocess",
    }
    return mapping.get(normalized, "New")


def load_local_records() -> pd.DataFrame:
    ensure_local_storage()
    df = pd.read_csv(LOCAL_DATA_PATH)
    if df.empty:
        return pd.DataFrame(columns=[
            "process_name",
            "description",
            "team_name",
            "request_date",
            "benefit",
            "ask",
            "efforts_required",
            "assigned_to",
            "stakeholder_name",
            "ba_name",
            "tech_stack",
            "developer_name",
            "manager_name",
            "status",
        ])
    df["status"] = df["status"].apply(normalize_status)
    return df


def save_local_record(record: dict) -> None:
    ensure_local_storage()
    df = load_local_records()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df = df[[
        "process_name",
        "description",
        "team_name",
        "request_date",
        "benefit",
        "ask",
        "efforts_required",
        "assigned_to",
        "stakeholder_name",
        "ba_name",
        "tech_stack",
        "developer_name",
        "manager_name",
        "status",
    ]]
    df.to_csv(LOCAL_DATA_PATH, index=False)


def save_to_snowflake(record: dict) -> tuple[bool, str]:
    config = get_snowflake_config()
    if not config:
        return False, "Snowflake environment variables are not configured."

    try:
        conn = snowflake.connector.connect(
            account=config["SNOWFLAKE_ACCOUNT"],
            user=config["SNOWFLAKE_USER"],
            password=config["SNOWFLAKE_PASSWORD"],
            warehouse=config["SNOWFLAKE_WAREHOUSE"],
            database=config["database"],
            schema=config["schema"],
            role=config["role"],
        )
        table_name = config["table"]

        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    process_name VARCHAR,
                    description VARCHAR,
                    team_name VARCHAR,
                    request_date DATE,
                    benefit VARCHAR,
                    ask VARCHAR,
                    efforts_required VARCHAR,
                    assigned_to VARCHAR,
                    stakeholder_name VARCHAR,
                    ba_name VARCHAR,
                    tech_stack VARCHAR,
                    developer_name VARCHAR,
                    manager_name VARCHAR,
                    status VARCHAR
                )
                """
            )
            cur.execute(
                f"""
                INSERT INTO "{table_name}" (
                    process_name,
                    description,
                    team_name,
                    request_date,
                    benefit,
                    ask,
                    efforts_required,
                    assigned_to,
                    stakeholder_name,
                    ba_name,
                    tech_stack,
                    developer_name,
                    manager_name,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record["process_name"],
                    record["description"],
                    record["team_name"],
                    record["request_date"],
                    record["benefit"],
                    record["ask"],
                    record["efforts_required"],
                    record["assigned_to"],
                    record["stakeholder_name"],
                    record["ba_name"],
                    record["tech_stack"],
                    record["developer_name"],
                    record["manager_name"],
                    normalize_status(record["status"]),
                ),
            )
            conn.commit()

        return True, "Saved successfully to Snowflake."
    except Exception as exc:  # pragma: no cover - runtime connectivity guard
        return False, f"Snowflake save failed: {exc}"


def load_from_snowflake() -> pd.DataFrame:
    config = get_snowflake_config()
    if not config:
        return load_local_records()

    try:
        conn = snowflake.connector.connect(
            account=config["SNOWFLAKE_ACCOUNT"],
            user=config["SNOWFLAKE_USER"],
            password=config["SNOWFLAKE_PASSWORD"],
            warehouse=config["SNOWFLAKE_WAREHOUSE"],
            database=config["database"],
            schema=config["schema"],
            role=config["role"],
        )
        query = f'SELECT * FROM "{config["table"]}" ORDER BY request_date DESC'
        df = pd.read_sql(query, conn)
        conn.close()
        if df.empty:
            return pd.DataFrame(columns=[
                "process_name",
                "description",
                "team_name",
                "request_date",
                "benefit",
                "ask",
                "efforts_required",
                "assigned_to",
                "stakeholder_name",
                "ba_name",
                "tech_stack",
                "developer_name",
                "manager_name",
                "status",
            ])
        df["status"] = df["status"].apply(normalize_status)
        return df
    except Exception:
        return load_local_records()


def render_status_badge(status: str) -> str:
    color_map = {
        "New": "background: #38bdf8;",
        "Onhold": "background: #f59e0b;",
        "Inprocess": "background: #8b5cf6;",
        "Completed": "background: #22c55e;",
    }
    style = color_map.get(status, "background: #64748b;")
    return f'<span class="status-badge" style="{style}">{status}</span>'


def render_dashboard(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No intake requests have been recorded yet.")
        return

    df = df.copy()
    df["status"] = df["status"].apply(normalize_status)

    total = len(df)
    completed = int((df["status"] == "Completed").sum())
    in_progress = int((df["status"] == "Inprocess").sum())
    on_hold = int((df["status"] == "Onhold").sum())
    new = int((df["status"] == "New").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Requests", total)
    c2.metric("In Process", in_progress)
    c3.metric("Completed", completed)
    c4.metric("On Hold", on_hold)

    st.markdown("### Roadmap Status")
    roadmap_cols = st.columns(4)
    for idx, status in enumerate(STATUS_ORDER):
        with roadmap_cols[idx]:
            filtered = df[df["status"] == status]
            st.markdown(f"<div class='roadmap-card'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{status}</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='status-badge' style='{color_map(status)}'>{status}</div>", unsafe_allow_html=True)
            st.caption(f"{len(filtered)} items")
            for _, row in filtered.head(3).iterrows():
                st.write(f"• {row['process_name']}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Request Table")
    display_df = df.copy()
    display_df = display_df[[
        "process_name",
        "team_name",
        "request_date",
        "assigned_to",
        "developer_name",
        "manager_name",
        "status",
    ]]

    def style_status(value: str) -> str:
        bg = color_map(value)
        return f"background-color: {bg.replace('background: ', '').replace(';', '')}; color: white; font-weight: 600;"

    styled_df = display_df.style.applymap(
        lambda v: style_status(v) if isinstance(v, str) and v in STATUS_ORDER else "",
        subset=["status"],
    )
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    csv_data = df.to_csv(index=False)
    st.download_button(
        label="Download records as CSV",
        data=csv_data,
        file_name="intake_requests.csv",
        mime="text/csv",
    )


def color_map(status: str) -> str:
    color_map_values = {
        "New": "background: #38bdf8;",
        "Onhold": "background: #f59e0b;",
        "Inprocess": "background: #8b5cf6;",
        "Completed": "background: #22c55e;",
    }
    return color_map_values.get(status, "background: #64748b;")


def main() -> None:
    apply_custom_theme()
    st.title("📈 Intake Request Tracker")
    st.caption("Capture initiative intake requests and monitor delivery status in one dashboard.")

    with st.sidebar:
        st.header("Configuration")
        snowflake_status = get_snowflake_config()
        if snowflake_status:
            st.success("Snowflake connection is configured.")
            st.caption("Connected database: " + snowflake_status["database"])
        else:
            st.warning("Snowflake credentials are not set. The app is using local CSV storage until configured.")
        st.markdown("""
        Add these environment variables in a .env file:
        - SNOWFLAKE_ACCOUNT
        - SNOWFLAKE_USER
        - SNOWFLAKE_PASSWORD
        - SNOWFLAKE_WAREHOUSE
        - SNOWFLAKE_DATABASE
        - SNOWFLAKE_SCHEMA
        - SNOWFLAKE_TABLE
        """)

    form = st.form("intake_form")
    with form:
        st.subheader("Add New Intake Request")
        c1, c2 = st.columns(2)
        with c1:
            process_name = st.text_input("Name of Process")
            description = st.text_area("Description")
            team_name = st.text_input("Team Name")
            request_date = st.date_input("Date")
            benefit = st.text_area("Benefit")
            ask = st.text_area("Ask")
        with c2:
            efforts_required = st.text_input("Efforts Required")
            assigned_to = st.text_input("Assigned To")
            stakeholder_name = st.text_input("Stakeholder Name")
            ba_name = st.text_input("BA Name")
            tech_stack = st.text_input("Tech Stack")
            developer_name = st.text_input("Developer Name")
            manager_name = st.text_input("Manager Name")
            status = st.selectbox("Status", options=STATUS_ORDER)

        submitted = st.form_submit_button("Save Request")

    if submitted:
        required_fields = [
            process_name,
            description,
            team_name,
            benefit,
            ask,
            efforts_required,
            assigned_to,
            stakeholder_name,
            ba_name,
            tech_stack,
            developer_name,
            manager_name,
        ]
        if any(value is None or str(value).strip() == "" for value in required_fields):
            st.error("Please fill in all required fields before submitting the request.")
            return

        record = {
            "process_name": process_name.strip(),
            "description": description.strip(),
            "team_name": team_name.strip(),
            "request_date": request_date.isoformat(),
            "benefit": benefit.strip(),
            "ask": ask.strip(),
            "efforts_required": efforts_required.strip(),
            "assigned_to": assigned_to.strip(),
            "stakeholder_name": stakeholder_name.strip(),
            "ba_name": ba_name.strip(),
            "tech_stack": tech_stack.strip(),
            "developer_name": developer_name.strip(),
            "manager_name": manager_name.strip(),
            "status": status,
        }

        snowflake_ok, snowflake_message = save_to_snowflake(record)
        save_local_record(record)

        if snowflake_ok:
            st.success(f"{snowflake_message}")
        else:
            st.warning(f"{snowflake_message} The request was saved locally as a fallback.")

        st.balloons()

    df = load_from_snowflake()
    render_dashboard(df)


if __name__ == "__main__":
    main()
