import os
import glob
import pandas as pd
from gemini_helper import get_gemini_response
import matplotlib.pyplot as plt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import networkx as nx

def load_csv_files(directory="data"):
    """
    Loads CSV files from the specified directory and categorizes them based on
    their filenames into:
      - 'politician_trades'
      - 'news'
      - 'usa_spending'
    """
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    categorized_files = {}
    for file in csv_files:
        basename = os.path.basename(file).lower()
        if "politician_trades" in basename:
            categorized_files.setdefault("politician_trades", []).append(file)
        elif "news" in basename:
            categorized_files.setdefault("news", []).append(file)
        elif "usa_spending" in basename or "federal_contracts" in basename:
            categorized_files.setdefault("usa_spending", []).append(file)
        else:
            categorized_files.setdefault("other", []).append(file)
    return categorized_files

def read_csv_as_text(file_path):
    """
    Reads the CSV file content as a text string.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def combine_csv_data(data_files):
    """
    Combines the content of CSV files from each category into a single text body.
    For each file, it adds a header with the filename and limits the excerpt
    to 1000 characters (to keep the prompt from being too large).
    """
    combined_text = ""
    for category, files in data_files.items():
        combined_text += f"=== {category.upper()} DATA ===\n"
        for file in files:
            combined_text += f"File: {os.path.basename(file)}\n"
            content = read_csv_as_text(file)
            # Optionally limit content per file for prompt brevity
            excerpt = content[:1000]
            combined_text += excerpt
            if len(content) > 1000:
                combined_text += "\n... (truncated)\n"
            combined_text += "\n-----------------------------------\n"
    return combined_text

def run_data_analysis(combined_data_text):
    """
    Passes the combined CSV data to the analytic AI model.
    The query asks the AI to analyze the CSV data across all categories,
    look for trends, patterns, anomalies, and then provide actionable insights.
    """
    query = (
        "Analyze the following CSV data, which includes Politician Trades data, "
        "News data, and USA Spending data. Identify key trends, patterns, outliers, "
        "and provide actionable insights and recommendations for further investigation. "
        "Summarize your analysis in a concise report."
    )
    
    # Call the analytic AI model (assumed to be implemented via get_gemini_response)
    response = get_gemini_response(combined_data_text, query)
    return response

def main():
    # Load CSV files grouped by their category
    data_files = load_csv_files("data")
    print("Loaded CSV files by category:")
    for category, files in data_files.items():
        print(f"{category}: {files}")
    
    # Combine the CSV contents into one text body for analysis
    combined_data_text = combine_csv_data(data_files)
    
    # Run the data analysis with the analytic AI model
    analysis_report = run_data_analysis(combined_data_text)
    
    # Output the analysis report
    print("\n\n===== ANALYSIS REPORT =====\n")
    print(analysis_report)

    # Additional Detailed Analysis Section
    trades_file = "data/politician_trades_latest.csv"
    news_file = "data/stock_news_latest.csv"
    spending_file = "data/federal_contracts_latest.csv"
    
    if os.path.exists(trades_file) and os.path.exists(news_file) and os.path.exists(spending_file):
        # Read datasets with date parsing
        trades = pd.read_csv(trades_file, parse_dates=["date"])
        news = pd.read_csv(news_file, parse_dates=["published_date"])
        spending = pd.read_csv(spending_file, parse_dates=["awarded_date"])
        
        # Resample trades and spending data to daily frequency
        trades_daily = trades.set_index("date").resample("D").count()
        spending_daily = spending.set_index("awarded_date").resample("D").count()
        
        # Plot trading volume and spending events over time
        plt.figure(figsize=(12, 6))
        plt.plot(trades_daily.index, trades_daily["trader"], label="Daily Trades")
        plt.plot(spending_daily.index, spending_daily["company"], label="Daily Contracts Awarded")
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.title("Time Series Analysis of Trades and Federal Contracts")
        plt.legend()
        plt.show()
        
        # Filter for trades related to Senator Carper or his spouse
        insider_trades = trades[trades["trader"].str.contains("Carper", case=False, na=False)]
        print("Insider Trades Summary:")
        print(insider_trades.describe())
        print(insider_trades.head())
        
        # Initialize VADER sentiment analyzer
        analyzer = SentimentIntensityAnalyzer()
        def get_sentiment(text):
            scores = analyzer.polarity_scores(text)
            return scores["compound"]
        
        # Apply sentiment analysis on news article content
        news["sentiment"] = news["full_content"].apply(get_sentiment)
        print("News Sentiment Summary:")
        print(news["sentiment"].describe())
        
        # Additional Sentiment Analysis: Plot daily average sentiment of news articles
        news_daily_sentiment = news.set_index("published_date")["sentiment"].resample("D").mean()
        plt.figure(figsize=(12, 6))
        plt.plot(news_daily_sentiment.index, news_daily_sentiment, marker="o", color="purple", label="Daily Average Sentiment")
        plt.xlabel("Date")
        plt.ylabel("Average Sentiment")
        plt.title("Daily News Sentiment Analysis")
        plt.legend()
        plt.show()
        
        # Network Analysis: Build a graph of trades (politicians vs. companies)
        trades_simple = pd.read_csv(trades_file)  # re-read without date parsing if needed
        contracts = pd.read_csv(spending_file)
        G = nx.Graph()
        for trader in trades_simple["trader"].unique():
            G.add_node(trader, type="politician")
        for company in trades_simple["stock"].unique():
            G.add_node(company, type="company")
        for _, row in trades_simple.iterrows():
            G.add_edge(row["trader"], row["stock"])
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(G, k=0.5)
        nx.draw(G, pos, with_labels=True, node_color="#A0CBE2", edge_color="#BB0000", node_size=500)
        plt.title("Network of Politician Trades and Companies")
        plt.show()
    else:
        print("One or more required CSV files for detailed analysis were not found. Skipping detailed analysis.")

if __name__ == "__main__":
    main() 