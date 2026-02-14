import gspread

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentStorage:
    def __init__(self):
        self.client = None
        self.sheet = None
        self.connect()

    def connect(self):
        """Connects to Google Sheets using credentials from env var."""
        try:
            creds_json = os.getenv("GOOGLE_VARS")
            if not creds_json:
                logger.error("GOOGLE_VARS environment variable not found.")
                return

            # Check if it's a file path or JSON content
            if os.path.exists(creds_json):
                 self.client = gspread.service_account(filename=creds_json)
            else:
                # Parse the JSON string
                if isinstance(creds_json, str):
                    creds_dict = json.loads(creds_json)
                else:
                    creds_dict = creds_json
                
                # FIX: Handle newline escaping issues in private_key (common in Render/Heroku)
                if 'private_key' in creds_dict:
                    creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')

                self.client = gspread.service_account_from_dict(creds_dict)
            
            # Open the sheet
            sheet_name = os.getenv("GOOGLE_SHEET_NAME", "NewsAggregatorBot")
            try:
                self.sheet = self.client.open(sheet_name).sheet1
            except gspread.SpreadsheetNotFound:
                logger.error(f"Spreadsheet '{sheet_name}' not found. Make sure to share it with the service account email.")
                
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            # Raise to see full trace in logs if needed
            # raise e

    def get_existing_links(self):
        """Fetches all existing links from the sheet (Column 3)."""
        if not self.sheet:
            return set()
        try:
            # Column 3 contains the links
            links = self.sheet.col_values(3)
            # Remove header if present (assuming first row is header)
            if links and links[0] == 'Link':  # Adjust 'Link' if your header is different
                return set(links[1:])
            return set(links)
        except Exception as e:
            logger.error(f"Error fetching tokens: {e}")
            return set()

    def add_article(self, link, headline, published_date=""):
        """Adds a processed article to the sheet."""
        if not self.sheet:
            return
        
        try:
            # Columns: Processed Time, Published Time, Link, Headline
            row = [str(datetime.now()), published_date, link, headline]
            self.sheet.append_row(row)
        except Exception as e:
            logger.error(f"Error adding article: {e}")

    def get_recent_headlines(self, limit=50):
        """Fetches the last 'limit' headlines to check for duplicates."""
        if not self.sheet:
            return []
        try:
            # Assuming Headline is the 4th column (index 4)
            # get_all_values is expensive for large sheets, but okay for start.
            # Optimization: get only last N rows.
            # But gspread doesn't support 'tail' easily without knowing row count.
            # We will grab all and slice for now (assuming < 1000 rows typically for a few weeks)
            # Or better: just grab the last column data? No, row count needed.
            
            all_values = self.sheet.get_all_values()
            if not all_values:
                return []
                
            # Skip header if exists (usually row 1)
            data = all_values[1:] 
            
            # Slice last 'limit'
            recent = data[-limit:]
            
            # Extract headlines (col index 3 -> 4th column)
            headlines = [row[3] for row in recent if len(row) > 3]
            return headlines
        except Exception as e:
            logger.error(f"Error fetching recent headlines: {e}")
            return []
