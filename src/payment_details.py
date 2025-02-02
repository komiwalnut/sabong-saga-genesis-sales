import aiohttp

TOKEN_MAPPING = {
    "0xc99a6a985ed2cac1ef41640596c5a5f9f4e19ef5": ("WETH", 1e18),
    "0x97a9107c1793bc407d6f527b77e7fff4d812bece": ("AXS", 1e18),
    "0x0b7007c13325c48911f73a2dad5fa5dcbf808adc": ("USDC", 1e6),
    "0x1a89ecd466a23e98f07111b0510a2d6c1cd5e400": ("BANANA", 1e18)
}


async def hex_to_decimal(hex_str: str, divisor: float = 1e18) -> float:
    try:
        value_int = int(hex_str, 16)
        return value_int / divisor
    except Exception as e:
        print(f"Error converting hex {hex_str}: {e}")
        return 0.0


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


async def fetch_internal_payment(transaction_hash: str) -> (float, str):
    url = f"https://skynet-api.roninchain.com/ronin/explorer/v2/txs/{transaction_hash}/internal_txs?offset=0&limit=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get("result", {}).get("items", [])
                if items:
                    item = items[0]
                    value_hex = item.get("value", "0x0")
                    amount = await hex_to_decimal(value_hex, divisor=1e18)
                    if amount > 0.0001:
                        return amount, "RON"

    url_logs = f"https://skynet-api.roninchain.com/ronin/explorer/v2/txs/{transaction_hash}/logs?offset=0&limit=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url_logs) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get("result", {}).get("items", [])
                if items[0]['data'] != "0x":
                    item = items[0]
                    token_address = item.get("address", "").lower()

                    token_info = TOKEN_MAPPING.get(token_address)
                    if token_info is None:
                        token_symbol, divisor = await get_token_info(token_address)
                    else:
                        token_symbol, divisor = token_info
                    data_hex = item.get("data", "0x0")
                    amount = await hex_to_decimal(data_hex, divisor=divisor)
                    return amount, token_symbol
    return None, None


async def fetch_exchange_rate(token_symbol: str) -> float:
    token_param = token_symbol.lower()
    url = f"https://exchange-rate.skymavis.com/{token_param}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("usd", 0.0)
    return 0.0


async def get_payment_details(transaction_hash: str) -> dict:
    amount, token_symbol = await fetch_internal_payment(transaction_hash)
    if amount and token_symbol:
        rate = await fetch_exchange_rate(token_symbol)
        usd_value = amount * rate

        amount = round(amount, 3)
        usd_value = round(usd_value, 3)

        return {
            "amount": int(amount) if amount.is_integer() else f"{amount:.3f}",
            "token": token_symbol,
            "usd_value": int(usd_value) if usd_value.is_integer() else f"{usd_value:.3f}"
        }
