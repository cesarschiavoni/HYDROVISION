import traceback
try:
    from app.routers.simulate import simulate_start
    import asyncio
    asyncio.run(simulate_start())
    print("OK")
except Exception as e:
    traceback.print_exc()
