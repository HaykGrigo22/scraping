import asyncio
import aiohttp
import asyncpg
from bs4 import BeautifulSoup
import config


class FightersFights:

    def __init__(self):
        self.fights_info = []
        self.num = 0

    async def main(self, fighter_name):
        name, surname = fighter_name.split()
        async with aiohttp.ClientSession(trust_env=True) as session:
            url = f"https://www.ufc.com/athlete/{name}-{surname}"
            print(url)
            async with session.get(url, ssl=False) as resp:
                html_data = await resp.text()
                await self.parse_fighter(html_data, fighter_name)

    async def parse_fighter(self, html_data, fighter_name):
        soup = BeautifulSoup(html_data, "lxml")
        fights = soup.find_all("article", class_="c-card-event--athlete-results")

        for info in fights:
            fight = "".join(list(map(lambda x: x.text.replace("\n", " "), info.find_all("h3")))).strip().replace(
                fighter_name.title().split()[1], "").replace(" vs ", "")
            print(fight)
            round_num, time, method = list(map(lambda x: x.text, info.find_all("div", class_="c-card-event--athlete-results__result-text")))

            self.fights_info.append({
                "name": fighter_name,
                "opponent": fight,
                "round": round_num,
                "time": time,
                "method": method
            })

            print(self.fights_info)

        self.num += 1
        await self.save_to_postgresql()

    async def main_tasks(self):
        fighters = input("Fighters names: ")
        await asyncio.gather(*[self.main(name) for name in fighters.split(", ")])

    async def save_to_postgresql(self):
        conn = await asyncpg.connect(
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            port=5432,
        )

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fighters_and_fights (
                name TEXT,
                opponent TEXT,
                round TEXT,
                time TEXT,
                method TEXT
            )
        """)

        for info in self.fights_info:
            await conn.execute("""
                INSERT INTO fighters_and_fights (name, opponent, round, time, method)
                VALUES ($1, $2, $3, $4, $5)
            """, info["name"], info["opponent"], info["round"], info["time"], info["method"])

        await conn.close()


if __name__ == "__main__":
    fighters_fights = FightersFights()
    asyncio.run(fighters_fights.main_tasks())
