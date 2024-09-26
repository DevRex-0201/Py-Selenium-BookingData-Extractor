from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Set up the driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # Open the website
    driver.get("https://io.dexscreener.com/dex/log/amm/v3/solamm/top/solana/CU6JLMqYQv1hyrQNspGyLQtbbrViuFLybVLPcMpKKzyu?q=So11111111111111111111111111111111111111112")
    
    # Wait for the page to load and element to be present
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )
    
    # Get page source
    page_source = driver.page_source.encode('utf-8').decode('utf-8')

    # Initialize the list of URLs
    urls = []
    index = 0
    while index < len(page_source):
        # Look for yBX and yBV simultaneously
        index_bx = page_source.find('yBX', index)
        index_bv = page_source.find('yBV', index)

        # Determine the next occurrence to process
        if index_bx == -1 and index_bv == -1:
            break  # No more occurrences of either prefix
        elif index_bx != -1 and (index_bx < index_bv or index_bv == -1):
            current_index = index_bx
            num_letters = 44
            prefix_length = 3
        else:
            current_index = index_bv
            num_letters = 43
            prefix_length = 3

        # Ensure there's enough characters left in the string for a valid address
        if current_index + prefix_length + num_letters <= len(page_source):
            address = page_source[current_index + prefix_length: current_index + prefix_length + num_letters]
            urls.append(f"https://solscan.io/account/{address}")

        # Move past this entry to continue search
        index = current_index + prefix_length + num_letters

    # Write URLs to a CSV file
    with open('wallet_addresses.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Wallet URL'])  # Write header
        for url in urls:
            writer.writerow([url])  # Write each URL on a new row

    print("Wallet URLs have been saved to 'wallet_addresses.csv'.")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()
