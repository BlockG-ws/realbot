import logging

import aiohttp
import re
import html
import asyncio

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from abp.filters import parse_filterlist
from aiogram.types import Message

from config import config

whitelist_param_links = ['www.iesdouyin.com','item.taobao.com', 'detail.tmall.com', 'h5.m.goofish.com', 'music.163.com', 'y.music.163.com',
                                           'www.bilibili.com', 'm.bilibili.com', 'bilibili.com', 'mall.bilibili.com',
                                           'space.bilibili.com', 'live.bilibili.com','item.m.jd.com','item.jd.com',
                                            'www.xiaohongshu.com','zhuanlan.zhihu.com','www.baidu.com','m.youtube.com','www.youtube.com',
                                            'music.youtube.com','youtu.be', 'mp.weixin.qq.com']

has_self_redirection_links = ['www.cnbeta.com.tw','m.cnbeta.com.tw','www.landiannews.com', 'www.bilibili.com']

has_better_alternative_links = ['www.iesdouyin.com','bilibili.com', 'm.bilibili.com', 'youtu.be','m.youtube.com','x.com', 'twitter.com']

def matches_adb_selector(url, selector):
    """Check if URL matches the given selector"""
    if selector['type'] == 'url-pattern':
        pattern = selector['value']
        # Convert AdBlock pattern to regex
        # ||domain/* becomes ^https?://[^/]*domain.*
        # domain/* becomes .*domain.*
        if pattern.startswith('||'):
            domain_pattern = pattern[2:]
            # Escape special regex chars except * which we'll convert to .*
            domain_pattern = re.escape(domain_pattern).replace(r'\*', '.*')
            regex_pattern = f"^https?://[^/]*{domain_pattern}"
        else:
            # Escape special regex chars except * which we'll convert to .*
            regex_pattern = re.escape(pattern).replace(r'\*', '.*')

        return bool(re.search(regex_pattern, url))
    return False

def should_remove_param(url, filter_rule):
    """Check if parameter should be removed based on filter rule"""
    if filter_rule.action == 'allow':
        return False  # Allowlist rules prevent removal

    if filter_rule.selector:
        return matches_adb_selector(url, filter_rule.selector)

    return True  # No selector means apply to all URLs

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
                if r.headers['Location'].startswith(('http://', 'https://')):
                    return r.headers['Location']
                else:
                    # 如果 Location 头部没有 http 前缀，可能是相对路径
                    # 需要将其转换正确的链接
                    return urlparse(url)._replace(path=r.headers['Location']).geturl()
            elif not r.status in [200,403,404,502,503]:
                # 对于一些需要“正常”浏览器才能访问的链接，尝试修复
                async with session.get(url, allow_redirects=False, headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.48 Safari/537.36'}) as r_fix:
                    if r_fix.status in [301, 302, 304, 307, 308] and 'Location' in r_fix.headers:
                        if r_fix.headers['Location'].startswith(('http://', 'https://')):
                            return r_fix.headers['Location']
                        else:
                            # 如果 Location 头部没有 http 前缀，可能是相对路径
                            # 需要将其转换正确的链接
                            return urlparse(url)._replace(path=r_fix.headers['Location']).geturl()
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


def remove_tracking_params(url):
    """ 移除跟踪参数 """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Modified tracking_params collection
    tracking_rules = []

    with open('assets/LegitimateURLShortener.txt', 'r', encoding='utf-8') as f:
        for line in parse_filterlist(f):
            if hasattr(line, 'options') and line.options:
                for option in line.options:
                    if option[0] == 'removeparam':
                        tracking_rules.append(line)
                        break  # Only add rule once even if multiple removeparam options

    for rule in tracking_rules:
        if not should_remove_param(url, rule):
            continue

        for option in rule.options or []:
            if option[0] == 'removeparam':
                param_pattern = option[1]

                if param_pattern is True:  # Remove all params
                    query_params.clear()
                    break
                elif isinstance(param_pattern, str):
                    # Handle regex patterns
                    if param_pattern.startswith('/') and param_pattern.endswith('/'):
                        regex_pattern = param_pattern[1:-1]
                        params_to_remove = [
                            param for param in query_params.keys()
                            if re.search(regex_pattern, param)
                        ]
                    else:
                        # Exact match
                        params_to_remove = [param_pattern] if param_pattern in query_params else []

                    for param in params_to_remove:
                        query_params.pop(param, None)
    # Remove UTM parameters
    utm_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
    for param in utm_params:
        if param in query_params:
            query_params.pop(param, None)

    # Reconstruct URL
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))

