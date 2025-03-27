import os
import glob
import pandas as pd
from gemini_helper import get_gemini_response
import matplotlib.pyplot as plt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import networkx as nx
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import requests
import json

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

class ContractAnalysis:
    """Terminal-based federal contract analysis component"""
    
    def __init__(self, symbol='LMT', company='Lockheed Martin'):
        self.symbol = symbol
        self.company = company
        self.data_dir = 'data'
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def fetch_stock_data(self, start_date='2020-01-01'):
        """Fetch stock data from yfinance"""
        print(f"Fetching stock data for {self.symbol} from {start_date}...")
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(start=start_date)
            
            if df.empty:
                print(f"No data available for {self.symbol} from {start_date}")
                df = ticker.history(period="max")
            
            return df
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            return ticker.history(period="1y")
    
    def fetch_contract_data(self, company_name=None, start_date='2020-01-01', end_date=None):
        """Fetch contract data from USA Spending API"""
        if company_name is None:
            company_name = self.company
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        print(f"Fetching contract data for {company_name} from {start_date} to {end_date}...")
        
        try:
            base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
            
            payload = {
                "filters": {
                    "award_type_codes": ["A", "B", "C", "D"],
                    "recipient_search_text": [company_name],
                    "time_period": [
                        {
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    ]
                },
                "fields": [
                    "Award ID",
                    "Recipient Name",
                    "Start Date",
                    "End Date",
                    "Award Amount",
                    "Description",
                    "Awarding Agency",
                    "Awarding Sub Agency",
                    "Contract Award Type"
                ],
                "page": 1,
                "limit": 100,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            response = requests.post(base_url, json=payload)
            
            if response.status_code == 200:
                contracts_data = response.json()
                
                if 'results' in contracts_data and contracts_data['results']:
                    # Save to CSV
                    df = pd.DataFrame(contracts_data['results'])
                    output_file = os.path.join(self.data_dir, 'federal_contracts_latest.csv')
                    df.to_csv(output_file, index=False)
                    print(f"Saved {len(df)} contracts to {output_file}")
                    return df
                else:
                    print("No contract data found")
                    return None
            else:
                print(f"Error fetching contract data: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception fetching contract data: {e}")
            return None
    
    def analyze_market_impact(self, contracts_df=None):
        """Analyze stock market impact for each contract"""
        if contracts_df is None:
            contracts_file = os.path.join(self.data_dir, 'federal_contracts_latest.csv')
            if os.path.exists(contracts_file):
                contracts_df = pd.read_csv(contracts_file)
            else:
                print("No contract data available for analysis")
                return None
        
        print("Analyzing market impact of contracts...")
        stock_data = self.fetch_stock_data()
        if stock_data.empty:
            print("No stock data available for analysis")
            return None
        
        # Create analysis results for each contract
        analysis_results = []
        
        for _, contract in contracts_df.iterrows():
            try:
                award_date = pd.to_datetime(contract['Start Date'])
                
                # Get stock data around the contract date
                pre_window = 10  # 10 trading days before
                post_window = 10  # 10 trading days after
                
                # Find data around award date
                pre_award_data = stock_data.loc[stock_data.index < award_date].tail(pre_window)
                post_award_data = stock_data.loc[stock_data.index >= award_date].head(post_window)
                
                # Calculate impact metrics
                impact = {
                    'contract_id': contract['Award ID'],
                    'award_amount': contract['Award Amount'],
                    'award_date': award_date,
                    'pre_price_avg': pre_award_data['Close'].mean() if not pre_award_data.empty else None,
                    'post_price_avg': post_award_data['Close'].mean() if not post_award_data.empty else None,
                    'pre_volume_avg': pre_award_data['Volume'].mean() if not pre_award_data.empty else None,
                    'post_volume_avg': post_award_data['Volume'].mean() if not post_award_data.empty else None
                }
                
                # Calculate percentage changes
                if impact['pre_price_avg'] and impact['post_price_avg']:
                    impact['price_change_pct'] = ((impact['post_price_avg'] - impact['pre_price_avg']) / impact['pre_price_avg']) * 100
                else:
                    impact['price_change_pct'] = None
                
                if impact['pre_volume_avg'] and impact['post_volume_avg']:
                    impact['volume_change_pct'] = ((impact['post_volume_avg'] - impact['pre_volume_avg']) / impact['pre_volume_avg']) * 100
                else:
                    impact['volume_change_pct'] = None
                
                analysis_results.append(impact)
            except Exception as e:
                print(f"Error analyzing contract {contract.get('Award ID', 'unknown')}: {e}")
                continue
        
        # Save analysis results
        analysis_df = pd.DataFrame(analysis_results)
        output_file = os.path.join(self.data_dir, 'contract_market_impact.csv')
        analysis_df.to_csv(output_file, index=False)
        print(f"Saved market impact analysis to {output_file}")
        
        return analysis_df
    
    def visualize_contract_impact(self, impact_df=None):
        """Create visualization of contract impact on stock prices"""
        if impact_df is None:
            impact_file = os.path.join(self.data_dir, 'contract_market_impact.csv')
            if os.path.exists(impact_file):
                impact_df = pd.read_csv(impact_file)
            else:
                print("No impact data available for visualization")
                return
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Plot price impact
        plt.subplot(2, 1, 1)
        plt.bar(range(len(impact_df)), impact_df['price_change_pct'], color='blue')
        plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        plt.title(f'Price Impact of {self.company} Contracts')
        plt.ylabel('Price Change (%)')
        plt.xticks([])
        
        # Plot volume impact
        plt.subplot(2, 1, 2)
        plt.bar(range(len(impact_df)), impact_df['volume_change_pct'], color='green')
        plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
        plt.title('Volume Impact of Contracts')
        plt.ylabel('Volume Change (%)')
        plt.xlabel('Contracts (ordered by award date)')
        plt.tight_layout()
        
        # Save figure
        output_file = os.path.join(self.data_dir, 'contract_impact_visualization.png')
        plt.savefig(output_file)
        print(f"Saved visualization to {output_file}")
        plt.close()
    
    def analyze_with_gemini(self, contracts_df=None, impact_df=None):
        """Use Gemini to analyze contracts and their market impact"""
        if contracts_df is None:
            contracts_file = os.path.join(self.data_dir, 'federal_contracts_latest.csv')
            if os.path.exists(contracts_file):
                contracts_df = pd.read_csv(contracts_file)
            else:
                print("No contract data available for analysis")
                return None
        
        if impact_df is None:
            impact_file = os.path.join(self.data_dir, 'contract_market_impact.csv')
            if os.path.exists(impact_file):
                impact_df = pd.read_csv(impact_file)
            else:
                print("No impact data available for analysis")
                return None
        
        # Prepare the data for analysis
        contract_data = contracts_df.head(10).to_string()  # Limit to top 10 contracts
        impact_data = impact_df.head(10).to_string()  # Corresponding impact data
        
        # Create the analysis prompt
        prompt = f"""
        Analyze the following federal contract data for {self.company} ({self.symbol}) and their stock market impact:

        FEDERAL CONTRACTS:
        {contract_data}

        MARKET IMPACT:
        {impact_data}

        Please provide:
        1. Key insights about the contracts (patterns, sizes, agencies, etc.)
        2. Analysis of market impact (average price/volume changes)
        3. Potential correlation between contract characteristics and market reactions
        4. Recommendations for investors based on historical contract impacts
        """
        
        # Get the analysis from Gemini
        print("Generating AI analysis of contracts...")
        analysis = get_gemini_response(prompt, "")
        
        # Save the analysis
        output_file = os.path.join(self.data_dir, 'contract_ai_analysis.txt')
        with open(output_file, 'w') as f:
            f.write(analysis)
        print(f"Saved AI analysis to {output_file}")
        
        return analysis
    
    def run_analysis(self):
        """Run the complete contract analysis pipeline"""
        print("\n========== FEDERAL CONTRACTS ANALYSIS ==========\n")
        
        # Step 1: Fetch contract data
        contracts_df = self.fetch_contract_data()
        if contracts_df is None or contracts_df.empty:
            print("No contracts found. Analysis complete.")
            return
        
        # Step 2: Analyze market impact
        impact_df = self.analyze_market_impact(contracts_df)
        if impact_df is None or impact_df.empty:
            print("Could not analyze market impact. Analysis complete.")
            return
        
        # Step 3: Visualize impact
        self.visualize_contract_impact(impact_df)
        
        # Step 4: AI analysis
        analysis = self.analyze_with_gemini(contracts_df, impact_df)
        
        # Print summary
        print("\n===== CONTRACT ANALYSIS SUMMARY =====")
        print(f"Company: {self.company} ({self.symbol})")
        print(f"Contracts analyzed: {len(contracts_df)}")
        
        avg_price_impact = impact_df['price_change_pct'].mean()
        avg_volume_impact = impact_df['volume_change_pct'].mean()
        
        print(f"Average price impact: {avg_price_impact:.2f}%")
        print(f"Average volume impact: {avg_volume_impact:.2f}%")
        
        print("\nAI Analysis Excerpt:")
        print("-" * 40)
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print("-" * 40)
        
        print("\nFull results saved to data directory.")


def run_federal_contracts_analysis(symbol='LMT', company='Lockheed Martin'):
    """Run the federal contracts analysis as a separate module"""
    contract_analyzer = ContractAnalysis(symbol, company)
    contract_analyzer.run_analysis()


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
        plt.savefig("data/time_series_analysis.png")
        print("Saved time series plot to data/time_series_analysis.png")
        plt.close()
        
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
        plt.savefig("data/sentiment_analysis.png")
        print("Saved sentiment analysis plot to data/sentiment_analysis.png")
        plt.close()
        
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
        plt.savefig("data/network_analysis.png")
        print("Saved network analysis plot to data/network_analysis.png")
        plt.close()
        
        # Run the federal contracts analysis as a separate model
        print("\nRunning Federal Contracts Analysis Module...")
        run_federal_contracts_analysis()
        
    else:
        print("One or more required CSV files for detailed analysis were not found. Skipping detailed analysis.")
        
        # Run contract analysis with default settings even if other data is missing
        print("\nRunning Federal Contracts Analysis Module with default settings...")
        run_federal_contracts_analysis()


if __name__ == "__main__":
    main() 