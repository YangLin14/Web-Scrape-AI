from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from dotenv import load_dotenv
import os
import requests
from urllib.parse import urljoin, urlparse
import re

import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service

# load_dotenv()

# SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")


def scrape_website(url):
    """
    Comprehensively scrape a website including all text content, links, and nested content.
    """
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Validate and clean URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Make request
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for script in soup(["script", "style", "meta", "noscript", "header", "footer"]):
            script.decompose()
            
        # Extract all text content
        content = []
        
        # Get title
        if soup.title:
            content.append(f"Title: {soup.title.string}")
            
        # Get meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content.append(f"Description: {meta_desc.get('content', '')}")
            
        # Get all headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            content.append(f"Heading: {heading.get_text(strip=True)}")
            
        # Get all paragraphs
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text:  # Only add non-empty paragraphs
                content.append(f"Paragraph: {text}")
                
        # Get all list items
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if text:
                content.append(f"List item: {text}")
                
        # Get all links with their text
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/'):  # Convert relative URLs to absolute
                href = urljoin(url, href)
            text = a.get_text(strip=True)
            if text:
                content.append(f"Link: {text} -> {href}")
                
        # Get all table content
        for table in soup.find_all('table'):
            content.append("Table content:")
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if cells:
                    content.append(" | ".join(cells))
                    
        # Get all div content
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if text and len(text) > 50:  # Only get substantial div content
                content.append(f"Content: {text}")
                
        # Get all article content
        for article in soup.find_all('article'):
            text = article.get_text(strip=True)
            if text:
                content.append(f"Article: {text}")
                
        # Get all section content
        for section in soup.find_all('section'):
            text = section.get_text(strip=True)
            if text:
                content.append(f"Section: {text}")
                
        # Get all image alt text and sources
        for img in soup.find_all('img', alt=True):
            alt = img.get('alt', '').strip()
            src = img.get('src', '')
            if alt and src:
                if src.startswith('/'):
                    src = urljoin(url, src)
                content.append(f"Image: {alt} -> {src}")
        
        # Clean and join content
        cleaned_content = []
        seen = set()  # For deduplication
        for item in content:
            # Remove extra whitespace and normalize
            cleaned = ' '.join(item.split())
            # Only add if not seen and not empty
            if cleaned and cleaned not in seen:
                cleaned_content.append(cleaned)
                seen.add(cleaned)
        
        return '\n\n'.join(cleaned_content)
        
    except Exception as e:
        return f"Error scraping website: {str(e)}"


def extract_body_content(html_content):
    """Extract content from body tag."""
    soup = BeautifulSoup(html_content, 'html.parser')
    if soup.body:
        return soup.body.get_text(separator='\n', strip=True)
    return html_content


def clean_body_content(content):
    """Enhanced cleaning for financial content."""
    # Keep existing cleaning code
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = re.sub(r'\s+', ' ', content)
    
    # Additional financial data cleaning
    def is_financial_line(line):
        # Keep lines with financial indicators
        financial_indicators = [
            r'\$\d+',           # Dollar amounts
            r'\d+\.\d{2}',      # Decimal numbers
            r'[A-Z]{2,5}',      # Stock symbols
            r'(buy|sell|trade)', # Trading terms
            r'(million|billion)', # Large numbers
            r'(\d+\s*shares)',   # Share quantities
            r'(stock|market|trading)' # Market terms
        ]
        return (
            len(line.strip()) > 20 or
            any(re.search(pattern, line.lower()) for pattern in financial_indicators)
        )
    
    lines = [line for line in content.split('\n') 
            if is_financial_line(line.strip())]
    
    return '\n'.join(lines)


def split_dom_content(content, max_chunk_size=1000):
    """Split content into manageable chunks."""
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in content.split('\n'):
        line_size = len(line)
        if current_size + line_size > max_chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(line)
        current_size += line_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

    # print("Connecting to Scraping Browser...")
    # sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
    # with Remote(sbr_connection, options=ChromeOptions()) as driver:
    #     driver.get(website)
    #     print("Waiting captcha to solve...")
    #     solve_res = driver.execute(
    #         "executeCdpCommand",
    #         {
    #             "cmd": "Captcha.waitForSolve",
    #             "params": {"detectTimeout": 10000},
    #         },
    #     )
    #     print("Captcha solve status:", solve_res["value"]["status"])
    #     print("Navigated! Scraping page content...")
    #     html = driver.page_source
    #     return html
