import aiohttp

async def get_random_seed() -> dict:
    """从 drand 获取一个随机种子"""
    url = "https://drand.cloudflare.com/public/latest"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {"round": data["round"], "seed": data["randomness"]}
            else:
                raise Exception(f"Failed to fetch random seed: {response.status}")

async def _test_get_random_number():
    """测试从 drand 的种子生成随机数"""
    round = (await get_random_seed())["round"]
    print(f"Drand Round: {round}")
    seed = (await get_random_seed())["seed"]
    print(f"Random Seed: {seed}")
    import random
    random.seed(seed)
    rand_number = random.randint(1, 100)
    print(f"Random Number: {rand_number}")

async def choose_random_winners(participants: list[int], number_of_winners: int) -> dict[str, int]:
    """从参与者列表中随机选择获奖者"""
    rounds = (await get_random_seed())["round"]
    seed = (await get_random_seed())["seed"]
    import random
    random.seed(seed)
    winners = random.sample(participants, k=number_of_winners)
    return {
        "winners": winners,
        "round": rounds,
        "seed": seed
    }

if __name__ == "__main__":
    import asyncio
    asyncio.run(_test_get_random_number())