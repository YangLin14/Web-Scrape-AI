# AI-Web-Scraper
An AI-powered web scraper and data analysis platform using Streamlit, Google Gemini, yfinance, and various data APIs to analyze financial and government contract data.

## Features

The application provides multiple analysis tools through a tabbed interface:

1. **🌐 Web Scraping**: Scrape and analyze content from websites, X (Twitter), Instagram, and government sources
2. **💬 Analysis & Chat**: AI-powered chat interface to analyze scraped content
3. **📊 Politician Trades**: Track and analyze stock trades made by US politicians
4. **📰 News**: Monitor stock market news and politician trading news
5. **🏢 USA Spending**: Analyze federal contracts and their impact on stock prices

## Environment Setup

1. Clone the repository
2. Create and activate a virtual environment named "ai":
   ```bash
   # Create virtual environment
   python -m venv ai
   
   # Activate virtual environment
   # On Windows:
   ai\Scripts\activate
   # On macOS/Linux:
   source ai/bin/activate
   ```

3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your API keys:
   - QUIVER_API_KEY: Your Quiver Quantitative API key
   - GEMINI_API_KEY: Your Google Gemini API key
   - INSTAGRAM_API_KEY: Your Instagram API key
   - X_API_KEY: Your X (Twitter) API key
   - AZURE_API_KEY: Your Azure API key
   - IB configuration (if needed)

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Run the application:
   ```bash
   streamlit run main.py
   ```

## Tab Functionality

### 🌐 Web Scraping
- **Custom URL Scraping**: Enter any website URL to scrape and analyze its content
- **X (Twitter) Scraping**: Scrape tweets from specific accounts or hashtags
- **Instagram Scraping**: Extract posts and data from Instagram accounts
- **Government Website Scraping**: Specialized scraping for government websites

All scraped content is automatically analyzed for financial and trading information.

### 💬 Analysis & Chat
- **AI Chat Assistant**: Ask questions about the scraped content
- **Content Analysis**: View raw scraped content and get AI-generated insights
- **Custom Queries**: Request specific analyses of the data

The chat interface uses Google's Gemini AI to provide intelligent responses about the scraped content.

### 📊 Politician Trades
- **Search Politicians**: Find trading activity for specific US politicians
- **Trading Data Analysis**: View and analyze politicians' stock trades
- **Data Visualization**: See trading patterns and statistics
- **Download Data**: Export trading data as CSV files

This tab connects to the US Senate Financial Disclosure database to track politician trading activity.

### 📰 News
- **Stock Market News**: Search and filter news about specific stocks
- **Politician Trading News**: Find news about politician trading activities
- **News Analysis**: Get AI-generated summaries and insights from news articles
- **Save & Export**: Save news data for later analysis

The news tab has two sub-sections for stock market news and politician trading news.

### 🏢 USA Spending (Federal Contracts)
- **Contract Data**: Search and analyze federal contracts by company and date range
- **Stock Market Impact**: Analyze how contract awards affect stock prices
- **AI Analysis**: Generate detailed AI analysis of specific contracts
- **Timeline Visualization**: View contract awards on an interactive timeline with stock price data

This tab connects to the USA Spending API to fetch real federal contract data and analyze its market impact.

## Interactive Brokers Setup (Optional)

### TWS Workstation Installation
1. Download TWS Workstation:
   - Visit [TWS Installation](https://www.interactivebrokers.com/en/trading/tws.php)
   - Visit [How to Download Trader Workstation](https://www.youtube.com/watch?v=vWEMoxg-V40&list=PLfKEHQhkx9-Z1_BsNTM6pflj7v7dPzZV0) for a step by step guide
   - Click "Download" for your operating system
   - Follow the installation wizard

2. Configure TWS:
   - Launch TWS Workstation
   - Log in with your IB account
   - Go to File > Global Configuration > API > Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Set Socket port to 7497 (default)
   - Check "Read-Only API"

**Important**: TWS Workstation must be running and connected when using the IB API functions in this application.

### TWS API Setup

1. Download the TWS API (IBJts) from Interactive Brokers:
   - Visit [Interactive Brokers TWS API](https://interactivebrokers.github.io/#)
   - Click on "Download" in the API section
   - Download the latest version of "TWS API" for your operating system
   - Accept the license agreement

2. Extract the IBJts files:
   - Extract the downloaded zip file
   - Copy the `IBJts` folder to your project directory

3. Install the IB API Python package:
   ```bash
   cd IBJts/source/pythonclient
   python setup.py install
   ```

## Federal Contracts Analysis

The Federal Contracts Analysis tab provides detailed insights into government contracts:

1. **Contract Data Tab**:
   - Search for contracts by company name (e.g., Lockheed Martin, Boeing)
   - Filter by date range
   - View detailed contract information including award amounts, dates, and agencies

2. **Stock Market Impact Tab**:
   - Analyze how contract awards affect stock prices
   - View average price and volume impact metrics
   - See detailed impact data for each contract

3. **AI Analysis Tab**:
   - Select specific contracts for in-depth AI analysis
   - Generate downloadable HTML reports with contract insights
   - View contract summaries and market implications

4. **Timeline Visualization Tab**:
   - Interactive visualization of stock prices with contract award markers
   - View contract timeline with detailed event information
   - Analyze the relationship between contract awards and stock performance

## Data Storage

The application stores data in the following locations:
- Scraped content: Stored in memory during the session
- Downloaded data: Saved to the `data/` directory
- Analysis reports: Saved to the `reports/` directory

## Troubleshooting

If you encounter issues:
1. Ensure all API keys are correctly set in the `.env` file
2. Check that all dependencies are installed
3. For IB-related features, verify that TWS Workstation is running
4. For web scraping issues, check your internet connection and website accessibility
