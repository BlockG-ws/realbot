from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent


async def handle_inline_query(query: InlineQuery):
    """
    Handle inline queries.
    This function is called when an inline query is received.
    It can be used to provide inline results based on the query.
    """
    print(f"Received inline query")
    query_text = query.query
    if query_text == "":
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
        search_query = query_text.replace("search", "").strip()
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
        text = query_text.replace("pg", "").strip()
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
    if query_text.startswith("将军："):
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
            result = await fetch_from_b23_api(keywords)
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
            description="很抱歉，我还不能理解你说的内容。"
        )
    ], cache_time=0)
    return

