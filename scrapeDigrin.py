import re
import requests
from bs4 import BeautifulSoup


def fetch_financial_info(ticker):
    # Define the Digrin URL
    digrin_url = f'https://www.digrin.com/stocks/detail/{ticker}'

    try:
        # Send HTTP request
        response = requests.get(digrin_url)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract Digrin data
        digrin_data = {
            'DGR3': get_digrin_data(soup, 'DGR3:'),
            'DGR5': get_digrin_data(soup, 'DGR5:'),
            'DGR10': get_digrin_data(soup, 'DGR10:'),
            'DGR20': get_digrin_data(soup, 'DGR20:')
        }

        return digrin_data

    except requests.RequestException as e:
        print(f"Error: Unable to fetch Digrin data for {ticker}. {e}")
        return None


def get_digrin_data(soup, label):
    label_element = soup.find('p', string=label)
    if label_element:
        data_element = label_element.find_next('strong')
        if data_element:
            return data_element.get_text(strip=True)
    return 'N/A'


def main():
    # Get user input for the ticker symbol
    ticker_symbol = input(
        "Enter the ticker symbol (e.g., T for AT&T): ").upper()

    # Fetch Digrin data
    digrin_data = fetch_financial_info(ticker_symbol)

    # Display the obtained Digrin data
    if digrin_data:
        print(f"\nDigrin Data for {ticker_symbol}:")
        for key, value in digrin_data.items():
            print(f"{key}: {value}")
    else:
        print("Exiting due to an error.")


if __name__ == "__main__":
    main()
