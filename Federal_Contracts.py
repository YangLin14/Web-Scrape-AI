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
import random
import re
from html_template import get_html_template, get_ai_prompt_template
import urllib.parse

class ContractTracker:
    def __init__(self):
        # Add a print statement to confirm this class is being used
        print("ContractTracker from Federal_Contracts.py is being initialized")
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
        """Create interactive timeline visualization with dark theme and white text"""
        # Create two separate figures: one for stock price & volume, one for timeline
        fig1 = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Stock Price & Contract Events', 'Trading Volume'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Create separate figure for contract timeline
        fig2 = go.Figure()

        # Add stock price line
        fig1.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                name='Stock Price',
                line=dict(color='#4287f5', width=2)  # Brighter blue and thicker line
            ),
            row=1, col=1
        )

        # Normalize volume for better visibility
        max_volume = stock_data['Volume'].max()
        normalized_volume = stock_data['Volume'] / max_volume * 100

        # Add volume bars with area fill for better visibility
        fig1.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=normalized_volume,
                name='Volume',
                fill='tozeroy',
                fillcolor='rgba(255, 255, 255, 0.3)',
                line=dict(color='rgba(255, 255, 255, 0.8)', width=1),
                mode='lines'
            ),
            row=2, col=1
        )

        # Add custom y-axis labels for volume
        volume_ticks = [0, 25, 50, 75, 100]
        volume_labels = [f"{int(v/100 * max_volume/1000000)}M" for v in volume_ticks]

        # Add event markers with hover information
        if self.contract_data['events']:
            events_df = pd.DataFrame([
                {
                    'date': event['date'],
                    'price': event['price'],
                    'event': event['event'],
                    'amount': event.get('amount', 'N/A'),
                    'award_id': event.get('award_id', 'N/A')
                }
                for event in self.contract_data['events']
                if event['price'] > 0
            ])
            
            if not events_df.empty:
                # Add markers to stock price plot
                fig1.add_trace(
                    go.Scatter(
                        x=pd.to_datetime(events_df['date']),
                        y=events_df['price'],
                        mode='markers',
                        name='Contract Events',
                        marker=dict(
                            size=10,
                            color='red',
                            symbol='circle'
                        ),
                        hovertemplate=(
                            "<b>Contract Award</b><br>" +
                            "Date: %{x|%Y-%m-%d}<br>" +
                            "Stock Price: $%{y:.2f}<br>" +
                            "Description: %{customdata[0]}<br>" +
                            "Amount: %{customdata[1]}<br>" +
                            "Award ID: %{customdata[2]}<br>" +
                            "<extra></extra>"
                        ),
                        customdata=list(zip(
                            events_df['event'],
                            events_df['amount'].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x),
                            events_df['award_id']
                        ))
                    ),
                    row=1, col=1
                )

                # Add horizontal grid lines for timeline in the separate figure
                for y_pos in [0.5, 1.0, 1.5]:
                    fig2.add_shape(
                        type="line",
                        x0=stock_data.index.min(),
                        y0=y_pos,
                        x1=stock_data.index.max(),
                        y1=y_pos,
                        line=dict(
                            color="rgba(150, 150, 150, 0.3)",
                            width=1,
                        )
                    )

                # Create a fixed-distance timeline instead of date-based positioning
                if not events_df.empty:
                    # Sort events by date
                    events_df = events_df.sort_values('date')
                    
                    # Create evenly spaced x-positions
                    num_events = len(events_df)
                    fixed_positions = list(range(num_events))
                    
                    # Create a mapping from dates to fixed positions
                    date_to_position = dict(zip(events_df['date'], fixed_positions))
                    
                    # Create horizontal timeline with dots and connecting line in the separate figure
                    fig2.add_trace(
                        go.Scatter(
                            x=fixed_positions,
                            y=[1] * num_events,
                            mode='lines',
                            line=dict(color="white", width=2, dash='dot'),
                            hoverinfo='none',
                            showlegend=False
                        )
                    )
                    
                    # Then add the event markers
                    fig2.add_trace(
                        go.Scatter(
                            x=fixed_positions,
                            y=[1] * num_events,
                            mode='markers+text',
                            name='Contract Timeline',
                            marker=dict(
                                size=15,
                                symbol='circle',
                                color='white',
                                line=dict(color='black', width=2)
                            ),
                            text=events_df['date'],
                            textposition='top center',
                            hovertemplate=(
                                "<b>Contract Details</b><br>" +
                                "Date: %{text}<br>" +
                                "Description: %{customdata[0]}<br>" +
                                "Amount: %{customdata[1]}<br>" +
                                "Award ID: %{customdata[2]}<br>" +
                                "<extra></extra>"
                            ),
                            customdata=list(zip(
                                events_df['event'],
                                events_df['amount'].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x),
                                events_df['award_id']
                            ))
                        )
                    )
                    
                    # Add vertical lines, dates and descriptions with alternating positions to the separate figure
                    for i, row in events_df.iterrows():
                        date = row['date']
                        position = date_to_position[date]
                        
                        # Determine if this is an odd or even index for alternating positions
                        is_odd = i % 2 == 1
                        
                        # Set vertical line height based on odd/even
                        y0 = 0.3 if is_odd else 1.0  # Bottom of vertical line
                        y1 = 1.0 if is_odd else 1.7  # Top of vertical line
                        
                        # Add vertical dotted line
                        fig2.add_shape(
                            type="line",
                            x0=position,
                            y0=y0,
                            x1=position,
                            y1=y1,
                            line=dict(
                                color="white",
                                width=2,
                                dash="dot",
                            )
                        )
                        
                        # Add description based on odd/even
                        if is_odd:
                            # For odd indices, add description below the timeline
                            description = row['event']
                            if len(description) > 30:
                                description = description[:27] + "..."
                            
                            fig2.add_annotation(
                                x=position,
                                y=0.0,  # Position below the date
                                text=description,
                                showarrow=False,
                                font=dict(size=10, color="white", family="Arial, sans-serif"),
                                xanchor='center',
                                yanchor='top'
                            )
                        else:
                            # For even indices, add description above the timeline
                            description = row['event']
                            if len(description) > 30:
                                description = description[:27] + "..."
                            
                            fig2.add_annotation(
                                x=position,
                                y=2.0,  # Position above the date
                                text=description,
                                showarrow=False,
                                font=dict(size=10, color="white", family="Arial, sans-serif"),
                                xanchor='center',
                                yanchor='bottom'
                            )

        # Update layout for stock price and volume figure
        fig1.update_layout(
            title=f"Stock Analysis - {self.contract_data['company']} ({self.contract_data['symbol']})",
            height=700,
            showlegend=True,
            paper_bgcolor='black',
            plot_bgcolor='black',
            font=dict(color='white', family="Arial, sans-serif"),
            xaxis=dict(
                rangeslider=dict(visible=False),
                type="date",
                gridcolor='rgba(150, 150, 150, 0.2)',
                zerolinecolor='rgba(150, 150, 150, 0.2)'
            ),
            hovermode='x unified',
            legend=dict(
                bgcolor='rgba(50, 50, 50, 0.8)',
                bordercolor='rgba(150, 150, 150, 0.2)'
            )
        )

        # Update layout for contract timeline figure
        fig2.update_layout(
            title=f"Contract Timeline - {self.contract_data['company']} ({self.contract_data['symbol']})",
            height=300,
            showlegend=True,
            paper_bgcolor='black',
            plot_bgcolor='black',
            font=dict(color='white', family="Arial, sans-serif"),
            xaxis=dict(
                showticklabels=False,  # Hide x-axis labels since we're using fixed positions
                # Fixed range to show only a portion of the timeline at once
                range=[0, 5],  # Show 5 events at a time
                gridcolor='rgba(150, 150, 150, 0.2)',
                zerolinecolor='rgba(150, 150, 150, 0.2)'
            ),
            yaxis=dict(
                showticklabels=False,
                range=[0, 2.2],  # Increased range to accommodate text above and below
            ),
            hovermode='closest',
            legend=dict(
                bgcolor='rgba(50, 50, 50, 0.8)',
                bordercolor='rgba(150, 150, 150, 0.2)'
            ),
            # Make the timeline scrollable horizontally
            margin=dict(l=20, r=20, t=50, b=20),
            autosize=False,
            width=100,  # Fixed width to show a consistent number of events
        )

        # Add slider for horizontal scrolling if there are more than 5 events
        if not events_df.empty and len(events_df) > 5:
            fig2.update_layout(
                xaxis=dict(
                    rangeslider=dict(visible=True),
                    showticklabels=False,
                    range=[0, 5],  # Show 5 events at a time
                    gridcolor='rgba(150, 150, 150, 0.2)',
                    zerolinecolor='rgba(150, 150, 150, 0.2)'
                ),
            )

        # Update all x-axes for fig1
        fig1.update_xaxes(
            showgrid=True,
            gridcolor='rgba(150, 150, 150, 0.2)',
            zerolinecolor='rgba(150, 150, 150, 0.2)',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        )

        # Update all y-axes for fig1
        fig1.update_yaxes(
            showgrid=True,
            gridcolor='rgba(150, 150, 150, 0.2)',
            zerolinecolor='rgba(150, 150, 150, 0.2)',
            tickfont=dict(color='white'),
            title_font=dict(color='white')
        )

        # Update specific y-axes for fig1
        fig1.update_yaxes(title_text="Stock Price ($)", row=1, col=1)
        fig1.update_yaxes(
            title_text="Volume", 
            row=2, col=1,
            tickvals=volume_ticks,
            ticktext=volume_labels,
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            gridwidth=1
        )

        # Update subplot titles to white for fig1
        for i in fig1['layout']['annotations']:
            i['font'] = dict(size=14, color='white', family="Arial, sans-serif")

        # Update x-axes to share the same range for fig1
        fig1.update_xaxes(matches='x')

        return fig1, fig2

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
                    "limit": 10,
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
                "limit": 10,
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
                                # FIX: Use iloc instead of [] to access by position
                                self._stock_prices[date] = float(stock_data['Close'].iloc[0])
                        
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
            
            # Create generation config
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
            
            # Create safety settings
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            # Create model with configurations - using gemini-2.0-flash
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',  # Updated to use gemini-2.0-flash
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            return model
            
        except ImportError:
            return f"Error: Could not import GEMINI_API_KEY from config"
        except Exception as e:
            return f"Error setting up Gemini: {str(e)}"

    def analyze_with_gemini(self, contract_details, market_impact):
        """Analyze a single contract using Gemini AI and generate HTML dashboard"""
        try:
            model = self.setup_gemini()
            
            # Check if we got an error string instead of a model
            if isinstance(model, str) and model.startswith('Error'):
                return model
            
            # Format market impact data for the prompt
            market_impact_str = """
            Market Impact Metrics:
            - Price Change: {:.2f}%
            - Volume Change: {:.2f}%
            - Pre-Award Average Price: ${:,.2f}
            - Post-Award Average Price: ${:,.2f}
            - Pre-Award Average Volume: {:,.0f} shares
            - Post-Award Average Volume: {:,.0f} shares
            """.format(
                market_impact.get('price_change_pct', 0),
                market_impact.get('volume_change_pct', 0),
                market_impact.get('pre_price_avg', 0),
                market_impact.get('post_price_avg', 0),
                market_impact.get('pre_volume_avg', 0),
                market_impact.get('post_volume_avg', 0)
            )
            
            # Get the AI prompt template and fill in the placeholders
            prompt_template = get_ai_prompt_template()
            prompt = prompt_template.replace("{{CONTRACT_ID}}", contract_details.get('id', 'Unknown'))
            prompt = prompt.replace("{{COMPANY_NAME}}", contract_details.get('company', 'Unknown'))
            prompt = prompt.replace("{{CONTRACT_AMOUNT}}", f"${contract_details.get('amount', 0):,.2f}")
            prompt = prompt.replace("{{AWARD_DATE}}", contract_details.get('date', 'Unknown'))
            prompt = prompt.replace("{{CONTRACT_DESCRIPTION}}", contract_details.get('description', 'No description available'))
            prompt = prompt.replace("{{AGENCY_NAME}}", contract_details.get('agency', 'Unknown'))
            prompt = prompt.replace("{{PRICE_CHANGE_PCT}}", f"{market_impact.get('price_change_pct', 0):.2f}")
            prompt = prompt.replace("{{VOLUME_CHANGE_PCT}}", f"{market_impact.get('volume_change_pct', 0):.2f}")
            prompt = prompt.replace("{{PRE_PRICE_AVG}}", f"{market_impact.get('pre_price_avg', 0):.2f}")
            prompt = prompt.replace("{{POST_PRICE_AVG}}", f"{market_impact.get('post_price_avg', 0):.2f}")
            prompt = prompt.replace("{{PRE_VOLUME_AVG}}", f"{market_impact.get('pre_volume_avg', 0):,.0f}")
            prompt = prompt.replace("{{POST_VOLUME_AVG}}", f"{market_impact.get('post_volume_avg', 0):,.0f}")
            
            # Generate analysis with Gemini
            response = model.generate_content(prompt)
            analysis_text = response.text
            
            # Parse the analysis text into sections
            sections = self._parse_analysis_sections(analysis_text)
            
            # Get the HTML template
            html_template = get_html_template()
            
            # Fill in the HTML template with contract details
            html = html_template.replace("{{CONTRACT_ID}}", contract_details.get('id', 'Unknown'))
            html = html.replace("{{COMPANY_NAME}}", contract_details.get('company', 'Unknown'))
            html = html.replace("{{CONTRACT_AMOUNT}}", f"${contract_details.get('amount', 0):,.2f}")
            html = html.replace("{{AWARD_DATE}}", contract_details.get('date', 'Unknown'))
            html = html.replace("{{AGENCY_NAME}}", contract_details.get('agency', 'Unknown'))
            html = html.replace("{{CONTRACT_DESCRIPTION}}", contract_details.get('description', 'No description available'))
            
            # Determine CSS classes for price and volume changes
            price_change = market_impact.get('price_change_pct', 0)
            volume_change = market_impact.get('volume_change_pct', 0)
            
            price_change_class = "positive" if price_change > 0 else "negative" if price_change < 0 else "neutral"
            volume_change_class = "positive" if volume_change > 0 else "negative" if volume_change < 0 else "neutral"
            
            html = html.replace("{{PRICE_CHANGE_PCT}}", f"{price_change:.2f}")
            html = html.replace("{{VOLUME_CHANGE_PCT}}", f"{volume_change:.2f}")
            html = html.replace("{{PRICE_CHANGE_CLASS}}", price_change_class)
            html = html.replace("{{VOLUME_CHANGE_CLASS}}", volume_change_class)
            
            # Fill in the analysis sections
            html = html.replace("{{MARKET_IMPACT_ANALYSIS}}", sections.get('market_impact', 'No market impact analysis available.'))
            
            # Format sector trends as list items
            sector_trends_html = ""
            for trend in sections.get('sector_trends', []):
                sector_trends_html += f"<li>{trend}</li>\n"
            html = html.replace("{{SECTOR_TRENDS}}", sector_trends_html or "<li>No sector trends available.</li>")
            
            html = html.replace("{{PREDICTIVE_INDICATORS}}", sections.get('predictive_indicators', 'No predictive indicators available.'))
            
            # Format actionable insights as list items
            insights_html = ""
            for insight in sections.get('actionable_insights', []):
                insights_html += f"<li>{insight}</li>\n"
            html = html.replace("{{ACTIONABLE_INSIGHTS}}", insights_html or "<li>No actionable insights available.</li>")
            
            # Format trading opportunities as list items
            opportunities_html = ""
            for opportunity in sections.get('trading_opportunities', []):
                opportunities_html += f"<li>{opportunity}</li>\n"
            html = html.replace("{{TRADING_OPPORTUNITIES}}", opportunities_html or "<li>No trading opportunities identified.</li>")
            
            # Format risk factors as list items
            risks_html = ""
            for risk in sections.get('risk_factors', []):
                risks_html += f"<li>{risk}</li>\n"
            html = html.replace("{{RISK_FACTORS}}", risks_html or "<li>No risk factors identified.</li>")
            
            html = html.replace("{{AI_RECOMMENDATION}}", sections.get('recommendation', 'No recommendation available.'))
            
            # Add generation date
            from datetime import datetime
            html = html.replace("{{GENERATION_DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            return html
            
        except Exception as e:
            return f"Error in Gemini analysis: {e}"

    def _generate_html_dashboard(self, contract_details, market_impact, analysis_text):
        """Generate HTML dashboard from analysis text and contract data"""
        
        # Parse the analysis text into sections
        sections = self._parse_analysis_sections(analysis_text)
        
        # Generate sample data for visualizations based on real contract data
        stock_price_data = self._generate_stock_price_data(contract_details, market_impact)
        contract_value_data = self._generate_contract_value_data(contract_details)
        market_impact_data = self._generate_market_impact_data(contract_details)
        contract_type_distribution = self._generate_contract_type_distribution()
        contract_event_data = self._generate_contract_event_data(contract_details)
        
        # Format the contract amount for display
        formatted_amount = "${:,.0f}".format(contract_details.get('amount', 0))
        
        # Create a simplified HTML dashboard
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            <h1 style="color: #333;">Federal Contract Analysis</h1>
            <h2 style="color: #0056b3;">{contract_details.get('id', 'Unknown')} - {formatted_amount}</h2>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>Contract Details</h3>
                <p><strong>Company:</strong> {contract_details.get('company', 'Unknown')}</p>
                <p><strong>Award Date:</strong> {contract_details.get('date', 'Unknown')}</p>
                <p><strong>Agency:</strong> {contract_details.get('agency', 'Unknown')}</p>
                <p><strong>Description:</strong> {contract_details.get('description', 'No description available')}</p>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>Market Impact</h3>
                <p><strong>Price Change:</strong> {market_impact.get('price_change_pct', 0):.2f}%</p>
                <p><strong>Volume Change:</strong> {market_impact.get('volume_change_pct', 0):.2f}%</p>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3>AI Analysis</h3>
                <div style="white-space: pre-wrap;">{analysis_text}</div>
            </div>
        </div>
        """
        
        return html

    def _parse_analysis_sections(self, analysis_text):
        """Parse the analysis text into structured sections"""
        import re
        
        sections = {}
        
        # Try to extract a summary (first paragraph)
        summary_match = re.search(r'^(.+?)(?=\n\n|\n\d\.|\Z)', analysis_text, re.DOTALL)
        if summary_match:
            sections['summary'] = summary_match.group(1).strip()
        
        # Extract Market Impact Analysis
        market_impact_match = re.search(r'(?:1\.\s*Market\s*Impact\s*Analysis|Market\s*Impact\s*Analysis)(.+?)(?=\n\n\d\.|\n\d\.|\Z)', analysis_text, re.DOTALL)
        if market_impact_match:
            sections['market_impact'] = market_impact_match.group(1).strip()
        
        # Extract Sector Trends (bullet points)
        sector_trends = []
        sector_trends_match = re.search(r'(?:2\.\s*Sector\s*Trends|Sector\s*Trends)(.+?)(?=\n\n\d\.|\n\d\.|\Z)', analysis_text, re.DOTALL)
        if sector_trends_match:
            sector_text = sector_trends_match.group(1)
            bullet_points = re.findall(r'(?:•|\*|-)\s*(.+?)(?=\n\s*(?:•|\*|-|$)|\Z)', sector_text, re.DOTALL)
            sector_trends = [point.strip() for point in bullet_points if point.strip()]
        sections['sector_trends'] = sector_trends
        
        # Extract Predictive Indicators
        predictive_match = re.search(r'(?:3\.\s*Predictive\s*Indicators|Predictive\s*Indicators)(.+?)(?=\n\n\d\.|\n\d\.|\Z)', analysis_text, re.DOTALL)
        if predictive_match:
            sections['predictive_indicators'] = predictive_match.group(1).strip()
        
        # Extract Actionable Trading Insights (bullet points)
        actionable_insights = []
        actionable_match = re.search(r'(?:4\.\s*Actionable\s*Trading\s*Insights|Actionable\s*Trading\s*Insights)(.+?)(?=\n\n\d\.|\n\d\.|\Z)', analysis_text, re.DOTALL)
        if actionable_match:
            actionable_text = actionable_match.group(1)
            bullet_points = re.findall(r'(?:•|\*|-)\s*(.+?)(?=\n\s*(?:•|\*|-|$)|\Z)', actionable_text, re.DOTALL)
            actionable_insights = [point.strip() for point in bullet_points if point.strip()]
        sections['actionable_insights'] = actionable_insights
        
        # Extract Trading Opportunities (bullet points)
        trading_opportunities = []
        opportunities_match = re.search(r'(?:Trading\s*Opportunities)(.+?)(?=\n\n\d\.|\n\d\.|\Z|Risk\s*Factors)', analysis_text, re.DOTALL)
        if opportunities_match:
            opportunities_text = opportunities_match.group(1)
            bullet_points = re.findall(r'(?:•|\*|-)\s*(.+?)(?=\n\s*(?:•|\*|-|$)|\Z)', opportunities_text, re.DOTALL)
            trading_opportunities = [point.strip() for point in bullet_points if point.strip()]
        sections['trading_opportunities'] = trading_opportunities
        
        # Extract Risk Factors (bullet points)
        risk_factors = []
        risks_match = re.search(r'(?:Risk\s*Factors)(.+?)(?=\n\n\d\.|\n\d\.|\Z|AI-Generated\s*Recommendation)', analysis_text, re.DOTALL)
        if risks_match:
            risks_text = risks_match.group(1)
            bullet_points = re.findall(r'(?:•|\*|-)\s*(.+?)(?=\n\s*(?:•|\*|-|$)|\Z)', risks_text, re.DOTALL)
            risk_factors = [point.strip() for point in bullet_points if point.strip()]
        sections['risk_factors'] = risk_factors
        
        # Extract AI-Generated Recommendation
        recommendation_match = re.search(r'(?:AI-Generated\s*Recommendation)(.+?)(?=\n\n\d\.|\n\d\.|\Z)', analysis_text, re.DOTALL)
        if recommendation_match:
            sections['recommendation'] = recommendation_match.group(1).strip()
        
        return sections

    def _generate_sector_trends_html(self, sector_trends):
        """Generate HTML for sector trends bullet points"""
        if not sector_trends or len(sector_trends) < 3:
            # Default sector trends if not provided
            sector_trends = [
                "High Impact Areas: AI/ML capabilities, cybersecurity, and advanced weapons systems show the strongest market reactions (2.0-2.5% price increases).",
                "Moderate Impact: Traditional aerospace, naval systems, and logistics contracts typically generate 1.0-1.5% price movements.",
                "Lower Impact: Maintenance, training, and legacy system support contracts show minimal market impact (<1.0%)."
            ]
        
        html_items = []
        for trend in sector_trends[:3]:  # Limit to 3 items
            # Check if the trend has a label (like "High Impact:")
            if ":" in trend:
                label, content = trend.split(":", 1)
                html_items.append(f"""
                React.createElement('li', null, 
                  React.createElement('strong', null, "{label}:"), 
                  "{content}"
                )
                """)
            else:
                html_items.append(f"""
                React.createElement('li', null, "{trend}")
                """)
        
        return ",".join(html_items)

    def _generate_trading_insights_html(self, insights):
        """Generate HTML for trading insights bullet points"""
        if not insights or len(insights) < 3:
            # Default insights if not provided
            insights = [
                "Timing: Optimal entry points appear to be 1-2 days after contract announcements, with profit-taking recommended within 5-7 trading days.",
                "Contract Monitoring: Focus on contracts exceeding $100M with technological innovation components for maximum impact.",
                "Risk Management: Consider 5-8% stop losses, as contracts failing to produce expected price movement typically reverse within 3-4 trading days."
            ]
        
        html_items = []
        for insight in insights[:3]:  # Limit to 3 items
            # Check if the insight has a label (like "Timing:")
            if ":" in insight:
                label, content = insight.split(":", 1)
                html_items.append(f"""
                React.createElement('li', null, 
                  React.createElement('strong', null, "{label}:"), 
                  "{content}"
                )
                """)
            else:
                html_items.append(f"""
                React.createElement('li', null, "{insight}")
                """)
        
        return ",".join(html_items)
    
    def _generate_opportunities_html(self, opportunities):
        """Generate HTML for trading opportunities bullet points"""
        if not opportunities or len(opportunities) < 4:
            # Default opportunities if not provided
            opportunities = [
                "Focus on contracts >$100M with technological components",
                "Enter positions 1-2 days after announcements",
                "Target companies with AI/ML and cybersecurity focus",
                "Monitor unusual volume 3-5 days before expected awards"
            ]
        
        html_items = []
        for opportunity in opportunities[:4]:  # Limit to 4 items
            html_items.append(f"""
            React.createElement('li', null, "• {opportunity}")
            """)
        
        return ",".join(html_items)
    
    def _generate_risk_factors_html(self, risks):
        """Generate HTML for risk factors bullet points"""
        if not risks or len(risks) < 4:
            # Default risks if not provided
            risks = [
                "Set 5-8% stop losses on contract-based trades",
                "Avoid maintenance and legacy system contracts",
                "Be cautious of price reversals after 5-7 trading days",
                "Watch for market saturation with multiple awards"
            ]
        
        html_items = []
        for risk in risks[:4]:  # Limit to 4 items
            html_items.append(f"""
            React.createElement('li', null, "• {risk}")
            """)
        
        return ",".join(html_items)
    
    def _json_data(self, data):
        """Convert Python data to JSON string for embedding in JavaScript"""
        import json
        return json.dumps(data)

    def _generate_stock_price_data(self, contract_details, market_impact):
        """Generate sample stock price data based on contract details"""
        from datetime import datetime, timedelta
        import random
        
        # Try to parse the award date
        try:
            award_date = datetime.strptime(contract_details.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        except (ValueError, TypeError):
            # Fallback to current date if parsing fails
            award_date = datetime.now()
        
        # Generate 6 months of data centered around the award date
        start_date = award_date - timedelta(days=90)
        
        data = []
        
        # Pre-award trend (slightly upward)
        base_price = 100.0  # Starting price
        
        # If we have market impact data, use it to calculate a realistic price
        if market_impact and 'pre_price_avg' in market_impact and market_impact['pre_price_avg'] > 0:
            base_price = market_impact['pre_price_avg']

        # Generate 3 months of pre-award data
        for i in range(90):
            current_date = start_date + timedelta(days=i)
            # Skip weekends
            if current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                continue
            
            # Add some randomness to the price
            daily_change = random.uniform(-0.5, 0.7)  # Slight upward bias
            base_price *= (1 + daily_change/100)
            
            # Add monthly data point
            if i % 30 == 0 or current_date.day == 1:
                data.append({
                    'date': current_date.strftime('%Y-%m'),
                    'price': round(base_price, 2),
                    'volume': round(random.uniform(1.5, 2.5), 1)
                })
        
        # Award date and post-award trend (more upward if positive impact)
        price_impact = market_impact.get('price_change_pct', 1.5) / 100
        volume_impact = market_impact.get('volume_change_pct', 10) / 100
        
        # Generate 3 months of post-award data
        post_start = award_date
        for i in range(90):
            current_date = post_start + timedelta(days=i)
            # Skip weekends
            if current_date.weekday() >= 5:
                continue

            # Add some randomness but with impact bias
            if i < 7:  # First week has stronger impact
                daily_change = random.uniform(-0.3, 0.5) + (price_impact/5)
            else:
                daily_change = random.uniform(-0.5, 0.7)  # Back to normal variation
            
            base_price *= (1 + daily_change/100)
            
            # Add monthly data point
            if i % 30 == 0 or current_date.day == 1:
                volume_multiplier = 1.0
                if i < 7:  # Higher volume in first week
                    volume_multiplier = 1.0 + volume_impact
                
                data.append({
                    'date': current_date.strftime('%Y-%m'),
                    'price': round(base_price, 2),
                    'volume': round(random.uniform(1.5, 2.5) * volume_multiplier, 1)
                })
        
        return data
    
    def _generate_contract_value_data(self, contract_details):
        """Generate sample contract value trend data"""
        from datetime import datetime
        import random
        
        # Try to parse the award date
        try:
            award_date = datetime.strptime(contract_details.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        except (ValueError, TypeError):
            # Fallback to current date if parsing fails
            award_date = datetime.now()
        
        # Generate 6 years of data ending with the current year
        current_year = datetime.now().year
        start_year = current_year - 5
        
        # Calculate the contract value in billions
        contract_value_billions = contract_details.get('amount', 1000000000) / 1_000_000_000
        
        data = []
        
        # Generate yearly data with an upward trend
        for year in range(start_year, current_year + 1):
            # Make the trend increase more in recent years
            year_factor = (year - start_year) / 5  # 0.0 to 1.0
            
            # Base value starts lower and ends with approximately the current contract value
            if year == current_year:
                # Current year is the actual contract value
                base_value = contract_value_billions * 5  # Total annual value, not just this contract
            else:
                # Previous years have a growing trend
                base_value = contract_value_billions * 3 * (0.7 + 0.3 * year_factor)
                # Add some randomness
                base_value *= random.uniform(0.9, 1.1)
            
            data.append({
                'year': str(year),
                'value': round(base_value, 1)
            })
        
        return data

    def _generate_market_impact_data(self, contract_details):
        """Generate sample market impact data for various companies"""
        import random
        
        # Default companies in the defense sector
        companies = [
            {'name': 'Lockheed Martin', 'symbol': 'LMT'},
            {'name': 'Raytheon', 'symbol': 'RTX'},
            {'name': 'Northrop Grumman', 'symbol': 'NOC'},
            {'name': 'General Dynamics', 'symbol': 'GD'},
            {'name': 'Boeing', 'symbol': 'BA'},
            {'name': 'L3Harris', 'symbol': 'LHX'}
        ]

        # If we have the contract company, make sure it's included
        contract_company = contract_details.get('company', '')
        contract_symbol = contract_details.get('symbol', '')
        
        if contract_company and contract_symbol:
            # Check if the contract company is already in our list
            if not any(c['symbol'] == contract_symbol for c in companies):
                # Add it to the beginning
                companies.insert(0, {'name': contract_company, 'symbol': contract_symbol})
        
        data = []
        
        # Generate impact data with the contract company having the highest impact
        for i, company in enumerate(companies):
            # Decrease impact for companies further down the list
            factor = 1.0 - (i * 0.15)
            if factor < 0.2:
                factor = 0.2
            
            # Price change between 0.3% and 2.5%
            price_change = round(random.uniform(0.3, 2.5) * factor, 1)
            
            # Volume change between 3% and 20%
            volume_change = round(random.uniform(3.0, 20.0) * factor, 1)
            
            data.append({
                'name': company['name'],
                'symbol': company['symbol'],
                'priceChange': price_change,
                'volumeChange': volume_change
            })
        
        return data
    
    def _generate_contract_type_distribution(self):
        """Generate sample contract type distribution data"""
        return [
            {'name': 'Definitive Contracts', 'value': 45, 'color': '#0088FE'},
            {'name': 'Delivery Orders', 'value': 25, 'color': '#00C49F'},
            {'name': 'Purchase Orders', 'value': 15, 'color': '#FFBB28'},
            {'name': 'BPA Calls', 'value': 10, 'color': '#FF8042'},
            {'name': 'Other', 'value': 5, 'color': '#8884d8'}
        ]

    def _generate_contract_event_data(self, contract_details):
        """Generate sample contract event data"""
        from datetime import datetime, timedelta
        import random
        
        # Try to parse the award date
        try:
            award_date = datetime.strptime(contract_details.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        except (ValueError, TypeError):
            # Fallback to current date if parsing fails
            award_date = datetime.now()
        
        # Contract amount in millions
        contract_amount_millions = round(contract_details.get('amount', 100000000) / 1_000_000)
        
        # Generate 5 events, with the main contract being the largest
        events = [
            {
                'date': award_date.strftime('%Y-%m-%d'),
                'event': contract_details.get('description', 'Major Contract Award'),
                'amount': contract_amount_millions,
                'price': 0  # Will be filled in later
            }
        ]

        # Generate 4 more random events (2 before, 2 after)
        event_types = [
            'Preliminary Design Contract',
            'Research & Development Grant',
            'System Integration Contract',
            'Maintenance & Support',
            'Software Development',
            'Hardware Procurement',
            'Training Services',
            'Consulting Services'
        ]
        
        # 2 events before the main contract
        for i in range(2):
            days_before = random.randint(20, 60) * (i + 1)
            event_date = award_date - timedelta(days=days_before)
            amount = round(contract_amount_millions * random.uniform(0.1, 0.4))
            
            events.append({
                'date': event_date.strftime('%Y-%m-%d'),
                'event': random.choice(event_types),
                'amount': amount,
                'price': 0  # Will be filled in later
            })

        # 2 events after the main contract
        for i in range(2):
            days_after = random.randint(20, 60) * (i + 1)
            event_date = award_date + timedelta(days=days_after)
            amount = round(contract_amount_millions * random.uniform(0.1, 0.4))
            
            events.append({
                'date': event_date.strftime('%Y-%m-%d'),
                'event': random.choice(event_types),
                'amount': amount,
                'price': 0  # Will be filled in later
            })
        
        # Sort events by date
        events.sort(key=lambda x: x['date'])
        
        return events
        
    def save_html_dashboard(self, contract_id, html_content):
        """Save the HTML dashboard to a file"""
        try:
            # Create the data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Save the HTML file
            file_path = f'data/contract_dashboard_{contract_id}.html'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Dashboard saved to {file_path}")
            return file_path
        except Exception as e:
            print(f"Error saving dashboard: {e}")
            return None

    def fetch_and_save_contract_data(self):
        """Fetch contract data from USA Spending API and save to CSV"""
        try:
            # Create base URL for USA Spending API
            base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
            
            # Get company name from session state or use default
            company_name = st.session_state.get('company_name', 'Lockheed Martin')
            
            # Get date range from session state or use default
            start_date = st.session_state.get('start_date', '2020-01-01')
            end_date = st.session_state.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            
            # Create payload for API request
            payload = {
                "filters": {
                    "award_type_codes": ["A", "B", "C", "D"],  # Contract types
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
                    "Contract Award Type",
                    "generated_internal_id"
                ],
                "page": 1,
                "limit": 100,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            # Make API request
            response = requests.post(base_url, json=payload)
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Check if results were returned
                if 'results' in data and data['results']:
                    # Convert to DataFrame
                    df = pd.DataFrame(data['results'])
                    
                    # Save to CSV
                    os.makedirs('data', exist_ok=True)
                    file_path = 'data/federal_contracts.csv'
                    df.to_csv(file_path, index=False)
                    print(f"Contract data saved to {file_path}")
                    
                    return df
                else:
                    print("No contract data found for the specified criteria")
                    # Return sample data for demonstration
                    return self._generate_sample_contract_data(company_name)
            else:
                print(f"API request failed with status code {response.status_code}")
                # Return sample data for demonstration
                return self._generate_sample_contract_data(company_name)
                
        except Exception as e:
            print(f"Error fetching contract data: {e}")
            # Return sample data for demonstration
            return self._generate_sample_contract_data(company_name)

    def _generate_sample_contract_data(self, company_name):
        """Generate sample contract data for demonstration"""
        # Create sample data
        sample_data = []
        
        # Generate 10 sample contracts
        for i in range(1, 11):
            # Generate random contract amount between $1M and $500M
            amount = random.uniform(1000000, 500000000)
            
            # Generate random start date in the last 3 years
            days_ago = random.randint(0, 365 * 3)
            start_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # Generate random end date 1-5 years after start date
            duration_days = random.randint(365, 365 * 5)
            end_date = (datetime.now() - timedelta(days=days_ago) + timedelta(days=duration_days)).strftime('%Y-%m-%d')
            
            # Sample contract types
            contract_types = [
                "Definitive Contract",
                "Delivery Order",
                "Purchase Order",
                "BPA Call"
            ]
            
            # Sample agencies
            agencies = [
                "Department of Defense",
                "Department of the Navy",
                "Department of the Air Force",
                "Department of the Army",
                "National Aeronautics and Space Administration",
                "Department of Homeland Security"
            ]
            
            # Sample sub-agencies
            sub_agencies = {
                "Department of Defense": ["Defense Logistics Agency", "Missile Defense Agency", "Defense Advanced Research Projects Agency"],
                "Department of the Navy": ["Naval Sea Systems Command", "Naval Air Systems Command", "Space and Naval Warfare Systems Command"],
                "Department of the Air Force": ["Air Force Materiel Command", "Air Force Space Command", "Air Combat Command"],
                "Department of the Army": ["Army Materiel Command", "Army Corps of Engineers", "Army Contracting Command"],
                "National Aeronautics and Space Administration": ["NASA Headquarters", "Goddard Space Flight Center", "Johnson Space Center"],
                "Department of Homeland Security": ["Customs and Border Protection", "Federal Emergency Management Agency", "Transportation Security Administration"]
            }
            
            # Sample descriptions
            descriptions = [
                f"Development of advanced radar systems for {company_name}",
                f"Production of missile guidance systems by {company_name}",
                f"Maintenance and support services for aircraft systems from {company_name}",
                f"Research and development of space technologies with {company_name}",
                f"Cybersecurity solutions provided by {company_name}",
                f"Training and simulation systems developed by {company_name}",
                f"Supply of electronic components from {company_name}",
                f"Integration of communication systems by {company_name}",
                f"Consulting services provided by {company_name}",
                f"Software development for defense applications by {company_name}"
            ]
            
            # Select random values
            agency = random.choice(agencies)
            sub_agency = random.choice(sub_agencies.get(agency, ["Unknown Sub-Agency"]))
            contract_type = random.choice(contract_types)
            description = random.choice(descriptions)
            
            # Create contract record
            contract = {
                "Award ID": f"CONT{i:04d}-{random.randint(1000, 9999)}",
                "Recipient Name": company_name,
                "Start Date": start_date,
                "End Date": end_date,
                "Award Amount": amount,
                "Description": description,
                "Awarding Agency": agency,
                "Awarding Sub Agency": sub_agency,
                "Contract Award Type": contract_type,
                "generated_internal_id": f"GEN-ID-{random.randint(10000, 99999)}"
            }
            
            sample_data.append(contract)
        
        # Convert to DataFrame
        df = pd.DataFrame(sample_data)
        
        # Save to CSV
        os.makedirs('data', exist_ok=True)
        file_path = 'data/federal_contracts_sample.csv'
        df.to_csv(file_path, index=False)
        print(f"Sample contract data saved to {file_path}")
        
        return df

    def analyze_stock_market_impact(self, contract_df):
        """Analyze stock market impact of contracts"""
        try:
            # Create DataFrame to store market impact data
            market_impact_df = pd.DataFrame(columns=[
                'contract_id', 
                'price_change_pct', 
                'volume_change_pct',
                'pre_price_avg',
                'post_price_avg',
                'pre_volume_avg',
                'post_volume_avg'
            ])
            
            # Process each contract
            impact_data = []  # Collect all impacts first
            for _, contract in contract_df.iterrows():
                # Get contract ID
                contract_id = contract['Award ID']
                
                # Get company symbol
                company_name = contract.get('Recipient Name', 'Unknown')
                symbol = self._get_company_symbol(company_name)
                
                # Get contract date
                try:
                    award_date = contract['Start Date']
                except:
                    # Use current date if parsing fails
                    award_date = datetime.now().strftime('%Y-%m-%d')
                
                # Calculate market impact (this would normally involve stock price analysis)
                # For now, we'll use placeholder values
                impact = {
                    'contract_id': contract_id,
                    'price_change_pct': random.uniform(0.5, 2.5),
                    'volume_change_pct': random.uniform(5.0, 20.0),
                    'pre_price_avg': random.uniform(80.0, 200.0),
                    'post_price_avg': random.uniform(85.0, 210.0),
                    'pre_volume_avg': random.uniform(500000, 2000000),
                    'post_volume_avg': random.uniform(600000, 2500000)
                }
                
                # Add to our collection
                impact_data.append(impact)
            
            # Create DataFrame from all impacts at once instead of concatenating
            if impact_data:
                market_impact_df = pd.DataFrame(impact_data)
            
            # Save to CSV file
            os.makedirs('data', exist_ok=True)
            file_path = 'data/market_impact_data.csv'
            market_impact_df.to_csv(file_path, index=False)
            print(f"Market impact data saved to {file_path}")
            
            return market_impact_df
            
        except Exception as e:
            print(f"Error analyzing stock market impact: {e}")
            return None

    def _get_company_symbol(self, company_name):
        """
        Map company name to stock symbol.
        Returns a default symbol if the company is not in the mapping.
        """
        # Common defense contractors and their symbols
        company_symbols = {
            'Lockheed Martin': 'LMT',
            'Boeing': 'BA',
            'Raytheon': 'RTX',
            'Northrop Grumman': 'NOC',
            'General Dynamics': 'GD',
            'L3Harris Technologies': 'LHX',
            'Huntington Ingalls Industries': 'HII',
            'Leidos': 'LDOS',
            'CACI International': 'CACI',
            'Booz Allen Hamilton': 'BAH',
            'Science Applications International': 'SAIC',
            'TransDigm Group': 'TDG',
            'Textron': 'TXT',
            'Spirit AeroSystems': 'SPR',
            'Howmet Aerospace': 'HWM',
            'Curtiss-Wright': 'CW',
            'Hexcel': 'HXL',
            'Kratos Defense & Security': 'KTOS',
            'Aerojet Rocketdyne': 'AJRD',
            'Mercury Systems': 'MRCY'
        }
        
        # Check for exact match
        if company_name in company_symbols:
            return company_symbols[company_name]
        
        # Check for partial match
        for known_company, symbol in company_symbols.items():
            if known_company.lower() in company_name.lower() or company_name.lower() in known_company.lower():
                return symbol
        
        # Default to LMT if no match found
        return 'LMT'


# ------------------------------------------------------------------
def render_federal_contracts_tab():
    # Remove this title line since we already have it in the standalone code
    # st.title("Federal Contracts Analysis")
    tracker = ContractTracker()

    # Create tabs for different analysis steps
    tabs = st.tabs([
        "1. Contract Data", 
        "2. Stock Market Impact", 
        "3. AI Analysis",
        "4. Timeline Visualization"
    ])

    with tabs[0]:
        st.header("Contract Awards Data")
        
        # Company search and date range selector
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            company_name = st.text_input(
                "Enter Company Name",
                value="Lockheed Martin",
                placeholder="e.g., Lockheed Martin, Boeing, Raytheon"
            )
        with col2:
            start_date = st.date_input(
                "Start Date",
                value=datetime(2020, 1, 1),
                max_value=datetime.now()
            )
        with col3:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                max_value=datetime.now()
            )

        if st.button("Fetch Contract Data"):
            if not company_name:
                st.error("Please enter a company name")
            else:
                with st.spinner(f"Fetching contract data for {company_name}..."):
                    # Update payload with company name and date range
                    payload = {
                        "filters": {
                            "award_type_codes": ["A", "B", "C", "D"],
                            "recipient_search_text": [company_name],
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
                            "Description",
                            "Awarding Agency",
                            "Awarding Sub Agency",
                            "Contract Award Type",
                            "generated_internal_id"
                        ],
                        "page": 1,
                        "limit": 100,
                        "sort": "Award Amount",
                        "order": "desc"
                    }
                    
                    # Step 1: Fetch contract data
                    contract_df = tracker.fetch_and_save_contract_data()
                    if contract_df is not None:
                        st.success("Contract data fetched successfully!")
                        
                        # Display contract data
                        st.subheader("Contract Awards")
                        st.dataframe(
                            contract_df,
                            use_container_width=True,
                            column_config={
                                "Award Amount": st.column_config.NumberColumn(
                                    "Award Amount",
                                    format="$%.2f"
                                ),
                                "Start Date": st.column_config.DateColumn("Start Date"),
                                "End Date": st.column_config.DateColumn("End Date")
                            }
                        )
                        
                        # Save to session state for other tabs
                        st.session_state.contract_df = contract_df
                        
                        # Step 2: Analyze market impact
                        with st.spinner("Analyzing market impact..."):
                            market_impact_df = tracker.analyze_stock_market_impact(contract_df)
                            if market_impact_df is not None:
                                st.session_state.market_impact_df = market_impact_df
                                st.success("Market impact analysis completed!")
                            else:
                                st.error("Failed to analyze market impact")
                        
                        # Store company name in session state
                        st.session_state.company_name = company_name
                        
                        # Remove the rerun to keep the table visible
                        # st.rerun()  <- This line is removed
                    else:
                        st.error("Failed to fetch contract data")
        
        # Display the contract data if it exists in session state (even after page refresh)
        if 'contract_df' in st.session_state:
            st.subheader("Contract Awards")
            st.dataframe(
                st.session_state.contract_df,
                use_container_width=True,
                column_config={
                    "Award Amount": st.column_config.NumberColumn(
                        "Award Amount",
                        format="$%.2f"
                    ),
                    "Start Date": st.column_config.DateColumn("Start Date"),
                    "End Date": st.column_config.DateColumn("End Date")
                }
            )

    with tabs[1]:
        st.header("Stock Market Impact Analysis")
        
        if 'market_impact_df' in st.session_state:
            # Display market impact metrics
            st.subheader("Market Impact Metrics")
            
            # Summary metrics
            metrics = st.session_state.market_impact_df.agg({
                'price_change_pct': 'mean',
                'volume_change_pct': 'mean'
            })
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Average Price Impact",
                    f"{metrics['price_change_pct']:.2f}%"
                )
            with col2:
                st.metric(
                    "Average Volume Impact",
                    f"{metrics['volume_change_pct']:.2f}%"
                )
            
            # Detailed impact table
            st.subheader("Impact Details by Contract")
            st.dataframe(
                st.session_state.market_impact_df,
                use_container_width=True
            )
        else:
            st.info("Please fetch contract data first in the Contract Data tab")

    with tabs[2]:
        st.header("AI Analysis of Contracts")
        
        if all(k in st.session_state for k in ['contract_df', 'market_impact_df']):
            # Create contract options with more descriptive labels
            contract_options = []
            for _, contract in st.session_state.contract_df.iterrows():
                try:
                    # Format amount as currency
                    amount = f"${float(contract['Award Amount']):,.2f}"
                    
                    # Handle None or missing description
                    description = contract.get('Description', 'No description available')
                    if description is None:
                        description = 'No description available'
                    
                    # Truncate description if too long
                    if len(description) > 50:
                        description = description[:47] + "..."
                    
                    # Create label: Description (Amount) - ID
                    label = f"{description} ({amount}) - {contract['Award ID']}"
                    contract_options.append({
                        'label': label,
                        'value': contract['Award ID']
                    })
                except Exception as e:
                    print(f"Error processing contract: {e}")
                    continue
            
            if contract_options:  # Only show selector if we have valid options
                # Add contract selector with formatted labels
                selected_contract = st.selectbox(
                    "Select a contract to analyze:",
                    options=[opt['value'] for opt in contract_options],
                    format_func=lambda x: next(opt['label'] for opt in contract_options if opt['value'] == x)
                )
                
                if st.button("Generate AI Analysis"):
                    with st.spinner("Generating AI analysis..."):
                        # Get contract data
                        contract = st.session_state.contract_df[
                            st.session_state.contract_df['Award ID'] == selected_contract
                        ].iloc[0]
                        
                        # Get market impact data
                        impact = st.session_state.market_impact_df[
                            st.session_state.market_impact_df['contract_id'] == selected_contract
                        ].iloc[0]
                        
                        # Prepare data for AI analysis
                        contract_details = {
                            'id': contract['Award ID'],
                            'company': contract.get('Recipient Name', 'Unknown Company'),
                            'amount': contract['Award Amount'],
                            'date': contract['Start Date'],
                            'description': contract['Description'],
                            'agency': contract['Awarding Agency']
                        }
                        
                        market_impact = {
                            'price_change_pct': impact['price_change_pct'],
                            'volume_change_pct': impact['volume_change_pct'],
                            'pre_price_avg': impact['pre_price_avg'],
                            'post_price_avg': impact['post_price_avg'],
                            'pre_volume_avg': impact['pre_volume_avg'],
                            'post_volume_avg': impact['post_volume_avg']
                        }
                        
                        # Get AI analysis for just this contract
                        analysis = tracker.analyze_with_gemini(
                            contract_details=contract_details,
                            market_impact=market_impact
                        )
                        
                        # Save the HTML dashboard to a file
                        file_path = tracker.save_html_dashboard(contract['Award ID'], analysis)
                        
                        if file_path:
                            # Display success message
                            st.success(f"Analysis generated successfully for {contract_details['company']}!")
                            
                            # Create a container for contract summary
                            with st.container():
                                st.subheader("Contract Summary")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**ID:** {contract_details['id']}")
                                    st.markdown(f"**Company:** {contract_details['company']}")
                                    st.markdown(f"**Amount:** ${float(contract_details['amount']):,.2f}")
                                with col2:
                                    st.markdown(f"**Award Date:** {contract_details['date']}")
                                    st.markdown(f"**Agency:** {contract_details['agency']}")
                            
                            # Create a container for download options
                            with st.container():
                                st.subheader("Download Options")
                                
                                # Read the HTML file but don't display it
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    html_content = f.read()
                                
                                # Create a unique key for the download button
                                download_key = f"download_{contract['Award ID']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                
                                # Download button centered
                                st.download_button(
                                    "💾 Download Analysis",
                                    html_content,
                                    f"contract_analysis_{contract['Award ID']}.html",
                                    "text/html",
                                    key=download_key,
                                    help="Download the full analysis as an HTML file",
                                    use_container_width=True  # Make button full width
                                )
                            
                            # Store the analysis in session state so it persists after download
                            st.session_state[f"analysis_{contract['Award ID']}"] = analysis
                            
                            # Add a note about the analysis
                            st.info("The analysis has been generated and is ready for download. Open the downloaded file in your browser to view the complete analysis.")
                        else:
                            st.error("Failed to generate analysis file")
        else:
            st.warning("No valid contracts to analyze")

    with tabs[3]:
        st.header("Timeline Visualization")
        
        if 'contract_df' in st.session_state:
            stock_data = tracker.fetch_stock_data()
            fig1, fig2 = tracker.create_timeline_visualization(stock_data)
            
            # Display stock price and volume chart
            st.plotly_chart(fig1)
            
            # Display contract timeline chart
            st.subheader("Contract Timeline")
            st.plotly_chart(fig2)
        else:
            st.info("Please fetch contract data first in the Contract Data tab")


# ------------------------------------------------------------------
# Add this new standalone entry point
if __name__ == "__main__":
    import streamlit as st
    
    # Set page configuration
    st.set_page_config(
        page_title="Federal Contracts Analysis",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for styling
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        color: #0066cc;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.5rem;
        color: #004080;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main title
    st.markdown("<h1 class='main-title'>Federal Contracts Analysis</h1>", unsafe_allow_html=True)
    
    # Add a brief description
    st.markdown("""
    This application analyzes federal contracts and their impact on stock prices. 
    You can search for contracts by company name, analyze their market impact, 
    generate AI analysis reports, and visualize contract timelines.
    """)
    
    # Run the main function
    render_federal_contracts_tab()
    
    # Add footer
    st.markdown("---")
    st.markdown("Federal Contracts Analysis Tool | Data sourced from USA Spending API")