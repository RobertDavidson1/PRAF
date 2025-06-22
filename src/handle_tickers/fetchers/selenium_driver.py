import random  # Randomly select a screen resolution from a list of presets.
import tempfile  # Creates a temporary directory for file downloads.

from fake_useragent import UserAgent  # Random user agent string to mimic different browsers.
from selenium import webdriver  # For controlling the Chrome browser.
from selenium.webdriver.chrome.options import Options  # For configuring the Selenium WebDriver.


class BaseSeleniumDriver:
    """Encapsulates Selenium setup and usage in a reusable class."""

    def __init__(self):
        self.download_dir = tempfile.mkdtemp(prefix="dl_")  # Generates a temporary directory for downloads.
        self.implicit_wait = 5  # Implicit wait for element searches.
        self.page_load_timeout = 10  # Max page load time to 10 seconds.
        self.width, self.height = random.choice([(1024, 768), (1280, 800), (1366, 768)])  # Randomizes browser resolution.

        self.ua = UserAgent()  # Instantiates the fake user-agent generator.
        self.browser_options = Options()  # Creates browser options
        self.browser_options.headless = True  # Sets headless mode.
        self.browser_options.binary_location = "/usr/bin/chromium"  # Path to the Chromium binary.

        #  Stability tweaks for headless Chrome in Docker or Linux.
        self.browser_options.add_argument("--no-sandbox")
        self.browser_options.add_argument("--disable-dev-shm-usage")
        self.browser_options.add_argument("--disable-gpu")

        # Sets the browser window size and user agent.
        self.browser_options.add_argument(f"--window-size={self.width},{self.height}")  # Set the browser window size explicitly.
        self.browser_options.add_argument("--disable-blink-features=AutomationControlled")  # Removes automation-related flags.
        self.browser_options.add_argument(f"user-agent={self.ua.random}")  # Sets a random, real-looking user agent.

        #  Disables Selenium-specific automation flags.
        self.browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.browser_options.add_experimental_option("useAutomationExtension", False)
        self.browser_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": self.download_dir,  # Sets the default download directory to the temporary directory.
                "download.prompt_for_download": False,  # Disables download prompts.
                "profile.default_content_settings.popups": 0,  # Disables pop-ups.
            },
        )

        self.driver = webdriver.Chrome(options=self.browser_options)  # Initializes the Chrome WebDriver with the specified options.
        self.driver.implicitly_wait(self.implicit_wait)  # Sets the implicit wait time for finding elements.
        self.driver.set_page_load_timeout(self.page_load_timeout)  # Sets the maximum time to wait for a page to load.

        # Execute script to remove navigator.webdriver property and avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def quit(self):
        """Gracefully closes the WebDriver session and releases resources."""
        if self.driver:
            self.driver.quit()  # Ensures resources are released after use.
