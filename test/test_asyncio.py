import asyncio
from asyncio import tasks
import time

async def cancel_me():
    print('cancel_me(): before sleep')

    try:
        # Wait for 1 hour
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print('cancel_me(): cancel sleep')
        raise
    finally:
        print('cancel_me(): after sleep')


async def sleep_asyncio():
    print('sleep_asyncio(): start sleep')

    await asyncio.sleep(1)

    print('sleep_asyncio(): end sleep')


async def main():
    # Create a "cancel_me" Task
    sleep_task = asyncio.create_task(sleep_asyncio())
    task = asyncio.create_task(cancel_me())


    # Wait for 1 second
    await sleep_task

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("main(): cancel_me is cancelled now")

if __name__ == '__main__':
    asyncio.run(main())