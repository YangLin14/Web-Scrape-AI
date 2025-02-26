import streamlit as st
from scrape import (
    scrape_website, 
    split_dom_content, 
    clean_body_content, 
    extract_body_content,
)
from gemini_helper import get_gemini_response, format_table_response, process_image_response, preprocess_query
from parse import scrape_x, scrape_instagram, scrape_government
from datetime import datetime, timedelta
import os
import pandas as pd
from main_collector import collect_politician_trades
from politician_trades import PoliticianTradesApp
from config import GEMINI_API_KEY
from tiingo_helper import fetch_stock_news, search_tickers, get_news_statistics, save_news_data, fetch_politician_trading_news
import requests
from Federal_Contracts import render_federal_contracts_tab

# Set page config
st.set_page_config(
    layout="wide", 
    page_title="AI Web Scraper",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS with better visual hierarchy and modern styling
st.markdown("""
<style>
    /* Global styles */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
        padding: 2rem;
        min-height: 100vh;
    }
    
    /* Main title styling */
    .main-title {
        text-align: center;
        padding: 2rem 0;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 2.5rem;
        background: linear-gradient(120deg, #2196F3, #1565C0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    
    /* Section titles */
    .section-title {
        color: #1565C0;
        padding: 0.75rem 0;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid rgba(33, 150, 243, 0.3);
        letter-spacing: -0.3px;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.2em;
        background: linear-gradient(135deg, #2196F3, #1565C0);
        color: white;
        border: none;
        font-weight: 500;
        letter-spacing: 0.3px;
        transition: all 0.3s ease;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        background: linear-gradient(135deg, #1E88E5, #0D47A1);
    }
    
    /* Input fields - Updated for better text visibility */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid rgba(33, 150, 243, 0.2);
        padding: 0.75rem 1rem;
        background-color: white;
        transition: all 0.2s ease;
        color: #0A1929;  /* Darker text color for better readability */
        font-size: 1rem;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #2196F3;
        box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
    }
    
    /* Placeholder text styling */
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #64748B;  /* Softer color for placeholder text */
        opacity: 0.8;
    }
    
    /* Text area specific styling */
    .stTextArea > div > div {
        color: #0A1929;  /* Ensures consistent text color */
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        color: #0A1929;
    }
    
    /* Make sure all text inputs have good contrast */
    [data-baseweb="input"], 
    [data-baseweb="textarea"] {
        color: #0A1929 !important;
    }
    
    /* Chat styling - Dark mode */
    .chat-message {
        padding: 1.25rem;
        margin: 0.75rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: #E2E8F0;  /* Light text for dark mode */
    }
    .user-message {
        background: #1E293B;  /* Dark blue background */
        border-left: 4px solid #3B82F6;
    }
    .assistant-message {
        background: #0F172A;  /* Darker blue background */
        border-left: 4px solid #64748B;
    }
    
    /* Chat container styling */
    [data-testid="stChatMessageContent"] {
        background-color: transparent !important;
        box-shadow: none !important;
        color: #E2E8F0 !important;
    }
    
    /* Chat message avatar container */
    [data-testid="stChatMessageAvatar"] {
        background-color: transparent !important;
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        border-color: #1E293B !important;
    }
    
    /* Chat input text */
    .stChatInputContainer textarea {
        color: #E2E8F0 !important;
        background-color: #1E293B !important;
    }
    
    /* Chat input placeholder */
    .stChatInputContainer textarea::placeholder {
        color: #94A3B8 !important;
    }
    
    /* Chat background */
    [data-testid="stChatMessageContainer"] {
        background-color: #0F172A !important;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Tab styling */
    .stTabs {
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 56px;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 12px 12px 0 0;
        gap: 8px;
        padding: 0 24px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2196F3, #1565C0) !important;
        color: white !important;
    }
    
    /* Success message styling */
    .stSuccess {
        background: linear-gradient(135deg, #4CAF50, #388E3C);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(76, 175, 80, 0.2);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        border: 1px solid rgba(33, 150, 243, 0.2);
    }
    
    /* Column styling */
    [data-testid="column"] {
        padding: 1.5rem;
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(33, 150, 243, 0.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #2196F3, #1565C0);
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #1E88E5, #0D47A1);
    }
    
    /* Remove container backgrounds */
    .element-container {
        background-color: transparent !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #2196F3 !important;
    }
    
    /* Table styling */
    .element-container div.markdown-body table {
        background-color: #1E293B;
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
        color: #E2E8F0;
    }
    
    .element-container div.markdown-body table th,
    .element-container div.markdown-body table td {
        border: 1px solid #2D3748;
        padding: 8px 12px;
        text-align: left;
    }
    
    .element-container div.markdown-body table th {
        background-color: #2D3748;
        font-weight: 600;
    }
    
    .element-container div.markdown-body table tr:nth-child(even) {
        background-color: #243246;
    }
    
    .element-container div.markdown-body table tr:hover {
        background-color: #2D3748;
    }
    
    /* Table container */
    div[style*="overflow-x: auto"] {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Wrap the entire content in a div with the main class
# st.markdown('<div class="main">', unsafe_allow_html=True)

# Main title with custom styling
st.markdown("<h1 class='main-title'>AI Web Scraper & Analyzer</h1>", unsafe_allow_html=True)

# Create tabs for different scraping methods
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 Web Scraping", 
    "💬 Analysis & Chat", 
    "📊 Politician Trades", 
    "📰 News",
    "🏢 USA Spending"
])

with tab1:
    # Scraping section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<h3 class='section-title'>Custom URL Scraping</h3>", unsafe_allow_html=True)
        url = st.text_input("Enter Website URL:", placeholder="https://example.com")
        if st.button("🔍 Scrape Site", key="scrape_url"):
            st.write("Scraping the website...")
            result = scrape_website(url)
            body_content = extract_body_content(result)
            clean_content = clean_body_content(body_content)
            
            # Initialize storage if not exists
            if 'all_scraped_data' not in st.session_state:
                st.session_state.all_scraped_data = []
                st.session_state.dom_content = ""
            
            # Append new data and update combined content
            st.session_state.all_scraped_data.append({
                "source": url,
                "content": clean_content,
                "timestamp": datetime.now().isoformat()
            })
            st.session_state.dom_content = "\n\n".join([item['content'] for item in st.session_state.all_scraped_data])
            st.success("✅ Successfully scraped website!")
            # Automatically analyze stock trading information
            with st.spinner("Analyzing trading information..."):
                initial_analysis = get_gemini_response(
                    split_dom_content(result),
                    """Analyze the content"""
                )
                if initial_analysis:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": format_table_response(
                            "### Recent Trading Activities\n\n" + initial_analysis
                        )
                    })
                    st.rerun()

    with col2:
        st.markdown("<h3 class='section-title'>Quick Scrape</h3>", unsafe_allow_html=True)
        if st.button("🐦 X (Twitter)", key="scrape_x", help="Scrape from X/Twitter"):
            with st.spinner("Scraping X..."):
                result = scrape_x()
                if result:
                    # Initialize storage if not exists
                    if 'all_scraped_data' not in st.session_state:
                        st.session_state.all_scraped_data = []
                        st.session_state.dom_content = ""
                    
                    # Append new data and update combined content
                    st.session_state.all_scraped_data.append({
                        "source": "X (Twitter)",
                        "content": result,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.session_state.dom_content = "\n\n".join([item['content'] for item in st.session_state.all_scraped_data])
                    st.success("✅ Successfully scraped X!")
                    
                    # Automatically analyze stock trading information
                    with st.spinner("Analyzing trading information..."):
                        initial_analysis = get_gemini_response(
                            split_dom_content(result),
                            """Analyze the content and create a detailed table of stock trading activities with the following columns:
                            - Trader/Entity: Who made the trade
                            - Chamber: House or Senate or other
                            - Action: Buy or Sell
                            - Stock: Stock symbol and company name
                            - Price: Trading price for each share
                            - Volume: Number of shares for the stock
                            - Date: When the trade occurred
                            - Reason: Motivation or context for the trade
                            - Transaction Total: Total amount of money spent or received
                            
                            Only include actual trading activities, not general market commentary. Format as a clean markdown table.""",
                            response_format="table"
                        )
                        if initial_analysis:
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": format_table_response(
                                    "### Recent Trading Activities\n\n" + initial_analysis
                                )
                            })
                            st.rerun()
        
        if st.button("📸 Instagram", key="scrape_instagram", help="Scrape from Instagram"):
            with st.spinner("Scraping Instagram..."):
                result = scrape_instagram()
                if result:
                    cleaned_content = clean_body_content(extract_body_content(result))
                    # Append to storage
                    st.session_state.all_scraped_data.append({
                        "source": "Instagram",
                        "content": cleaned_content,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.session_state.dom_content = "\n\n".join([item['content'] for item in st.session_state.all_scraped_data])
                    st.success("✅ Successfully scraped Instagram!")
                    
                    # Automatically analyze stock trading information
                    with st.spinner("Analyzing trading information..."):
                        initial_analysis = get_gemini_response(
                            split_dom_content(cleaned_content),
                            """Analyze the content and create a detailed table of stock trading activities with the following columns:
                            - Trader/Entity: Who made the trade
                            - Action: Buy or Sell
                            - Stock: Stock symbol and company name
                            - Price: Trading price
                            - Volume: Number of shares (if available)
                            - Date: When the trade occurred
                            - Reason: Motivation or context for the trade
                            
                            Only include actual trading activities, not general market commentary. Format as a clean markdown table.""",
                            response_format="table"
                        )
                        if initial_analysis:
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": format_table_response(
                                    "### Recent Trading Activities\n\n" + initial_analysis
                                )
                            })
                            st.rerun()
        
        if st.button("🏛️ Government", key="scrape_gov", help="Scrape from Government site"):
            with st.spinner("Scraping Government site..."):
                result = scrape_government()
                if result:
                    cleaned_content = clean_body_content(extract_body_content(result))
                    # Append to storage
                    st.session_state.all_scraped_data.append({
                        "source": "Government",
                        "content": cleaned_content,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.session_state.dom_content = "\n\n".join([item['content'] for item in st.session_state.all_scraped_data])
                    st.success("✅ Successfully scraped Government site!")
                    
                    # Automatically analyze stock trading information
                    with st.spinner("Analyzing trading information..."):
                        initial_analysis = get_gemini_response(
                            split_dom_content(cleaned_content),
                            """Analyze the content and create a detailed table of stock trading activities with the following columns:
                            - Trader/Entity: Who made the trade
                            - Action: Buy or Sell
                            - Stock: Stock symbol and company name
                            - Price: Trading price
                            - Volume: Number of shares (if available)
                            - Date: When the trade occurred
                            - Reason: Motivation or context for the trade
                            
                            Only include actual trading activities, not general market commentary. Format as a clean markdown table.""",
                            response_format="table"
                        )
                        if initial_analysis:
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": format_table_response(
                                    "### Recent Trading Activities\n\n" + initial_analysis
                                )
                            })
                            st.rerun()

with tab2:
    st.markdown("<h3 class='section-title'>AI Analysis & Chat Assistant</h3>", unsafe_allow_html=True)
    
    # Show scraped content expander
    if "all_scraped_data" in st.session_state and len(st.session_state.all_scraped_data) > 0:
        with st.expander("📄 View Raw Content", expanded=False):
            for idx, data in enumerate(st.session_state.all_scraped_data, 1):
                st.markdown(f"**Scrape #{idx} ({data['source']}) - {data['timestamp']}**")
                st.text_area(f"Content #{idx}", data['content'], height=200, key=f"scraped_{idx}")
    
    # Initialize chat history if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface with analysis integration
    chat_container = st.container()
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            message_class = "user-message" if message["role"] == "user" else "assistant-message"
            with st.chat_message(message["role"]):
                if "```markdown" in message["content"]:
                    # It's a table, render with HTML
                    st.markdown(message["content"], unsafe_allow_html=True)
                else:
                    # Regular message
                    st.markdown(f"<div class='chat-message {message_class}'>{message['content']}</div>", 
                              unsafe_allow_html=True)
        
        # Chat/Analysis input
        if prompt := st.chat_input("Ask questions about financial data...", key="chat_input"):
            # Add user message to chat
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.spinner("Processing..."):
                # Preprocess the query
                processed_query = preprocess_query(prompt)
                
                # Show processing details in debug mode
                if st.session_state.get('debug_mode', False):
                    st.write("Processed Query:", processed_query)
                
                context = st.session_state.get('dom_content', '')
                if context:
                    dom_chunks = split_dom_content(context)
                    chat_context = "\n".join([
                        f"{msg['role']}: {msg['content']}" 
                        for msg in st.session_state.chat_history[-3:]
                    ])
                    
                    # Determine response format based on processed query
                    response_format = "text"
                    if processed_query['analysis_type'] in ['price', 'volume']:
                        response_format = "table"
                    elif "visualize" in processed_query['processed_query'].lower():
                        response_format = "image"
                    
                    # Get response using processed query
                    response = get_gemini_response(
                        dom_chunks,
                        processed_query['processed_query'],
                        response_format=response_format
                    )
                    
                    # Format response based on type
                    if isinstance(response, dict) and response.get('type') == 'image':
                        formatted_response = process_image_response(response)
                    elif response_format == "table":
                        formatted_response = format_table_response(response)
                    else:
                        formatted_response = response
                        
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": formatted_response
                    })
                else:
                    response = "Please scrape some content first before asking questions."
            
            st.rerun()
    
    # Control buttons in a horizontal layout
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# Restore original Politician Trades tab
with tab3:
    st.markdown("<h3 class='section-title'>Politician Trading Data (US Senate Financial Disclosure)</h3>", unsafe_allow_html=True)
    
    # Create input and scrape section
    input_col1, input_col2 = st.columns([3, 1])
    
    with input_col1:
        search_name = st.text_input(
            "Enter politician's first name:",
            placeholder="e.g. Thomas",
            key="politician_search_name"
        )
    
    with input_col2:
        if st.button("🔍 Scrape Trades", key="scrape_trades"):
            if not search_name:
                st.warning("Please enter a name to search")
            else:
                try:
                    with st.spinner(f"Scraping trade data for '{search_name}'..."):
                        app = PoliticianTradesApp()
                        app.fetch_senate_trades(search_name)
                        
                        # Save to CSV with timestamp
                        if app.data:
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            csv_filename = f"data/politician_trades_{timestamp}.csv"
                            os.makedirs('data', exist_ok=True)
                            
                            df = pd.DataFrame(app.data)
                            df.to_csv(csv_filename, index=False)
                            st.session_state.last_scrape_file = csv_filename
                            st.session_state.trade_data = app.data
                            st.success(f"✅ Successfully scraped and saved trade data!")
                        else:
                            st.warning("No trade data found for the given name")
                except Exception as e:
                    st.error(f"Error scraping trade data: {str(e)}")
    
    # Add a divider
    st.markdown("---")
    
    # Display saved data section
    try:
        # Get list of all saved CSV files
        data_files = []
        if os.path.exists('data'):
            for file in os.listdir('data'):
                if file.startswith('politician_trades_') and file.endswith('.csv'):
                    data_files.append(file)
        
        if data_files:
            # Sort files by date (newest first)
            data_files.sort(reverse=True)
            
            # Create file selector
            selected_file = st.selectbox(
                "Select saved trade data:",
                options=data_files,
                format_func=lambda x: f"Trade Data from {x.split('_')[2].split('.')[0]}"
            )
            
            if selected_file:
                # Load the selected data
                df = pd.read_csv(os.path.join('data', selected_file))
                
                # Get unique politicians and their chambers
                politicians = {}
                for _, row in df.iterrows():
                    trader = row.get('trader', 'Unknown')
                    chamber = row.get('chamber', 'Unknown')
                    politicians[trader] = chamber
                
                # Create selection columns
                search_col1, search_col2 = st.columns([3, 1])
                
                with search_col1:
                    # Create a selectbox with all politician names
                    selected_politician = st.selectbox(
                        "Select a politician:",
                        options=sorted(politicians.keys()),
                        format_func=lambda x: f"{x} ({politicians[x]})"
                    )
                
                with search_col2:
                    # Chamber filter still shows the selected politician's chamber
                    chamber = politicians.get(selected_politician, 'Unknown')
                    st.markdown(f"### Chamber\n{chamber}")
                
                if selected_politician:
                    # Filter data for selected politician
                    filtered_data = df[df['trader'] == selected_politician]
                    
                    if not filtered_data.empty:
                        # Display basic statistics
                        st.markdown("### Trading Summary")
                        stats_col1, stats_col2 = st.columns(2)
                        
                        with stats_col1:
                            st.metric("Total Trades", len(filtered_data))
                        with stats_col2:
                            unique_stocks = len(filtered_data['stock'].unique())
                            st.metric("Unique Stocks", unique_stocks)
                        
                        # Display the filtered data in a table
                        st.markdown("### Trading Details")
                        st.dataframe(
                            filtered_data,
                            column_config={
                                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")
                            },
                            hide_index=True
                        )
                        
                        # Add download button for the filtered data
                        csv = filtered_data.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Trading Data",
                            data=csv,
                            file_name=f"{selected_politician.replace(' ', '_')}_trades.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(f"No trading data found for {selected_politician}")
        else:
            st.info("No saved trade data available. Use the search above to scrape new data.")
            
    except Exception as e:
        st.error(f"Error loading trading data: {str(e)}")

# Update News tab to include both stock and politician news
with tab4:
    st.markdown("<h3 class='section-title'>News Dashboard (Tiingo)</h3>", unsafe_allow_html=True)
    
    # Create tabs within the News tab
    news_tab1, news_tab2 = st.tabs(["Stock Market News", "Politician Trading News"])
    
    with news_tab1:
        st.markdown("### Stock Market News")
        
        # Create search filters
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Stock ticker search with autocomplete
            ticker_search = st.text_input(
                "Search stocks:",
                placeholder="Enter company name or ticker (e.g., AAPL, Tesla)",
                key="ticker_search"
            )
            
            if ticker_search:
                results = search_tickers(ticker_search)
                if results:
                    ticker_options = [f"{r['ticker']} - {r['name']}" for r in results]
                    selected_tickers = st.multiselect(
                        "Select stocks to filter news:",
                        options=ticker_options,
                        key="selected_tickers"
                    )
                    # Extract just the tickers from selections
                    selected_ticker_symbols = [t.split(' - ')[0] for t in selected_tickers]
                else:
                    st.warning("No matching stocks found")
                    selected_ticker_symbols = []
        
        with col2:
            # Date range selector
            days_ago = st.slider(
                "News from the last X days:",
                min_value=1,
                max_value=30,
                value=7,
                key="news_days"
            )
            start_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        with col3:
            # Number of articles
            article_limit = st.number_input(
                "Number of articles:",
                min_value=5,
                max_value=50,
                value=10,
                key="article_limit"
            )
        
        # Add fetch button
        if st.button("🔍 Fetch News", key="fetch_stock_news"):
            with st.spinner("Fetching latest stock market news..."):
                news_articles = fetch_stock_news(
                    tickers=selected_ticker_symbols if 'selected_ticker_symbols' in locals() else None,
                    start_date=start_date,
                    limit=article_limit
                )
                
                if news_articles:
                    st.session_state.stock_news = news_articles
                    st.success(f"✅ Found {len(news_articles)} articles!")
                else:
                    st.error("Unable to fetch news articles")
        
        # Display stock market news
        if 'stock_news' in st.session_state and st.session_state.stock_news:
            for article in st.session_state.stock_news:
                with st.expander(f"📰 {article.get('title', 'Untitled Article')}", expanded=False):
                    # Article metadata
                    st.markdown(f"**Source:** {article.get('source', 'Unknown Source')}")
                    st.markdown(f"**Published:** {article.get('published_date', 'Unknown Date')}")
                    
                    tickers = article.get('tickers', [])
                    if tickers and isinstance(tickers, list):
                        st.markdown(f"**Related Stocks:** {', '.join(tickers)}")
                    
                    # Article content sections
                    if article.get('description'):
                        st.markdown("### Summary")
                        st.markdown(article['description'])
                    
                    if article.get('full_content'):
                        st.markdown("### Full Article Content")
                        st.text_area(
                            "Full Content", 
                            value=article['full_content'],
                            height=300,
                            key=f"stock_content_{article.get('id', datetime.now().isoformat())}"
                        )
                    
                    # Article statistics
                    st.markdown("### Article Statistics")
                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Title Length", article.get('title_length', 0))
                        st.metric("Description Length", article.get('description_length', 0))
                    with stats_col2:
                        st.metric("Full Content Length", article.get('full_content_length', 0))
                        st.metric("Related Tickers", article.get('ticker_count', 0))
                    
                    # Link to original article
                    if article.get('url'):
                        st.markdown(f"[Read original article]({article['url']})")
            
            # Add statistics and save data section
            st.markdown("---")
            st.markdown("### News Data Statistics")
            
            # Get and display statistics
            stats = get_news_statistics(st.session_state.stock_news)
            if stats:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Articles", stats['total_articles'])
                    st.metric("Unique Sources", stats['unique_sources'])
                
                with col2:
                    st.metric("Unique Tickers", stats['unique_tickers'])
                    st.metric("Avg. Article Length", f"{stats['avg_text_length']:.0f}")
                
                with col3:
                    st.metric("Date Range", 
                        f"{stats['date_range']['start']} to {stats['date_range']['end']}")
                
                # Show top tickers and tags
                st.markdown("#### Top Mentioned Tickers")
                st.write(stats['top_tickers'])
                
                st.markdown("#### Top Tags")
                st.write(stats['top_tags'])
            
            # Add save data button
            if st.button("💾 Save News Data", key="save_stock_news"):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/stock_news_{timestamp}.csv"
                
                saved_file = save_news_data(st.session_state.stock_news, filename)
                if saved_file:
                    st.success(f"✅ Successfully saved news data to {saved_file}")
                    
                    # Add download button
                    df = pd.DataFrame(st.session_state.stock_news)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download News Data",
                        data=csv,
                        file_name=f"stock_news_{timestamp}.csv",
                        mime="text/csv"
                    )
    
    with news_tab2:
        st.markdown("### Politician Trading News")
        
        # Create search filters
        news_col1, news_col2 = st.columns([3, 1])
        
        with news_col1:
            politician_news_name = st.text_input(
                "Search news about politician trading:",
                value=search_name if 'search_name' in locals() else "",
                placeholder="Enter politician name (optional)",
                key="politician_news_name"
            )
        
        with news_col2:
            news_limit = st.number_input(
                "Number of articles:",
                min_value=5,
                max_value=50,
                value=10,
                key="politician_news_limit"
            )
        
        if st.button("🔍 Fetch Trading News", key="fetch_politician_news"):
            with st.spinner("Fetching news about politician trading..."):
                news_articles = fetch_politician_trading_news(
                    politician_name=politician_news_name,
                    limit=news_limit
                )
                
                if news_articles:
                    st.session_state.politician_news = news_articles
                    st.success(f"✅ Found {len(news_articles)} articles!")
                else:
                    st.error("Unable to fetch news articles")
        
        # Display politician trading news
        if 'politician_news' in st.session_state and st.session_state.politician_news:
            for article in st.session_state.politician_news:
                with st.expander(f"📰 {article.get('title', 'Untitled Article')}", expanded=False):
                    # Article metadata
                    st.markdown(f"**Source:** {article.get('source', 'Unknown Source')}")
                    st.markdown(f"**Published:** {article.get('published_date', 'Unknown Date')}")
                    
                    # Article content sections
                    if article.get('description'):
                        st.markdown("### Summary")
                        st.markdown(article['description'])
                    
                    if article.get('full_content'):
                        st.markdown("### Full Article Content")
                        st.text_area(
                            "Full Content", 
                            value=article['full_content'],
                            height=300,
                            key=f"pol_content_{article.get('id', datetime.now().isoformat())}"
                        )
                    
                    # Article statistics
                    st.markdown("### Article Statistics")
                    stats_col1, stats_col2 = st.columns(2)
                    with stats_col1:
                        st.metric("Title Length", article.get('title_length', 0))
                        st.metric("Description Length", article.get('description_length', 0))
                    with stats_col2:
                        st.metric("Full Content Length", article.get('full_content_length', 0))
                    
                    # Link to original article
                    if article.get('url'):
                        st.markdown(f"[Read original article]({article['url']})")
            
            # Add save data button for politician news
            if st.button("💾 Save News Data", key="save_politician_news"):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/politician_trading_news_{timestamp}.csv"
                
                saved_file = save_news_data(st.session_state.politician_news, filename)
                if saved_file:
                    st.success(f"✅ Successfully saved news data to {saved_file}")
                    
                    # Add download button
                    df = pd.DataFrame(st.session_state.politician_news)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download News Data",
                        data=csv,
                        file_name=f"politician_trading_news_{timestamp}.csv",
                        mime="text/csv"
                    )

# Replace the entire USA Spending tab section with:
with tab5:
    st.markdown("<h3 class='section-title'>USA Spending (Federal Contracts)</h3>", unsafe_allow_html=True)
    render_federal_contracts_tab()

# Close the main div
st.markdown('</div>', unsafe_allow_html=True)

def show_trading_summary(trades):
    # Update this to remove transaction_total
    summary = {}
    for trade in trades:
        # Use only the fields that exist in the new data structure
        trader = trade['trader']
        stock = trade['stock']
        action = trade['action']
        volume = trade['volume']
        # Remove transaction_total from here
        
        # Update the summary calculation without transaction_total
        if trader not in summary:
            summary[trader] = {
                'total_trades': 0,
                'stocks_traded': set(),
                'buys': 0,
                'sells': 0
            }
        
        summary[trader]['total_trades'] += 1
        summary[trader]['stocks_traded'].add(stock)
        if 'buy' in action.lower():
            summary[trader]['buys'] += 1
        elif 'sell' in action.lower():
            summary[trader]['sells'] += 1

    # Display summary without transaction_total
    for trader, stats in summary.items():
        print(f"\nTrader: {trader}")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Unique Stocks: {len(stats['stocks_traded'])}")
        print(f"Buys: {stats['buys']}")
        print(f"Sells: {stats['sells']}")
