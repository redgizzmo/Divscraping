import requests
from bs4 import BeautifulSoup

def get_dividend_info(ticker):
    # Define the URL for the Finviz page
    url = f'https://finviz.com/quote.ashx?t={ticker}'

    # Send an HTTP request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract dividend-related information
        eps = soup.find(text='EPS (ttm):').find_next('b').text
        stock_price = soup.find(text='Price:').find_next('b').text
        dividend_yield = soup.find(text='Dividend %:').find_next('b').text

        return {
            'EPS': eps,
            'Stock Price': stock_price,
            'Dividend Yield': dividend_yield
        }
    else:
        print(f"Error: Unable to fetch data. Status Code: {response.status_code}")

# Specify the ticker symbol (e.g., 'T' for AT&T)
ticker_symbol = 'T'

# Get dividend information for the specified ticker
dividend_info = get_dividend_info(ticker_symbol)

# Print the obtained information
if dividend_info:
    print(f"Dividend Information for {ticker_symbol}:")
    print(f"EPS: {dividend_info['EPS']}")
    print(f"Stock Price: {dividend_info['Stock Price']}")
    print(f"Dividend Yield: {dividend_info['Dividend Yield']}")



