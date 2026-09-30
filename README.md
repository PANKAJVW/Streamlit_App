# Intake Request Tracker

A Streamlit application for collecting process-intake requests and monitoring their delivery status. Requests can be written to Snowflake and are also kept in a local CSV file.

## Features

- Intake form for process details, team, date, benefit, ask, effort, ownership, stakeholders, and technology stack.
- Required-field validation before submission.
- Snowflake table creation and request inserts when Snowflake is configured.
- Local CSV persistence at `data/intake_requests.csv`.
- Dashboard metrics and a roadmap grouped by status: **New**, **Onhold**, **Inprocess**, and **Completed**.
- Request table and downloadable CSV export.
- Local CSV fallback when Snowflake is not configured or cannot be reached.

## Requirements

- Python 3.10 or later
- Packages listed in `requirements.txt`
- Snowflake account details only if you want to use Snowflake

## Setup on Windows

Open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

If PowerShell prevents virtual-environment activation, allow it for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Configure Snowflake (optional)

The app works without Snowflake credentials. To enable Snowflake writes, copy the example file and edit the values:

```powershell
Copy-Item .env.example .env
```

Set these required values in `.env`:

```dotenv
SNOWFLAKE_ACCOUNT=your_account_name
SNOWFLAKE_USER=your_user_name
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
```

Optional settings and their defaults:

| Variable | Default |
| --- | --- |
| `SNOWFLAKE_DATABASE` | `DEMO_DB` |
| `SNOWFLAKE_SCHEMA` | `PUBLIC` |
| `SNOWFLAKE_TABLE` | `INTAKE_REQUESTS` |
| `SNOWFLAKE_ROLE` | No role specified |

The database and schema must already exist and be accessible to the configured user. The app creates the configured table if it does not already exist. Keep `.env` private and never commit Snowflake credentials.

## Run the app

With the virtual environment activated, start Streamlit:

```powershell
streamlit run app.py
```

Open the local URL printed in the terminal (usually `http://localhost:8501`). Stop the app with **Ctrl+C** in the terminal.

## Data behavior

- Every accepted request is written to `data/intake_requests.csv`.
- When Snowflake is configured, the app also attempts to insert the request into the configured Snowflake table.
- If Snowflake is not configured or a write fails, the app reports the issue and retains the local CSV copy.
- Dashboard data is read from Snowflake when it can be reached; otherwise, the app uses the local CSV file.
- The dashboard's **Download records as CSV** button exports the records currently displayed by the app.

The CSV file may contain real request information. Review it before sharing or committing it to source control.

## Project files

```text
.
├── app.py                 # Streamlit application
├── requirements.txt       # Python dependencies
├── .env.example           # Example Snowflake configuration
└── data/
    ├── .gitkeep           # Keeps the data directory in source control
    └── intake_requests.csv # Local request storage
```
