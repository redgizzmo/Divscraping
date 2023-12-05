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
        stock_price = get_valueFinviz(soup, 'Price')
        eps = safe_float_convert(get_valueFinviz(soup, 'EPS (ttm)'))
        EPS_forward = safe_float_convert(get_valueFinviz(soup, 'EPS next Y'))
        PE_ratio = safe_float_convert(get_valueFinviz(soup, 'P/E'))
        forwardPE = safe_float_convert(get_valueFinviz(soup, 'Forward P/E'))
        dividend_annual = get_valueFinviz(soup, 'Dividend')
        dividend_payout = calculate_payout_ratio(soup)
        dividend_yield = get_valueFinviz(soup, 'Dividend %')
        market_cap = int(safe_float_convert(
            get_numeric_value(soup, 'Market Cap')))
        sales_growth_rate_5y = get_valueFinviz(
            soup, 'Sales Q/Q')  # NAKIJKEN <--
        return_on_equity = get_valueFinviz(soup, 'ROE')
        shares_outstanding = int(get_numeric_value(soup, 'Shs Outstand'))
        fair_value = round(calculate_discounted_cash_flow(
            market_cap, EPS_forward, dividend_yield, sales_growth_rate_5y, stock_price), 2)
        price_difference = calculate_difference(fair_value, stock_price)

        financial_info = {
            # 'EPS (ttm)': eps,
            'Stock Price': stock_price,
            # Updated visualization
            # 'Dividend (Annual)': dividend_annual,
            # 'Dividend Payout Ratio': dividend_payout,
            # 'Dividend Yield': dividend_yield,
            # 'P/E': PE_ratio,
            # 'Forward P/E': forwardPE,
            # 'Shares Outstanding': shares_outstanding,
            'Fair Value': fair_value,
            'Price Difference': price_difference
        }

        return financial_info

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data for {ticker}. {e}")
        return None


def calculate_discounted_cash_flow(market_cap, earnings_per_share, dividend_yield, sales_growth_rate_5y, current_price):
    # Calculate Dividends per Share
    dividends_per_share = earnings_per_share * dividend_yield

    # Calculate Growth Rate
    growth_rate = sales_growth_rate_5y

    # Set your Discount Rate (this can be a constant or dynamic based on market conditions)
    discount_rate = 0.005

    # Calculate Fair Value
    fair_value = (dividends_per_share / (discount_rate - growth_rate)
                  ) + (current_price / (1 + discount_rate))

    return fair_value


def calculate_difference(fair_value, stock_price):
    if stock_price == 0:
        return "Stock price cannot be zero."

    percentage_difference = ((fair_value - stock_price) / abs(stock_price))
    return round(percentage_difference, 4)  # Rounding to 4 decimal places


def safe_float_convert(str):
    try:
        return float(str)
    except ValueError:
        return str


def get_valueFinviz(start_tag, label):
    label_element = start_tag.find('td', class_='snapshot-td2', string=label)
    if label_element:
        value_element = label_element.find_next('td', class_='snapshot-td2')
        if value_element:
            value_text = value_element.get_text(strip=True)
            if '%' in value_text:
                value = value_text.replace('%', '')
                try:
                    return round(float(value)/100, 4)
                except ValueError:
                    return 'N/A'
            else:
                try:
                    return round(float(value_text), 2)
                except ValueError:
                    return 'N/A'
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
    dividend_in_usd = str(get_valueFinviz(soup, 'Dividend'))
    eps_next_y = str(get_valueFinviz(soup, 'EPS next Y'))

    if dividend_in_usd != 'N/A' and eps_next_y != 'N/A' and float(eps_next_y) != 0:
        payout_ratio = (float(dividend_in_usd.replace(
            '$', '').replace(',', '')) / float(eps_next_y)) * 100
        return f"{payout_ratio:.2f}%"

    return 'N/A'


def main():
    # Get user input for the ticker symbol
    # !!!!
    # ticker_symbol = input("Enter the ticker symbol (e.g., T for AT&T): ").upper()

    # List of tickers
    tickers = ['T', 'AGNC', 'ABBV', 'BEN', 'O', 'PFE', 'KR', 'BRO']
    # tickers = ['BEN']

    # Iterate over each ticker
    for ticker_symbol in tickers:
        # Fetch financial information
        financial_info = fetch_financial_info(ticker_symbol)

        # Display the obtained information
        if financial_info:
            print(f"\nFinancial Information for {ticker_symbol}:")
            for key, value in financial_info.items():
                print(f"{key}: {value}")
        else:
            print(f"Error: Unable to fetch data for {ticker_symbol}.")


if __name__ == "__main__":
    main()
