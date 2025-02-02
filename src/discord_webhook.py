import aiohttp
from datetime import datetime, timezone
from src.config import DISCORD_WEBHOOK_URL


async def send_discord_notification(sale):
    nft_details = sale['nft_details']
    payment_details = sale['payment_details']

    token_id = nft_details['tokenId']
    cdn_image = nft_details['cdnImage']

    amount = payment_details['amount']
    token = payment_details['token']
    usd_value = payment_details['usd_value']
    payment_info = f"{amount} {token} (~${usd_value})"

    embed = {
        "author": {
            "name": "Sabong Saga Genesis",
            "icon_url": "https://cdn.skymavis.com/ronin/2020/erc721/0xee9436518030616bc315665678738a4348463df4/logo.png"
        },
        "title": f"Chicken #{token_id}",
        "url": f"https://marketplace.skymavis.com/collections/sabong-saga-genesis/{token_id}",
        "description": f"[View Transaction](https://marketplace.skymavis.com/tx/{sale['transactionHash']})",
        "color": 16514353,
        "fields": [
            {"name": "Price", "value": payment_info, "inline": True},
            {"name": "Seller", "value": f"[{sale['from']}](https://marketplace.skymavis.com/account/{sale['from']})", "inline": True},
            {"name": "Buyer", "value": f"[{sale['to']}](https://marketplace.skymavis.com/account/{sale['to']})", "inline": True},
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

    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}) as response:
            return response.status == 204
