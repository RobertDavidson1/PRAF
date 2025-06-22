from io import StringIO  # To treat raw text as a file for pandas
from typing import List  # For type hinting

import pandas as pd  # To load and process the tabular ticker data
import requests  # For downloading the NASDAQ listings file


class NasdaqFetcher:
    def __init__(self):
        pass  # No Selenium driver needed for this fetcher

    def scrape(self) -> List[str]:
        # Publicly available NASDAQ listings file with | delimiter and metadata/footer lines
        BASE_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
        response = requests.get(BASE_URL)

        if response.status_code == 200:  # Check if the request was successful
            text_data = response.text  # Get the content of the response as a string

        # Split file into lines and remove metadata/footer lines
        lines = text_data.strip().splitlines()
        lines = [line for line in lines if not line.startswith("File Creation Time")]

        # Read the cleaned string data into a DataFrame
        df = pd.read_csv(StringIO("\n".join(lines)), delimiter="|")

        # Only keep the 'Symbol' column which contains the ticker symbols
        df = df[["Symbol"]]

        all_tickers = df["Symbol"].tolist()  # Convert the column to a list

        # Return the final list of ticker symbols
        return all_tickers
