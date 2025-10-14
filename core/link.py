import logging

import aiohttp
import re
import html
import asyncio

from urllib.parse import urlparse, parse_qsl, parse_qs, urlencode, urlunparse

from aiogram.types import Message
from nio import AsyncClient

from config import config

whitelist_param_links = ['www.iesdouyin.com','item.taobao.com', 'detail.tmall.com', 'h5.m.goofish.com', 'music.163.com', 'y.music.163.com',
                                           'www.bilibili.com', 'm.bilibili.com', 'bilibili.com', 'mall.bilibili.com',
                                           'space.bilibili.com', 'live.bilibili.com','item.m.jd.com','item.jd.com',
                                            'www.xiaohongshu.com','www.zhihu.com','zhihu.com','zhuanlan.zhihu.com','www.baidu.com',
                                            'youtube.com','m.youtube.com','www.youtube.com',
                                            'music.youtube.com','youtu.be', 'mp.weixin.qq.com', 'mobile.yangkeduo.com']

has_self_redirection_links = ['www.cnbeta.com.tw','m.cnbeta.com.tw','www.landiannews.com', 'www.bilibili.com']

has_better_alternative_links = ['www.iesdouyin.com','bilibili.com', 'm.bilibili.com', 'youtube.com','youtu.be','m.youtube.com','x.com', 'twitter.com']

# Load ClearURLs rules from JSON file
with open('assets/clearurls.json', 'r', encoding='utf-8') as f:
    import json
    clearurls_rules = json.load(f)

