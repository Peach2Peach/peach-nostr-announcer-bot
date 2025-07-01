import asyncio
import json
import logging
import os
from logging import getLogger

from app.nostr import init_nostr_client, publish_offer_to_nostr
from app.peach import get_peach_offers

JSON_FILE = "./peach_offers_data/offers.json"

logger = getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main_loop() -> None:

    NOSTR_PRIVATE_KEY: str | None = os.getenv("NOSTR_PRIVATE_KEY")
    assert NOSTR_PRIVATE_KEY

    with open(JSON_FILE, "r") as f:
        saved_offers: list[int] = json.load(f)["offer_ids"]

    nostr_client = await init_nostr_client(secret_key_nsec=NOSTR_PRIVATE_KEY)

    while True:
        try:
            # logger.info("Getting Peach Offers from the Peach API...")

            offers = await get_peach_offers()

            # here we remove the irrelevant offer ids we had saved
            saved_offers = [x for x in saved_offers if x in [y["id"] for y in offers]]

            # we check which ones are new
            new_offers = [x for x in offers if x["id"] not in saved_offers]

            # logger.info("Found new offers: " + str([x["id"] for x in new_offers]))

            for new_offer in new_offers:

                await publish_offer_to_nostr(nostr_client=nostr_client, offer=new_offer)

                # we add the new saved offer id
                logger.info("Published to NOSTR Offer ID " + str(new_offer["id"]))
                saved_offers.append(new_offer["id"])
                with open(JSON_FILE, "w") as f:
                    # and we save a new file
                    json.dump({"offer_ids": saved_offers}, f, indent=2)
            # logger.info("Done with batch, sleeping...")
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error happened! {e}")
            logger.info("Sleeping...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main_loop())
