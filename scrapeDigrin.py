import requests
from bs4 import BeautifulSoup


def fetch_digrin_data(ticker):
    url = f'https://www.digrin.com/stocks/detail/{ticker}'

    try:
        # Send HTTP request with a custom User-Agent header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        dgr3 = extract_dgr(soup, 'DGR3')
        dgr5 = extract_dgr(soup, 'DGR5')
        dgr10 = extract_dgr(soup, 'DGR10')
        dgr20 = extract_dgr(soup, 'DGR20')

        return {
            'DGR3': dgr3,
            'DGR5': dgr5,
            'DGR10': dgr10,
            'DGR20': dgr20
        }
    except requests.RequestException as e:
        print(f"Error: Unable to fetch Digrin data for {ticker}. {e}")
        return None


def extract_dgr(soup, label):
    dgr_element = soup.find('div', class_='col-sm-3')
    if dgr_element:
        dgr_label = dgr_element.find('p', text=f"{label}:")
        if dgr_label:
            dgr_value = dgr_label.find_next('strong')
            if dgr_value:
                return dgr_value.get_text(strip=True)
    return 'N/A'


def main():
    ticker_symbol = input("Enter the ticker symbol (e.g., T): ").upper()
    digrin_data = fetch_digrin_data(ticker_symbol)

    if digrin_data:
        print(f"\nDigrin Data for {ticker_symbol}:")
        for key, value in digrin_data.items():
            print(f"{key}: {value}")
    else:
        print("Exiting due to an error.")


if __name__ == "__main__":
    main()
