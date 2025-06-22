import random  # For adding randomness to wait times
import time  # For waiting between page loads
from typing import List  # For type hinting

from selenium.common.exceptions import NoSuchElementException  # For handling cases where elements are not found
from selenium.webdriver.common.by import By  # For locating elements
from selenium.webdriver.support import expected_conditions as EC  # For waiting conditions like element visibility, clickability, etc.
from selenium.webdriver.support.ui import WebDriverWait  # For waiting for elements to load

from .SeleniumDriver import BaseSeleniumDriver  # For Selenium WebDriver automation


class NyseFetcher:
    def __init__(self):
        # Initialize the base Selenium driver with headless browser configuration
        self.base_driver = BaseSeleniumDriver()

        # Get the WebDriver instance for browser automation
        self.driver = self.base_driver.driver

    def scrape(self) -> List[str]:
        # CSS selectors for scraping table and ticker elements
        INDEX_TABLE = "table.table-data.w-full.table-border-rows"  # Table with ticker links
        LINKS = "tbody tr td:first-child a"  # Tickers are in the first column links
        NEXT_BUTTON = '//li/a[span[contains(text(), "Next")]]'  # XPath to locate "Next" button

        # Navigate to the NYSE page
        BASE_URL = "https://www.nyse.com/listings_directory/stock"
        self.driver.get(BASE_URL)

        all_tickers = []  # Store all scraped tickers here

        while True:
            # Wait until the table is loaded before parsing
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, INDEX_TABLE)))

            # Scrape tickers on the current page
            table = self.driver.find_element(By.CSS_SELECTOR, INDEX_TABLE)  # Find the table element
            links = table.find_elements(By.CSS_SELECTOR, LINKS)  # Within the table, find all ticker link elements
            all_tickers.extend([link.text.strip() for link in links])  # Extract the text of each link and strip whitespace

            try:
                next_button = self.driver.find_element(By.XPATH, NEXT_BUTTON)  # Attempt to find the "Next" pagination button
                next_button.click()

                # Random sleep to mimic human browsing behavior
                time.sleep(random.uniform(2, 8))
            except NoSuchElementException:
                # If no "Next" button is found, we've reached the last page — exit the loop
                break

        # Close the browser session
        self.base_driver.quit()

        # Return the final list of ticker symbols
        return all_tickers
