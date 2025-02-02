import aiohttp


async def fetch_nft_details(token_id: str) -> dict:
    query = {
        "operationName": "GetERC721TokenDetail",
        "variables": {
            "tokenId": token_id,
            "tokenAddress": "0xee9436518030616bc315665678738a4348463df4"
        },
        "query": """
                query GetERC721TokenDetail($tokenAddress: String, $tokenId: String!) {
                    erc721Token(tokenAddress: $tokenAddress, tokenId: $tokenId) {
                        tokenId
                        owner
                        attributes
                        cdnImage
                    }
                }
            """
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://marketplace-graphql.skymavis.com/graphql", json=query) as response:
            if response.status == 200:
                data = await response.json()

                return data.get("data", {}).get("erc721Token", {})
    return {}
