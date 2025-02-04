import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=True)

# API Keys
QUIVER_API_KEY = os.getenv('QUIVER_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
INSTAGRAM_API_KEY = os.getenv('INSTAGRAM_API_KEY')
X_API_KEY = os.getenv('X_API_KEY')
AZURE_API_KEY = os.getenv('AZURE_API_KEY')

# IB Configuration
IB_CONFIG = {
    'host': os.getenv('IB_HOST', '127.0.0.1'),
    'port': int(os.getenv('IB_PORT', '7497')),
    'client_id': int(os.getenv('IB_CLIENT_ID', '1'))
}

# List of stocks known to be traded by politicians
POLITICIAN_STOCKS = {}

# Add some recent mock data for testing
RECENT_TRADES = [
    {
        'date': '2024-02-15',
        'trader': 'Nancy Pelosi',
        'chamber': 'House',
        'stock': 'NVDA (NVIDIA Corporation)',
        'action': 'Purchase',
        'volume': '50,000',
        'transaction_total': '$15,000,000',
        'reason': 'New Investment'
    },
    {
        'date': '2024-02-10',
        'trader': 'Dan Crenshaw',
        'chamber': 'House',
        'stock': 'AAPL (Apple Inc.)',
        'action': 'Sale',
        'volume': '25,000',
        'transaction_total': '$5,000,000',
        'reason': 'Portfolio Rebalancing'
    },
    # Add more recent trades...
]

# Azure OpenAI Configuration
AZURE_OPENAI_CONFIG = {
    'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview'),
    'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT', 'https://SwingPhiDev.openai.azure.com/'),
    'deployment_name': os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
}

def add_mock_recent_trades(self):
    """Add mock recent trades for testing"""
    for trade in RECENT_TRADES:
        self.data.append(trade) 