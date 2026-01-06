import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def buy_item(client, endpoint):
    try:
        response = await client.post(f"{BASE_URL}/{endpoint}")
        return response.json()
    except:
        return {"status": "error"}

async def get_stock(client):
    response = await client.get(f"{BASE_URL}/status")
    return response.json()['stock']

async def run_attack(endpoint):
    print(f"\n════════════════════════════════════")
    print(f"⚔️  ATTACKING ENDPOINT: {endpoint}")
    print(f"════════════════════════════════════")
    
    async with httpx.AsyncClient() as client:
        # 1. Reset DB
        await client.get(f"{BASE_URL}/reset")
        start_stock = await get_stock(client)
        print(f"📉 Starting Stock: {start_stock}")

        # 2. Launch 10 concurrent requests
        print("🚀 Firing 10 concurrent requests...")
        tasks = [buy_item(client, endpoint) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # 3. Analyze Results
        success_count = sum(1 for r in results if r.get('status') == 'success')
        end_stock = await get_stock(client)
        
        print(f"📊 Results:")
        print(f"   - Successful 'Buys': {success_count} (Expected: 1)")
        print(f"   - Final Stock Count: {end_stock}")

        # THE FIX: We fail if we sold more than 1 item OR if stock is negative
        if success_count > 1 or end_stock < 0:
            print("\n❌ RACE CONDITION DETECTED!")
            print(f"   FAILURE: We sold {success_count} items but only had 1 in stock.")
            if end_stock >= 0:
                 print("   (Type: Lost Update - Everyone read '1' and wrote '0')")
            else:
                 print(f"   (Type: Negative Balance - Inventory is {end_stock})")
        else:
            print("\n✅ SECURE.")
            print(f"   We correctly sold {success_count} item.")
            print("   Inventory is safe.")

async def main():
    await run_attack("buy-vulnerable")
    await run_attack("buy-secure")

if __name__ == "__main__":
    asyncio.run(main())