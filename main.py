from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
import time
import pytz
import schedule
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

extracted_data = [["Venue", "Date", "Time", "Booked Courts"]]
# Load environment variables from .env file
load_dotenv()



# Format the date as YYYY-MM-DD



# Replace with your email from the .env file
YOUR_EMAIL = os.getenv('YOUR_EMAIL')
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')

# Path to your credentials.json file from the .env file
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def extract():    
    current_date = datetime.now()
    date_index = current_date.strftime("%Y-%m-%d")
    hour_index = int(current_date.strftime("%H"))
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--window-size=1920,1080")  # Set a window size
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = chrome_options)

    # Open the website
    driver.get("https://bookings.padel.haus/users/sign_in")
    time.sleep(5)    
    urls = ["https://bookings.padel.haus/home", "https://bookings.padel.haus/home"]
    venues = ["Williamsburg", "Dumbo"]

    # Wait for the email field to be loaded
    wait = WebDriverWait(driver, 2)


    email_field = wait.until(EC.visibility_of_element_located((By.ID, "user_email")))
    email_field.send_keys(USER_EMAIL)

    # Wait for the password field to be loaded
    password_field = wait.until(EC.visibility_of_element_located((By.ID, "user_password")))
    password_field.send_keys(USER_PASSWORD)

    # Wait for the login button to be clickable and click it
    login_button = wait.until(EC.element_to_be_clickable((By.NAME, "commit")))
    login_button.click()
    time.sleep(1)
        
    for i, url in enumerate(urls):
        driver.get(url)
        time.sleep(1)
        venue_buttons = driver.find_element(By.ID, "facilities-tags").find_elements(By.TAG_NAME, 'button')
        venue_buttons[i].click()
        time.sleep(3)
        book_button = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ui.button.large.fluid.white"))
        )
        book_button.click()
        # Wait for the buttons with the class name "ui button selectable basic" to be loaded
        time.sleep(1)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='submit'][name='commit'][value='Accept']")))
            accept_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][name='commit'][value='Accept']")
            accept_button.click()
        except TimeoutException:
            time.sleep(1)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ui.button.selectable.basic")))

        days_list_div = driver.find_element(By.CLASS_NAME, "DaysRangeOptions")
        day_buttons = days_list_div.find_elements(By.TAG_NAME, "button")    
        for d, day_button in enumerate(day_buttons):
            date = f"2024-01-{driver.find_element(By.CLASS_NAME, 'DaysRangeOptions').find_elements(By.TAG_NAME, 'button')[d].find_element(By.CLASS_NAME, 'day_number').text}"
            driver.find_element(By.CLASS_NAME, 'DaysRangeOptions').find_elements(By.TAG_NAME, 'button')[d].click()
            time.sleep(1)
            
            # Re-find the 'hours_list_div' and 'hour_buttons'
            hours_list_div = driver.find_element(By.CLASS_NAME, 'hours_list')
            hour_buttons = driver.find_element(By.CLASS_NAME, 'hours_list').find_elements(By.TAG_NAME, "button")            
                
            for index, hour_button in enumerate(hour_buttons):
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                class_name = soup.find(class_='hours_list').find_all('button')[index].get('class')
                if "red" in class_name:
                    venue = venues[i]
                    hour = soup.find(class_='hours_list').find_all('button')[index].text.replace(' +', '')
                    record = [venue, date, hour, 4]
                    print(record)                
                    extracted_data.append(record)
                    # Define the folder name where you want to save the file
                    folder_name = f"extracted-{date_index}"

                    # Create the folder if it doesn't exist
                    if not os.path.exists(folder_name):
                        os.makedirs(folder_name)

                    # Define the file name
                    file_name = f"Padel Haus {date_index}-({str(hour_index)}~{str(hour_index + 1)}).txt"

                    # Define the full path (folder + file name)
                    full_path = os.path.join(folder_name, file_name)

                    # Now, write to the file at the specified path
                    with open(full_path, 'a', encoding='utf-8') as file:
                        file.write(', '.join(map(str, record)) + '\n')
                else:
                    try:
                        driver.find_element(By.CLASS_NAME, 'hours_list').find_elements(By.TAG_NAME, "button")[index].click()
                    except TimeoutException:
                        time.sleep(1)   
                        try:
                            driver.find_element(By.CLASS_NAME, 'DaysRangeOptions').find_elements(By.TAG_NAME, 'button')[d].click()
                            time.sleep(1)   
                            driver.find_element(By.CLASS_NAME, 'hours_list').find_elements(By.TAG_NAME, "button")[index].click()
                        except TimeoutException:
                            time.sleep(1)   
                        except Exception as e:
                            print(f"An unexpected error occurred: {e}")  
                            time.sleep(1)    
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")  
                        time.sleep(1)         
                    time.sleep(1)
                    soup = BeautifulSoup(driver.page_source, features="html.parser")
                    courts = soup.find_all(class_='over_flex_mobile_button_container')[2].find_all('button')
                    venue = venues[i]
                    hour = soup.find(class_='hours_list').find_all('button')[index].text.replace(' +', '')            
                    booked_count = 4 - len(courts)
                    record = [venue, date, hour, booked_count]
                    extracted_data.append(record)
                    print(record)
                    # Define the folder name where you want to save the file
                    folder_name = f"extracted-{date_index}"

                    # Create the folder if it doesn't exist
                    if not os.path.exists(folder_name):
                        os.makedirs(folder_name)

                    # Define the file name
                    file_name = f"Padel Haus {date_index}-({str(hour_index)}~{str(hour_index + 1)}).txt"

                    # Define the full path (folder + file name)
                    full_path = os.path.join(folder_name, file_name)

                    # Now, write to the file at the specified path
                    with open(full_path, 'a', encoding='utf-8') as file:
                        file.write(', '.join(map(str, record)) + '\n')
                    driver.find_element(By.CLASS_NAME, 'DaysRangeOptions').find_elements(By.TAG_NAME, 'button')[d].click() 
                    time.sleep(1)  
                
            time.sleep(1)  # Wait for 2 seconds before clicking the next button

    # Close the browser
    driver.quit()
