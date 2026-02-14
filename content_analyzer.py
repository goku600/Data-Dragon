import os
import google.generativeai as genai
import logging
import time

logger = logging.getLogger(__name__)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not found in environment variables.")

def analyze_news(article_title, article_summary):
    """
    Analyzes a news article to check relevance for UPSC/SSC/Bank exams.
    Returns:
        - A one-line headline if relevant.
        - None if irrelevant.
    """
    if not GOOGLE_API_KEY:
        return None

    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Act as a strict news content filter for a student preparing for UPSC (Civil Services), SSC, and Bank exams in India.
        
        Analyze the following news article:
        Title: {article_title}
        Summary: {article_summary}
        
        Task:
        1. Determine if this news is RELEVANT for the exams mentioned above. 
           - Relevant topics: Government policies, economy, international relations, supreme court verdicts, major appointments, science & tech, environment.
           - Irrelevant topics: Local crime, political gossip/opinions, sports (unless major tournaments), entertainment, trivial accidents.
        
        2. If NOT RELEVANT, return exactly the string "NO".
        
        3. If RELEVANT, rewrite the headline into a single, concise, factual line suitable for current affairs notes. 
           - Do not use markdown (no bold/italics).
           - Do not start with "Relevant" or "Headline:". Just the line.
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if text.upper() == "NO":
            return None
        else:
            return text
            
    except Exception as e:
        logger.error(f"Error analyzing with Gemini: {e}")
        time.sleep(1) 
        return None

def generate_digest_feed(clusters):
    """
    Generates a categorized digest from clusters of articles.
    """
    if not GOOGLE_API_KEY:
        return "Error: Gemini API Key not set."

    # Prepare input text for Gemini
    # Limit to top 20 clusters to avoid token limits if necessary, or just send all if manageable.
    # For now, let's take top 30 clusters.
    input_text = ""
    for i, cluster in enumerate(clusters[:30]):
        input_text += f"\nCluster {i+1}:\n"
        for art in cluster:
            input_text += f"- Title: {art['title']}\n  Link: {art['link']}\n  Source: {art.get('source', 'Unknown')}\n"

    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Act as a senior editor for a UPSC/Civil Services exam preparation portal.
        
        I will provide you with clusters of news articles. Each cluster contains multiple reports on the same event from different sources.
        
        Your Task:
        1. **Filter**: Ignore clusters that are completely irrelevant for UPSC/SSC/Bank exams (e.g., local crime, pure political blame-games, sports trivialities).
        2. **Synthesize**: For each relevant cluster, write a SINGLE "Master Headline" that combines the key facts from all sources in that cluster. 
           - Example: If Source A says "India grows 7%" and Source B says "IMF praises India's reforms", Master Headline: "IMF praises India's reforms; forecasts 7% growth."
           - **Crucial**: Include the LINK to the best 1-2 articles (preferably official sources like PIB/IMF if present) in Markdown format `[Source Name](URL)`.
        3. **Categorize**: Group these Master Headlines under these themes:
           - 🏛️ Polity & Governance
           - 💰 Economy & Banking
           - 🌍 International Relations
           - 🔬 Science & Technology
           - 🌱 Environment
           - 🛡️ Defence & Security
           - 🏫 Society & Education
           - ⚖️ Legal & Constitutional
           
        Format:
        Return the output in clean Markdown.
        
        **Theme Name**
        *   **Master Headline** [Source A](link)
        *   **Master Headline** [Source B](link)
        
        If a theme has no news, do not show it.
        
        Input Data:
        {input_text}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
            
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        return "Failed to generate digest due to an error."
