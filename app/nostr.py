import json
import logging
import time
from datetime import timedelta
from logging import getLogger

from nostr_sdk import (  # type: ignore
    Client,
    Event,
    EventBuilder,
    Filter,
    Keys,
    Kind,
    NostrSigner,
    Tag,
)
from nostr_sdk.nostr_sdk import Events, PublicKey  # type: ignore

logger = getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

PEACH_ORDER_EXPIRATION = 1 * 60 * 60  # 1H in seconds

RELAYS: list[str] = [
    # "wss://nostr.pleb.network",
    # "wss://nostrvista.aaroniumii.com",
    # "was://nostr.satstralia.com",
    # "wss://freelay.sovbit.host",
    # "ws://localhost",
    "wss://nostr.pleb.network",
    "wss://relay.damus.io",
    "wss://nostr.wine",
]


async def init_nostr_client(secret_key_nsec: str) -> Client:
    logger.info("Starting Nostr client...")
    keys: Keys = Keys.parse(secret_key=secret_key_nsec)
    signer: NostrSigner = NostrSigner.keys(keys=keys)
    client = Client(signer=signer)

    for relay in RELAYS:
        logger.info(f"Adding relay {relay}")
        await client.add_relay(relay)

    await client.connect()

    logger.info("Nostr Client Connected!!!")

    return client


async def get_all_posted_events_on_nostr(nostr_client: Client) -> list[Event]:
    signer: NostrSigner = await nostr_client.signer()
    public_key: PublicKey = await signer.get_public_key()
    offer_filter: Filter = Filter().authors([public_key]).kind(Kind(1))

    events_obj: Events = await nostr_client.fetch_events(
        filter=offer_filter, timeout=timedelta(seconds=20)
    )

    events_list: list[Event] = events_obj.to_vec()
    return events_list


def get_events_from_offer(order: dict) -> list[EventBuilder]:

    event_builders: list[EventBuilder] = []

    identifier = order.get("id")
    timestamp_in_x_hours = int(time.time() + PEACH_ORDER_EXPIRATION)

    order_type = "sell" if order.get("type") == "ask" else "buy"

    if order_type == "buy":
        logger.warning(f"Found a Buy Offer #{identifier}. Ignoring...")
        return []

    rating_data = {
        "total_reviews": order.get("ratingCount", 0),
        "total_rating": order.get("rating", 0),
    }

    amount = order.get("amount")
    premium = order.get("premium")
    prices = order.get("prices")
    assert prices

    assert type(amount) in [int, float]

    amt = str(amount)

    first_currency = next(iter(prices))
    fa_value = prices[first_currency]
    fa = [str(fa_value)]

    source_url = ""
    network = "mainnet"
    layer = "onchain"
    bond = "0"

    means_of_payment = order.get("meansOfPayment", {})
    for currency, methods in means_of_payment.items():
        tags = [
            Tag.parse(["d", f"{identifier}_{currency}"]),
            Tag.parse(["k", order_type]),
            Tag.parse(["s", "pending"]),
            Tag.parse(["amt", amt]),
            Tag.parse(["fa"] + fa),
            Tag.parse(["premium", str(premium)]),
            Tag.parse(["rating", json.dumps(rating_data)]),
            Tag.parse(["source", source_url]),
            Tag.parse(["network", network]),
            Tag.parse(["layer", layer]),
            Tag.parse(["name", order.get("userId", "")]),
            Tag.parse(["bond", bond]),
            Tag.parse(["expiration", str(timestamp_in_x_hours)]),
            Tag.parse(["y", "peach"]),
            Tag.parse(["z", "order"]),
            Tag.parse(["f", currency]),
            Tag.parse(["pm"] + methods),
        ]

        event_builder = EventBuilder(
            kind=Kind(38383),
            content="",
        )

        event_builder = event_builder.tags(tags)

        event_builders.append(event_builder)

    return event_builders


async def publish_offer_to_nostr(nostr_client: Client, offer: dict) -> None:
    try:

        for event_builder in get_events_from_offer(offer):

            event_obj: Event = await nostr_client.sign_event_builder(event_builder)

            await nostr_client.send_event(event=event_obj)

        logger.info("Sent the event!!")

    except Exception as e:
        print(f"Error publishing: {e}")
