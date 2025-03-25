import asyncio
from datetime import datetime
import logging

from src.cache import load_cache, save_cache
from src.fetch_sales import fetch_sales
from src.payment_details import get_payment_details
from src.rns_lookup import check_rns
from src.discord_webhook import send_discord_notification

CHECK_INTERVAL = 60
MAX_RETRIES_PER_SALE = 5

logging.basicConfig(
    filename="sabungan_sales.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def truncate_address(addr: str, front: int = 6, back: int = 3) -> str:
    return f"{addr[:front]}...{addr[-back:]}"


async def process_sale(sale, cached_sales):
    tx_hash = sale["txHash"]
    retries = 0
    
    if tx_hash in cached_sales:
        logging.info(f"Sale {tx_hash} already processed, skipping")
        return False
    
    while retries < MAX_RETRIES_PER_SALE:
        payment_details = await get_payment_details(sale)
        sale["payment_details"] = payment_details
        
        usd_value = payment_details.get("usd_value", "0")
        rate_success = payment_details.get("rate_success", False)
        
        try:
            usd_float = float(usd_value.replace(',', '')) if isinstance(usd_value, str) else float(usd_value)
            if usd_float <= 0 or not rate_success:
                retries += 1
                logging.warning(f"Got zero/invalid USD value for sale {tx_hash}. Retry {retries}/{MAX_RETRIES_PER_SALE}")
                if retries < MAX_RETRIES_PER_SALE:
                    await asyncio.sleep(15)
                    continue
                else:
                    logging.error(f"Max retries reached for {tx_hash}. Unable to get valid price.")
                    return False
        except ValueError:
            logging.error(f"Invalid USD value format: {usd_value}")
            retries += 1
            if retries < MAX_RETRIES_PER_SALE:
                await asyncio.sleep(15)
                continue
            else:
                logging.error(f"Max retries reached for {tx_hash}. USD format error.")
                return False
        
        sale["nft_details"] = sale["assets"][0]["token"]

        if sale["orderKind"] == 2 or sale["orderKind"] == 0:
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

        notification_sent = await send_discord_notification(sale)
        
        if not notification_sent:
            logging.error(f"Failed to send Discord notification for sale {tx_hash}")
        
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
        
        return True


async def main():
    cached_sales = await load_cache()
    pending_sales = []

    while True:
        try:
            sales = await fetch_sales()
            
            for sale in sales:
                if sale["txHash"] not in cached_sales and sale["txHash"] not in [s["txHash"] for s in pending_sales]:
                    pending_sales.append(sale)
            
            pending_sales.sort(key=lambda sale: int(sale["timestamp"]))
            
            if pending_sales:
                logging.info(f"Processing {len(pending_sales)} pending sales")
                
                sale = pending_sales[0]
                
                success = await process_sale(sale, cached_sales)
                
                pending_sales.pop(0)
                if success:
                    cached_sales.append(sale["txHash"])
                    await save_cache(cached_sales)
                
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(CHECK_INTERVAL)
                
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
