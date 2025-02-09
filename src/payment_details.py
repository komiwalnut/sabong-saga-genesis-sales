import aiohttp
from src.utils import get_token_info, fetch_exchange_rate
from src.constants import TOKEN_MAPPING


async def get_payment_details(sale):
    tokenSymbol = TOKEN_MAPPING.get(sale["paymentToken"])
    amount = int(sale['realPrice']) / tokenSymbol[1]

    exchange_rate = await fetch_exchange_rate(tokenSymbol[0])
    usd_value = amount * exchange_rate

    return {
        "amount": int(amount) if amount.is_integer() else f"{amount:.3f}",
        "tokenSymbol": tokenSymbol[0],
        "usd_value": int(usd_value) if usd_value.is_integer() else f"{usd_value:.3f}"
    }