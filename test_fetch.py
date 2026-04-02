import asyncio
import json
import httpx

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # First login to get a token? We don't have token...
        # Let's bypass or use db directly
        pass

if __name__ == "__main__":
    asyncio.run(main())
