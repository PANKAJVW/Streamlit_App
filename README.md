# data_analytics_projects

This project includes a Snake game and a Streamlit intake request tracker.

## Streamlit app

1. Open a terminal in this project folder.
2. Install the dependencies using the requirements file.
3. Copy the example environment file and add your Snowflake details if you want direct database writes.
4. Start the app with Streamlit.

The app includes:
- A custom intake form for process requests
- Snowflake persistence with a local CSV fallback
- A KPI dashboard and status roadmap
- CSV export for all collected records

If Snowflake credentials are not configured, the app will still work in local mode and save requests in the data folder.
