import os
import time
import pytz
import schedule
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import gspread
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# Setup logging
logging.basicConfig(filename='extraction.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Load environment variables from .env file
load_dotenv()

# Replace with your email from the .env file
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL')

# Load Google Sheets credentials from environment variable
google_credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
if not google_credentials_path:
    raise ValueError("The Google Sheets credentials path is not set in the environment variables")

# Set the scope and credentials for Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(google_credentials_path, scope)
client = gspread.authorize(creds)

# Open the Google Spreadsheet by URL
sheet_url = os.getenv('SHEET_URL')
spreadsheet = client.open_by_url(sheet_url)

extracted_data = [["Venue", "Date", "Time", "Booked Courts"]]

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"File {file_path} has been deleted.")
    else:
        logging.warning(f"The file {file_path} does not exist.")

def send_notification(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = USER_EMAIL
        msg['To'] = NOTIFICATION_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_EMAIL, os.getenv('EMAIL_PASSWORD'))
        text = msg.as_string()
        server.sendmail(USER_EMAIL, NOTIFICATION_EMAIL, text)
        server.quit()
        logging.info("Notification email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send notification email: {e}")

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--window-size=1920,1080")  # Set a window size
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def login(driver):
    try:
        driver.get("https://bookings.padel.haus/users/sign_in")
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "user_email"))).send_keys(USER_EMAIL)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "user_password"))).send_keys(USER_PASSWORD)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "commit"))).click()
        time.sleep(5)
        logging.info("Logged in successfully.")
    except Exception as e:
        logging.error(f"Error during login: {e}")
        driver.quit()
        return False
    return True

def extract_data(driver, url, venue):
    try:
        driver.get(url)
        time.sleep(5)
        driver.find_element(By.ID, "facilities-tags").find_elements(By.TAG_NAME, 'button')[0].click()
        time.sleep(5)
        book_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ui.button.large.fluid.white")))
        book_button.click()
        time.sleep(5)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='submit'][name='commit'][value='Accept']"))).click()
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        day_buttons = soup.find(class_='DaysRangeOptions').find_all('button')
        day_buttons[0].click()
        time.sleep(5)
        
        hour_buttons = soup.find(class_='hours_list').find_all('button')
        for button in hour_buttons:
            if "red" in button['class']:
                hour = button.text.strip()
                record = [venue, datetime.now().strftime("%Y-%m-%d"), hour, 4]
                extracted_data.append(record)
                logging.info(f"Extracted record: {record}")
                save_to_file(record)
            else:
                button.click()
                time.sleep(3)
                courts = soup.find_all(class_='over_flex_mobile_button_container')[2].find_all('button')
                booked_count = 4 - len(courts)
                record = [venue, datetime.now().strftime("%Y-%m-%d"), button.text.strip(), booked_count]
                extracted_data.append(record)
                logging.info(f"Extracted record: {record}")
                save_to_file(record)
    except Exception as e:
        logging.error(f"Error during data extraction: {e}")

def save_to_file(record):
    date_index = datetime.now().strftime("%Y-%m-%d")
    hour_index = datetime.now().hour
    folder_name = f"extracted-{date_index}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    if hour_index < 9:
        file_name = f"Padel Haus {date_index}-(0{hour_index}~0{hour_index + 1)}).txt"
    elif hour_index == 9:
        file_name = f"Padel Haus {date_index}-(0{hour_index}~{hour_index + 1)}).txt"
    else:
        file_name = f"Padel Haus {date_index}-({hour_index}~{hour_index + 1)}).txt"
    full_path = os.path.join(folder_name, file_name)
    with open(full_path, 'a', encoding='utf-8') as file:
        file.write(', '.join(map(str, record)) + '\n')

def save_sheet_to_gsheet():
    try:
        worksheet1 = spreadsheet.get_worksheet(0)
        worksheet2 = spreadsheet.get_worksheet(1)
        header_names = ["Venue", "Date", "Time", "Booked Courts"]
        if not worksheet1.row_values(1):
            worksheet1.insert_row(header_names, index=1)
        if not worksheet2.row_values(1):
            worksheet2.insert_row(header_names, index=1)
        for record in extracted_data:
            if record[0] == 'Williamsburg':
                worksheet1.append_row(record)
            elif record[0] == 'Dumbo':
                worksheet2.append_row(record)
            time.sleep(1)
        logging.info('Data has been written to the spreadsheet.')
    except Exception as e:
        logging.error(f"Error saving to Google Sheets: {e}")

