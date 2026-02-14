import gspread
from oauth2client.service_account import ServiceAccountCredentials
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
            # We expect the JSON content to be in the GOOGLE_VARS env variable
            creds_json = os.getenv("GOOGLE_VARS")
            if not creds_json:
                logger.error("GOOGLE_VARS environment variable not found.")
                return

            creds_dict = json.loads(creds_json)
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            self.client = gspread.authorize(creds)
            
            # Open the sheet - User must share the sheet with the service account email
            sheet_name = os.getenv("GOOGLE_SHEET_NAME", "NewsAggregatorBot")
            try:
                self.sheet = self.client.open(sheet_name).sheet1
            except gspread.SpreadsheetNotFound:
                logger.error(f"Spreadsheet '{sheet_name}' not found. Make sure to create it and share with service account.")
                # Logic to create if not exists could go here, but requires Drive API permissions usually.
                
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")

    def article_exists(self, link):
        """Checks if a link has already been processed."""
        if not self.sheet:
            return False
        try:
            # Reading all links from the first column (assuming simple 1-col storage for now or searching)
            # To be efficient, we might cache this or use find. 
            # find is better.
            cell = self.sheet.find(link)
            return cell is not None
        except gspread.CellNotFound:
            return False
        except Exception as e:
            logger.error(f"Error checking existence: {e}")
            return False

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