import os
from googleapiclient.discovery import build

import os
from googleapiclient.discovery import build

import os
from googleapiclient.discovery import build

def save_sheet():
    current_date = datetime.now()
    date_index = current_date.strftime("%Y-%m-%d")
    folder_path = f"extracted-{date_index}"

    # Build the service for both Sheets and Drive API
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    # Create a new spreadsheet
    spreadsheet_body = {
        'properties': {
            'title': f"Padel Haus {date_index}"
        }
    }
    spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId').execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    print('Spreadsheet ID:', spreadsheet_id)

    # Share the spreadsheet with your email
    drive_permission_body = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': YOUR_EMAIL
    }
    drive_service.permissions().create(fileId=spreadsheet_id, body=drive_permission_body, fields='id').execute()

    # Retrieve spreadsheet details to get the ID of the default sheet
    spreadsheet_details = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet1_id = spreadsheet_details['sheets'][0]['properties']['sheetId']

    # Initialize a flag to check if we have created the first new sheet
    first_new_sheet_created = False

    # Loop through all files in the specified folder
    for file_name in os.listdir(folder_path):
        will_save_data = [["Venue", "Date", "Time", "Booked Courts"]]
        # Check if the file is a text file
        if file_name.endswith('.txt'):
            with open(os.path.join(folder_path, file_name), 'r', encoding='utf-8') as file:
                # Read each line in the file
                for line in file:
                    # Split the line by ', ' and strip any whitespace or newline characters
                    record = [element.strip() for element in line.split(', ')]
                    # Append the array to the list of records
                    will_save_data.append(record)

            # Create a new worksheet (subsheet) for each file
            subsheet_title = file_name.replace('.txt', '')
            batch_update_spreadsheet_request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': subsheet_title
                        }
                    }
                }]
            }
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_spreadsheet_request_body).execute()

            # After creating the first new sheet, delete the default "Sheet1"
            if not first_new_sheet_created:
                delete_sheet_request = {
                    'requests': [{
                        'deleteSheet': {
                            'sheetId': sheet1_id
                        }
                    }]
                }
                sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=delete_sheet_request).execute()
                first_new_sheet_created = True

            # Save data to the created subsheet
            data_body = {
                'values': will_save_data
            }
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{subsheet_title}!A1',
                valueInputOption='RAW',
                body=data_body).execute()

            # Optional: Rename the file to indicate completion
            # os.rename(os.path.join(folder_path, file_name), os.path.join(folder_path, file_name.replace(".txt", "_completed.txt")))

    print('Data has been written to the spreadsheet.')




# while True:    
#     extract()
#     time.sleep(5)
schedule.every().day.at("06:45").do(extract)


schedule.every().day.at("07:45").do(extract)


schedule.every().day.at("08:45").do(extract)


schedule.every().day.at("09:45").do(extract)


schedule.every().day.at("10:45").do(extract)


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
schedule.every().day.at("22:00").do(save_sheet)

while True:
    schedule.run_pending()
    time.sleep(1)
