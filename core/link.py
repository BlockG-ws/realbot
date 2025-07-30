import requests
import re
import html
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from abp.filters import parse_filterlist
from aiogram.types import Message

from config import config


def extend_short_urls(url):
    """ 扩展短链接 """
    r = requests.get(url)
    if 'tb.cn' in urlparse(url).hostname:
        # 淘宝短链接特殊处理
        html_content = r.text
        url = extract_tb_url_from_html(html_content)
        if not url:
            return url
    if r.status_code != 200:
        return url
    elif r.status_code in [301,302,304,307,308]:
        return r.headers['Location']
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

    tracking_params = []

    with open('assets/LegitimateURLShortener.txt','r', encoding='utf-8') as f:
        for line in parse_filterlist(f):
            if hasattr(line, 'options') and line.options:
                for option in line.options:
                    if option[0] == 'removeparam':
                        tracking_params.append(option[1])
    for param in tracking_params:
        query_params.pop(param, None)

    # Rebuild the URL without tracking parameters
    cleaned_query = urlencode(query_params, doseq=True)
    cleaned_url = urlunparse(parsed_url._replace(query=cleaned_query))

    return cleaned_url

def reserve_whitelisted_params(url):
    """ 保留白名单中的参数 """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if parsed_url.hostname in ['item.taobao.com','detail.tmall.com','h5.m.goofish.com','music.163.com']:
        if 'id' in query_params:
            # 只保留id参数，创建新的query_params
            new_query_params = {'id': query_params['id']}
            # 重新构建URL
            cleaned_query = urlencode(new_query_params, doseq=True)
            return urlunparse(parsed_url._replace(query=cleaned_query))
    elif parsed_url.hostname in ['mall.bilibili.com','space.bilibili.com','live.bilibili.com']:
        # 只保留spm_id_from参数，创建新的query_params
        new_query_params = {}
        # 重新构建URL
        cleaned_query = urlencode(new_query_params, doseq=True)
        return urlunparse(parsed_url._replace(query=cleaned_query))
    return url

def transform_into_fixed_url(url):
    """ 转换为修复了链接预览的链接 """
    parsed_url = urlparse(url)

    if parsed_url.hostname in ['x.com', 'twitter.com']:
        # 把 twitter 的链接转换为 fixupx.com
        return urlunparse(parsed_url._replace(hostname='i.fixupx.com'))
    return url


async def handle_links(message: Message):
    if not config.is_feature_enabled('link', message.chat.id):
        return
    # URL regex pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    # Extract URLs from message text
    if message.text:
        urls = re.findall(url_pattern, message.text)
        for url in urls:
            # Process each URL with your functions
            cleaned_url = remove_tracking_params(url)
            extended_url = extend_short_urls(cleaned_url)
            only_wl_params_url = reserve_whitelisted_params(extended_url)
            #untracked_url = remove_tracking_params(only_wl_params_url)
            fixed_url = transform_into_fixed_url(only_wl_params_url)
            # Do something with the processed URL
            await message.reply(f"清理完成：\n{fixed_url}")