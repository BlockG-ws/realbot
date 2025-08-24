# 一个暂时性的办法用来存储歌曲信息
import aiohttp

from helpers.wbi import get_signed_params

songs = {
    "将军的小曲,三太阳的小曲": "你若三冬 - 阿悠悠",
    "全斗焕的小曲,光州跑男的小曲,打成一片的小曲,无限制格斗的小曲,重拳的小曲,光州的小曲": "Shake and Sway",
    "牛姐的养老保险,美国版难忘今宵,圣诞要你命": "All I Want for Christmas Is You - Mariah Carey",
}

song_links = {
    "你若三冬 - 阿悠悠": "https://www.bilibili.com/video/BV1wAdhYBEVg",
    "Shake and Sway": "https://www.bilibili.com/video/av113101403850151",
    "All I Want for Christmas Is You - Mariah Carey": "https://www.bilibili.com/video/BV1VJ411b7ah",
}

def get_song_name(key):
    """根据关键词获取歌曲名称"""
    return songs.get(key)

def get_song_link(key):
    """根据歌曲名称获取歌曲链接"""
    return song_links.get(key)

def get_song_by_partial_match(partial_key):
    """根据部分匹配获取歌曲名称"""
    for key, value in songs.items():
        if partial_key in key:
            return value
    return None

async def fetch_from_b23_api(song_name):
    """从 Bilibili API 获取歌曲信息"""
    resp = None
    async with aiohttp.ClientSession() as session:
        # 先访问 bilibili.com 获取 cookies
        async with session.get('https://bilibili.com', headers={"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"}) as response:
            pass

        # 使用获取的 cookies 请求搜索 API
        params = {'keyword': song_name, 'search_type': 'video', 'duration': 1, 'order': 'click', 'tid': 3}
        # 过一次 wbi 签名，防止被风控
        signed_params = get_signed_params(params)
        async with session.get(
                'https://api.bilibili.com/x/web-interface/wbi/search/type',
                params=signed_params,
                headers={
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
                    "referer": "https://www.bilibili.com/",
                }
        ) as response:
            resp = await response.json()
    if resp and resp.get('data').get('result'):
        # 假设我们只取第一个视频的结果
        videos = next((item for item in resp['data']['result'] if item.get('type') == 'video'), None)
        first_result = videos['data'][0]
        title = first_result.get('title').replace('<em class="keyword">', '').replace('</em>', '') # 清理标题中的 HTML 标签
        link = first_result.get('arcurl')
        return title, link
    return None