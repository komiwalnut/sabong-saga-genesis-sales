import aiohttp
from src.config import SM_KEY


async def get_token_info(token_address: str) -> (str, float):
    url = f"https://skynet-api.roninchain.com/ronin/explorer/v2/tokens/{token_address}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                result = data.get("result", {})
                symbol = result.get("symbol", "UNKNOWN")
                decimals = result.get("decimals", 18)
                divisor = 10 ** decimals
                return symbol, divisor
    return "UNKNOWN", 1e18


async def fetch_exchange_rate(token_symbol: str) -> float:
    token_param = token_symbol.lower()
    url = f"https://exchange-rate.skymavis.com/{token_param}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("usd", 0.0)
    return 0.0
