import sys
import os

# Add IBJts directory to Python path
ibapi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'IBJts')
if ibapi_path not in sys.path:
    sys.path.append(ibapi_path)

import time
import signal
from datetime import datetime
from politician_trades import PoliticianTradesApp
from config import IB_CONFIG

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    global running
    print("\nReceived shutdown signal. Cleaning up...")
    running = False

def collect_politician_trades():

    max_attempts = 3
    attempt = 0
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    while attempt < max_attempts and running:
        try:
            print(f"\nAttempt {attempt + 1} of {max_attempts}")
            app = PoliticianTradesApp()
            
            # Connect to IB TWS using config
            print(f"Connecting to IB at {IB_CONFIG['host']}:{IB_CONFIG['port']}...")
            app.connect(IB_CONFIG['host'], IB_CONFIG['port'], IB_CONFIG['client_id'])
            
            # Start the socket in a separate thread
            print("Starting socket thread...")
            app.run()
            
            # Wait for connection confirmation
            timeout = 15  # seconds
            start_time = time.time()
            print("Waiting for connection confirmation...")
            while not app.connected and time.time() - start_time < timeout and running:
                time.sleep(0.1)
                
            if not app.connected or not running:
                print("Connection timeout or interrupted")
                app.disconnect()
                attempt += 1
                continue
                
            print("Connected successfully, waiting for data collection...")
            
            # Wait for data collection to complete
            timeout = 300  # Increase timeout to 5 minutes since we're collecting a lot of data
            start_time = time.time()
            while (not app.done or not app.data_received) and app.isConnected() and time.time() - start_time < timeout and running:
                time.sleep(1)
                if len(app.data) > 0 and len(app.data) % 100 == 0:  # Print status every 100 records
                    print(f"Waiting for collection to complete... Currently have {len(app.data)} records")
            
            if app.isConnected():
                if app.data:
                    print(f"\nCollection complete. Total data points: {len(app.data)}")
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d')
                        filename = os.path.join('data', f'politician_trades_{timestamp}.csv')
                        print(f"Exporting data to {os.path.abspath(filename)}")
                        if app.export_to_csv(filename):
                            print("CSV export completed successfully")
                            app.disconnect()
                            print("Data collection complete. Exiting program.")
                            sys.exit(0)
                        else:
                            print("CSV export failed, will retry...")
                            attempt += 1
                            continue
                    except Exception as e:
                        print(f"Error exporting CSV: {e}")
                        import traceback
                        traceback.print_exc()
                        attempt += 1  # Retry on export error
                        continue
                else:
                    print("No data was collected")
            else:
                print("Connection lost during data collection")
            
            # Disconnect
            print("Disconnecting from IB...")
            app.disconnect()
            
            if app.data:  # If we got data, break the retry loop
                break
                
        except Exception as e:
            print(f"Error during execution: {e}")
            import traceback
            traceback.print_exc()
            attempt += 1
            time.sleep(2)  # Wait before retrying
            
        if attempt == max_attempts:
            print("Max connection attempts reached")

    if not running:
        print("Program terminated by user")
        sys.exit(0)

if __name__ == "__main__":
    collect_politician_trades() 