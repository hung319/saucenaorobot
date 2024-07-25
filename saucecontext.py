from telegram import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    CallbackContext,
    ExtBot,
    Application,
)
from telegram.error import (
    BadRequest,
)
import httpx
import asyncio
import re

def chunks(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class SauceContext(CallbackContext[ExtBot, dict, dict, dict]):
    # taken directly from https://github.com/Eptagone/SauceNAObot/blob/f5437363aacb51f0159872c995f3bd3c49f86667/src/Core/Application/Kitchen.cs#L24C6-L51C35
    WEBSITE_NAMES = (
        ("pixiv", "Pixiv"),
        ("danbooru", "Danbooru"),
        ("gelbooru", "Gelbooru"),
        ("sankaku", "Sankaku"),
        ("anime-pictures.net", "Anime Pictures"),
        ("yande.re", "Yandere"),
        ("imdb", "IMDB"),
        ("deviantart", "Deviantart"),
        ("patreon", "Patreon"),
        ("anilist", "AniList"),
        ("artstation", "ArtStation"),
        ("twitter", "Twitter"),
        ("x.com", "Twitter"),
        ("nijie.info", "Nijie"),
        ("pawoo.net", "Pawoo"),
        ("seiga.nicovideo.jp", "Seiga Nicovideo"),
        ("tumblr.com", "Tumblr"),
        ("anidb.net", "Anidb"),
        ("sankakucomplex.com", "Sankaku"),
        ("mangadex.org", "MangaDex"),
        ("mangaupdates.com", "MangaUpdates"),
        ("myanimelist.net", "MyAnimeList"),
        ("furaffinity.net", "FurAffinity"),
        ("fakku.net", "FAKKU!"),
        ("nhentai.net", "nhentai"),
        ("e-hentai.org", "E-Hentai"),
        ("e621.net", "e621"),
        ("kemono.su", "Kemono"),
        ("konachan", "Konachan"),
    )
    def __init__(self, application: Application, chat_id: int | None = None, user_id: int | None = None):
        super().__init__(application, chat_id, user_id)
        self.client = httpx.AsyncClient()
    
    @property
    def api_key(self) -> str:
        return self.user_data.get("api_key")
    
    @api_key.setter
    def api_key(self, value: str):
        self.user_data["api_key"] = value

    async def saucenao_request(self, url: str):
        req = await self.client.get(
            "https://saucenao.com/search.php",
            params = {
                "db": 999,
                "output_type": 2,
                "url": url,
                "api_key": self.api_key
            }
        )
        return req.json()

    @staticmethod
    def get_search_keyboard(url: str):
        return [
            [
                InlineKeyboardButton("Search on Google", f"https://lens.google.com/uploadbyurl?url={url}"),
                InlineKeyboardButton("Search on Yandex", f"https://yandex.com/images/search?rpt=imageview&url={url}")
            ],
            [
                InlineKeyboardButton("View results on SauceNAO", f"https://saucenao.com/search.php?url={url}")
            ]
        ]
    
    @staticmethod
    def build_search_keyboard(url: str):
        return InlineKeyboardMarkup(SauceContext.get_search_keyboard(url))

    @staticmethod
    def parse_results(sauce_results: list[dict], min_similarity = 50):
        results = []
        for result in sauce_results:
            if float(result["header"]["similarity"]) < min_similarity:
                continue
            for url in result["data"].get("ext_urls", []) + [result["data"].get("source")]:
                if url and re.match(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)", url):
                    results.append(
                        (
                            SauceContext.get_website_name(url) + " - " + result["header"]["similarity"] + "%",
                            url
                        )
                    )
        return results


    @staticmethod
    def get_website_name(url: str):
        for website in SauceContext.WEBSITE_NAMES:
            if website[0] in url:
                return website[1]
        return "Other"

    async def get_sauce(self, url: str, message: Message):
        sauce = await self.saucenao_request(url)

        if sauce["header"]["status"] == -1:
            await message.edit_text("The api key is not set or invalid, please set it with /api_key", reply_markup=message.reply_markup)
            return
        if sauce["header"]["status"] == -2:
            try:
                await message.edit_text("Rate limit reached. Will retry in 30 seconds", reply_markup=message.reply_markup)
            except BadRequest:
                pass
            await asyncio.sleep(30)
            await self.get_sauce(url, message)
            return

        results = self.parse_results(sauce["results"])

        if not results:
            await message.edit_text("No sauce found", reply_markup=message.reply_markup)
            return

        await message.edit_text(
            "Results:",
            reply_markup=InlineKeyboardMarkup(
                list(
                    chunks(
                        [InlineKeyboardButton(result[0], result[1]) for result in results],
                        3
                    )
                ) + self.get_search_keyboard(url)
            )
        )

