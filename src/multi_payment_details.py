import aiohttp
from src.utils import hex_to_decimal, get_token_info, fetch_exchange_rate
from src.constants import TOKEN_MAPPING

MULTI_SEND_PROXY = "0x21a0a1c081dc2f3e48dc391786f53035f85ce0bc".lower()
MARKET_GATEWAY_PROXY = "0x3b3adf1422f84254b7fbb0e7ca62bd0865133fe3".lower()


async def get_multi_payment_details(transaction_hash: str) -> list:
    url_logs = f"https://skynet-api.roninchain.com/ronin/explorer/v2/txs/{transaction_hash}/internal_txs?offset=0&limit=100"

    async with aiohttp.ClientSession() as session:
        async with session.get(url_logs) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get("result", {}).get("items", [])
                payments = []

                for item in items:
                    if (item.get("from", "").lower() == MULTI_SEND_PROXY and
                            item.get("to", "").lower() == MARKET_GATEWAY_PROXY):

                        if item.get("data", "0x") != "0x":
                            token_address = item.get("address", "").lower()
                            token_info = TOKEN_MAPPING.get(token_address)

                            if token_info is None:
                                token_symbol, divisor = await get_token_info(token_address)
                            else:
                                token_symbol, divisor = token_info

                            amount = await hex_to_decimal(item.get("data", "0x0"), divisor=divisor)
                        else:
                            token_symbol = "RON"
                            amount = await hex_to_decimal(item.get("value", "0x0"), divisor=1e18)

                        if amount > 0.0001:
                            rate = await fetch_exchange_rate(token_symbol)
                            usd_value = amount * rate

                            amount_rounded = round(amount, 3)
                            usd_value_rounded = round(usd_value, 3)

                            payment_detail = {
                                "amount": int(amount_rounded) if amount_rounded.is_integer() else f"{amount_rounded:.3f}",
                                "token": token_symbol,
                                "usd_value": int(usd_value_rounded) if usd_value_rounded.is_integer() else f"{usd_value_rounded:.3f}"
                            }
                            payments.append(payment_detail)
                return payments
    return []