def extract():
    try:
        driver = initialize_driver()
        if not login(driver):
            return
        urls = ["https://bookings.padel.haus/home", "https://bookings.padel.haus/home"]
        venues = ["Williamsburg", "Dumbo"]
        for url, venue in zip(urls, venues):
            extract_data(driver, url, venue)
        driver.quit()
        save_sheet_to_gsheet()
    except Exception as e:
        logging.error(f"Error in extract function: {e}")
        send_notification("Extraction Script Error", str(e))

def schedule_extractions():
    for hour in range(5, 22):  # Scheduling from 5 AM to 10 PM
        schedule.every().day.at(f"{hour:02d}:45").do(extract)
    while True:
        schedule.run_pending()
        time.sleep(1)

def save_sheet_to_me():
    try:
        # Get the worksheet by name
        worksheet_name = "Sheet1"
        worksheet = spreadsheet.get_worksheet(0)
        worksheet2 = spreadsheet.get_worksheet(1)

        # If the worksheet is not found, create a new one
        if worksheet is None:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="100", cols="20")

        # Define the header names
        header_names = ["Venue", "Date", "Time", "Booked Courts"]
        # Check if the worksheet is empty (no header row) and add headers if needed
        existing_headers = worksheet.row_values(1)
        existing_headers2 = worksheet2.row_values(1)
        if not existing_headers:
            worksheet.insert_row(header_names, index=1)
        if not existing_headers2:
            worksheet2.insert_row(header_names, index=1)
        
        current_date = datetime.now()
        date_index = current_date.strftime("%Y-%m-%d")
        hour_index = int(current_date.strftime("%H"))
        # Define the folder name where you want to save the file
        folder_name = f"extracted-{date_index}"

        # Create the folder if it doesn't exist
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Define the file name
        if hour_index <=8:
            file_name = f"Padel Haus {date_index}-(0{str(hour_index)}~0{str(hour_index + 1)}).txt"
        elif hour_index ==9:
            file_name = f"Padel Haus {date_index}-(0{str(hour_index)}~{str(hour_index + 1)}).txt"
        else:
            file_name = f"Padel Haus {date_index}-({str(hour_index)}~{str(hour_index + 1)}).txt"

        # Define the full path (folder + file name)
        full_path = os.path.join(folder_name, file_name) 

        # Check if the file is a text file
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as file:
                # Read each line in the file
                for line in file:
                    # Split the line by ', ' and strip any whitespace or newline characters
                    record = [element.strip() for element in line.split(', ')]
                    if record[0] == 'Williamsburg':
                        worksheet.append_row(record)
                    elif record[0] == 'Dumbo':
                        worksheet2.append_row(record)
                    time.sleep(1)
            
        print('Data has been written to the spreadsheet.')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")  
        time.sleep(1)
        return save_sheet_to_me()    

schedule.every().day.at("05:45").do(extract)

schedule.every().day.at("06:45").do(extract)


schedule.every().day.at("07:45").do(extract)


schedule.every().day.at("08:45").do(extract)


schedule.every().day.at("09:45").do(extract)


schedule.every().day.at("10:49").do(extract)


schedule.every().day.at("11:45").do(extract)


schedule.every().day.at("12:45").do(extract)


schedule.every().day.at("13:45").do(extract)


schedule.every().day.at("14:45").do(extract)


schedule.every().day.at("15:45").do(extract)


schedule.every().day.at("16:45").do(extract)


schedule.every().day.at("17:45").do(extract)


schedule.every().day.at("18:45").do(extract)


schedule.every().day.at("19:45").do(extract)


schedule.every().day.at("20:45").do(extract)


schedule.every().day.at("21:45").do(extract)



while True:
    schedule.run_pending()
    time.sleep(1)
