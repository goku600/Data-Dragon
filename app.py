import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Import our modules
import news_fetcher
import content_analyzer
import storage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
db = storage.ContentStorage()

# Initialize Flask app for Render keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# Telegram Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your Exam Prep News Bot. Send /news to get the latest relevant updates.")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Fetching and analyzing news based on your exam preferences... This may take a minute.")

    # 1. Fetch News (Deduplicated by fetcher)
    articles = news_fetcher.fetch_news()
    if not articles:
        await update.message.reply_text("No news found from sources at the moment.")
        return

    # 2. Get Recent Headlines for Cross-Check
    recent_headlines = db.get_recent_headlines(limit=50)

    new_articles_count = 0
    
    # 3. Process Articles
    # 3. Process Articles
    existing_links = db.get_existing_links()
    
    for article in articles:
        link = article['link']
        title = article['title']
        summary = article['summary']

        # Link-based Deduplication (Exact Match)
        if link in existing_links:
            continue

        # Analyze with Gemini
        analysis = content_analyzer.analyze_news(title, summary)
        
        if analysis and analysis != "NO":
            # Semantic/Fuzzy Deduplication (Check against recent history)
            is_semantic_duplicate = False
            for old_headline in recent_headlines:
                if news_fetcher.is_similar(analysis, old_headline):
                    is_semantic_duplicate = True
                    break
            
            if is_semantic_duplicate:
                logger.info(f"Skipping semantic duplicate: {analysis}")
                continue

            # It's relevant and unique!
            message = f"📰 {analysis}\n🔗 {link}"
            try:
                await update.message.reply_text(message)
                db.add_article(link, analysis, article.get('published', ''))
                # Add to local lists
                existing_links.add(link)
                recent_headlines.append(analysis)
                new_articles_count += 1
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                
            # Anti-Spam: Stop after sending 7 updates
            if new_articles_count >= 7:
                 await update.message.reply_text("Stopped after 7 updates to avoid spamding. /news again for more.")
                 break
        
    if new_articles_count == 0:
        await update.message.reply_text("Checked latest news. No *new* relevant updates found since last check.")
    else:
        await update.message.reply_text(f"✅ Implementation complete. Sent {new_articles_count} new relevant articles.")

async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🍳 Cooking up your Daily Master Digest... This analyzes all current news sources. Please wait (approx 10-20s).")
    
    # 1. Fetch All (Raw)
    articles = news_fetcher.fetch_news()
    if not articles:
        await update.message.reply_text("No news found to digest.")
        return

    # 2. Cluster
    all_clusters = news_fetcher.cluster_articles(articles)
    
    # NEW: Filter out clusters that have already been sent/processed
    # We check if the "representative" (first) article of the cluster is in DB.
    existing_links = db.get_existing_links()
    
    new_clusters = []
    for cluster in all_clusters:
        # Check top 3 articles in cluster to be safe, if any match, skip cluster
        # This prevents sending the same story just because the top link changed slightly
        is_old_story = False
        for art in cluster[:3]:
            if art['link'] in existing_links:
                is_old_story = True
                break
        
        if not is_old_story:
            new_clusters.append(cluster)
            
    if not new_clusters:
        await update.message.reply_text("All current important news has already been sent or digested! ✅")
        return

    # 3. Generate Digest via Gemini
    digest_text = content_analyzer.generate_digest_feed(new_clusters)
    
    # 4. Save to Database (Mark as processed)
    # We assume if it was in 'new_clusters', it's included in the digest.
    count = 0
    
    for cluster in new_clusters:
        for art in cluster:
            # We save the original title since we don't have the Master Headline mapped 1:1 easily here
            # This is sufficient for the 'article_exists' check later.
            if art['link'] not in existing_links:
                db.add_article(art['link'], f"[Digest] {art['title']}", art.get('published', ''))
                existing_links.add(art['link'])
                count += 1
    
    logger.info(f"Marked {count} articles as processed from digest.")

    # 5. Send (Split if too long)
    # Telegram limit is 4096 chars.
    if len(digest_text) > 4000:
        # Naive split by paragraphs
        parts = digest_text.split('\n\n')
        current_msg = ""
        for part in parts:
            if len(current_msg) + len(part) < 4000:
                current_msg += part + "\n\n"
            else:
                await update.message.reply_text(current_msg, parse_mode='Markdown')
                current_msg = part + "\n\n"
        if current_msg:
            await update.message.reply_text(current_msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(digest_text, parse_mode='Markdown')

def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start Telegram Bot
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", get_news))
    application.add_handler(CommandHandler("digest", digest))

    logger.info("Bot is polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
