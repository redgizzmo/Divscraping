import re
import requests
from bs4 import BeautifulSoup


def fetch_financial_info(ticker):
    # Define the Finviz and Digrin URLs
    finviz_url = f'https://finviz.com/quote.ashx?t={ticker}'
    digrin_url = f'https://dividendvaluebuilder.com/{ticker}-dividend-history/'

    try:
        # Fetch data from Finviz
        finviz_data = fetch_finviz_data(finviz_url)

        # Fetch data from Digrin
        digrin_data = fetch_digrin_data(digrin_url)

        # Combine data from Finviz and Digrin
        financial_info = {
            'EPS (ttm)': finviz_data.get('EPS (ttm)', 'N/A'),
            'Stock Price': finviz_data.get('Stock Price', 'N/A'),
            'Dividend in USD (Annual)': calculate_annual_dividend(finviz_data.get('Dividend')),
            'Dividend Payout Ratio': calculate_payout_ratio(finviz_data),
            'Dividend Yield': finviz_data.get('Dividend Yield', 'N/A'),
            'P/E': finviz_data.get('P/E', 'N/A'),
            'Forward P/E': finviz_data.get('Forward P/E', 'N/A'),
            'Shares Outstanding': int(get_numeric_value(finviz_data, 'Shares Outstanding')),
            'DGR3': digrin_data.get('DGR3', 'N/A'),
            'DGR5': digrin_data.get('DGR5', 'N/A'),
            'DGR10': digrin_data.get('DGR10', 'N/A'),
            'DGR20': digrin_data.get('DGR20', 'N/A'),
        }

        return financial_info

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data for {ticker}. {e}")
        return None


def fetch_finviz_data(url):
    # ... (Existing finviz scraping logic, no changes needed)
    pass


def fetch_digrin_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract DGR data from Digrin
        dgr_data = {
            'DGR3': get_digrin_dgr(soup, '3-Year DGR'),
            'DGR5': get_digrin_dgr(soup, '5-Year DGR'),
            'DGR10': get_digrin_dgr(soup, '10-Year DGR'),
            'DGR20': get_digrin_dgr(soup, '20-Year DGR'),
        }

        return dgr_data

    except requests.RequestException as e:
        print(f"Error: Unable to fetch Digrin data for {url}. {e}")
        return {'DGR3': 'N/A', 'DGR5': 'N/A', 'DGR10': 'N/A', 'DGR20': 'N/A'}


def get_digrin_dgr(soup, label):
    label_element = soup.find('td', string=label)
    if label_element:
        value_element = label_element.find_next('td')
        if value_element:
            return value_element.get_text(strip=True)
    return 'N/A'


def calculate_annual_dividend(dividend):
    # Assuming the provided dividend is quarterly, convert it to annual
    if dividend != 'N/A':
        quarterly_dividend = float(dividend.replace('$', '').replace(',', ''))
        annual_dividend = quarterly_dividend * 4
        return f"${annual_dividend:,.2f}"
    return 'N/A'


def get_value(start_tag, label):
    label_element = start_tag.find('td', class_='snapshot-td2', string=label)
    if label_element:
        value_element = label_element.find_next('td', class_='snapshot-td2')
        if value_element:
            return value_element.get_text(strip=True)
    return 'N/A'


def get_numeric_value(start_tag, label):
    label_element = start_tag.find('td', class_='snapshot-td2', string=label)
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