def reserve_whitelisted_params(url):
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
    elif parsed_url.hostname in ['www.iesdouyin.com','www.bilibili.com','m.bilibili.com','bilibili.com','mall.bilibili.com','space.bilibili.com','live.bilibili.com','item.m.jd.com','item.jd.com','www.xiaohongshu.com', 'zhuanlan.zhihu.com']:
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
        if 'xiaohongshu.com' in parsed_url.hostname and 'xsec_token' in query_params:
            # 为了保证能正常访问，小红书链接保留 xsec_token 参数
            # 我是不是也应该 f**k 小红书一下
            new_query_params = {'xsec_token': query_params['xsec_token']}
        # 重新构建URL
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    elif parsed_url.hostname in ['www.baidu.com','m.youtube.com','www.youtube.com','music.youtube.com','youtu.be']:
        new_query_params = {}
        if parsed_url.hostname == 'www.baidu.com' and 'wd' in query_params:
            # 百度搜索链接保留 wd 参数
            new_query_params['wd'] = query_params['wd']
        if 'youtube.com' in parsed_url.hostname and query_params:
            # YouTube 视频链接保留 v 参数
            if 'v' in query_params:
                new_query_params['v'] = query_params['v'] # 保留 v 参数
            if 't' in query_params:
                new_query_params['t'] = query_params['t'] # 保留 t 参数
            if 'list' in query_params:
                new_query_params['list'] = query_params['list']  # 保留 list 参数
        # 重新构建URL
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
    if parsed_url.hostname in ['youtu.be','m.youtube.com']:
        # 把 youtu.be 和 m.youtube.com 的链接转换为 www.youtube.com
        if parsed_url.hostname == 'youtu.be':
            # youtu.be 的链接需要把 path 的 / 替换为 v 参数
            video_id = parsed_url.path.lstrip('/')
            return urlunparse(parsed_url._replace(netloc='www.youtube.com', path='/watch', query=urlencode({'v': video_id})))
        return urlunparse(parsed_url._replace(netloc='www.youtube.com'))
    return url

async def process_url(url):
    logging.debug('发现链接，正在尝试清理')
    if urlparse(url).hostname in has_self_redirection_links and not urlparse(url).query:
        # 对于有自我纠正的重定向而且不携带任何参数的链接，直接返回
        return None
    # 对于适配的网站，直接保留白名单参数并返回
    if urlparse(url).hostname in whitelist_param_links:
        final_url = reserve_whitelisted_params(url)
        if urlparse(final_url).hostname in has_better_alternative_links:
            final_url = transform_into_fixed_url(final_url)
        if url != final_url:
            return final_url
        else:
            # 链接没有变化，直接返回 None，避免重复处理
            return None
    # 对于其它的网站，首先清理跟踪参数
    cleaned_url = remove_tracking_params(url)
    # 扩展短链接
    extended_url = await extend_short_urls(cleaned_url)
    if urlparse(extended_url).hostname in ['chatglm.cn']:
        final_url = reserve_whitelisted_params(extended_url)
        if url != final_url:
            return final_url
    # 对于扩展短链接之后的适配的网站，直接保留白名单参数并返回
    if urlparse(extended_url).hostname in whitelist_param_links:
        final_url = reserve_whitelisted_params(extended_url)
        if urlparse(final_url).hostname in has_better_alternative_links:
            final_url = transform_into_fixed_url(final_url)
        if url != final_url:
            return final_url
        else:
            # 链接没有变化，直接返回 None，避免重复处理
            return None
    if urlparse(extended_url).hostname in has_better_alternative_links:
        removed_tracking_url = remove_tracking_params(extended_url)
        final_url = transform_into_fixed_url(removed_tracking_url)
    else:
        # 对于其他链接，直接对其进行跟踪参数清理
        final_url = remove_tracking_params(extended_url)
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

async def handle_links(message: Message):
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
