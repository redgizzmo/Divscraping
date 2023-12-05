import re
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
            'EPS (ttm)': get_value(soup, 'EPS (ttm)'),
            'Stock Price': get_value(soup, 'Price'),
            'Dividend in USD': get_value(soup, 'Dividend'),
            'Dividend Payout Ratio': calculate_payout_ratio(soup),
            'Dividend Yield': get_value(soup, 'Dividend %'),
            'P/E': get_value(soup, 'P/E'),
            'Forward P/E': get_value(soup, 'Forward P/E'),
            'Shares Outstanding': int(get_numeric_value(soup, 'Shs Outstand')),
        }

        return financial_info

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data for {ticker}. {e}")
        return None


def get_value(soup, label):
    label_element = soup.find('td', class_='snapshot-td2', string=label)
    if label_element:
        value_element = label_element.find_next('td', class_='snapshot-td2')
        if value_element:
            return value_element.get_text(strip=True)
    return 'N/A'


def get_numeric_value(soup, label):
    label_element = soup.find('td', class_='snapshot-td2', string=label)
    if label_element:
        value_element = label_element.find_next('td', class_='snapshot-td2')
        if value_element:
            numeric_value = value_element.get_text(strip=True)
            # Convert abbreviations to numbers
            numeric_value = convert_abbreviations(numeric_value)
            # Check if the numeric value is valid
            return numeric_value if isinstance(numeric_value, (int, float)) else 'N/A'
    return 'N/A'


def convert_abbreviations(value):
    # Define a dictionary for common abbreviations
    abbreviations = {'B': 1e9, 'M': 1e6, 'K': 1e3}
    # Use regular expression to find numeric and abbreviation parts
    match = re.match(r'(?P<numeric>[\d.]+)\s*(?P<abbrev>\w*)', value)
    if match:
        numeric_part = float(match.group('numeric'))
        abbrev_part = match.group('abbrev').upper()
        # Multiply numeric part by the corresponding factor from the dictionary
        return numeric_part * abbreviations.get(abbrev_part, 1)
    return value


def calculate_payout_ratio(soup):
    dividend_in_usd = get_value(soup, 'Dividend')
    eps_next_y = get_value(soup, 'EPS next Y')

    if dividend_in_usd != 'N/A' and eps_next_y != 'N/A' and float(eps_next_y) != 0:
        payout_ratio = (float(dividend_in_usd.replace(
            '$', '').replace(',', '')) / float(eps_next_y)) * 100
        return f"{payout_ratio:.2f}%"

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
