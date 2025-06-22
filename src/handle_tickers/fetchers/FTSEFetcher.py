import random  # For adding randomness to wait times
import time  # For waiting between page loads
from typing import List  # For type hinting

from selenium.webdriver.common.by import By  # For locating elements
from selenium.webdriver.support import expected_conditions as EC  # For waiting conditions like element visibility, clickability, etc.
from selenium.webdriver.support.ui import WebDriverWait  # For waiting for elements to load

from .SeleniumDriver import BaseSeleniumDriver  # For Selenium WebDriver automation


class FtseFetcher:
    def __init__(self):
        # Initialize the base Selenium driver with headless browser configuration
        self.base_driver = BaseSeleniumDriver()

        # Get the WebDriver instance for browser automation
        self.driver = self.base_driver.driver

    def scrape(self) -> List[str]:
        MAX_PAGE = None  # Maximum pages available - will be determined dynamically from the pagination
        PAGE_NUM = 1  # Start scraping from the first page

        # CSS selectors for scraping table and ticker elements
        INDEX_TABLE = "table.ftse-index-table-table"
        CELLS = "tbody tr td.instrument-tidm"

        all_tickers = []  # Store all scraped tickers here

        # Navigate to the FTSE All-Share constituents page
        BASE_URL = "https://www.londonstockexchange.com/indices/ftse-all-share/constituents/table"
        self.driver.get(BASE_URL)

        # Try to determine how many pages of data there are
        try:
            last_page_link = self.driver.find_element(By.CSS_SELECTOR, "a.page-last")  # Get last page link
            last_page_href = last_page_link.get_attribute("href")  # Extract href to find page number
            MAX_PAGE = int(last_page_href.split("page=")[1])  # Parse page number from the URL
        except Exception:
            # If no pagination info is found, assume a single page
            pass

        while True:
            # Wait until the index table is present in the DOM
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, INDEX_TABLE)))

            # Locate the table and extract all ticker symbols from the cells
            table = self.driver.find_element(By.CSS_SELECTOR, INDEX_TABLE)
            cells = table.find_elements(By.CSS_SELECTOR, CELLS)

            # Add each ticker symbol to the list, stripping whitespace
            all_tickers.extend([cell.text.strip() for cell in cells])

            # Move to the next page
            PAGE_NUM += 1
            self.driver.get(f"{BASE_URL}?page={PAGE_NUM}")

            # Random sleep to mimic human browsing behavior
            time.sleep(random.uniform(3, 5))

            # Break if we've reached the last page
            if MAX_PAGE and PAGE_NUM >= MAX_PAGE:
                break

        # Append ".L" to each ticker to indicate it's a London Stock Exchange ticker
        all_tickers = [ticker + ".L" for ticker in all_tickers]

        # Close the browser session
        self.base_driver.quit()

        # Return the final list of ticker symbols
        return all_tickers
