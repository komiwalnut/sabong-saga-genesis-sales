import asyncio
from datetime import datetime
import logging
import collections

from src.cache import load_cache, save_cache
from src.fetch_sales import fetch_sales
from src.payment_details import get_payment_details
from src.rns_lookup import check_rns
from src.discord_webhook import send_discord_notification

CHECK_INTERVAL = 60

logging.basicConfig(
    filename="sabungan_sales.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def truncate_address(addr: str, front: int = 6, back: int = 3) -> str:
    return f"{addr[:front]}...{addr[-back:]}"


async def main():
    cached_sales = await load_cache()

    while True:
        sales = await fetch_sales()
        new_sales = [sale for sale in sales if sale["txHash"] not in cached_sales]
        new_sales.sort(key=lambda sale: int(sale["timestamp"]))

        for sale in new_sales:
            payment_details = await get_payment_details(sale)
            sale["payment_details"] = payment_details

            sale["nft_details"] = sale["assets"][0]["token"]

            if sale["orderKind"] == 2:
                buyer_address = sale["maker"]
                seller_address = sale["matcher"]
            else:
                buyer_address = sale["matcher"]
                seller_address = sale["maker"]

            sale["buyer"] = buyer_address
            sale["seller"] = seller_address

            buyer_rns = await check_rns(buyer_address)
            seller_rns = await check_rns(seller_address)
            sale["matcher"] = buyer_rns if buyer_rns else truncate_address(buyer_address)
            sale["maker"] = seller_rns if seller_rns else truncate_address(seller_address)

            await send_discord_notification(sale)

            log_message = (
                f"TokenID: {sale['assets'][0]['token']['tokenId']}, "
                f"Timestamp: {sale['timestamp']}, "
                f"TxHash: {sale['txHash']}, "
                f"Buyer: {sale['matcher']}, "
                f"Seller: {sale['maker']}, "
                f"DateTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, "
                f"Price: {sale['payment_details']}"
            )
            logging.info(log_message)
            await asyncio.sleep(0.5)

            cached_sales.append(sale["txHash"])

        await save_cache(cached_sales)
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
