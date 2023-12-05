import requests
from bs4 import BeautifulSoup


def fetch_financial_info(ticker):
    # Define the Finviz URL
    url = f'https://finviz.com/quote.ashx?t={ticker}'

    try:
        # Send HTTP request and check for successful response
        response = requests.get(url)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract general financial information
        financial_info = {
            'EPS': soup.find(text='EPS (ttm):').find_next('b').text,
            'Stock Price': soup.find(text='Price:').find_next('b').text,
            'Dividend Yield': soup.find(text='Dividend %:').find_next('b').text
        }

        return financial_info

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data for {ticker}. {e}")
        return None


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