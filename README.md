# AI-Web-Scraper
An AI web scraper using ollama, brightdata, selenium and other libraries.

## Environment Setup

1. Clone the repository
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API keys:
   - QUIVER_API_KEY: Your Quiver Quantitative API key
   - GEMINI_API_KEY: Your Google Gemini API key
   - INSTAGRAM_API_KEY: Your Instagram API key
   - X_API_KEY: Your X (Twitter) API key
   - AZURE_API_KEY: Your Azure API key
   - IB configuration (if needed)

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Security Notes

- Never commit `.env` file to version control
- Keep your API keys secure and rotate them regularly
- Use environment variables for all sensitive information

## Setup
1. Copy `.env.example` to `.env`
2. Add your API keys to `.env`
3. Never commit `.env` file# Web-Scrape-AI
