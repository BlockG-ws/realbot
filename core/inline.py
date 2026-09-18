import logging
import urllib.parse

import aiohttp

from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, LinkPreviewOptions
from aiogram.utils.formatting import Text, ExpandableBlockQuote, TextLink

from core.link import clean_link_in_text

fake_edge_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/138.0.0.0"

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
            # 使用 urllib.parse.quote 来对查询进行 URL 编码，防止特殊字符导致链接无效
            ddg_html = TextLink(f"用 DuckDuckGo 搜一下 {search_query}",url=f"https://duckduckgo.com/?q={urllib.parse.quote(search_query)}")
            google_html = TextLink(f"用 Google 搜一下 {search_query}",url=f"https://www.google.com/search?q={urllib.parse.quote(search_query)}")
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="丢一个 DuckDuckGo 的搜索结果",
                    input_message_content=InputTextMessageContent(
                        # 使用 TextLink 来创建带有链接的文本，避免手动转义
                        message_text=f"我建议你{ddg_html.as_html()}",
                        parse_mode=ParseMode.HTML
                    ),
                    description=f"在 DuckDuckGo 上搜索 {search_query}"
                ),
                InlineQueryResultArticle(
                    id="2",
                    title="丢一个 Google 的搜索结果",
                    input_message_content=InputTextMessageContent(
                        message_text=f"我建议你{google_html.as_html()}",
                        parse_mode=ParseMode.HTML
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
        # Use user ID as seed for consistent results per user
        seed = query.from_user.id if query.from_user else 42
        gayness = random.Random(seed).randint(1, 100)
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
        ],cache_time=0)
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
        # 创建一个 cookie 存储
        b23_cookie = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=b23_cookie) as session:
            # 先访问 bilibili.com 获取 cookies
            async with session.get('https://bilibili.com', headers={
                "user-agent": fake_edge_ua }) as response:
                pass

            # 使用获取的 cookies 请求搜索 API
            params = {'keyword': b23_query}
            async with session.get(
                    'https://api.bilibili.com/x/web-interface/search/all/v2',
                    params=params,
                    headers={
                        "user-agent": fake_edge_ua
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
                    description = video.get('description', '') + '...'

                    #async with aiohttp.ClientSession(cookie_jar=b23_cookie) as session:
                        # 因为b站搜索API会把简介截断，所以再使用获取视频信息的API获取一次简介
                        # 20260918: b 站收紧了视频信息 API 的限制，不再使用此方式
                        #async with session.get(
                                #'https://api.bilibili.com/x/web-interface/view',
                                #params={'bvid': bvid},
                                #headers={ "user-agent": fake_edge_ua }) as vid_info_resp:
                            #vid_info_data = (await vid_info_resp.json()).get('data', {})
                            #if vid_info_data:
                                #desc_v2 = vid_info_data.get('desc_v2', {})
                                #if desc_v2 and desc_v2[0].get('type') == 2:  # type 2 是有 @ 他人的简介
                                    #new_desc = desc_v2.get('raw_text','')
                                #else:
                                    #new_desc = vid_info_data.get('desc','')
                                #description = new_desc or description

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
            ], cache_time=24*3600*7)
        def calc(expression):
            try:
                q_result = subprocess.run(['qalc', '--set', "base 10", expression], capture_output=True, text=True, check=True)
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
    if query_text.startswith("roll"):
        roll_query = query_text.replace("roll", "", 1).strip()
        import re
        dice_pattern = r'(\d*)d(\d+)'  # 匹配 NdM 格式的骰子表达式
        match = re.match(dice_pattern, roll_query)
        if match:
            num_dice = int(match.group(1)) if match.group(1) else 1
            max_num = int(match.group(2))
            if num_dice > 42:
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="1",
                        title="掷骰子数量过多",
                        input_message_content=InputTextMessageContent(
                            message_text="一次掷骰子数量不能超过 42 个。",
                            parse_mode=None
                        ),
                        description="请减少掷骰子的数量。"
                    )
                ], cache_time=0)
                return
            from helpers.rand import get_random_dice_number
            results = await get_random_dice_number(num_dice, max_num)
            results_text = ', '.join(str(r) for r in results)
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="掷骰子结果",
                    input_message_content=InputTextMessageContent(
                        message_text=f"你掷了 {num_dice} 个 D{max_num} 骰子，结果是：{results_text}",
                        parse_mode=None
                    ),
                    description=f"掷骰子结果：{results_text}"
                )
            ], cache_time=0)
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="无效的掷骰子格式",
                    input_message_content=InputTextMessageContent(
                        message_text="请使用 NdM 格式来掷骰子，例如 '2d6' 表示掷两个六面骰。",
                        parse_mode=None
                    ),
                    description="请提供有效的掷骰子表达式。"
                )
            ], cache_time=0)
        return
    if query_text.startswith("tarot") or query_text.startswith("塔罗"):
        tarot_query = query_text.replace("tarot", "", 1).replace("塔罗", "",1).strip()
        num_cards = 1
        if tarot_query.isdigit():
            num_cards = int(tarot_query)
            if num_cards < 1 or num_cards > 10:
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="1",
                        title="无效的塔罗牌数量",
                        input_message_content=InputTextMessageContent(
                            message_text="请指定 1 到 10 张塔罗牌。",
                            parse_mode=None
                        ),
                        description="请提供有效的塔罗牌数量。"
                    )
                ], cache_time=0)
                return
        from helpers.rand import get_random_tarot_card
        tarot_result = await get_random_tarot_card(num_cards)
        cards_text = '，'.join(tarot_result['cards'])
        await query.answer(results=[
            InlineQueryResultArticle(
                id="1",
                title="抽取的塔罗牌",
                input_message_content=InputTextMessageContent(
                    message_text=f"我抽取了 {num_cards} 张塔罗牌：\n<code>{cards_text}</code>\n* 此轮抽牌的随机种子为 {tarot_result['seed']}，来源于 drand 的第 {tarot_result['round']} 轮随机数据，抽牌结果仅供参考。",
                    parse_mode=ParseMode.HTML
                ),
                description=f"{cards_text}"
            )
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
        args = arch_query.split(" ")
        if args:
            arg_type = args[0]
            arg_value = " ".join(args[1:])
            if arg_type == 'wiki':
                result = [InlineQueryResultArticle(
                        id="1",
                        title="在 ArchWiki 上搜索",
                        input_message_content=InputTextMessageContent(
                            message_text=f"我建议你去 ArchWiki 搜一下 {arg_value}：\nhttps://wiki.archlinux.org/title/Special:Search?search={arch_query}&go=Go",
                            parse_mode=ParseMode.MARKDOWN
                        ),
                        description=f"发送 {arg_value} 的搜索结果页面链接"
                    )]
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://wiki.archlinux.org/rest.php/v1/search/title?q={arg_value}&limit=4") as resp:
                        arch_pkgs_data = await resp.json()
                        if arch_pkgs_data and len(arch_pkgs_data['pages']) >= 0:
                            i=2
                            for package in arch_pkgs_data['pages']:
                                title = package['title']
                                key = package['key']
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
            elif arg_type == 'packages' or arg_type == 'pkg' or arg_type == 'package':
                result = [InlineQueryResultArticle(
                    id="1",
                    title="在 Arch Linux 软件包仓库上搜索",
                    input_message_content=InputTextMessageContent(
                        message_text=f"可以搜一下 {arg_value}：\nhttps://archlinux.org/packages/?q={arg_value}",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"发送 {arg_value} 的搜索结果页面链接"
                )]
                async with aiohttp.ClientSession() as session:
                        # exact match search first (attempt to target pkgname), then partial match; merge & dedupe by pkgname
                        exact_url = f"https://archlinux.org/packages/search/json/?name={arg_value}"
                        # 限制结果的个数防止碰触到 telegram 限制
                        partial_url = f"https://archlinux.org/packages/search/json/?q={arg_value}&limit=10"
                        async with session.get(exact_url) as resp_exact:
                            exact_data = await resp_exact.json()
                        async with session.get(partial_url) as resp_partial:
                            partial_data = await resp_partial.json()
                        merged_results = []
                        seen = set()
                        for pkg in (exact_data.get('results', []) + partial_data.get('results', [])):
                            pkgname = pkg.get('pkgname') or pkg.get('pkgbase') or pkg.get('name')
                            if not pkgname or pkgname in seen:
                                continue
                            seen.add(pkgname)
                            merged_results.append(pkg)
                        arch_pkgs_data = {'results': merged_results}
                        if arch_pkgs_data and len(arch_pkgs_data['results']) >= 0:
                            i = 2
                            for package in arch_pkgs_data['results']:
                                title = package.get('title') or package.get('pkgname') or package.get('name') or ""
                                pkgname = package.get('pkgname') or package.get('pkgbase') or title
                                repo = package.get('repo') or package.get('repo_name') or "extra"
                                arch_page = package.get('arch') or "x86_64"
                                pkgver = package.get('pkgver') or package.get('version') or ""
                                pkgrel = package.get('pkgrel') or ""
                                pkgdesc = package.get('pkgdesc') or package.get('description') or ""
                                url = package.get('url') or ""
                                maintainers = package.get('maintainers') or []
                                build_date = package.get('build_date') or package.get('last_update') or ""
                                provides = package.get('provides') or []
                                conflicts = package.get('conflicts') or []
                                depends = package.get('depends') or []
                                optdepends = package.get('optdepends') or []
                                link = f"https://archlinux.org/packages/{repo}/{arch_page}/{pkgname}/"

                                html_lines = [
                                    f"<b>{repo}/{pkgname} {pkgver}{('-' + pkgrel) if pkgrel else ''}</b>",
                                    f"<i>{pkgdesc}</i>" if pkgdesc else "",
                                    f"<b>{build_date}</b>",
                                    f"<b>Arch:</b> {arch_page}",
                                    f"<b>URL:</b> {url}" if url else "",
                                    f"<b>Maintainers:</b> \n {', '.join(maintainers)}" if maintainers else "",
                                    f"<b>Provides:</b> \n {', '.join(provides)}" if provides else "",
                                    f"<b>Conflicts:</b> \n {', '.join(conflicts)}" if conflicts else "",
                                    f"<b>Depends:</b> \n {', '.join(depends)}" if depends else "",
                                    f"<b>Optional Depends:</b> \n {', '.join(optdepends)}" if optdepends else "",
                                    f'<a href="{link}">在 Arch Linux 网站上查看</a>'
                                ]
                                message_text = "\n".join([ln for ln in html_lines if ln])

                                result.append(InlineQueryResultArticle(
                                    id=str(i),
                                    title=title or pkgname,
                                    input_message_content=InputTextMessageContent(
                                        message_text=message_text,
                                        parse_mode=ParseMode.HTML
                                    ),
                                    description=f"{repo}/{arch_page} • {pkgver}{('-' + pkgrel) if pkgrel else ''}"
                                ))
                                i += 1
                await query.answer(results=result, cache_time=3600)
            elif arg_type == 'aur':
                result = [InlineQueryResultArticle(
                    id="1",
                    title="在 Arch User Repository (AUR) 上搜索",
                    input_message_content=InputTextMessageContent(
                        message_text=f"可以搜一下 {arg_value}：\nhttps://aur.archlinux.org/packages/?O=0&K={arg_value}",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description=f"发送 {arg_value} 的搜索结果页面链接"
                )]

                from datetime import datetime, timezone
                if arg_value:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                                f"https://aur.archlinux.org/rpc/v5/search/{arg_value}") as resp:
                            aur_pkgs_data = await resp.json()
                            if aur_pkgs_data and aur_pkgs_data.get('results'):
                                i = 2
                                max_results = 9
                                for package in aur_pkgs_data['results'][:max_results]:
                                    name = package.get('Name', '')
                                    version = package.get('Version', '')
                                    description = package.get('Description', '')
                                    maintainers = package.get('Maintainer', '')
                                    last_updated = datetime.fromtimestamp(package.get('LastModified', ''), timezone.utc).isoformat()
                                    source_url = package.get('URL', '')
                                    link = f"https://aur.archlinux.org/packages/{name}/"

                                    result.append(InlineQueryResultArticle(
                                        id=str(i),
                                        title=f"{name}",
                                        input_message_content=InputTextMessageContent(
                                            message_text=f'<b>{name} - {version}</b>\n<i>{description}</i>\nURL: {source_url}\nLast Updated: {last_updated}\nMaintainer: {maintainers}\nVersion: {version}\n<a href="{link}">在 AUR 网站上查看</a>',
                                            parse_mode=ParseMode.HTML,
                                            disable_web_page_preview=True
                                        ),
                                        description=f"{version}"
                                    ))
                                    i += 1
                await query.answer(results=result, cache_time=3600)
            else:
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="1",
                        title="未知的的查询类型",
                        input_message_content=InputTextMessageContent(
                            message_text="支持的查询： 'wiki', 'packages/pkg/package', 'aur'",
                            parse_mode=ParseMode.MARKDOWN
                        ),
                        description="请使用有效的搜索类型。"
                    )
                ], cache_time=0)
        else:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="1",
                    title="输入搜索内容",
                    input_message_content=InputTextMessageContent(
                        message_text="ta 好像想让你搜索这个问题，但 ta 没有输入任何内容。",
                        parse_mode=ParseMode.MARKDOWN
                    ),
                    description="请在 'arch' 后输入你想要搜索的类型以及内容。"
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
            title=f"嘿，你好啊 {query.from_user.full_name if query.from_user else '宋冬'}！",
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

