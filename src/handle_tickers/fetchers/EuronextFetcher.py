from .SeleniumDriver import BaseSeleniumDriver  # For Selenium WebDriver automation
from typing import List  # For type hinting
import time  # For waiting for the download to complete
import os  # For loading the downloaded CSV file
import pandas as pd  # For handling the downloaded CSV data

from selenium.webdriver.common.by import By  # For locating elements
from selenium.webdriver.support.ui import WebDriverWait  # For waiting for elements to load
from selenium.webdriver.support import expected_conditions as EC  # For waiting conditions like element visibility, clickability, etc.


class EuronextFetcher:
    """
    Fetches Euronext stock data using Selenium WebDriver.
    """

    def __init__(self):
        # Initialize the base Selenium driver with headless browser configuration
        self.base_driver = BaseSeleniumDriver()

        # Get the WebDriver instance for browser automation
        self.driver = self.base_driver.driver

    def scrape(self) -> List[str]:
        # CSS selectors for key UI elements on the Euronext page
        MENU_BUTTON = "div.dt-buttons .btn.btn-link"
        CSV_LABEL = "label[for='download_csv']"
        DECIMAL_LABEL = "label[for='deci_comma']"
        GO_BUTTON = "input[value='Go']"

        # Navigate to the Euronext equities listing page
        BASE_URL = "https://live.euronext.com/en/products/equities/list"
        self.driver.get(BASE_URL)

        # Click buttons in sequence: menu -> csv -> decimal -> go
        menu_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, MENU_BUTTON)))
        menu_button.click()

        csv_label = self.driver.find_element(By.CSS_SELECTOR, CSV_LABEL)
        csv_label.click()

        decimal_label = self.driver.find_element(By.CSS_SELECTOR, DECIMAL_LABEL)
        decimal_label.click()

        go_button = self.driver.find_element(By.CSS_SELECTOR, GO_BUTTON)
        go_button.click()

        # Wait for download
        time.sleep(5)

        # Look for downloaded CSV files in the temporary download directory
        csv_files = [f for f in os.listdir(self.base_driver.download_dir) if f.endswith(".csv")]
        if csv_files:
            # Get the most recently downloaded CSV file
            latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(self.base_driver.download_dir, x)))
            # Load the CSV into a pandas DataFrame using semicolon separator
            df = pd.read_csv(os.path.join(self.base_driver.download_dir, latest_csv), sep=";")
        else:
            # If no CSV file found, close browser and return empty list
            self.base_driver.quit()
            return []

        # Map exchange names (from CSV) to their Yahoo Finance suffixes
        EXCHANGE_MAPPING = {
            "Oslo Børs": ".OL",
            "Euronext Expand Oslo": ".OL",
            "Euronext Growth Oslo": ".OL",
            "Euronext Access Paris": ".PA",
            "Euronext Growth Paris": ".PA",
            "Euronext Growth Paris, Brussels": ".PA",
            "Euronext Paris": ".PA",
            "Euronext Paris, Amsterdam": ".PA",
            "Euronext Paris, Brussels": ".PA",
            "Euronext Paris, Amsterdam, Brussels": ".PA",
            "Euronext Growth Milan": ".MI",
            "Euronext Milan": ".MI",
            "Euronext Amsterdam": ".AS",
            "Euronext Amsterdam, Brussels": ".AS",
            "Euronext Amsterdam, Brussels, Paris": ".AS",
            "Euronext Amsterdam, Paris": ".AS",
            "Euronext Brussels": ".BR",
            "Euronext Growth Brussels": ".BR",
            "Euronext Growth Brussels, Paris": ".BR",
            "Euronext Access Brussels": ".BR",
            "Euronext Brussels, Paris": ".BR",
            "Euronext Brussels, Amsterdam": ".BR",
            "Euronext Brussels, Amsterdam, Paris": ".BR",
            "Euronext Dublin": ".IR",
            "Euronext Growth Dublin": ".IR",
            "Euronext Lisbon": ".LS",
            "Euronext Access Lisbon": ".LS",
            "Euronext Growth Lisbon": ".LS",
        }

        # Filter the DataFrame to only include markets in our mapping
        df = df[df["Market"].isin(EXCHANGE_MAPPING.keys())].copy()
        # Ensure all symbols are treated as strings
        df["Symbol"] = df["Symbol"].astype(str)

        # Append the correct exchange suffix to each symbol based on its market
        df["Symbol"] = df.apply(lambda row: row["Symbol"] + EXCHANGE_MAPPING.get(row["Market"], ""), axis=1)
        # Convert the final list of full tickers (e.g., 'AAPL.PA') to a Python list
        all_tickers = df["Symbol"].tolist()

        # Close the browser session
        self.base_driver.quit()

        # Return the final list of ticker symbols
        return all_tickers
