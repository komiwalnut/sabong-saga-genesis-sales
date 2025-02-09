import aiohttp
from src.config import SM_KEY


async def fetch_sales():
    url = "https://api-gateway.skymavis.com/graphql/mavis-marketplace"

    query = """
    query SalesFetching {
      recentlySolds(
        from: 0
        size: 40
        tokenAddress: "0xee9436518030616bc315665678738a4348463df4"
      ) {
        results {
          maker
          matcher
          paymentToken
          realPrice
          txHash
          assets {
            address
            token {
              ... on Erc721 {
                name
                cdnImage
                tokenId
                attributes
              }
            }
          }
          timestamp
        }
      }
    }
    """

    payload = {"query": query}
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": SM_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                return data["data"]["recentlySolds"]["results"]
            return []
