import logging

from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, LinkPreviewOptions
from aiogram.utils.formatting import Text, ExpandableBlockQuote

from core.link import clean_link_in_text


async def handle_inline_query(query: InlineQuery):
    """
    Handle inline queries.
    This function is called when an inline query is received.
    It can be used to provide inline results based on the query.
    """
    print(f"Received inline query")
    query_text = query.query
    if not query_text:
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="你还没什么都没输入呢",
                input_message_content=InputTextMessageContent(
                    message_text=f"难说！",
                    parse_mode=ParseMode.MARKDOWN
                ),
                description=f"或许你可以试试 'search' 什么的"
            ),
        ], cache_time=0)
        return

    if query_text.startswith("search"):
        search_query = query_text.replace("search", "",1).strip()
        if search_query:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="丢一个 DuckDuckGo 的搜索结果",
                    input_message_content=InputTextMessageContent(
                        message_text=f"我建议你用 [DuckDuckGo 搜一下 {search_query}](https://duckduckgo.com/?q={search_query})",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"在 DuckDuckGo 上搜索 {search_query}"
                ),
                InlineQueryResultArticle(
                    id="2",
                    title="丢一个 Google 的搜索结果",
                    input_message_content=InputTextMessageContent(
                        message_text=f"我建议你用 [Google 搜一下 {search_query}](https://www.google.com/search?q={search_query})",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"在 Google 上搜索 {search_query}"
                )
            ], cache_time=0)
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="输入搜索内容",
                    input_message_content=InputTextMessageContent(
                        message_text="ta 好像想让你用搜索引擎搜索这个问题，但 ta 没有输入任何内容。",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description="请在 'search' 后输入你想要搜索的内容。"
                )
            ], cache_time=0)
        return

    if query_text.startswith("pg"):
        text = query_text.replace("pg", "",1).strip()
        import pangu
        text = pangu.spacing_text(text)
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="发送 Pangu 格式化之后的结果",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode=ParseMode.MARKDOWN
                ),
                description=f"格式化后的文本：{text}"
            )
        ], cache_time=0)
        return
    if query_text == "你的头怎么尖尖的":
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="阿诺模式",
                input_message_content=InputTextMessageContent(
                    message_text="你的头怎么尖尖的，那我问你",
                    parse_mode=ParseMode.MARKDOWN
                ),
                description="我可能是阿诺，但我是阿诺不太可能"
            )
        ], cache_time=0)
        return
    if query_text == "gay":
        import random
        gayness = random.randint(1, 100)
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="🌈 How gay are you?",
                thumbnail_url="https://equity.ubc.ca/files/2022/10/Gay_men_flag.jpg",
                input_message_content=InputTextMessageContent(
                    message_text=f"🌈 I am {gayness}% gay!",
                ),
                description="Send your gayness to the chat!"
            )
        ])
        return
    """
    if query_text.startswith("你的头怎么绿绿的"):
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="头上总得有点绿",
                input_message_content=InputTextMessageContent(
                    message_text="你说的对，我的头是绿的",
                    parse_mode=ParseMode.MARKDOWN
                ),
                description="说实话，你一般问出来这个问题的时候，我一般不建议你再继续下去了"
            )
        ], cache_time=0)
        return
    """
    if query_text.startswith('anuo'):
        main = query_text.replace("anuo", "",1).strip()
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="阿诺的公式",
                input_message_content=InputTextMessageContent(
                    message_text=f"{"我可能是阿诺，但我是阿诺不太可能" if not main else f"{main}有可能，但{main}不太可能"}",
                    parse_mode=ParseMode.MARKDOWN
                ),
                description=f"{"我可能是阿诺，但我是阿诺不太可能" if not main else f"{main}有可能，但{main}不太可能"}"
            )
        ], cache_time=0)
        return
    if query_text.startswith("b23"):
        b23_query = query_text.replace("b23", "",1).strip()
        b23_resp = None
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # 先访问 bilibili.com 获取 cookies
            async with session.get('https://bilibili.com', headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/138.0.0.0"}) as response:
                pass

            # 使用获取的 cookies 请求搜索 API
            params = {'keyword': b23_query}
            async with session.get(
                    'https://api.bilibili.com/x/web-interface/search/all/v2',
                    params=params,
                    headers={
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/138.0.0.0"
                    }
            ) as response:
                b23_resp = await response.json()
        search_results = []
        if b23_resp and b23_resp.get('data'):
            # 假设我们只取第一个视频的结果
            videos = next((item for item in b23_resp['data']['result'] if item.get('result_type') == 'video'), None)
            if videos and videos.get('data'):
                # 取前十个结果
                for i, video in enumerate(videos['data'][:10]):
                    title = video.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
                    bvid = video.get('bvid', '')
                    link = video.get('arcurl', '').replace('http://','https://',1)
                    video_type = video.get('typename', '')
                    author = video.get('author', '')
                    play = video.get('play', 0)
                    thumbnail = f"https:{video.get('pic')}"
                    description = video.get('description', '')

                    search_results.append(InlineQueryResultArticle(
                        id=str(i + 1),
                        title=title,
                        thumbnail_url=thumbnail,
                        input_message_content=InputTextMessageContent(
                            message_text=f"<a href=\"{link}\">{title}</a>\n{video_type} | 作者：{author} | "
                                         f"播放量：{play} {Text(ExpandableBlockQuote(description)).as_html()}",
                            parse_mode=ParseMode.HTML,
                            link_preview_options=LinkPreviewOptions(url=f'https:{video.get('pic')}',prefer_large_media=True),
                            disable_web_page_preview=False
                        ),
                        description=f"{bvid} | {author} | {play}次播放"
                    ))
        if b23_query and search_results:
            await query.answer(results=search_results, cache_time=0)
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="输入搜索内容",
                    input_message_content=InputTextMessageContent(
                        message_text="ta 好像想在 b 站搜索视频，但 ta 没有输入任何内容。",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description="请在 'b23' 后输入你想要搜索的内容。"
                )
            ], cache_time=0)
        return
    if query_text.startswith("calc"):
        import subprocess
        expr = query_text.replace("calc", "", 1).strip()
        if not expr:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="算树",
                    input_message_content=InputTextMessageContent(
                        message_text=f"我不会，长大后再学习",
                        parse_mode=None
                    ),
                    description=f"Powered by qalcualate!"
                )
            ], cache_time=0)
        def calc(expression):
            try:
                q_result = subprocess.run(['qalc', expression], capture_output=True, text=True, check=True)
                return q_result.stdout.strip()
            except subprocess.CalledProcessError as e:
                logging.debug("Error while calculating: %s%s", e, expression)
                return None
        result = calc(expr)
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="计算结果",
                input_message_content=InputTextMessageContent(
                    message_text=f"{result if result else "42"}",
                    parse_mode=None
                ),
                description=f"这个算式的计算结果为 {result.splitlines()[-1] if result else '42'}"
            )
        ], cache_time=0)
        return
    if "http" in query_text:
        # 实现清理 URL 的功能
        cleaned_links = await clean_link_in_text(query_text)
        if cleaned_links:
            result = '\n\n'.join(cleaned_links)
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="清理后的链接",
                    input_message_content=InputTextMessageContent(
                        message_text=Text(ExpandableBlockQuote(result)).as_markdown(),
                        parse_mode=ParseMode.MARKDOWN_V2
                    ),
                    description=f"发送清理后的链接：{result}"
                )
            ], cache_time=0)
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="似乎没有链接需要被清理",
                    input_message_content=InputTextMessageContent(
                        message_text=query_text,
                        parse_mode=None
                    ),
                    description="发送原始文本")
            ], cache_time=0)
        return
    if query_text.startswith("bp"):
        blood_pressured_query = query_text.replace("bp", "", 1).strip()
        if blood_pressured_query:
            # 使用结巴分词对文本进行分词
            import jieba
            words = jieba.lcut(blood_pressured_query)
            import random
            words.insert(random.randint(0, len(words)), random.choice(["这个", "那个"]))
            split_text = '\n'.join(words)
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="高血压",
                    input_message_content=InputTextMessageContent(
                        message_text=split_text,
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"有一种说半天话也没说明白的感觉"
                ),
            ], cache_time=0)
            return
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="高血压",
                    input_message_content=InputTextMessageContent(
                        message_text="这个 那个",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"你到底要说啥啊"
                ),
            ], cache_time=0)
    if query_text.startswith("arch"):
        arch_query = query_text.replace("arch", "",1).strip()
        if arch_query:
            result = [InlineQueryResultArticle(
                    id="1",
                    title="在 ArchWiki 上搜索",
                    input_message_content=InputTextMessageContent(
                        message_text=f"我建议你去 ArchWiki 搜一下 {arch_query}：\nhttps://wiki.archlinux.org/title/Special:Search?search={arch_query}&go=Go",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"发送 {arch_query} 的搜索结果页面链接"
                )]
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://wiki.archlinux.org/rest.php/v1/search/title?q={arch_query}&limit=4") as resp:
                    arch_data = await resp.json()
                    if arch_data and len(arch_data['pages']) >= 0:
                        i=2
                        for page in arch_data['pages']:
                            title = page['title']
                            key = page['key']
                            link = f"https://wiki.archlinux.org/title/{key}"
                            result.append(InlineQueryResultArticle(
                                id=str(i),
                                title=f"{title}",
                                input_message_content=InputTextMessageContent(
                                    message_text=f'<a href="{link}">ArchWiki 上的 {title}</a>',
                                    parse_mode=ParseMode.HTML
                                ),
                                description=f"由 ArchWiki 直接返回的搜索结果"
                            ))
                            i+=1
            await query.answer(results=result, cache_time=3600)
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="输入搜索内容",
                    input_message_content=InputTextMessageContent(
                        message_text="ta 好像想让你用 Arch Wiki 搜索这个问题，但 ta 没有输入任何内容。",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description="请在 'arch' 后输入你想要在 archwiki 搜索的内容。"
                )
            ], cache_time=0)
        return
    if query_text.startswith("将军"):
        # fallback support for users who forget the colon
        if not query_text.startswith('将军：'):
            query_text = query_text.replace('将军', '将军：',1)
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="这句话不用记",
                input_message_content=InputTextMessageContent(
                    message_text=f"{query_text}\n\n旁边的手下：✍✍✍✍✍✍✍✍✍✍✍\n️围观的群众：\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o"
                                 f"/\\o/\\o/\\o/",
                    parse_mode=ParseMode.MARKDOWN
                ),
                description=f"\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/\\o/"
            ),
        ], cache_time=0)
        return
    # 如果查询以 "是什么歌" 结尾，则尝试根据关键词获取歌曲名称
    if query_text.endswith("是什么歌"):
        keywords = query_text[:-4].strip()
        from helpers.songs import get_song_by_partial_match, get_song_link
        # 尝试根据关键词获取歌曲名称
        song_name = get_song_by_partial_match(keywords)
        song_link = get_song_link(song_name) if song_name else None
        if song_name:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title=f"我感觉你应该在找 {song_name}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"你是不是在找：{song_name}\n{song_link}\n如果不是，可能你需要[在网络上搜索](https://search.bilibili.com/all?keyword={keywords})",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"根据关键词 '{keywords}' 找到的歌曲"
                )
            ], cache_time=0)
            return
        else:
            from helpers.songs import fetch_from_b23_api
            # 如果没有在本地找到歌曲，则尝试从 Bilibili API 获取
            #result = await fetch_from_b23_api(keywords)
            result = None
            # 因为 B 站的搜索 API 经常失效，所以这里暂时注释掉
            if result:
                song_name, song_link = result
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="1",
                        title=f"我感觉你应该在找 {song_name}",
                        input_message_content=InputTextMessageContent(
                            message_text=f"你是不是在找：{song_name}\n{song_link}\n如果不是，可能你需要[在网络上搜索](https://search.bilibili.com/all?keyword={keywords})",
                            parse_mode=ParseMode.MARKDOWN
                        ),
                        description=f"根据关键词 '{keywords}' 找到的歌曲"
                    )
                ], cache_time=0)
                return
            # 如果还是没有找到，则返回一个默认的结果
            else:
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="1",
                        title=f"抱歉，数据库中没有搜索到 '{keywords}' 的歌曲",
                        input_message_content=InputTextMessageContent(
                            message_text=f"可能你需要[在网络上搜索](https://search.bilibili.com/all?keyword={keywords})",
                            parse_mode=ParseMode.MARKDOWN
                        ),
                        description=f"或许你应该尝试在网上搜索"
                    )
                ], cache_time=0)
                return
    # 如果没有匹配到任何内容，则返回一个默认的结果
    await query.answer(results=[
        InlineQueryResultArticle(
            id="2",
            title=f"嘿，你好啊 {query.from_user.full_name}！",
            input_message_content=InputTextMessageContent(
                message_text="小娜😭",
                parse_mode=ParseMode.MARKDOWN
            ),
            description="很抱歉，我还不能理解你说的内容，但你可以试试："
        ),
        InlineQueryResultArticle(
            id="3",
            title=f"全 部 加 上 空 格",
            input_message_content=InputTextMessageContent(
                message_text=" ".join(query_text),
                parse_mode=ParseMode.MARKDOWN
            ),
            description="很臭的功能"
        ),
        InlineQueryResultArticle(
            id="4",
            title=f"命令列表",
            input_message_content=InputTextMessageContent(
                message_text=query_text,
                parse_mode=ParseMode.MARKDOWN
            ),
            description="search, pg, anuo, bp, arch, 将军"
        ),
    ], cache_time=0)
    return

