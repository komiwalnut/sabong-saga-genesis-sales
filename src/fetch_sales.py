import aiohttp


async def fetch_sales():
    url = "https://skynet-api.roninchain.com/ronin/explorer/v2/collections/0xee9436518030616bc315665678738a4348463df4/transfers?offset=0&limit=15"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                return data.get("result", {}).get("items", [])
    return []
