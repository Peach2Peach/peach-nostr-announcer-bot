import httpx
from httpx import Response


async def get_peach_offers() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp: Response = await client.get(
            url="https://api.peachbitcoin.com/v1/offer/search/nostr"
        )

    peach_offers: dict = resp.json()

    return peach_offers["offers"]
