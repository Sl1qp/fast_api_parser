from bs4 import BeautifulSoup

st_accept = "text/html"
st_useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 " \
               "Safari/605.1.15"
headers = {
    "Accept": st_accept,
    "User-Agent": st_useragent
}


async def parse(url, session):
    async with session.get(url, headers=headers) as response:
        return await response.text()


async def get_ref(page_id: int, session) -> list:
    html = await parse(
        f"https://spimex.com/markets/oil_products/trades/results/?page=page-{page_id}&bxajaxid"
        "=d609bce6ada86eff0b6f7e49e6bae904", session)
    soup = BeautifulSoup(html, 'html.parser')

    hrefs = soup.select(".accordeon-inner__item-title.link.xls")
    trade_dates = [ref["href"] for ref in hrefs]

    return trade_dates
