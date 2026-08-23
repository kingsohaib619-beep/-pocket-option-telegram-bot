import asyncio
import os

from BinaryOptionsToolsV2 import PocketOptionAsync


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
