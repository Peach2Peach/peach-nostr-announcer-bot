# Peach Nostr Announcer Bot

This project consists of the following logic:

- an infinite loop that:
    - requests the Peach API for the available Offers
    - submits each one as a NIP-69 Event on Nostr

# How to run the project

`cp env.example .env`

Modify the .env file to include the NOSTR_PRIVATE_KEY (nsec)

`docker-compose up -d`

A Docker Volume is created directly, that updates the `./peach_offers_data/offers.json` file with the IDs of the Offers submitted, to avoid re-posting. This file simply contains a list of IDs as a Json, and is useful if we need to stop and restart the project. It wont grow forever: it checks for Offer IDs that are not present anymore in the Peach API response.

# How to develop this project

`poetry install --no-root`

`poetry run start` or `poetry run python -m app.main`

to check if the code is up to the standards:
`poetry run poe check_all`


# Future improvements

Option 1 - move this logic to the Peach-server
Option 2 - make this a Message Queue consumer for an event created by the Peach-Server
Option 3 - use Async logic to send all events simultaneously (currently it is sequential)

Common improvement - add tests