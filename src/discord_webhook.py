import aiohttp
import logging
from datetime import datetime, timezone
from src.config import DISCORD_WEBHOOK_URL


async def send_discord_notification(sale):
    payment_details = sale.get('payment_details', {})
    usd_value = payment_details.get('usd_value', '0')
    try:
        usd_float = float(str(usd_value).replace(',', ''))
        if usd_float <= 0:
            logging.warning(f"Skipping Discord notification for sale with $0 value: {sale.get('txHash')}")
            return False
    except (ValueError, TypeError):
        logging.error(f"Invalid USD value when sending notification: {usd_value}")
        return False

    token_id = sale["assets"][0]["token"]["tokenId"]
    cdn_image = sale["assets"][0]["token"]['cdnImage']
    nft_details = sale['nft_details']
    
    amount = payment_details['amount']
    token = payment_details['tokenSymbol']
    payment_info = f"{str(float(amount)).rstrip('0').rstrip('.')} {token} (~${str(float(usd_value)).rstrip('0').rstrip('.')})"

    embed = {
        "author": {
            "name": "Sabong Saga Genesis",
            "icon_url": "https://cdn.skymavis.com/ronin/2020/erc721/0xee9436518030616bc315665678738a4348463df4/logo.png"
        },
        "title": f"Chicken #{token_id}",
        "url": f"https://marketplace.skymavis.com/collections/sabong-saga-genesis/{token_id}",
        "description": f"[View Transaction](https://app.roninchain.com/tx/{sale['txHash']})",
        "color": 16514353,
        "fields": [
            {"name": "Price", "value": payment_info, "inline": True},
            {"name": "Seller", "value": f"[{sale['maker']}](https://marketplace.skymavis.com/account/{sale['seller']})", "inline": True},
            {"name": "Buyer", "value": f"[{sale['matcher']}](https://marketplace.skymavis.com/account/{sale['buyer']})", "inline": True},
        ],
        "thumbnail": {"url": cdn_image},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    group1_keys = [
        "feet", "tail", "body", "wings", "eyes",
        "beak", "comb", "instinct", "color",
        "daily feathers", "legendary count"
    ]
    attributes = nft_details.get("attributes", {})
    for key in group1_keys:
        if key in attributes:
            field_value = ", ".join(attributes[key]).capitalize()
            embed["fields"].append({
                "name": key.title(),
                "value": field_value.title(),
                "inline": True
            })

    if "birthdate" in attributes:
        birth_epoch = int(attributes["birthdate"][0])
        birthdate_str = datetime.fromtimestamp(birth_epoch).strftime("%d %b %Y")
        embed["fields"].append({
            "name": "Birthdate",
            "value": birthdate_str,
            "inline": True
        })

    innate_keys = ["innate attack", "innate defense", "innate speed", "innate health"]
    innate_values = []
    for key in innate_keys:
        if key in attributes:
            value = ", ".join(attributes[key])
            innate_values.append(f"{key.split()[1].title()}: {value}")
    if innate_values:
        embed["fields"].append({
            "name": "Innate",
            "value": "\n".join(innate_values),
            "inline": True
        })

    grit_keys = ["grit attack", "grit defense", "grit speed", "grit health"]
    grit_values = []
    for key in grit_keys:
        if key in attributes:
            value = ", ".join(attributes[key])
            grit_values.append(f"{key.split()[1].title()}: {value}")
    if grit_values:
        embed["fields"].append({
            "name": "Grit",
            "value": "\n".join(grit_values),
            "inline": True
        })

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}) as response:
                success = response.status == 204
                if not success:
                    response_text = await response.text()
                    logging.error(f"Discord API error: Status {response.status}, Response: {response_text}")
                return success
    except Exception as e:
        logging.error(f"Exception when sending Discord notification: {str(e)}")
        return False
