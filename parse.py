import os
import time
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import AZURE_API_KEY, AZURE_OPENAI_CONFIG, X_USERNAME, X_PASSWORD

template = """You are an AI financial analyst processing web content. Focus on extracting trading activities, stock prices, and market movements.

Context: {dom_content}

Analysis Request: {parse_description}

Instructions:
1. Extract key financial information:
   - Trading activities (buy/sell orders)
   - Stock prices and movements
   - Trading volumes
   - Market sentiment indicators
   - Company announcements
   
2. For each trading activity found:
   - Identify the trader/entity
   - Specify the action (buy/sell)
   - Note the stock symbol/name
   - Record price and quantity
   - Document the reason if available
   
3. Format information in tables when possible:
   | Date | Trader | Action | Stock | Price | Quantity | Reason |
   
4. Additional Analysis:
   - Market impact of trades
   - Related news or announcements
   - Potential implications
   
5. Quality Checks:
   - Verify price formats
   - Confirm date consistency
   - Cross-reference multiple sources
   - Flag any inconsistencies

6. Response Structure:
   - Start with key findings
   - Present detailed trade tables
   - Add supporting context
   - Include relevant quotes
   - End with summary insights

Remember to maintain accuracy and cite sources when available.


"""

# Use environment variables only
os.environ["AZURE_OPENAI_API_KEY"] = AZURE_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = AZURE_OPENAI_CONFIG['endpoint']

model = AzureChatOpenAI(
    deployment_name=AZURE_OPENAI_CONFIG['deployment_name'],
    api_version=AZURE_OPENAI_CONFIG['api_version']
)

class WebScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)

    def __del__(self):
        self.driver.quit()

    def scrape_x(self):
        """Scrape data from X"""
        try:
            print("\n=== Starting X Scraper ===")
            url = "https://x.com"
            self.driver.get(url)

            # wait for login button and click
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='loginButton']"))
            )
            login_button.click()

            # Enter username
            username = self.wait.until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username.send_keys(X_USERNAME)

            # Click next
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()

            # Enter password
            password = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password.send_keys(X_PASSWORD)

            # Click login
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
            )
            login_button.click()
            
            # Wait for login to complete and page to load
            time.sleep(2)

            # Click Grok button using XPATH instead of CSS_SELECTOR
            grok_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/i/grok']"))
            )
            grok_button.click()
            print("✓ Clicked Grok button")

            # Wait and enter text in Grok input
            grok_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
            )
            grok_input.send_keys("give me posts that are related to recent news on stock market related information. I want to focus on knowing who buy and sale what stocks at what price. need both resources from X posts and websites")
            print("✓ Entered search query")

            # Click the "Grok something" button
            enter_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Grok something']"))
            )
            enter_button.click()
            print("✓ Clicked 'Grok something' button")

            time.sleep(5)

            # Click X Posts button
            x_posts_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-175oi2r.r-1awozwy.r-g2wdr4.r-1roi411.r-sdzlij.r-1phboty.r-rs99b7.r-1loqt21.r-18u37iz.r-1cmwbt1.r-1udh08x.r-11f147o.r-3o4zer.r-xbdcod"))
            )
            x_posts_button.click()
            print("✓ Clicked X Posts button")
            time.sleep(3)  # Wait for posts to load

            # Wait for feed to load and get tweets
            tweets_data = []
            desired_tweet_count = 10
            max_scroll_attempts = 10
            scroll_attempts = 0
            
            print("\n=== Loading Tweets ===")
            while len(tweets_data) < desired_tweet_count and scroll_attempts < max_scroll_attempts:
                # Get current tweets
                tweets = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']")
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Process new tweets
                for tweet in tweets:
                    try:
                        tweet_info = {}
                        
                        # Get username
                        try:
                            username_elem = tweet.find_element(By.CSS_SELECTOR, "[data-testid='User-Name']")
                            username = username_elem.text
                            tweet_info['username'] = username
                        except:
                            continue  # Skip tweets where we can't get username
                        
                        # Get tweet text
                        try:
                            text_elem = tweet.find_element(By.CSS_SELECTOR, "[data-testid='tweetText']")
                            text = text_elem.text
                            tweet_info['text'] = text
                        except:
                            continue  # Skip tweets without text
                        
                        # Get tweet stats
                        try:
                            replies = tweet.find_element(By.CSS_SELECTOR, "[data-testid='reply']").text
                            retweets = tweet.find_element(By.CSS_SELECTOR, "[data-testid='retweet']").text
                            likes = tweet.find_element(By.CSS_SELECTOR, "[data-testid='like']").text
                            tweet_info['stats'] = {
                                'replies': replies,
                                'retweets': retweets,
                                'likes': likes
                            }
                        except:
                            tweet_info['stats'] = {}
                        
                        # Only add new tweets
                        if tweet_info not in tweets_data:
                            tweets_data.append(tweet_info)
                            print(f"\nTweet {len(tweets_data)} collected:")
                            print(f"Username: {username}")
                            print(f"Text: {text[:100]}...")
                            
                            if len(tweets_data) >= desired_tweet_count:
                                break
                        
                    except Exception as e:
                        print(f"Error processing tweet: {e}")
                        continue
                
                if len(tweets_data) >= desired_tweet_count:
                    break
                    
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Check if page has loaded new content
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_attempts += 1
                
                if new_height == current_height:
                    print("\n⚠️ No new content loaded")
                    break
                
                print(f"\nScrolling... ({len(tweets_data)}/{desired_tweet_count} tweets collected)")
            
            print(f"\n=== Scraping Complete ===")
            print(f"Total tweets collected: {len(tweets_data)}")
            
            if not tweets_data:
                raise Exception("No tweets found")
            
            # Format as table
            formatted_data = "| Username | Tweet | Replies | Retweets | Likes |\n"
            formatted_data += "|----------|-------|---------|-----------|--------|\n"
            
            for tweet in tweets_data:
                username = tweet['username'].split('\n')[0]  # Get first line of username
                text = tweet['text'].replace('\n', ' ').replace('|', '/')  # Handle table delimiters
                stats = tweet.get('stats', {})
                
                formatted_data += f"| {username} | {text} | {stats.get('replies', 'N/A')} | {stats.get('retweets', 'N/A')} | {stats.get('likes', 'N/A')} |\n"
            
            print("\n=== Scraping Links and Their Content ===")
            
            # Store original window handle
            main_window = self.driver.current_window_handle
            
            # Collect and process links
            links_data = []
            max_scroll_attempts = 50
            scroll_attempts = 0
            processed_links = set()  # Keep track of processed links
            
            while scroll_attempts < max_scroll_attempts:
                # Find all link elements
                links = self.driver.find_elements(By.CSS_SELECTOR, "a[role='link'][target='_blank']")
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                for link in links:
                    try:
                        # Get href
                        href = link.get_attribute('href')
                        
                        # Skip if already processed or no href
                        if not href or href in processed_links:
                            continue
                            
                        processed_links.add(href)
                        
                        # Get link text
                        try:
                            text = link.text
                        except:
                            text = ""
                        
                        print(f"\nProcessing link {len(links_data) + 1}:")
                        print(f"Title: {text}")
                        print(f"URL: {href}")
                        
                        try:
                            # Click the link (opens in new tab)
                            link.click()
                            time.sleep(3)  # Wait for new tab
                            
                            # Switch to new tab
                            new_window = [window for window in self.driver.window_handles if window != main_window][0]
                            self.driver.switch_to.window(new_window)
                            
                            # Wait for page load
                            time.sleep(5)
                            
                            # Scrape content from the new page
                            page_content = {}
                            page_content['title'] = text
                            page_content['url'] = href
                            
                            # Get main content
                            try:
                                # Get all text content
                                content_elements = self.driver.find_elements(
                                    By.XPATH,
                                    "//article | //p | //div[contains(@class, 'content')] | //div[contains(@class, 'article')]"
                                )
                                
                                content_text = []
                                for element in content_elements:
                                    text = element.text.strip()
                                    if text and len(text) > 100:  # Only substantial content
                                        content_text.append(text)
                                
                                page_content['content'] = '\n\n'.join(content_text)
                                
                                # Get metadata if available
                                try:
                                    date = self.driver.find_element(
                                        By.XPATH,
                                        "//time | //span[contains(@class, 'date')] | //div[contains(@class, 'date')]"
                                    ).text
                                    page_content['date'] = date
                                except:
                                    page_content['date'] = 'Not found'
                                
                                print(f"✓ Successfully scraped content ({len(content_text)} sections)")
                                
                            except Exception as e:
                                print(f"Error scraping content: {e}")
                                page_content['content'] = 'Error scraping content'
                            
                            # Close tab and switch back
                            self.driver.close()
                            self.driver.switch_to.window(main_window)
                            
                            # Add to collected data
                            links_data.append(page_content)
                            
                        except Exception as e:
                            print(f"Error processing link: {e}")
                            continue
                    
                    except Exception as e:
                        print(f"Error with link element: {e}")
                        continue
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Check if page has loaded new content
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_attempts += 1
                
                if new_height == current_height:
                    print("\n⚠️ No new content loaded")
                    break
                
                print(f"\nScrolling... ({len(links_data)} links processed)")
            
            print(f"\n=== Link Scraping Complete ===")
            print(f"Total links processed: {len(links_data)}")
            
            if not links_data:
                raise Exception("No links found")
            
            # Format as table with content
            formatted_data += "\n\n=== Links and Content ==="
            
            for link_data in links_data:
                formatted_data += f"\n\n## {link_data['title']}\n"
                formatted_data += f"URL: {link_data['url']}\n"
                if 'date' in link_data:
                    formatted_data += f"Date: {link_data['date']}\n"
                formatted_data += f"\nContent:\n{link_data['content']}\n"
                formatted_data += "\n---"  # Separator between links
            
            return formatted_data

        except TimeoutException as e:
            print(f"\n❌ Timeout error: {e}")
            return None
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return None
        finally:
            try:
                self.driver.save_screenshot("error_screenshot.png")
            except:
                pass

    def scrape_instagram(self):
        """Scrape data from Instagram"""
        try:
            url = "https://www.instagram.com"
            self.driver.get(url)

            # Add Instagram-specific scraping logic here
            # Similar structure to X scraping but with Instagram's elements

            return "Instagram content"  # Replace with actual scraped content
        except Exception as e:
            print(f"Error scraping Instagram: {e}")
            return None

    def scrape_government(self):
        """Scrape data from government website"""
        try:
            url = "https://www.gov.sg"  # Replace with actual government website
            self.driver.get(url)

            # Add government site-specific scraping logic here
            # Similar structure but with government site's elements

            return "Government content"  # Replace with actual scraped content
        except Exception as e:
            print(f"Error scraping government site: {e}")
            return None

def parse_with_ollama(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    
    parsed_results = []
    
    for chunk in dom_chunks:
        try:
            response = chain.invoke({
                "dom_content": chunk,
                "parse_description": parse_description
            })
            
            # Extract and validate financial data
            parsed_content = response.content
            
            # Add validation for financial data
            if any(financial_term in parsed_content.lower() 
                  for financial_term in ['stock', 'trade', 'price', '$']):
                parsed_results.append(parsed_content)
                
        except Exception as e:
            print(f"Error parsing chunk: {e}")
            continue
    
    return "\n".join(parsed_results)

# Create wrapper functions for the scraping methods
def scrape_x():
    scraper = WebScraper()
    return scraper.scrape_x()

def scrape_instagram():
    scraper = WebScraper()
    return scraper.scrape_instagram()

def scrape_government():
    scraper = WebScraper()
    return scraper.scrape_government()
