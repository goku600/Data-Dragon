# Telegram News Aggregator for Exam Prep

A smart news bot that aggregates, filters, and synthesizes news from government sources (PIB, DD News) and major newspapers for UPSC/SSC/Bank exam aspirants.

## Features
- **Universal Search**: Monitors official sources (MEA, RBI, ISRO) and custom Google News queries.
- **Smart Deduplication**: Prioritizes official sources over private media; clusters similar stories.
- **AI Analysis**: Uses Google Gemini to filter irrelevant news (crime, sports, gossip).
- **Daily Digest**: `/digest` command generates a synthesized master report categorized by Ministry/Theme.
- **Persistence**: Uses Google Sheets to store history and prevent duplicate alerts.

## Setup

1.  **Clone & Install**
    ```bash
    git clone <your-repo-url>
    cd news_aggregator
    pip install -r requirements.txt
    ```

2.  **Environment Variables**
    Create a `.env` file (see `.env.example`) with:
    - `TELEGRAM_BOT_TOKEN`: From @BotFather.
    - `GOOGLE_API_KEY`: From Google AI Studio.
    - `GOOGLE_VARS`: Your Google Service Account JSON (minified).
    - `GOOGLE_SHEET_NAME`: Name of your Google Sheet.

3.  **Run Locally**
    ```bash
    python main.py
    ```

## Deployment
Ready for deployment on **Render**.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`

See `deployment_guide.md` for full details.
