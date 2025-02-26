import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import streamlit as st
import requests
import json
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class ContractTracker:
    def __init__(self):
        self.contract_data = {
            'id': 'LMT2024001',
            'company': 'Lockheed Martin',
            'symbol': 'LMT',
            'amount': 156000000,
            'awarded_date': '2024-01-15',
            'completion_date': '2025-12-31',
            'events': self.fetch_initial_contract_events(),  # Now fetching real contract events
            'stakeholders': {
                'politicians': [
                    {
                        'name': 'Sen. Jane Smith',
                        'role': 'Armed Services Committee',
                        'transactions': [
                            {'date': '2024-01-20', 'type': 'Buy', 'amount': 50000}
                        ]
                    }
                ],
                'institutions': [
                    {
                        'name': 'BlackRock',
                        'transactions': [
                            {'date': '2024-01-30', 'type': 'Increase', 'percent': 2.3}
                        ]
                    }
                ]
            }
        }

    def fetch_stock_data(self):
        """Fetch stock data from yfinance starting from 1985"""
        start_date = '1985-01-01'  # Changed to start from 1985
        try:
            ticker = yf.Ticker(self.contract_data['symbol'])
            df = ticker.history(start=start_date)
            
            if df.empty:
                print(f"No data available for {self.contract_data['symbol']} from {start_date}")
                # Fallback to more recent data if historical data is not available
                df = ticker.history(period="max")
            
            return df
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            # Return last year's data as fallback
            return ticker.history(period="1y")

    def create_timeline_visualization(self, stock_data):
        """Create interactive timeline visualization"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Stock Price & Contract Events', 'Trading Volume'),
            vertical_spacing=0.15,
            row_heights=[0.7, 0.3]
        )

        # Add stock price line
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                name='Stock Price',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=stock_data.index,
                y=stock_data['Volume'],
                name='Volume',
                marker_color='lightgray'
            ),
            row=2, col=1
        )

        # Add event markers
        if self.contract_data['events']:
            events_df = pd.DataFrame([
                {
                    'date': event['date'],
                    'price': event['price'],
                    'event': event['event']
                }
                for event in self.contract_data['events']
                if event['price'] > 0  # Only include events with valid prices
            ])
            
            if not events_df.empty:
                fig.add_trace(
                    go.Scatter(
                        x=pd.to_datetime(events_df['date']),
                        y=events_df['price'],
                        mode='markers+text',
                        name='Contract Events',
                        text=events_df['event'],
                        textposition="top center",
                        marker=dict(size=10, color='red'),
                        textfont=dict(size=10)
                    ),
                    row=1, col=1
                )

        # Update layout
        fig.update_layout(
            title=f"Contract Analysis - {self.contract_data['company']} ({self.contract_data['symbol']})",
            height=800,
            showlegend=True,
            xaxis=dict(
                rangeslider=dict(visible=False),
                type="date"
            )
        )

        # Update y-axes
        fig.update_yaxes(title_text="Stock Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

        return fig

    def generate_stakeholder_report(self):
        """Generate stakeholder analysis report"""
        report = []
        report.append("## Stakeholder Analysis")
        
        # Political stakeholders
        report.append("\n### Political Stakeholders")
        for politician in self.contract_data['stakeholders']['politicians']:
            report.append(f"\n* {politician['name']}")
            report.append(f"  - Role: {politician['role']}")
            for transaction in politician['transactions']:
                report.append(f"  - Transaction: {transaction['type']} ${transaction['amount']:,} "
                            f"on {transaction['date']}")

        # Institutional stakeholders
        report.append("\n### Institutional Stakeholders")
        for institution in self.contract_data['stakeholders']['institutions']:
            report.append(f"\n* {institution['name']}")
            for transaction in institution['transactions']:
                report.append(f"  - {transaction['type']}d position by {transaction['percent']}% "
                            f"on {transaction['date']}")

        return '\n'.join(report)
    

# --- USA Spending API Integration Methods ---

    def _save_json_to_csv(self, json_data, filename):
        """Helper function to save JSON data to CSV in the 'data' folder."""
        data_folder = 'data'
        if not os.path.exists(data_folder):
            os.makedirs(data_folder) # Create 'data' folder if it doesn't exist

        if json_data and 'results' in json_data and json_data['results']: # Check if results key exists and is not empty
            df = pd.DataFrame(json_data['results'])
            csv_filename = os.path.join(data_folder, f"{filename}.csv") # Save in 'data' folder
            df.to_csv(csv_filename, index=False)
            print(f"Data saved to {csv_filename}")
        else:
            csv_filename = os.path.join(data_folder, f"{filename}.csv") # Define filename even if no data
            with open(csv_filename, 'w') as f: # Create an empty file
                f.write("No data fetched from API for this section.")
            print(f"No data to save to CSV for {filename}. Empty file created at {csv_filename}")

    def _save_all_award_details_to_csv(self, all_award_details):
        """Helper function to save all award details to a single CSV in 'data' folder."""
        data_folder = 'data'
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        if all_award_details:
            df = pd.DataFrame(all_award_details)
            csv_filename = os.path.join(data_folder, "USA Spending - All Award Details.csv")
            df.to_csv(csv_filename, index=False)
            print(f"All Award Details saved to {csv_filename}")
        else:
            csv_filename = os.path.join(data_folder, "USA Spending - All Award Details.csv")
            with open(csv_filename, 'w') as f:
                f.write("No award details fetched to save.")
            print(f"No award details to save. Empty file created at {csv_filename}")


    def fetch_recipient_data(self, query_params=None):
        """Monitor recipient organizations via USA Spending API (/api/v2/recipient/)"""
        base_url = "https://api.usaspending.gov/api/v2"
        endpoint = f"{base_url}/recipient/"
        try:
            # Use POST instead of GET for advanced filtering
            payload = query_params if query_params is not None else {}
            response = requests.post(endpoint, json=payload)
            if response.status_code == 200:
                json_data = response.json()
                self._save_json_to_csv(json_data, "USA Spending - Recipient Data") # Save to CSV with specific filename
                return json_data
            else:
                print("Error fetching recipient data:", response.text)
                return None
        except Exception as e:
            print("Exception fetching recipient data:", e)
            return None

    def fetch_agency_references(self):
        """Access agency and sub-agency details via USA Spending API (/api/v2/agency/<TOPTIER_AGENCY_CODE>/sub_agency/)"""
        base_url = "https://api.usaspending.gov/api/v2"
        # Using a default toptier agency code "012" as an example
        endpoint = f"{base_url}/agency/012/sub_agency/"
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                json_data = response.json()
                self._save_json_to_csv(json_data, "USA Spending - Agency References") # Save to CSV with specific filename
                return json_data
            else:
                print("Error fetching agency references:", response.text)
                return None
        except Exception as e:
            print("Exception fetching agency references:", e)
            return None

    def download_bulk_historical_data(self, query_params=None):
        """Retrieve bulk historical data via USA Spending API (/api/v2/download/awards/)"""
        base_url = "https://api.usaspending.gov/api/v2"
        endpoint = f"{base_url}/download/awards/"  # Changed endpoint to correct one
        try:
            # Default payload based on documentation
            default_payload = {
                "filters": {
                    "time_period": [
                        {
                            "start_date": "2023-01-01",
                            "end_date": "2023-12-31",
                            "date_type": "action_date"
                        }
                    ],
                    "award_type_codes": [
                        "A", "B", "C", "D"  # Contract award types
                    ]
                },
                "columns": [
                    "award_id_piid",
                    "total_obligation",
                    "period_of_performance_start_date",
                    "period_of_performance_current_end_date",
                    "awarding_agency_name",
                    "recipient_name"
                ],
                "file_format": "csv"
            }

            # Merge any provided query_params into the payload
            if query_params is not None:
                if "filters" in query_params:
                    default_payload["filters"].update(query_params["filters"])
                if "columns" in query_params:
                    default_payload["columns"] = query_params["columns"]
                if "file_format" in query_params:
                    default_payload["file_format"] = query_params["file_format"]

            response = requests.post(endpoint, json=default_payload)
            
            if response.status_code == 200:
                json_data = response.json()
                # Store download information
                if "file_url" in json_data:
                    st.success("Download link generated successfully!")
                    st.markdown(f"[Download CSV]({json_data['file_url']})")
                return json_data
            else:
                print(f"Error downloading bulk historical data: {response.text}")
                return None
        except Exception as e:
            print(f"Exception downloading bulk historical data: {e}")
            return None

    def fetch_award_details(self, award_id):
        """
        Fetch details for a specific award using multiple USA Spending API endpoints.
        Includes fetching federal accounts data using /api/v2/awards/accounts/.
        This function now focuses on displaying federal account data.
        """
        base_url = "https://api.usaspending.gov/api/v2"
        results = {}
        try:
            # 1. Award Federal Accounts: POST /api/v2/awards/accounts/ returns federal accounts for the given award.
            url_award_accounts = f"{base_url}/awards/accounts/"
            payload_award_accounts = {
                "award_id": award_id,  # award_id as a string per API specification
                "limit": 10,
                "page": 1,
                "sort": "total_transaction_obligated_amount",
                "order": "desc"
            }
            print(f"Payload being sent to /api/v2/awards/accounts/: {json.dumps(payload_award_accounts)}") # Print payload for debugging
            response_award_accounts = requests.post(url_award_accounts, json=payload_award_accounts)
            if response_award_accounts.status_code == 200:
                award_accounts_data = response_award_accounts.json() # Store the json response
                self._save_json_to_csv(award_accounts_data, "USA Spending - Award Federal Accounts") # Save to CSV
                results['award_accounts'] = award_accounts_data

            else:
                print("Error fetching award accounts:", response_award_accounts.text)
                results['award_accounts'] = None


            # 2. Federal account count: Derived from award accounts result.
            if results.get('award_accounts') and 'page_metadata' in results['award_accounts']:
                results['count_federal_account'] = results['award_accounts']['page_metadata'].get('count', None)
            else:
                results['count_federal_account'] = None

            # 3. Last updated info: GET /api/v2/awards/last_updated/
            url_last_updated = f"{base_url}/awards/last_updated/"
            response_last_updated = requests.get(url_last_updated)
            if response_last_updated.status_code == 200:
                last_updated_data = response_last_updated.json()
                # Last updated endpoint response is not in 'results' format, save directly if needed.
                # pd.DataFrame([last_updated_data], index=[0]).to_csv("award_last_updated.csv", index=False)
                print("Award last updated info received, CSV saving for this endpoint might need specific handling if required.")
                results['last_updated'] = last_updated_data
            else:
                print("Error fetching last updated info:", response_last_updated.text)
                results['last_updated'] = None

            return results
        except Exception as e:
            print("Exception in fetching award details:", e)
            return None

    def fetch_award_details_by_id(self, award_id):
        """
        Fetch details for a specific award using /api/v2/awards/<AWARD_ID>/ endpoint.
        This endpoint provides comprehensive details about a single award.
        Now using generated_internal_id as award_id.
        Returns award details data instead of saving to CSV directly.
        """
        base_url = "https://api.usaspending.gov/api/v2"
        endpoint = f"{base_url}/awards/{award_id}/" # Using generated_internal_id as award_id
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                award_details_by_id_data = response.json()
                print(f"Award details fetched for generated_internal_id (used as Award ID): {award_id}")
                return award_details_by_id # Return data, don't save here
            else:
                print(f"Error fetching award details for award ID {award_id} from /api/v2/awards/<AWARD_ID>/: {response.text}")
                return None
        except Exception as e:
            print(f"Exception fetching award details for award ID {award_id} from /api/v2/awards/<AWARD_ID>/: {e}")
            return None

    def fetch_generated_internal_ids_from_transaction_search(self, payload=None):
        """
        Fetches award data using the /api/v2/search/spending_by_award/ endpoint.
        Specifically filtered for Lockheed Martin contracts.
        """
        base_url = "https://api.usaspending.gov/api/v2"
        endpoint = f"{base_url}/search/spending_by_award/"  # Changed endpoint
        try:
            if payload is None:
                # Default payload following the API documentation structure
                payload = {
                    "filters": {
                        "award_type_codes": [
                            "A",  # Definitive Contracts
                            "B",  # Purchase Orders
                            "C",  # Delivery Orders
                            "D"   # BPA Calls
                        ],
                        "recipient_search_text": ["Lockheed Martin"],
                        "time_period": [
                            {
                                "start_date": "2023-01-01",
                                "end_date": "2024-12-31"
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
                        "Contract Award Type",
                        "generated_internal_id",
                        "Place of Performance State Code",
                        "Place of Performance Country Code"
                    ],
                    "page": 1,
                    "limit": 100,
                    "sort": "Award Amount",  # Changed to match available sort fields
                    "order": "desc",
                    "subawards": False
                }

            print(f"Fetching Lockheed Martin contracts from {endpoint}")
            response = requests.post(endpoint, json=payload)

            if response.status_code == 200:
                award_data = response.json()
                
                # Save to CSV with Lockheed Martin specific name
                self._save_json_to_csv(
                    award_data, 
                    "USA Spending - Lockheed Martin Awards"
                )
                
                return award_data
            else:
                print(f"Error fetching Lockheed Martin awards: {response.text}")
                return None
        except Exception as e:
            print(f"Exception in fetch_award_data: {e}")
            return None

    def fetch_initial_contract_events(self):
        """Fetch recent Lockheed Martin contract awards and convert them to events"""
        try:
            # Set up the payload for recent Lockheed Martin awards
            payload = {
                "filters": {
                    "award_type_codes": ["A", "B", "C", "D"],
                    "recipient_search_text": ["Lockheed Martin"],
                    "time_period": [
                        {
                            "start_date": "2023-01-01",
                            "end_date": datetime.now().strftime("%Y-%m-%d")
                        }
                    ]
                },
                "fields": [
                    "Award ID",
                    "Start Date",
                    "Award Amount",
                    "Description",
                    "Awarding Agency"
                ],
                "page": 1,
                "limit": 100,  # Changed from 10 to 100 to match the table view
                "sort": "Award Amount",
                "order": "desc",
                "subawards": False
            }

            # Fetch the award data
            award_data = self.fetch_generated_internal_ids_from_transaction_search(payload)
            
            if award_data and 'results' in award_data:
                events = []
                ticker = yf.Ticker('LMT')
                
                # Process all awards in batches to avoid rate limiting
                for award in award_data['results']:
                    try:
                        date = award['Start Date']
                        # Use a single API call for each date to avoid rate limiting
                        if not hasattr(self, '_stock_prices') or date not in self._stock_prices:
                            stock_data = ticker.history(
                                start=date,
                                end=(datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                            )
                            if not hasattr(self, '_stock_prices'):
                                self._stock_prices = {}
                            if not stock_data.empty:
                                self._stock_prices[date] = float(stock_data['Close'][0])
                        
                        price = self._stock_prices.get(date)
                        
                        if price:
                            # Get description, truncate if too long
                            description = award.get('Description', 'No description available')
                            if len(description) > 50:  # Truncate long descriptions
                                description = description[:47] + "..."
                            
                            events.append({
                                'date': date,
                                'price': price,
                                'event': description
                            })
                    except Exception as e:
                        print(f"Error processing award {award.get('Award ID', 'unknown')}: {str(e)}")
                        continue
                
                return sorted(events, key=lambda x: x['date'])
            
            return [{'date': '2024-01-15', 'event': 'No data', 'price': 0}]
        
        except Exception as e:
            print(f"Error fetching contract events: {str(e)}")
            return [{'date': '2024-01-15', 'event': 'Error', 'price': 0}]


# ------------------------------------------------------------------
# Market Impact Analysis Functions
    def get_pre_award_data(self, symbol, award_date, days_before=30):
        """Fetches stock data for a specified period before the award date."""
        start_date = (datetime.strptime(award_date, '%Y-%m-%d') - timedelta(days=days_before)).strftime('%Y-%m-%d')
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=award_date)
        return df

    def get_post_award_data(self, symbol, award_date, days_after=90):
        """Fetches stock data for a specified period after the award date."""
        end_date = (datetime.strptime(award_date, '%Y-%m-%d') + timedelta(days=days_after)).strftime('%Y-%m-%d')
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=award_date, end=end_date)
        return df
    
    def analyze_market_impact(self, symbol, award_date):
        """Analyzes market impact by comparing pre- and post-award stock data."""
        pre_award_data = self.get_pre_award_data(symbol, award_date)
        post_award_data = self.get_post_award_data(symbol, award_date)

        # Calculate average closing price and volume for pre-award period
        pre_avg_close = pre_award_data['Close'].mean()
        pre_avg_volume = pre_award_data['Volume'].mean()

        # Calculate average closing price and volume for post-award period
        post_avg_close = post_award_data['Close'].mean()
        post_avg_volume = post_award_data['Volume'].mean()
        
        # Calculate percentage changes
        close_price_change = ((post_avg_close - pre_avg_close) / pre_avg_close) * 100 if pre_avg_close else 0
        volume_change = ((post_avg_volume - pre_avg_volume) / pre_avg_volume) * 100 if pre_avg_volume else 0

        # Fetch options chain data (if available)
        ticker = yf.Ticker(symbol)
        try:
            options_chain = ticker.option_chain()  # Get all options chains
            
            #Calculate average values for calls and puts
            calls_avg_volume = options_chain.calls['volume'].mean()
            puts_avg_volume = options_chain.puts['volume'].mean()

            calls_avg_oi = options_chain.calls['openInterest'].mean()
            puts_avg_oi = options_chain.puts['openInterest'].mean()

        except Exception as e:
            print(f"Error fetching options chain data: {e}")
            calls_avg_volume = puts_avg_volume = calls_avg_oi = puts_avg_oi = None

        return {
            'pre_award_avg_close': pre_avg_close,
            'post_award_avg_close': post_avg_close,
            'close_price_change_percent': close_price_change,
            'pre_award_avg_volume': pre_avg_volume,
            'post_award_avg_volume': post_avg_volume,
            'volume_change_percent': volume_change,
            'calls_avg_volume': calls_avg_volume,
            'puts_avg_volume': puts_avg_volume,
            'calls_avg_open_interest': calls_avg_oi,
            'puts_avg_open_interest': puts_avg_oi
        }

    def setup_gemini(self):
        """Setup Gemini API with your credentials"""
        try:
            from config import GEMINI_API_KEY  # Import from config file
            
            if not GEMINI_API_KEY:
                return f"Error: GEMINI_API_KEY not found in config"
            
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Configure the model
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            model = genai.GenerativeModel('gemini-pro', safety_settings=safety_settings)
            return model
            
        except ImportError:
            return f"Error: Could not import GEMINI_API_KEY from config"
        except Exception as e:
            return f"Error setting up Gemini: {str(e)}"

    def analyze_with_gemini(self, stock_data, events_df, market_impacts=None):
        """Use Gemini to analyze stock and contract data"""
        try:
            model = self.setup_gemini()
            
            # Check if we got an error string instead of a model
            if isinstance(model, str) and model.startswith('Error'):
                return model
            
            # Prepare data for analysis
            recent_stock_data = stock_data.tail(30).describe().to_string()
            recent_contracts = events_df.tail(5).to_string() if not events_df.empty else "No recent contracts"
            
            # Format market impact data if available
            market_impact_str = ""
            if market_impacts:
                market_impact_str = """
                Market Impact Metrics:
                
                Stock Price Impact:
                - Average Price Change: {:.2f}%
                - Pre-Award Average Price: ${:,.2f}
                - Post-Award Average Price: ${:,.2f}
                
                Volume Impact:
                - Average Volume Change: {:.2f}%
                - Pre-Award Average Volume: {:,.0f}
                - Post-Award Average Volume: {:,.0f}
                
                Options Activity:
                - Average Call Volume: {:,.0f}
                - Average Call Open Interest: {:,.0f}
                - Average Put Volume: {:,.0f}
                - Average Put Open Interest: {:,.0f}
                """.format(
                    market_impacts['avg_price_change'],
                    market_impacts['pre_avg_price'],
                    market_impacts['post_avg_price'],
                    market_impacts['avg_volume_change'],
                    market_impacts['pre_avg_volume'],
                    market_impacts['post_avg_volume'],
                    market_impacts['avg_call_volume'],
                    market_impacts['avg_call_oi'],
                    market_impacts['avg_put_volume'],
                    market_impacts['avg_put_oi']
                )
            
            prompt = f"""
            **Role:**
            You are a financial analysis assistant specializing in market impact analysis. Your role is to analyze the relationship between Lockheed Martin's (LMT) recent contract awards and its stock performance, providing actionable insights for decision-making.

            **Objective:**
            Perform a detailed market impact analysis of Lockheed Martin's stock performance in relation to its recent contract awards, focusing on key trends, patterns, and strategic recommendations.

            **Task Details:**

            *Data to Analyze:*

            - Recent Stock Statistics: {recent_stock_data}

            - Recent Contract Awards: {recent_contracts}

            - Market Impact Analysis: {market_impact_str}

            *Timeframe Tracking:*
            Analyze market behavior across three critical timeframes for EACH contract. Take 5 most important contracts or has the most impact on the stock price and analyze the market impact for each of these contracts. The output should have 5 most impactful contact name, award amount, and the market impact analysis for each of the 5 contracts:

            - Pre-award period (T-30 days): Assess stock price movement, trading volume, and other metrics leading up to the award announcement.

            - Award announcement (T0): Evaluate immediate market reactions on the day of the announcement.

            - Post-award execution (T+90 days or later): Examine long-term impacts after the award execution.

            *Key Metrics to Monitor:*
            For each timeframe, analyze and report on:

            - Stock Price Movement: Identify trends and significant changes in stock prices.

            - Trading Volume Anomalies: Detect unusual spikes or drops in trading volumes.

            - Option Chain Activity: Examine changes in open interest, implied volatility, and unusual options activity.

            - Short Interest Changes: Track fluctuations in short interest levels to gauge market sentiment.
            
            *Output Requirements:*
            Provide a structured report that includes:

            1. Explanation of the market impact metrics and what they indicate
            2. Key trends in Lockheed Martin's stock performance
            3. Analysis of the impact of recent contract awards on stock behavior
            4. Notable patterns or correlations between contracts and stock movement
            5. Strategic insights and actionable recommendations based on findings

            *Analysis Guidelines:*

            - Use historical data, financial indicators, and observed patterns to contextualize findings.

            Highlight any anomalies or deviations from expected behavior.

            - Ensure clarity and precision in presenting results.

            *Constraints & Considerations:*

            - Focus on accuracy and relevance when analyzing data.

            - Avoid speculative conclusions without supporting evidence.

            - Tailor insights to assist stakeholders in understanding market impacts effectively.


            **Note:**
            - Do NOT only give general information about the market impact, but also provide specific information about the contract awards and how they impact the market.
            - Make the analysis VERY specific to the contract awards and the market impact using the data from {recent_stock_data} and {recent_contracts}.
            - An example of the output is:
            Market Impact Analysis Report: Lockheed Martin (LMT)
            Date of Analysis: February 22, 2025
            Contract Evaluated: $10 Billion Fighter Jet Contract Awarded on January 15, 2025
            
            Market Impact:
            Average Price Impact: +1.5%
            Average Volume Change: +5.7%
            Average Call Volume: 60
            Average Call Open Interest: 85
            Average Put Volume: 30
            Average Put Open Interest: 60

            1. Pre-Award Period (T-30 Days)
            Timeframe: December 16, 2024 – January 14, 2025

            Stock Price Movement:
            LMT stock showed a steady upward trend, increasing by 5.2% from $440 to $463 in the 30 days leading up to the contract announcement. This suggests investor optimism or insider anticipation of the award.

            Trading Volume Anomalies:
            Trading volume spiked by 35% on January 10, 2025, compared to the daily average over the previous month. This could indicate early market speculation about the contract.

            Option Chain Activity:
            A significant increase in call option open interest was observed between January 8 and January 12, with implied volatility rising by 18%. This reflects bullish sentiment among options traders.

            Short Interest Changes:
            Short interest decreased by 12% during this period, indicating reduced bearish sentiment among investors.

            2. Award Announcement (T0)
            Date: January 15, 2025

            Stock Price Movement:
            On the day of the announcement, LMT stock surged by 3.8%, closing at $480. This immediate reaction reflects strong investor confidence in the financial impact of the contract.

            Trading Volume Anomalies:
            Trading volume was unusually high, at nearly double the daily average for the past month (12 million shares traded).

            Option Chain Activity:
            Call options expiring in February saw a sharp increase in open interest (+45%), with implied volatility peaking at 28%.

            Short Interest Changes:
            No significant changes in short interest were observed on the announcement day.

            3. Post-Award Execution (T+90 Days)
            Timeframe: January 16, 2025 – April 15, 2025

            Stock Price Movement:
            Over the three months following the award, LMT stock continued its upward trajectory, reaching $510 (+6.25%). This suggests sustained investor confidence and positive market perception of the contract's long-term value.

            Trading Volume Anomalies:
            Trading volume normalized after the first week post-announcement but remained slightly above average during earnings reports tied to contract updates.

            Option Chain Activity:
            A gradual decline in implied volatility was observed as market uncertainty surrounding the contract execution diminished.

            Short Interest Changes:
            Short interest fell by an additional 8% during this period, signaling continued bullish sentiment.

            4. Strategic Insights and Recommendations
            Investor Sentiment Analysis:
            The consistent upward trend in stock price and reduced short interest indicate strong investor confidence in Lockheed Martin's ability to execute this contract successfully.

            Market Behavior Patterns:
            The pre-award trading volume spike and increased call option activity suggest that some investors may have anticipated this contract award.

            Recommendation for Stakeholders:

            Monitor upcoming earnings reports for further updates on contract execution to assess potential revenue impact.

            Consider leveraging similar patterns in trading volume and options activity as predictive indicators for future contract awards.

            Risk Consideration:
            Watch for geopolitical or budgetary changes that could affect defense spending and impact long-term stock performance.

            - Make sure to follow the exact format of the example output.
            """

            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Error in Gemini analysis: {str(e)}"


# ------------------------------------------------------------------
def render_federal_contracts_tab():
    st.title("Federal Contracts Analysis")
    tracker = ContractTracker()

    # Create tabs for different data views
    tabs = st.tabs(["Stock Analysis", "Lockheed Martin Contract Awards", "Recipient Data", "Agency References", "Historical Data"])

    with tabs[0]:
        st.header("Stock Price Analysis")
        try:
            stock_data = tracker.fetch_stock_data()
            fig = tracker.create_timeline_visualization(stock_data)
            st.plotly_chart(fig)

            # Market Impact Analysis with improved UI
            st.markdown("---")  # Add a divider
            st.header("Market Impact Analysis")
            st.markdown("""
            <style>
            .metric-row {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Analyze market impact for each contract event
            if tracker.contract_data['events']:
                all_impacts = []
                for event in tracker.contract_data['events']:
                    if event['price'] > 0:
                        impact = tracker.analyze_market_impact('LMT', event['date'])
                        if impact:
                            all_impacts.append(impact)
                
                if all_impacts:
                    # Stock Price Impact
                    st.subheader("Stock Price Impact")
                    with st.container():
                        col1, col2, col3 = st.columns(3)
                        avg_price_change = sum(impact['close_price_change_percent'] for impact in all_impacts) / len(all_impacts)
                        
                        with col1:
                            st.metric(
                                "Average Price Impact",
                                f"{avg_price_change:.2f}%",
                                delta=f"{avg_price_change:.1f}%"
                            )
                        with col2:
                            pre_avg = sum(impact['pre_award_avg_close'] for impact in all_impacts) / len(all_impacts)
                            st.metric("Pre-Award Avg. Price", f"${pre_avg:,.2f}")
                        with col3:
                            post_avg = sum(impact['post_award_avg_close'] for impact in all_impacts) / len(all_impacts)
                            st.metric(
                                "Post-Award Avg. Price",
                                f"${post_avg:,.2f}",
                                delta=f"${post_avg - pre_avg:,.2f}"
                            )

                    # Volume Impact
                    st.subheader("Trading Volume Impact")
                    with st.container():
                        col1, col2, col3 = st.columns(3)
                        avg_volume_change = sum(impact['volume_change_percent'] for impact in all_impacts) / len(all_impacts)
                        
                        with col1:
                            st.metric(
                                "Average Volume Impact",
                                f"{avg_volume_change:.2f}%",
                                delta=f"{avg_volume_change:.1f}%"
                            )
                        with col2:
                            pre_vol = sum(impact['pre_award_avg_volume'] for impact in all_impacts) / len(all_impacts)
                            st.metric("Pre-Award Avg. Volume", f"{pre_vol:,.0f}")
                        with col3:
                            post_vol = sum(impact['post_award_avg_volume'] for impact in all_impacts) / len(all_impacts)
                            st.metric(
                                "Post-Award Avg. Volume",
                                f"{post_vol:,.0f}",
                                delta=f"{post_vol - pre_vol:,.0f}"
                            )

                    # Options Analysis
                    if all_impacts[0]['calls_avg_volume'] is not None:
                        st.subheader("Options Market Activity")
                        with st.container():
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("##### Call Options")
                                call_vol = sum(impact['calls_avg_volume'] for impact in all_impacts) / len(all_impacts)
                                call_oi = sum(impact['calls_avg_open_interest'] for impact in all_impacts) / len(all_impacts)
                                st.metric("Average Daily Volume", f"{call_vol:,.0f}")
                                st.metric("Average Open Interest", f"{call_oi:,.0f}")
                            
                            with col2:
                                st.markdown("##### Put Options")
                                put_vol = sum(impact['puts_avg_volume'] for impact in all_impacts) / len(all_impacts)
                                put_oi = sum(impact['puts_avg_open_interest'] for impact in all_impacts) / len(all_impacts)
                                st.metric("Average Daily Volume", f"{put_vol:,.0f}")
                                st.metric("Average Open Interest", f"{put_oi:,.0f}")

            # AI Analysis after Market Impact
            st.markdown("---")  # Add a divider
            st.header("AI Analysis")
            with st.spinner("Analyzing data with Gemini..."):
                events_df = pd.DataFrame([
                    {
                        'date': event['date'],
                        'price': event['price'],
                        'event': event['event']
                    }
                    for event in tracker.contract_data['events']
                    if event['price'] > 0
                ])

            # Prepare market impact data for Gemini
            market_impacts = {
                'avg_price_change': avg_price_change,
                'pre_avg_price': pre_avg,
                'post_avg_price': post_avg,
                'avg_volume_change': avg_volume_change,
                'pre_avg_volume': pre_vol,
                'post_avg_volume': post_vol,
                'avg_call_volume': call_vol if 'call_vol' in locals() else 0,
                'avg_call_oi': call_oi if 'call_oi' in locals() else 0,
                'avg_put_volume': put_vol if 'put_vol' in locals() else 0,
                'avg_put_oi': put_oi if 'put_oi' in locals() else 0
            }

            analysis = tracker.analyze_with_gemini(stock_data, events_df, market_impacts)
            st.markdown(analysis)
            
            # Add download button for the analysis
            st.download_button(
                "Download AI Analysis",
                analysis,
                "lmt_analysis.txt",
                "text/plain",
                key='download-analysis'
            )

            # Display stakeholder report at the end
            st.markdown("---")  # Add a divider
            report = tracker.generate_stakeholder_report()
            st.markdown(report)

        except Exception as e:
            st.error(f"Error in stock analysis: {str(e)}")
            st.info("Proceeding with other data sources...")

    with tabs[1]:
        st.header("Lockheed Martin Contract Awards")
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime(2023, 1, 1),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                max_value=datetime.now()
            )

        # Custom payload with selected date range
        custom_payload = {
            "filters": {
                "award_type_codes": ["A", "B", "C", "D"],
                "recipient_search_text": ["Lockheed Martin"],
                "time_period": [
                    {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    }
                ]
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Start Date",
                "End Date",
                "Award Amount",
                "Awarding Agency",
                "Awarding Sub Agency",
                "Contract Award Type",
                "Award Type",
                "Funding Agency",
                "Funding Sub Agency",
                "Description"
            ],
            "page": 1,
            "limit": 100,
            "sort": "Award Amount",
            "order": "desc",
            "subawards": False
        }

        # Fetch contract data
        transaction_search_results = tracker.fetch_generated_internal_ids_from_transaction_search(
            payload=custom_payload
        )

        if transaction_search_results and 'results' in transaction_search_results:
            # Create a DataFrame for better display
            df = pd.DataFrame(transaction_search_results['results'])
            
            # Format the data
            if not df.empty:
                # Format the Award Amount as currency
                df['Award Amount'] = df['Award Amount'].apply(
                    lambda x: f"${float(x):,.2f}" if pd.notnull(x) else "N/A"
                )
                
                # Format the dates
                for date_col in ['Start Date', 'End Date']:
                    if date_col in df.columns:
                        df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
                
                # Display as an interactive table with all fields
                st.dataframe(
                    df[[
                        'Award ID',
                        'Recipient Name',
                        'Start Date',
                        'End Date',
                        'Award Amount',
                        'Awarding Agency',
                        'Awarding Sub Agency',
                        'Contract Award Type',
                        'Award Type',
                        'Funding Agency',
                        'Funding Sub Agency',
                        'Description'
                    ]],
                    use_container_width=True
                )

                # Add download button with all fields
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Complete Contract Data",
                    csv,
                    "lockheed_martin_contracts.csv",
                    "text/csv",
                    key='download-csv'
                )

                # Show summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    if 'Award Amount' in df.columns:
                        total_value = sum(float(str(x).replace('$', '').replace(',', '')) 
                                        for x in df['Award Amount'] if pd.notnull(x))
                        st.metric("Total Contract Value", f"${total_value:,.2f}")
                with col2:
                    st.metric("Number of Contracts", len(df))
                with col3:
                    unique_agencies = len(df['Awarding Agency'].unique())
                    st.metric("Number of Awarding Agencies", unique_agencies)
        else:
            st.warning("No Lockheed Martin contract awards found for the selected period.")

    with tabs[2]:
        st.header("Recipient Data")
        recipient_data = tracker.fetch_recipient_data()
        if recipient_data:
            st.json(recipient_data)
        else:
            st.warning("No recipient data available")

    with tabs[3]:
        st.header("Agency References")
        agency_data = tracker.fetch_agency_references()
        if agency_data:
            st.json(agency_data)
        else:
            st.warning("No agency reference data available")

    with tabs[4]:
        st.header("Historical Data")
        bulk_data = tracker.download_bulk_historical_data()
        if bulk_data:
            st.json(bulk_data)
        else:
            st.warning("No historical data available")


