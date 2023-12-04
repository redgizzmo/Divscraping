import requests
from bs4 import BeautifulSoup
ticker = "T"
url = f"https://finviz.com/quote.ashx?t={ticker}"
response = requests.get(url)

soup = BeautifulSoup(response.content, "html.parser")

eps = soup.select_one("td:contains('EPS (ttm)')").find_next("b").text
stock_price = soup.select_one(
    ".snapshot-table2 td:contains('Price')").find_next("b").text
dividend_yield = soup.select_one(
    "td:contains('Dividend %')").find_next("b").text

print(f"EPS: {eps}")
print(f"Stock Price: {stock_price}")
print(f"Dividend Yield: {dividend_yield}")
