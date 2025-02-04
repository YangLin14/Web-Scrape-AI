import sys
import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add IBJts directory to Python path
ibapi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'IBJts')
if ibapi_path not in sys.path:
    sys.path.append(ibapi_path)

import csv
import time
from datetime import datetime
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData
from config import POLITICIAN_STOCKS, IB_CONFIG, QUIVER_API_KEY, AZURE_API_KEY
import os

class PoliticianTradesApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, self)
        self.data = []
        self.contract = None
        self.done = False
        self.connected = False
        self.pending_requests = set()
        self.data_received = False
        
        # Initialize CSV writer
        self.csv_file = None
        self.csv_writer = None
        self.fieldnames = [
            'Date',
            'Trader/Entity',
            'Chamber',
            'Ticker',
            'Stock',
            'Asset Type',
            'Action',
            'Volume',
            'Filing Date',
            'Filing URL'
        ]
        
        # Create CSV file and writer
        timestamp = datetime.now().strftime('%Y%m%d')
        self.filename = os.path.join('data', f'politician_trades_{timestamp}.csv')
        os.makedirs('data', exist_ok=True)
        
        try:
            self.csv_file = open(self.filename, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
            self.csv_writer.writeheader()
            print(f"Created CSV file: {os.path.abspath(self.filename)}")
        except Exception as e:
            print(f"Error creating CSV file: {e}")
            
        self.base_url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com"
        
    def __del__(self):
        # Close CSV file when object is destroyed
        if self.csv_file:
            self.csv_file.close()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        # Ignore non-critical messages
        if errorCode in [2104, 2106, 2158]:  # Market data connection messages
            return
            
        if errorCode == 2176:  # Fractional shares warning
            print("Warning: Fractional shares will be rounded")
            return
            
        print(f'IB Error {errorCode}: {errorString}')
        if errorCode == 502:  # Connection refused
            print("Could not connect to TWS. Make sure TWS/IB Gateway is running and accepting connections.")
            self.done = True
        elif errorCode == 501:  # Already connected
            self.connected = True
        
    def connectionClosed(self):
        print('Connection to IB closed')
        self.connected = False
        self.done = True

    def connectAck(self):
        print('Successfully connected to IB')
        self.connected = True
        
    def historicalData(self, reqId, bar):
        try:
            self.data_received = True
            
            # Find the corresponding stock info based on reqId
            found_stock = False
            current_stock_info = None
            for stock_info in POLITICIAN_STOCKS.values():
                if hash(stock_info['symbol']) % 10000 == reqId:
                    current_stock_info = stock_info
                    found_stock = True
                    break
            
            if not found_stock:
                print(f"Warning: Could not find stock info for reqId {reqId}")
                return
            
            # Format the bar date
            bar_datetime = datetime.strptime(bar.date, "%Y%m%d").strftime("%Y-%m-%d")
            
            # Create trade data for each politician who traded this stock
            for trade_info in current_stock_info.get('trades', []):
                # Create formatted strings for CSV
                formatted_price = f"${float(bar.close):.2f}"
                formatted_volume = f"{trade_info.get('volume', 0):,} shares"
                formatted_total = f"${float(bar.close) * trade_info.get('volume', 0):,.2f}"
                
                trade_data = {
                    'Date': bar_datetime,
                    'Trader/Entity': trade_info.get('trader', 'Unknown'),
                    'Chamber': trade_info.get('chamber', 'Unknown'),
                    'Action': trade_info.get('action', 'Unknown'),
                    'Stock': f"{current_stock_info['symbol']} ({current_stock_info['company']})",
                    'Price': formatted_price,
                    'Volume': formatted_volume,
                    'Transaction Total': formatted_total,
                    'Reason': trade_info.get('reason', 'Not specified')
                }
                
                # Store in memory
                self.data.append(trade_data)
                
                # Write to CSV immediately
                if self.csv_writer:
                    self.csv_writer.writerow(trade_data)
                    self.csv_file.flush()  # Force write to disk
                
                # Print each trade in a formatted table row
                print(
                    f"\n{'='*100}\n"
                    f"TRADE DETAILS:\n"
                    f"Trader/Entity: {trade_data['Trader/Entity']:<20} | "
                    f"Chamber: {trade_data['Chamber']:<8} | "
                    f"Action: {trade_data['Action']:<4}\n"
                    f"Stock: {trade_data['Stock']}\n"
                    f"Price: {trade_data['Price']} | "
                    f"Volume: {trade_data['Volume']} | "
                    f"Date: {trade_data['Date']}\n"
                    f"Transaction Total: {trade_data['Transaction Total']}\n"
                    f"Reason: {trade_data['Reason']}\n"
                    f"{'='*100}"
                )
                
                # Print summary every 10 trades
                if len(self.data) % 10 == 0:
                    print(f"\n>>> Collection Progress: {len(self.data)} trades recorded <<<")
                    print(f"CSV file location: {os.path.abspath(self.filename)}\n")
            
        except Exception as e:
            print(f"Error processing historical data: {e}")
            import traceback
            traceback.print_exc()

    def historicalDataEnd(self, reqId, start, end):
        print(f"Historical data complete for {reqId}")
        if reqId in self.pending_requests:
            self.pending_requests.remove(reqId)
        if not self.pending_requests:
            print("All data collection complete")
            self.done = True

    def nextValidId(self, orderId):
        print("Connected and ready to process data")
        self.start_historical_data()

    def start_historical_data(self):
        try:
            self.process_multiple_stocks()
        except Exception as e:
            print(f"Error starting historical data request: {e}")
            self.done = True

    def export_to_csv(self, filename=None):
        try:
            if not self.data:
                print("No data to export - data list is empty")
                return False
                
            if not self.data_received:
                print("No data was received from IB")
                return False
                
            # Generate filename with timestamp if not provided
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f'data/politician_trades_{timestamp}.csv'
            
            # Get absolute path and create directory
            abs_path = os.path.abspath(filename)
            directory = os.path.dirname(abs_path)
            
            print(f"\nExport Details:")
            print(f"Working Directory: {os.getcwd()}")
            print(f"Target Directory: {directory}")
            print(f"Full File Path: {abs_path}")
            
            # Ensure the directory exists
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"Directory verified/created: {directory}")
            except Exception as e:
                print(f"Error creating directory: {e}")
                return False
            
            print(f"\nAttempting to export {len(self.data)} records...")
            
            with open(abs_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
                rows_written = 0
                
                # Write the formatted data
                for trade in self.data:
                    # Map the data to match fieldnames
                    row = {
                        'Date': trade['Date'],
                        'Trader/Entity': trade['Trader/Entity'],
                        'Chamber': trade['Chamber'],
                        'Ticker': trade['Ticker'],
                        'Stock': trade['Stock'],
                        'Asset Type': trade['Asset Type'],
                        'Action': trade['Action'],
                        'Volume': trade['Volume'],
                        'Filing Date': trade['Filing Date'],
                        'Filing URL': trade['Filing URL']
                    }
                    writer.writerow(row)
                    rows_written += 1
                    if rows_written % 100 == 0:
                        print(f"Wrote {rows_written} rows...")
                
                csvfile.flush()
            
            print(f"\nSuccessfully exported {rows_written} trades to CSV")
            return True
            
        except Exception as e:
            print(f"\nError exporting to CSV: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_multiple_stocks(self):
        self.pending_requests.clear()
        
        print(f"\nProcessing {len(POLITICIAN_STOCKS)} stocks...")
        
        for stock_info in POLITICIAN_STOCKS.values():
            try:
                self.contract = Contract()
                self.contract.symbol = stock_info['symbol']
                self.contract.secType = "STK"
                self.contract.exchange = "SMART"
                self.contract.currency = "USD"
                self.contract.primaryExch = "NASDAQ"  # Add primary exchange
                
                reqId = hash(stock_info['symbol']) % 10000
                self.pending_requests.add(reqId)
                
                print(f"\nRequesting data for {stock_info['symbol']} (reqId: {reqId})")
                print(f"Contract details: {vars(self.contract)}")
                
                self.reqHistoricalData(
                    reqId=reqId,
                    contract=self.contract,
                    endDateTime="",
                    durationStr="1 Y",
                    barSizeSetting="1 day",
                    whatToShow="TRADES",
                    useRTH=1,
                    formatDate=1,
                    keepUpToDate=False,
                    chartOptions=[]
                )
                
                # Small delay between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {stock_info['symbol']}: {e}")
                import traceback
                traceback.print_exc()
                if reqId in self.pending_requests:
                    self.pending_requests.remove(reqId)

    def clean_transaction_amount(self, amount):
        """Clean and format transaction amount"""
        if not amount:
            return 'N/A'
        
        try:
            # Convert to string if not already
            amount_str = str(amount)
            
            # Remove currency symbols and commas
            amount_str = amount_str.replace('$', '').replace(',', '')
            
            # Handle ranges (e.g., "1001 - 15000" or "1001 -")
            if '-' in amount_str:
                # Take the lower bound of the range
                amount_str = amount_str.split('-')[0].strip()
            
            # Convert to float and format
            amount = float(amount_str)
            return f"${amount:,.2f}"
        except (ValueError, TypeError):
            return str(amount)

    def fix_date_format(self, date_str):
        """Fix malformed dates and handle various date formats"""
        try:
            if not date_str or date_str == 'N/A':
                return None
            
            # Remove any whitespace
            date_str = date_str.strip()
            
            # Try to parse different date formats
            try:
                # Try MM/DD/YYYY format
                if '/' in date_str:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    return date_obj.strftime('%Y-%m-%d')
            except:
                pass
            
            try:
                # Try YYYY-MM-DD format
                if '-' in date_str:
                    # Handle incomplete dates
                    if date_str.endswith('-'):
                        date_str = date_str.rstrip('-')
                        # If only year, add January 1st
                        if len(date_str) == 4:
                            date_str += '-01-01'
                        # If year and month, add 1st day
                        elif len(date_str.split('-')) == 2:
                            date_str += '-01'
                    
                    # Fix years with extra digits
                    parts = date_str.split('-')
                    if len(parts[0]) > 4:
                        parts[0] = parts[0][-4:]  # Take last 4 digits
                    
                    # Ensure we have all parts
                    while len(parts) < 3:
                        parts.append('01')  # Add default month/day if missing
                    
                    # Reconstruct date string
                    date_str = '-'.join(parts)
                    
                    # Validate the date
                    datetime.strptime(date_str, '%Y-%m-%d')
                    return date_str
            except:
                pass
            
            return None
        except:
            return None

    def fetch_latest_trades(self):
        """Fetch real trading data"""
        try:
            # Only fetch real data
            success = self._fetch_real_data()
            return success
        except Exception as e:
            print(f"Error in data fetch: {e}")
            return False

    def fetch_house_trades(self):
        """Fetch House trading data"""
        try:
            # House Stock Watcher API - Real data source
            url = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
            
            print("Fetching House trading data...")
            response = requests.get(url)
            
            if response.status_code == 200:
                trades = response.json()
                for trade in trades:
                    try:
                        date_str = self.fix_date_format(trade.get('transaction_date', ''))
                        if not date_str:
                            continue
                        
                        # Format stock information
                        ticker = trade.get('ticker', '--')
                        asset_name = trade.get('asset_name', '')
                        if ticker == '--' and asset_name:
                            stock_display = asset_name
                        elif asset_name:
                            stock_display = f"{ticker} ({asset_name})"
                        else:
                            stock_display = ticker
                        
                        trade_data = {
                            'date': date_str,
                            'trader': trade.get('representative', 'Unknown'),
                            'chamber': 'House',
                            'ticker': ticker,
                            'stock': stock_display,
                            'asset_type': 'Stock',  # Default for House trades
                            'action': trade.get('type', 'Unknown'),
                            'volume': trade.get('amount', 'N/A'),
                            'filing_date': date_str,  # Use transaction date as filing date
                            'filing_url': trade.get('source', '')
                        }
                        self.data.append(trade_data)
                        
                    except Exception as e:
                        print(f"Error processing House trade: {e}")
                        continue
                
                print(f"Successfully fetched {len(self.data)} House trades")
                return True
            else:
                print(f"Error fetching House data: {response.status_code}")
                return False
            
        except Exception as e:
            print(f"Error in House data fetch: {e}")
            return False

    def fetch_senate_trades(self, politician_name="Thomas"):
        """
        Fetch real Senate trading data from eFD system using Selenium.
        Scrapes PTR data for all different names found in search results.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Dictionary to store trades by full name
            trades_by_politician = {}
            
            print("Initializing Senate data collection...")
            options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(options=options)
            
            base_url = "https://efdsearch.senate.gov"
            
            try:
                # Step 1: Navigate to the search page
                print("Accessing Senate eFD system...")
                driver.get(f"{base_url}/search/")
                
                # Step 2: Wait for and click the agreement checkbox
                print("Waiting for agreement checkbox...")
                checkbox = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "/html/body/div/main/div/div/div[3]/div[2]/div/div/form/div/label/input"))
                )
                if not checkbox.is_selected():
                    checkbox.click()
                    print("Clicked agreement checkbox")
                
                # Step 3: Submit the agreement form
                print("Submitting agreement...")
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
                
                # Step 4: Wait for search form to load
                print("Waiting for search form...")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "searchForm"))
                )
                
                # Add a small delay to ensure form is fully loaded
                time.sleep(2)
                
                # Enter first name
                print(f"Entering name: {politician_name}")
                first_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@id='firstName']"))
                )
                first_name_input.clear()
                first_name_input.send_keys(politician_name)
                
                # Add a small delay after entering name
                time.sleep(1)
                
                # Click the search button
                print("Clicking search button...")
                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Search')]"))
                )
                search_button.click()
                
                # Wait for search results to load
                print("Waiting for search results...")
                time.sleep(3)
                
                # Sort by date (click the date column header twice to get most recent first)
                print("Sorting by most recent date...")
                try:
                    date_sort_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id='filedReports']/thead/tr/th[5]"))
                    )
                    # Click twice to sort by most recent
                    date_sort_button.click()
                    time.sleep(1)
                    date_sort_button.click()
                    time.sleep(2)  # Wait for sort to complete
                    
                    print("Successfully sorted by date")
                except Exception as e:
                    print(f"Error sorting by date: {e}")
                    screenshot_path = "sort_error.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Screenshot saved to: {screenshot_path}")
                
                # After sorting, continue with collecting names...
                print("Collecting all senator names...")
                try:
                    table = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "filedReports"))
                    )
                    
                    # Get all rows and collect names
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    senator_data = []  # List to store senator data with PTR links
                    
                    print("\nScanning all entries...")
                    for row_idx, row in enumerate(rows[1:], start=2):  # Start from 2 to match XPath index
                        try:
                            # Find PTR link using specific XPath pattern
                            ptr_xpath = f"//*[@id='filedReports']/tbody/tr[{row_idx}]/td[4]/a"
                            try:
                                ptr_link = driver.find_element(By.XPATH, ptr_xpath)
                                if "Periodic Transaction Report" in ptr_link.text:
                                    # Get name columns
                                    first_name = row.find_element(By.XPATH, f"//*[@id='filedReports']/tbody/tr[{row_idx}]/td[1]").text.strip()
                                    last_name = row.find_element(By.XPATH, f"//*[@id='filedReports']/tbody/tr[{row_idx}]/td[2]").text.strip()
                                    full_name = f"{first_name} {last_name}"
                                    
                                    print(f"Found PTR for {full_name} at row {row_idx}")
                                    
                                    senator_data.append({
                                        'full_name': full_name,
                                        'first_name': first_name,
                                        'last_name': last_name,
                                        'row_index': row_idx,
                                        'ptr_link': ptr_link
                                    })
                            except Exception as e:
                                # No PTR link in this row, skip
                                continue
                                
                        except Exception as e:
                            print(f"Error processing row {row_idx}: {e}")
                            continue
                    
                    # Group senators by first name
                    senators_by_first_name = {}
                    for data in senator_data:
                        first_name = data['first_name'].lower()
                        if first_name not in senators_by_first_name:
                            senators_by_first_name[first_name] = []
                        senators_by_first_name[first_name].append(data)
                    
                    # Print summary of found names
                    print("\nFound senators grouped by first name:")
                    for first_name, senators in senators_by_first_name.items():
                        print(f"\n{first_name.title()}:")
                        for senator in senators:
                            print(f"- {senator['full_name']}")
                    
                    # After collecting senator_data, process each unique name
                    processed_names = set()  # Keep track of processed names
                    
                    for first_name, senators in senators_by_first_name.items():
                        print(f"\nProcessing senators with first name '{first_name.title()}':")
                        
                        for senator in senators:
                            senator_name = senator['full_name']
                            if senator_name in processed_names:
                                continue
                                
                            print(f"\nStarting PTR collection for {senator_name}...")
                            processed_names.add(senator_name)
                            
                            # Initialize list for this senator
                            trades_by_politician[senator_name] = []
                            
                            # Get all PTRs for this senator
                            senator_ptrs = [data for data in senator_data 
                                          if data['full_name'] == senator_name][:3]  # Limit to 3 most recent
                            
                            # Process each PTR for this senator
                            for ptr_idx, ptr_data in enumerate(senator_ptrs, 1):
                                print(f"\nProcessing PTR #{ptr_idx} for {senator_name}...")
                                
                                try:
                                    # Click the PTR link
                                    ptr_link = ptr_data['ptr_link']
                                    driver.execute_script("arguments[0].scrollIntoView(true);", ptr_link)
                                    time.sleep(1)
                                    driver.execute_script("arguments[0].click();", ptr_link)
                                    
                                    # Switch to new tab
                                    handles = driver.window_handles
                                    driver.switch_to.window(handles[-1])
                                    
                                    # Process trades table
                                    print("Waiting for trades table to load...")
                                    try:
                                        # First wait for page load
                                        WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                                        )
                                        
                                        trades_table = WebDriverWait(driver, 15).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, ".table-responsive, .table"))
                                        )
                                        
                                        time.sleep(2)
                                        print("\nFound trades table. Processing transactions...")
                                        print("=" * 80)
                                        
                                        # Process trades
                                        rows = trades_table.find_elements(By.TAG_NAME, "tr")
                                        
                                        # Process data rows
                                        for row in rows[1:]:  # Skip header row
                                            trade_data = self._process_trade_row(row, senator_name, driver)
                                            if trade_data:
                                                trades_by_politician[senator_name].append(trade_data)
                                                self.data.append(trade_data)
                                        
                                        print(f"\nCompleted processing PTR #{ptr_idx}")
                                        print("=" * 80)
                                        
                                    except Exception as e:
                                        print(f"Error processing trades table: {e}")
                                        continue
                                    finally:
                                        # Close tab and return to main window
                                        driver.close()
                                        driver.switch_to.window(handles[0])
                                        time.sleep(1)
                                        
                                except Exception as e:
                                    print(f"Error processing PTR for {senator_name}: {e}")
                                    continue
                                
                            # Print summary for this senator
                            trades = trades_by_politician.get(senator_name, [])
                            print(f"\nSummary for {senator_name}:")
                            print(f"Total trades processed: {len(trades)}")
                            if trades:
                                print("Recent trades:")
                                for trade in trades[:3]:
                                    print(f"- {trade['date']}: {trade['action']} {trade['stock']}")
                            print("=" * 80)
                    
                    # Print final summary
                    print("\nFinal Processing Summary:")
                    print(f"Total senators processed: {len(processed_names)}")
                    print(f"Total trades collected: {len(self.data)}")
                    for senator_name, trades in trades_by_politician.items():
                        print(f"\n{senator_name}: {len(trades)} trades")
                    
                    return True
                    
                except Exception as e:
                    print(f"Error collecting senator data: {e}")
                    screenshot_path = "search_results.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Screenshot saved to: {screenshot_path}")
                    raise
                
            finally:
                print("Closing browser...")
                driver.quit()
                
        except Exception as e:
            print(f"Error in Senate data fetch: {e}")
            traceback.print_exc()
            return False

    def _process_trade_row(self, row, senator_name, driver):
        """Helper method to process a single trade row"""
        try:
            # Get row index
            rows = driver.find_elements(By.XPATH, "//*[@id='content']/div/div/section/div/div/table/tbody/tr")
            row_idx = rows.index(row) + 1  # Add 1 because XPath indices start at 1
            
            # Use specific XPath patterns for each column
            try:
                transaction_date = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[2]"
                ).text.strip()
                
                owner = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[3]"
                ).text.strip()
                
                ticker = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[4]"
                ).text.strip()
                
                asset_name = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[5]"
                ).text.strip()
                
                asset_type = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[6]"
                ).text.strip()
                
                transaction_type = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[7]"
                ).text.strip()
                
                amount = driver.find_element(
                    By.XPATH, 
                    f"//*[@id='content']/div/div/section/div/div/table/tbody/tr[{row_idx}]/td[8]"
                ).text.strip()
                
                print(f"\nTransaction Details:")
                print(f"Transaction Date: {transaction_date}")
                print(f"Owner: {owner}")
                print(f"Ticker: {ticker}")
                print(f"Asset Name: {asset_name}")
                print(f"Asset Type: {asset_type}")
                print(f"Transaction Type: {transaction_type}")
                print(f"Amount: {amount}")
                print("-" * 50)
                
                # Create trade data dictionary
                return {
                    'date': transaction_date,
                    'trader': f"{senator_name} ({owner})",
                    'chamber': 'Senate',
                    'ticker': ticker if ticker != '--' else '',
                    'stock': asset_name,
                    'asset_type': asset_type,
                    'action': transaction_type,
                    'volume': amount,
                    'filing_url': driver.current_url
                }
                
            except Exception as e:
                print(f"Error getting column data: {e}")
                return None
            
        except Exception as e:
            print(f"Error processing trade row: {e}")
            return None

    def fetch_from_data_provider(self):
        """Fetch from a reliable third-party data provider"""
        try:
            headers = {'Authorization': f'Bearer {QUIVER_API_KEY}'}
            response = requests.get(
                'https://api.quiverquant.com/beta/live/congresstrading',
                headers=headers
            )
            if response.status_code == 200:
                trades = response.json()
                for trade in trades:
                    self.data.append({
                        'date': trade['ReportDate'],
                        'trader': trade['Representative'],
                        'chamber': trade['Chamber'],
                        'ticker': trade['Ticker'],
                        'stock': trade['Ticker'],
                        'action': trade['Transaction'],
                        'volume': trade['Shares'],
                        'asset_type': 'Stock',
                        'filing_date': trade['ReportDate'],
                        'filing_url': trade.get('Source', '')
                    })
            return True
        except Exception as e:
            print(f"Error fetching from data provider: {e}")
            return False

    def _fetch_real_data(self):
        """Internal method to fetch real data from all sources"""
        try:
            # Only fetch Senate data for now as it's more reliable
            senate_success = self.fetch_senate_trades()
            return senate_success
        except Exception as e:
            print(f"Error fetching real data: {e}")
            return False 