# ------------------------------------------------------------------
def main():
    tracker = ContractTracker()
    
    # Fetch stock data
    stock_data = tracker.fetch_stock_data()
    
    # Create visualization
    fig = tracker.create_timeline_visualization(stock_data)
    fig.show()
    
    # Generate stakeholder report
    stakeholder_report = tracker.generate_stakeholder_report()
    print(stakeholder_report)

    # --- Demonstration: Fetch USA Spending Awards Data ---

    # Define payload for /api/v2/search/spending_by_transaction/
    transaction_search_payload = {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"] # Example: Contracts
        },
        "fields": ["generated_internal_id", "Transaction Amount"], # Request generated_internal_id and Transaction Amount
        "limit": 10,
        "sort": "Transaction Amount",
        "order": "desc"
    }

    # Fetch and save recipient data
    recipient_data = tracker.fetch_recipient_data()

    # Fetch and save agency references
    agency_data = tracker.fetch_agency_references()

    # Fetch and save bulk historical data
    bulk_data = tracker.download_bulk_historical_data(query_params={'data_type': 'historical'})

    # Fetch and save award federal accounts and last updated (not saving last updated to CSV as per previous agreement, only federal accounts)
    award_details = tracker.fetch_award_details(tracker.contract_data.get('id', ''))

    # Fetch generated_internal_ids and save transaction search results
    transaction_search_results = tracker.fetch_generated_internal_ids_from_transaction_search(payload=transaction_search_payload)

    all_award_details = [] # Initialize list to store all award details
    generated_internal_ids_from_transaction_search = []
    if transaction_search_results and 'results' in transaction_search_results:
        generated_internal_ids_from_transaction_search = [item.get('generated_internal_id') for item in transaction_search_results['results'] if item.get('generated_internal_id')]

        if generated_internal_ids_from_transaction_search:
            print("\nFetched generated_internal_id from /api/v2/search/spending_by_transaction/ successfully!") # Updated print message
            print(f"Number of generated_internal_id fetched: {len(generated_internal_ids_from_transaction_search)}") # Updated print message

            # Fetch and print details for the first 2 generated_internal_ids for demonstration
            print("\n--- Award Details fetched using generated_internal_id as Award ID from Transaction Search ---") # Updated print message
            for fetched_generated_internal_id in generated_internal_ids_from_transaction_search[:2]: # Limit to first 2 for console output
                award_details_by_id = tracker.fetch_award_details_by_id(fetched_generated_internal_id) # Using fetched_generated_internal_id as award_id
                if award_details_by_id:
                    print(f"\nAward Details for generated_internal_id (used as Award ID): {fetched_generated_internal_id}:") # Updated print message
                    print("Award Details Keys:", award_details_by_id.keys()) # Print keys for summary
                    all_award_details.append(award_details_by_id) # Append to list
                else:
                    print(f"Failed to fetch Award Details by ID for generated_internal_id (used as Award ID): {fetched_generated_internal_id}") # Updated print message
        else:
            print("\nNo generated_internal_id found in transaction search results.")
    else:
        print("\nFailed to fetch generated_internal_id from /api/v2/search/spending_by_transaction/ or no results found.")

    tracker._save_all_award_details_to_csv(all_award_details) # Save all award details to CSV after fetching all
    
    # --- Demonstration: Market Impact Analysis ---
    print("\n--- Market Impact Analysis ---")
    analysis_results = tracker.analyze_market_impact(tracker.contract_data['symbol'], tracker.contract_data['awarded_date'])
    print(analysis_results)


if __name__ == "__main__":
    main()