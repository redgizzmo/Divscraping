import requests
from bs4 import BeautifulSoup


def fetch_financial_info(ticker):
    # Define the Finviz URL
    url = f'https://finviz.com/quote.ashx?t={ticker}'

    try:
        # Send HTTP request with a custom User-Agent header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract general financial information
        financial_info = {
            'EPS': get_value(soup, 'EPS (ttm):'),
            'Stock Price': get_value(soup, 'Price:'),
            'Dividend Yield': get_value(soup, 'Dividend %:')
        }

        return financial_info

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data for {ticker}. {e}")
        return None


def get_value(soup, label):
    element = soup.find('td', text=label)
    if element:
        return element.find_next('b').get_text(strip=True)
    else:
        return 'N/A'


def main():
    # Get user input for the ticker symbol
    ticker_symbol = input(
        "Enter the ticker symbol (e.g., T for AT&T): ").upper()

    # Fetch financial information
    financial_info = fetch_financial_info(ticker_symbol)

    # Display the obtained information
    if financial_info:
        print(f"\nFinancial Information for {ticker_symbol}:")
        for key, value in financial_info.items():
            print(f"{key}: {value}")
    else:
        print("Exiting due to an error.")


if __name__ == "__main__":
    main()
