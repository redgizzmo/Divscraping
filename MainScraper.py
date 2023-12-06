import re
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint as pp
import time


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
        if dividend_yield == "N/A":
            dividend_yield = 0

        market_cap = int(safe_float_convert(
            get_numeric_value(soup, 'Market Cap')))
        sales_growth_rate_5y = get_valueFinviz(
            soup, 'Sales Q/Q')  # NAKIJKEN <--
        return_on_equity = get_valueFinviz(soup, 'ROE')
        shares_outstanding = int(get_numeric_value(soup, 'Shs Outstand'))
        fair_value = round(calculate_discounted_cash_flow(
            ticker, market_cap, eps, EPS_forward, dividend_yield, sales_growth_rate_5y, stock_price), 2)
        price_difference = calculate_difference(fair_value, stock_price)

        response.close()

        financial_info = {
            'Ticker': ticker,
            'Stock Price': stock_price,
            'Dividend (Annual)': dividend_annual,
            'Dividend Yield': dividend_yield,
            'Dividend Payout Ratio': dividend_payout,
            'Fair Value': fair_value,
            'Price Difference': price_difference,
            'EPS (ttm)': eps,
            'P/E': PE_ratio,
            'Forward P/E': forwardPE,
            'Shares Outstanding': shares_outstanding
        }

        return financial_info

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data for {ticker}. {e}")
        return None


def calculate_discounted_cash_flow(ticker, market_cap, earnings_per_share, forward_earnings_per_share, dividend_yield, sales_growth_rate_5y, current_price):
    # Calculate Dividends per Share
    dividends_per_share = 0
    if earnings_per_share != 'N/A':
        dividends_per_share = earnings_per_share * dividend_yield

    if forward_earnings_per_share != 'N/A':
        dividends_per_share = forward_earnings_per_share * dividend_yield

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
            '$', '').replace(',', '')) / float(eps_next_y))
        return round(float(payout_ratio), 4)
        # return f"{payout_ratio:.2f}"
    return 'N/A'


def write_financial_data_to_google_sheets(data_list, spreadsheet_name, sheet_name):
    """
    Write a list of key-value pairs for multiple tickers to a Google Sheets spreadsheet.

    Parameters:
    - data_list (list of dictionaries): List containing dictionaries of financial data for each ticker.
    - spreadsheet_name (str): Name of the Google Sheets spreadsheet.
    - sheet_name (str): Name of the sheet within the spreadsheet.

    Returns:
    - None
    """
    # Set up credentials
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'key.json', scope)
    gc = gspread.authorize(credentials)

    # Open the spreadsheet
    try:
        spreadsheet = gc.open(spreadsheet_name)
    except gspread.SpreadsheetNotFound:
        # If the spreadsheet does not exist, create a new one
        spreadsheet = gc.create(spreadsheet_name)

    # Select or create the sheet
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(sheet_name, 1, len(data_list[0]))

    # Write data to the sheet
    headers = list(data_list[0].keys())

    # Make sure the header row exists
    if worksheet.row_values(1) != headers:
        worksheet.update('A1', [headers])

    # Create a list of lists for the new data
    new_data_values = [[ticker_data[header]
                        for header in headers] for ticker_data in data_list]

    # Get the range of cells to update
    # Assuming data starts from the second row (excluding headers)
    start_cell = f'A2'
    # End cell based on number of columns
    end_cell = f'{chr(ord("A") + len(headers) - 1)}{len(new_data_values) + 1}'

    # Update the entire range with the new data
    worksheet.update(f'{start_cell}:{end_cell}', new_data_values)
    gc.session.close()


def fetch_digrin_data(ticker):
    url = f'https://www.digrin.com/stocks/detail/{ticker}'

    try:
        # Send HTTP request with a custom User-Agent header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML content
        soup2 = BeautifulSoup(response.text, 'html.parser')

        dgr3 = get_valueDigrin(soup2, 'DGR3')
        dgr5 = get_valueDigrin(soup2, 'DGR5')
        dgr10 = get_valueDigrin(soup2, 'DGR10')
        dgr20 = get_valueDigrin(soup2, 'DGR20')
        divYears = get_valueDigrin(soup2, 'Years Paying Dividends')

        response.close()

        return {
            'DGR3': dgr3,
            'DGR5': dgr5,
            'DGR10': dgr10,
            'DGR20': dgr20,
            'Years Paying Dividends': divYears
        }
    except requests.RequestException as e:
        print(f"Error: Unable to fetch Digrin data for {ticker}. {e}")
        return None