async def extend_short_urls(url):
    """ 扩展短链接 """
    async with aiohttp.ClientSession() as session:
        async with session.get(url,allow_redirects=False) as r:
            if 'tb.cn' in urlparse(url).hostname:
                # 淘宝短链接特殊处理
                html_content = await r.text()
                url = extract_tb_url_from_html(html_content)
                if not url:
                    return url
            if r.status in [301, 302, 304, 307, 308] and 'Location' in r.headers:
                redirect_url = r.headers['Location']
                if redirect_url.startswith(('http://', 'https://')):
                    if 'share.google' in redirect_url:
                        # 修复 share.google 这种跳转多次的链接
                        async with session.get(redirect_url, allow_redirects=True) as r_all_direct:
                            if r_all_direct.status == 200 and r_all_direct.url != url:
                                return str(r_all_direct.url)
                    return redirect_url
                else:
                    # 如果 Location 头部没有 http 前缀，可能是相对路径
                    # 需要将其转换正确的链接
                    return urlparse(url)._replace(path=redirect_url).geturl()
            elif not r.status in [200,403,404,502,503]:
                # 对于一些需要“正常”浏览器才能访问的链接，尝试修复
                async with session.get(url, allow_redirects=False, headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.48 Safari/537.36'}) as r_fix:
                    if r_fix.status in [301, 302, 304, 307, 308] and 'Location' in r_fix.headers:
                        fixed_redirect_url = r_fix.headers['Location']
                        if 'share.google' in fixed_redirect_url:
                            # 修复 share.google 这种跳转多次的链接
                            async with session.get(fixed_redirect_url, allow_redirects=True) as r_all_direct:
                                if r_all_direct.status == 200 and r_all_direct.url != url:
                                    return str(r_all_direct.url)
                        if fixed_redirect_url.startswith(('http://', 'https://')):
                            return fixed_redirect_url
                        else:
                            # 如果 Location 头部没有 http 前缀，可能是相对路径
                            # 需要将其转换正确的链接
                            return urlparse(url)._replace(path=fixed_redirect_url).geturl()
    return url

def extract_tb_url_from_html(html_content):
    # 使用正则表达式匹配 var url = '...' 的模式
    pattern = r"var url = ['\"]([^'\"]+)['\"]"
    match = re.search(pattern, html_content)

    if match:
        url = match.group(1)
        # 解码HTML实体
        decoded_url = html.unescape(url)
        return decoded_url
    return None


# Assume clearurls_rules is a dict loaded from the JSON
def remove_tracking_params(url, rules):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path
    matched_rule = None

    # Find matching rule by urlPattern
    for site, rule in rules['providers'].items():
        if re.match(rule['urlPattern'], url):
            matched_rule = rule
            break

    if not matched_rule or not matched_rule['rules']:
        return url

    # Remove tracking params
    query = parse_qsl(parsed.query, keep_blank_values=False)
    filtered_query = [
        (k, v) for k, v in query
        if not any(re.fullmatch(param, k) for param in matched_rule['rules'])
    ]

    # Remove UTM parameters
    utm_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
    for param in utm_params:
        if param in filtered_query:
            filtered_query.pop(param, None)

    new_query = urlencode(filtered_query)

    cleaned_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return cleaned_url

async def reserve_whitelisted_params(url):
    """ 保留白名单中的参数 """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if parsed_url.hostname in ['item.taobao.com','detail.tmall.com','h5.m.goofish.com','music.163.com','y.music.163.com']:
        if 'id' in query_params:
            # 只保留id参数，创建新的query_params
            new_query_params = {'id': query_params['id']}
            # 重新构建URL
            cleaned_query = urlencode(new_query_params, doseq=True)
            return urlunparse(parsed_url._replace(query=cleaned_query))
        if 'music.163.com' in parsed_url.hostname and 'id' not in query_params:
            # 如果网易云链接没有id参数，不保留任何参数
            # 例如 https://music.163.com/song/12345678
            new_query_params = {}
            cleaned_query = urlencode(new_query_params, doseq=True)
            return urlunparse(parsed_url._replace(query=cleaned_query))
    elif parsed_url.hostname in ['www.iesdouyin.com','www.bilibili.com','m.bilibili.com','bilibili.com','mall.bilibili.com','space.bilibili.com','live.bilibili.com','item.m.jd.com','item.jd.com','www.xiaohongshu.com']:
        # 不保留任何参数
        new_query_params = {}
        if parsed_url.hostname == 'mall.bilibili.com' and query_params.get('itemsId'):
            # 处理bilibili工房的商品链接，保留 itemsId 和 page 参数
            new_query_params['itemsId'] = query_params['itemsId']
            new_query_params['page'] = query_params.get('page')
        if parsed_url.hostname == 'gf.bilibili.com' and 'item/detail' in parsed_url.path:
            # TODO: fix
            new_query_params = {}
        if 'bilibili.com' in parsed_url.hostname and 'video' in parsed_url.path and query_params:
            # 对于 bilibili 的视频链接，保留一些必要的参数
            if 't' in query_params:
                new_query_params['t'] = query_params['t']
            if 'p' in query_params:
                new_query_params['p'] = query_params['p']
            # 评论跳转必需参数
            if 'comment_root_id' in query_params:
                new_query_params['comment_root_id'] = query_params['comment_root_id']
            if 'comment_secondary_id' in query_params:
                new_query_params['comment_secondary_id'] = query_params['comment_secondary_id']
        if 'xiaohongshu.com' in parsed_url.hostname and 'xsec_token' in query_params:
            # 为了保证能正常访问，小红书链接保留 xsec_token 参数
            # 我是不是也应该 f**k 小红书一下
            new_query_params = {'xsec_token': query_params['xsec_token']}
        # 重新构建URL
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    elif 'zhihu' in parsed_url.hostname and query_params:
        # 处理知乎链接
        new_query_params = {}
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    elif parsed_url.hostname in ['www.baidu.com', 'youtube.com', 'm.youtube.com','www.youtube.com','music.youtube.com','youtu.be']:
        new_query_params = {}
        if parsed_url.hostname == 'www.baidu.com' and 'wd' in query_params:
            # 百度搜索链接保留 wd 参数
            new_query_params['wd'] = query_params['wd']
        if 'youtube.com' in parsed_url.hostname:
            # Shorts 的特殊处理
            if 'shorts' in parsed_url.path and query_params and 't' in query_params:
                new_query_params['t'] = query_params['t']  # 保留 t 参数
            elif 'watch' in parsed_url.path:
                # YouTube 视频链接保留 v 参数
                if query_params and 'v' in query_params:
                    new_query_params['v'] = query_params['v'] # 保留 v 参数
                if 't' in query_params:
                    new_query_params['t'] = query_params['t'] # 保留 t 参数
                if 'list' in query_params:
                    new_query_params['list'] = query_params['list']  # 保留 list 参数
        # 重新构建URL
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    elif 'yangkeduo.com' in parsed_url.hostname and 'goods2' in parsed_url.path:
        # 拼夕夕商品链接
        new_query_params = {}
        if 'ps' in query_params:
            pxx_full_url = await extend_short_urls(url)
            pxx_params = parse_qs(urlparse(pxx_full_url).query)
            new_query_params = {'goods_id': pxx_params['goods_id']}
            cleaned_query = urlencode(new_query_params, doseq=True)
            return urlunparse(urlparse(pxx_full_url)._replace(query=cleaned_query))
        elif 'goods_id' in query_params:
            new_query_params['goods_id'] = query_params['goods_id']
            cleaned_query = urlencode(new_query_params, doseq=True)
            return urlunparse(parsed_url._replace(query=cleaned_query))
    elif parsed_url.hostname in ['chatglm.cn'] and query_params:
        # 就你叫智谱啊
        new_query_params = {'share_conversation_id': query_params['share_conversation_id']}
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    elif parsed_url.hostname == 'mp.weixin.qq.com' and query_params:
        # 微信公众号文章的长链接只保留 __biz, mid, idx, sn 参数
        new_query_params = {}
        for param in ['__biz', 'mid', 'idx', 'sn']:
            if param in query_params:
                new_query_params[param] = query_params[param]
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    return url

def transform_into_fixed_url(url):
    """ 转换为修复的链接 """
    parsed_url = urlparse(url)

    if parsed_url.hostname in ['x.com', 'twitter.com']:
        # 把 twitter 的链接转换为 fixupx.com
        return urlunparse(parsed_url._replace(netloc='i.fixupx.com'))
    if parsed_url.hostname in ['bilibili.com', 'm.bilibili.com']:
        # 把 bilibili 的链接转换为桌面端的 www.bilibili.com
        return urlunparse(parsed_url._replace(netloc='www.bilibili.com'))
    if parsed_url.hostname in ['www.iesdouyin.com']:
        # 把抖音分享链接转换为正常的 www.douyin.com
        return urlunparse(parsed_url._replace(netloc='www.douyin.com'))
    if parsed_url.hostname in ['youtu.be', 'm.youtube.com', 'youtube.com']:
        # 把 youtu.be 和 m.youtube.com 的链接转换为 www.youtube.com
        if parsed_url.hostname == 'youtu.be':
            # youtu.be 的链接需要把 path 的 / 替换为 v 参数
            video_id = parsed_url.path.lstrip('/')
            # fix: video_id 未传递
            return urlunparse(parsed_url._replace(netloc='www.youtube.com', path='/watch', query=f'v={video_id}&{parsed_url.query}' if parsed_url.query else f'v={video_id}'))
        # YouTube Shorts 转换成正常的链接
        if 'shorts' in parsed_url.path:
            video_id = parsed_url.path.split('/shorts/')[-1]
            return urlunparse(parsed_url._replace(netloc='www.youtube.com', path='/watch', query=f'v={video_id}&{parsed_url.query}' if parsed_url.query else f'v={video_id}'))
        return urlunparse(parsed_url._replace(netloc='www.youtube.com'))
    return url

async def process_url(url):
    logging.debug('发现链接，正在尝试清理')
    if urlparse(url).hostname in has_self_redirection_links and not urlparse(url).query:
        # 对于有自我纠正的重定向而且不携带任何参数的链接，直接返回
        return None
    # 对于适配的网站，直接保留白名单参数并返回
    if urlparse(url).hostname in whitelist_param_links:
        final_url = await reserve_whitelisted_params(url)
        if urlparse(final_url).hostname in has_better_alternative_links:
            final_url = transform_into_fixed_url(final_url)
        if url != final_url:
            return final_url
        else:
            # 链接没有变化，直接返回 None，避免重复处理
            return None
    # 对于其它的网站，首先清理跟踪参数
    cleaned_url = remove_tracking_params(url, clearurls_rules)
    # 扩展短链接
    extended_url = await extend_short_urls(cleaned_url)
    if urlparse(extended_url).hostname in ['chatglm.cn']:
        final_url = reserve_whitelisted_params(extended_url)
        if url != final_url:
            return final_url
    # 对于扩展短链接之后的适配的网站，直接保留白名单参数并返回
    if urlparse(extended_url).hostname in whitelist_param_links:
        final_url = await reserve_whitelisted_params(extended_url)
        if urlparse(final_url).hostname in has_better_alternative_links:
            final_url = transform_into_fixed_url(final_url)
        if url != final_url:
            return final_url
        else:
            # 链接没有变化，直接返回 None，避免重复处理
            return None
    if urlparse(extended_url).hostname in has_better_alternative_links:
        removed_tracking_url = remove_tracking_params(extended_url, clearurls_rules)
        final_url = transform_into_fixed_url(removed_tracking_url)
    else:
        # 对于其他链接，直接对其进行跟踪参数清理
        final_url = remove_tracking_params(extended_url, clearurls_rules)
    if url != final_url:
        return final_url
    return None

async def clean_link_in_text(text):
    # URL regex pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    if not urls:
        return None
    final_urls = await asyncio.gather(*[process_url(url) for url in urls])
    # Filter out None values
    final_urls = [url for url in final_urls if url is not None]
    return final_urls

async def handle_tg_links(message: Message):
    if not config.is_feature_enabled('link', message.chat.id):
        return

    text = message.text or message.caption
    # Extract URLs from message text
    if text:
        final_urls = await clean_link_in_text(text)
        # 回复处理后的链接
        if final_urls:
            await message.reply(
                f"Cleaned URL: <blockquote expandable>{"\n\n".join(final_urls)}\n</blockquote>\n",disable_web_page_preview=True)

async def handle_matrix_links(room, event, client: AsyncClient):
    if not config.is_feature_enabled('link', room.room_id):
        return None

    text = event.body
    if text:
        final_urls = await clean_link_in_text(text)
        if final_urls:
            await client.room_send(
                room_id=room.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": f"Cleaned URL: \n\n" + "\n".join(final_urls),
                    "m.relates_to": {
                        "m.in_reply_to": {
                            "event_id": event.event_id,
                        }
                    }
                }
            )
