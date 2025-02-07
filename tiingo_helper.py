import requests
from datetime import datetime, timedelta
import pandas as pd
import re
from typing import List, Dict, Any
from config import TIINGO_API_KEY
import os
import importlib.util
import random

def get_tiingo_headers():
    """Get headers for Tiingo API requests"""
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Token {TIINGO_API_KEY}'
    }

def clean_html(text: str) -> str:
    """Remove HTML tags and clean text"""
    if not text:  # Handle None or empty string
        return ""
        
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', str(text))  # Convert to string to handle any non-string input
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def format_date(date_str: str) -> str:
    """Format date string consistently"""
    if not date_str:
        return ""
    
    try:
        # Handle ISO format dates from Tiingo API
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Convert to local timezone
        local_dt = dt.astimezone()
        # Format as YYYY-MM-DD
        return local_dt.strftime('%Y-%m-%d')
    except Exception:
        # If date parsing fails, return original string up to 10 chars (YYYY-MM-DD portion)
        return date_str[:10]

def preprocess_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and preprocess a single news article"""
    if not article:
        return {}
    
    # Handle potential None values with safe defaults
    cleaned = {
        'id': article.get('id', ''),
        'title': clean_html(article.get('title', '')).strip(),
        'description': clean_html(article.get('description', '')).strip(),
        'full_content': clean_html(article.get('content', '')).strip(),
        'source': article.get('source', ''),
        'url': article.get('url', ''),
        'tickers': article.get('tickers', []) or [],
        'tags': article.get('tags', []) or [],
        'published_date': format_date(article.get('publishedDate', '')),
        'crawled_date': format_date(article.get('crawlDate', '')),
    }
    
    # Always try to fetch full content if URL is available
    if cleaned['url']:
        try:
            full_content = fetch_article_content(cleaned['url'])
            if full_content:
                # Only update if the fetched content is longer than existing content
                if len(full_content) > len(cleaned['full_content']):
                    cleaned['full_content'] = full_content
        except Exception:
            pass  # Silently continue if content fetching fails
    
    # Add derived features with safe calculations
    cleaned['ticker_count'] = len(cleaned['tickers'])
    cleaned['tag_count'] = len(cleaned['tags'])
    cleaned['title_length'] = len(cleaned['title'])
    cleaned['description_length'] = len(cleaned['description'])
    cleaned['full_content_length'] = len(cleaned['full_content'])
    
    return cleaned

def has_trafilatura():
    """Check if trafilatura is installed"""
    return importlib.util.find_spec("trafilatura") is not None

def get_random_user_agent():
    """Return a random user agent string"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
    ]
    return random.choice(user_agents)

def get_request_headers():
    """Get headers for web requests"""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

def fetch_article_content(url: str) -> str:
    """Fetch full article content from URL using multiple methods"""
    if not url:
        return ""
        
    content = ""
    headers = get_request_headers()
    
    # Special handling for known paywalled sites
    domain = url.split('/')[2] if len(url.split('/')) > 2 else ''
    
    if 'reuters.com' in domain:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                article_body = soup.find('div', {'class': ['article-body', 'article-text', 'paywall']})
                if article_body:
                    paragraphs = article_body.find_all('p')
                    content = ' '.join([p.get_text() for p in paragraphs])
        except Exception:
            pass  # Silently continue to next method
    
    # If content is still empty, try standard methods
    if not content:
        # Method 1: Try trafilatura
        if not has_trafilatura():
            try:
                import subprocess
                subprocess.check_call(["pip", "install", "trafilatura"], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
            except Exception:
                pass
        
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)  # Removed headers argument
            if downloaded:
                content = trafilatura.extract(downloaded,
                                            include_comments=False,
                                            include_tables=True,
                                            include_links=True,
                                            include_images=False)
        except Exception:
            pass  # Silently continue to next method
    
    # Method 2: Try newspaper3k
    if not content:
        try:
            from newspaper import Article, Config
            config = Config()
            config.browser_user_agent = headers['User-Agent']
            config.request_timeout = 10
            config.fetch_images = False
            
            article = Article(url, config=config)
            article.download()
            article.parse()
            content = article.text
        except Exception:
            pass  # Silently continue to next method
    
    # Method 3: Try requests + BeautifulSoup as fallback
    if not content:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'aside']):
                    element.decompose()
                
                # Try to find the main content
                main_content = None
                content_selectors = [
                    'article', 'main', '.article-content', '.post-content',
                    '#article-content', '#main-content', '.story-content',
                    '[role="main"]', '.entry-content', '.content-body',
                    '.article-body', '.article__body', '.story__body',
                    '.post__content', '.post-body', '.entry__content',
                    '[data-testid="article-body"]'
                ]
                
                for selector in content_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                if main_content:
                    paragraphs = main_content.find_all('p')
                    content = ' '.join([p.get_text() for p in paragraphs])
                else:
                    content = ' '.join([p.get_text() for p in soup.find_all('p')])
        except Exception:
            pass  # Silently continue
    
    # Clean and return the content
    if content:
        return clean_html(content)
    return ""