def get_valueDigrin(soup2, label):
    pattern = re.compile(fr'{label}.*?>(.*?)<\/strong>', re.DOTALL)
    match = pattern.search(str(soup2))
    if match:
        return match.group(1).strip().replace('<strong>', '').replace('</strong>', '')
    return 'N/A'


def extract_percentage(element):
    text = element.get_text(strip=True).replace('%', '').replace(',', '')
    return round(float(text) / 100, 4) if text.replace('.', '').isdigit() else None


def get_digrin_data(ticker_symbol):
    stock_url = 'https://www.digrin.com/stocks/detail/' + str(ticker_symbol)
    try:
        # Fetch the HTML content
        response = requests.get(stock_url)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract DGR3, DGR5, DGR10, and "Years Paying Dividends" values
        dgr_elements = soup.find_all('p')

        dgr3 = next((extract_percentage(dgr.find('strong'))
                    for dgr in dgr_elements if 'DGR3' in dgr.text), None)
        dgr5 = next((extract_percentage(dgr.find('strong'))
                    for dgr in dgr_elements if 'DGR5' in dgr.text), None)
        dgr10 = next((extract_percentage(dgr.find('strong'))
                     for dgr in dgr_elements if 'DGR10' in dgr.text), None)
        dgr20 = next((extract_percentage(dgr.find('strong'))
                     for dgr in dgr_elements if 'DGR20' in dgr.text), None)

        years_paying_dividends_elem = next((dgr.find(
            'strong').text for dgr in dgr_elements if 'Years Paying Dividends' in dgr.text), None)
        years_paying_dividends = int(
            years_paying_dividends_elem) if years_paying_dividends_elem else None

        return {'DGR3': dgr3, 'DGR5': dgr5, 'DGR10': dgr10, 'DGR20': dgr20, 'Years Paying Dividends': years_paying_dividends}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except (ValueError, TypeError) as e:
        print(f"Error processing data: {e}")
        return None


def getTickers():
    # Set up credentials (replace 'path/to/credentials.json' with your JSON file)
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'key.json', scope)
    gc = gspread.authorize(credentials)

    spreadsheet_name = 'Dividend aandelen Aankopen'
    sheet_name = 'IntermediateTable'

    # Open the spreadsheet
    try:
        spreadsheet = gc.open(spreadsheet_name)
    except gspread.SpreadsheetNotFound:
        # If the spreadsheet does not exist, create a new one
        spreadsheet = gc.create(spreadsheet_name)

    # Select or create the sheet
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(sheet_name, 1, 1)

    # Get values from the first column (excluding the first row)
    column_values = worksheet.col_values(1)[1:]
    gc.session.close()
    return column_values


def main():
    tickers = ['ABBV', 'ADM']
    tickers = getTickers()  # Get Latest Ticker list from Google Sheets

    financial_data_list = []
    # Iterate over each ticker
    for ticker in tickers:
        # Fetch financial information
        financial_info = []
        financial_info = fetch_financial_info(ticker)
        if financial_info:
            financial_data_list.append(financial_info)

    financial_data_list2 = []
    for ticker in financial_data_list:
        ticker_symbol = ""
        ticker_symbol = str(ticker['Ticker'])
        data = []
        time.sleep(2)
        digrin_data = get_digrin_data(ticker_symbol.upper())
        if digrin_data is not None:
            data = digrin_data
        else:
            print("???")  # <------ Hier naar kijken

        ticker.update(data)
        financial_data_list2.append(ticker)

    for ticker_row in financial_data_list2:
        pp(ticker_row)

    spreadsheet_name = 'Dividend aandelen Aankopen'
    sheet_name = 'IntermediateTable'
    write_financial_data_to_google_sheets(
        financial_data_list2, spreadsheet_name, sheet_name)


if __name__ == "__main__":
    main()
