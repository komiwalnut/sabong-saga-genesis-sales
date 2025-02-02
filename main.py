import asyncio
from datetime import datetime
import logging
from src.cache import load_cache, save_cache
from src.fetch_sales import fetch_sales
from src.fetch_nft_details import fetch_nft_details
from src.rns_lookup import check_rns
from src.discord_webhook import send_discord_notification
from src.payment_details import get_payment_details

CHECK_INTERVAL = 60

logging.basicConfig(filename="sabungan.log", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def truncate_address(addr: str, front: int = 6, back: int = 3) -> str:
    return f"{addr[:front]}...{addr[-back:]}"


async def main():
    cached_sales = await load_cache()

    while True:
        sales = await fetch_sales()
        new_sales = [sale for sale in sales if sale["transactionHash"] not in cached_sales]
        new_sales.sort(key=lambda sale: sale["blockTime"], reverse=True)

        tasks = []
        task_count = 0
        for sale in new_sales:
            payment_details = await get_payment_details(sale["transactionHash"])
            if payment_details:
                nft_details = await fetch_nft_details(sale["tokenId"])

                buyer_address = sale["to"]
                seller_address = sale["from"]

                buyer_rns = await check_rns(buyer_address)
                seller_rns = await check_rns(seller_address)

                sale["to"] = buyer_rns if buyer_rns else truncate_address(buyer_address)
                sale["from"] = seller_rns if seller_rns else truncate_address(seller_address)

                sale["payment_details"] = payment_details
                sale["nft_details"] = nft_details
                tasks.append(send_discord_notification(sale))

                log_message = (f"TokenID: {sale['tokenId']}, "
                               f"TransactionHash: {sale['transactionHash']}, "
                               f"Buyer: {sale['to']}, "
                               f"Seller: {sale['from']}, "
                               f"DateTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, "
                               f"Price: {payment_details}")
                logging.info(log_message)
                task_count += 1

                if task_count % 10 == 0:
                    await asyncio.sleep(2)

        if tasks:
            await asyncio.gather(*tasks)
            cached_sales.extend(sale['transactionHash'] for sale in new_sales)

        await save_cache(cached_sales)
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
