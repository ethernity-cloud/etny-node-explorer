import asyncio, time


async def first():
    print('am first async method')
    await asyncio.sleep(1)
    return await first()


async def second():
    print('-am second async method')
    time.sleep(10)
    return await second()


async def main():
    await asyncio.gather(
        first(),
        second()
    )

asyncio.run(main())