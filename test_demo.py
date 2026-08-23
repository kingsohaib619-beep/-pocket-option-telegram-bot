import asyncio
import os
import sys

sys.path.insert(0, "vendor")

from BinaryOptionsToolsV2.pocketoption.asynchronous import PocketOptionAsync


async def main():
    ssid = os.environ["POCKET_OPTION_SSID"]

    print("Starting Pocket Option connection...")

    async with PocketOptionAsync(ssid=ssid) as client:
        print("Connected successfully.")

        balance = await client.balance()
        print("Balance:", balance)

        print("Demo connection test completed.")


if __name__ == "__main__":
    asyncio.run(main())
