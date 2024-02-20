# Padel Court Booking Data Extractor and Scheduler

## Overview
The Padel Court Booking Data Extractor and Scheduler is a Python application designed to automate the process of extracting booking information for Padel courts from the website "Padel Haus". It captures details such as the venue, date, time, and number of booked courts at specified intervals throughout the day. The extracted data is then saved both locally and on Google Sheets for easy access and analysis.

## Features
- **Automated Extraction:** Extracts court booking data from the Padel Haus website at regular intervals.
- **Local and Cloud Storage:** Saves data in text files locally and updates Google Sheets.
- **Scheduled Extraction:** Executes data extraction at predefined times daily.
- **Headless Browser Automation:** Utilizes Selenium with Chrome in headless mode for website interaction.
- **Google Sheets API Integration:** Automates the process of creating and updating Google Sheets with extracted data.

## Prerequisites
- Python 3.6 or higher.
- Google account with Google Sheets and Google Drive API enabled.
- Selenium WebDriver for Chrome.
- Access to the Padel Haus website with valid credentials.

## Installation

1. **Clone the Repository**
   ```bash
   git clone [repository URL]
   cd [repository folder]
   ```

2. **Install Dependencies**
   ```bash
   pip install selenium pandas beautifulsoup4 pytz schedule google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client webdriver-manager python-dotenv
   ```

3. **Environment Setup**
   - Create a `.env` file in the project directory.
   - Add the following environment variables:
     ```
     USER_EMAIL=padel_user@example.com
     USER_PASSWORD=your_password
     GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/your/credentials.json
     ```

4. **Google API Credentials**
   - Create a service account on Google Cloud Platform and download the JSON credentials file.
   - Ensure that the service account has access to Google Sheets and Google Drive.

## Usage

1. **Run the Script**
   ```bash
   python [script_name].py
   ```
   This will start the scheduled extraction process.

2. **Data Extraction Schedule**
   - The script is configured to run the extraction process at specific times throughout the day (e.g., every hour from 6:45 AM to 10:45 PM).

3. **Viewing Data**
   - Local data can be found in the `extracted-[current_date]` folder in text files.
   - Cloud data will be available in a Google Sheet titled "Padel Haus [current_date]".

4. **Modifications**
   - To change extraction times or other parameters, modify the relevant sections in the script.

## Important Notes
- Ensure that the computer running the script is powered on and has a stable internet connection.
- Do not close the terminal or interrupt the script while it's running scheduled tasks.
- Adjust the `time.sleep()` values if the website's response time varies.

## Troubleshooting
- If extraction fails, check your internet connection and website credentials.
- Ensure that your Google API credentials have the necessary permissions.
- For issues with Selenium WebDriver, ensure that the Chrome version is compatible with the WebDriver version.

## Contributing
Contributions to enhance the functionality or efficiency of this project are welcome. Please follow the standard fork-pull request workflow.