def fetch_stock_news(tickers=None, tags=None, start_date=None, limit=10) -> List[Dict[str, Any]]:
    """
    Fetch and clean news articles from Tiingo API with full content
    """
    try:
        url = "https://api.tiingo.com/tiingo/news"
        params = {
            'limit': limit,
            'sortBy': 'relevance',  # Sort by relevance to get most important articles
            'detail': 3  # Request detailed response including full content
        }
        
        if tickers:
            params['tickers'] = ','.join(tickers)
        if tags:
            params['tags'] = ','.join(tags)
        if start_date:
            params['startDate'] = start_date
            
        response = requests.get(
            url,
            headers=get_tiingo_headers(),
            params=params
        )
        
        if response.status_code == 200:
            articles = response.json()
            # Clean and preprocess articles with progress indicator
            cleaned_articles = []
            for article in articles:
                cleaned = preprocess_article(article)
                if cleaned:
                    cleaned_articles.append(cleaned)
            return cleaned_articles
        else:
            print(f"Error fetching news: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def search_tickers(query: str) -> List[Dict[str, Any]]:
    """Search for stock tickers/companies"""
    try:
        url = f"https://api.tiingo.com/tiingo/utilities/search/{query}"
        response = requests.get(url, headers=get_tiingo_headers())
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error searching tickers: {str(e)}")
        return None

def save_news_data(articles: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Save news articles to CSV file for future training
    
    Args:
        articles: List of preprocessed article dictionaries
        filename: Optional filename, if None generates timestamp-based name
    
    Returns:
        Path to saved file
    """
    if not articles:
        return None
        
    # Convert to DataFrame
    df = pd.DataFrame(articles)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/market_news_{timestamp}.csv"
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save to CSV
    df.to_csv(filename, index=False)
    return filename

def load_news_data(filename: str) -> pd.DataFrame:
    """Load saved news data from CSV"""
    return pd.read_csv(filename)

def get_news_statistics(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics about the news articles"""
    if not articles:
        return None
        
    try:
        df = pd.DataFrame(articles)
        
        # Convert date columns to datetime
        date_columns = ['published_date', 'crawled_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        # Handle potential string representations of lists
        def parse_list(x):
            if isinstance(x, str):
                try:
                    import ast
                    return ast.literal_eval(x)
                except:
                    return []
            return x if isinstance(x, list) else []
        
        # Safely convert tickers and tags columns
        df['tickers'] = df['tickers'].apply(parse_list)
        df['tags'] = df['tags'].apply(parse_list)
        
        # Explode tickers and tags lists for counting
        tickers_series = df['tickers'].explode()
        tags_series = df['tags'].explode()
        
        # Calculate average content length
        avg_length = df['full_content_length'].mean() if 'full_content_length' in df.columns else 0
        
        # Format date range
        date_range = {
            'start': df['published_date'].min().strftime('%Y-%m-%d') if 'published_date' in df.columns and not df['published_date'].empty else 'N/A',
            'end': df['published_date'].max().strftime('%Y-%m-%-d') if 'published_date' in df.columns and not df['published_date'].empty else 'N/A'
        }
        
        stats = {
            'total_articles': len(df),
            'unique_sources': df['source'].nunique(),
            'unique_tickers': len(set(filter(None, tickers_series))),
            'avg_text_length': avg_length,
            'date_range': date_range,
            'top_tickers': tickers_series.value_counts().head(10).to_dict() if not tickers_series.empty else {},
            'top_tags': tags_series.value_counts().head(10).to_dict() if not tags_series.empty else {}
        }
        
        return stats
    except Exception as e:
        print(f"Error generating statistics: {str(e)}")
        return {
            'total_articles': len(articles),
            'unique_sources': 0,
            'unique_tickers': 0,
            'avg_text_length': 0,
            'date_range': {'start': 'N/A', 'end': 'N/A'},
            'top_tickers': {},
            'top_tags': {}
        }

def fetch_politician_trading_news(politician_name=None, limit=10) -> List[Dict[str, Any]]:
    """
    Fetch news articles about politician trading activities
    
    Args:
        politician_name: Optional name of specific politician
        limit: Maximum number of articles to return
    """
    try:
        url = "https://api.tiingo.com/tiingo/news"
        
        # Keywords for politician trading
        keywords = [
            'congress trading', 'senate trading', 'politician stock', 
            'congressional disclosure', 'stock act', 'congressional trading',
            'insider trading congress', 'politician investment'
        ]
        
        if politician_name:
            # Add politician-specific search terms
            keywords.extend([
                f"{politician_name} trading",
                f"{politician_name} stock",
                f"{politician_name} investment"
            ])
        
        params = {
            'limit': limit,
            'sortBy': 'relevance',
            'tags': ','.join(keywords),
            'detail': 3
        }
        
        response = requests.get(
            url,
            headers=get_tiingo_headers(),
            params=params
        )
        
        if response.status_code == 200:
            articles = response.json()
            cleaned_articles = []
            for article in articles:
                cleaned = preprocess_article(article)
                if cleaned:
                    cleaned_articles.append(cleaned)
            return cleaned_articles
        else:
            print(f"Error fetching news: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None 