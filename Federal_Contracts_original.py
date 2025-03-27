import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

class ContractTracker:
    def __init__(self):
        self.contract_data = {
            'id': 'LMT2024001',
            'company': 'Lockheed Martin',
            'symbol': 'LMT',
            'amount': 156000000,
            'awarded_date': '2024-01-15',
            'completion_date': '2025-12-31',
            'events': [
                {'date': '2023-12-01', 'event': 'RFP Released', 'price': 450.20},
                {'date': '2024-01-15', 'event': 'Contract Awarded', 'price': 458.75},
                {'date': '2024-01-30', 'event': 'Program Initiation', 'price': 465.30},
                {'date': '2024-02-08', 'event': 'First Milestone', 'price': 472.15}
            ],
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
        """Fetch stock data from yfinance"""
        start_date = '2023-01-01'
        ticker = yf.Ticker(self.contract_data['symbol'])
        df = ticker.history(start=start_date)
        return df

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
        events_df = pd.DataFrame(self.contract_data['events'])
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
            showlegend=True
        )

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

if __name__ == "__main__":
    main()