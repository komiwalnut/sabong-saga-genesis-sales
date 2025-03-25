import aiohttp
import logging
from src.utils import get_token_info, fetch_exchange_rate
from src.constants import TOKEN_MAPPING


async def get_payment_details(sale):
    payment_token = sale.get("paymentToken", "")
    tokenSymbol = TOKEN_MAPPING.get(payment_token)
    
    if not tokenSymbol:
        try:
            symbol, divisor = await get_token_info(payment_token)
            tokenSymbol = (symbol, divisor)
        except Exception as e:
            logging.error(f"Error getting token info: {str(e)}")
            tokenSymbol = ("UNKNOWN", 1e18)
    
    amount = int(sale.get('realPrice', 0)) / tokenSymbol[1]
    
    exchange_rate = await fetch_exchange_rate(tokenSymbol[0])
    usd_value = amount * exchange_rate

    return {
        "amount": int(amount) if amount.is_integer() else f"{amount:.3f}",
        "tokenSymbol": tokenSymbol[0],
        "usd_value": int(usd_value) if usd_value.is_integer() else f"{usd_value:.2f}",
        "rate_success": exchange_rate > 0
    }
