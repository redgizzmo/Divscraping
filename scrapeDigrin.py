import requests
from bs4 import BeautifulSoup


def scrape_digrin(ticker):
    url = f"https://www.digrin.com/stocks/detail/{ticker}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        dgr3 = get_digrin_data(soup, 'DGR3')
        dgr5 = get_digrin_data(soup, 'DGR5')
        dgr10 = get_digrin_data(soup, 'DGR10')
        dgr20 = get_digrin_data(soup, 'DGR20')

        return {
            'DGR3': dgr3,
            'DGR5': dgr5,
            'DGR10': dgr10,
            'DGR20': dgr20,
        }

    except requests.RequestException as e:
        print(f"Error: Unable to fetch data from digrin.com for {ticker}. {e}")
        return None


def get_digrin_data(soup, label):
    label_element = soup.find('td', text=label)
    if label_element:
        data_element = label_element.find_next('td')
        if data_element:
            return data_element.get_text(strip=True)
    return 'N/A'


def main():
    ticker_symbol = input(
        "Enter the ticker symbol (e.g., T for AT&T): ").upper()

    digrin_data = scrape_digrin(ticker_symbol)

    if digrin_data:
        print(f"\nDividend Growth Rates (DGR) for {ticker_symbol}:")
        for key, value in digrin_data.items():
            print(f"{key}: {value}")
    else:
        print("Exiting due to an error.")


if __name__ == "__main__":
    main()
