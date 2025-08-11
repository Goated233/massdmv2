import asyncio

from dm_queue import RateLimiter


def test_rate_limiter_spacing(monkeypatch):
    current = 0.0

    def time_func():
        return current

    sleeps = []

    async def fake_sleep(delay):
        nonlocal current
        sleeps.append(delay)
        current += delay

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    rl = RateLimiter(2.0, time_func)

    async def run():
        nonlocal current
        await rl.wait()  # first call, no sleep
        current += 1.0
        await rl.wait()  # should sleep 1 second

    asyncio.run(run())
    assert sleeps == [1.0]
