# AI-Web-Scraper
An AI web scraper using ollama, brightdata, selenium and other libraries.

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

## Interactive Brokers Setup

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

## Setup
1. Copy `.env.example` to `.env`
2. Add your API keys to `.env`
