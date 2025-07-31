import requests
import re
import html
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from abp.filters import parse_filterlist
from aiogram.types import Message

from config import config


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

def extend_short_urls(url):
    """ 扩展短链接 """
    r = requests.get(url, allow_redirects=False)
    if 'tb.cn' in urlparse(url).hostname:
        # 淘宝短链接特殊处理
        html_content = r.text
        url = extract_tb_url_from_html(html_content)
        if not url:
            return url
    if r.status_code in [301,302,304,307,308] and 'Location' in r.headers:
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

    # Reconstruct URL
    new_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=new_query))

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
    elif parsed_url.hostname in ['www.bilibili.com','m.bilibili.com','bilibili.com','mall.bilibili.com','space.bilibili.com','live.bilibili.com']:
        # 不保留任何参数
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
        return urlunparse(parsed_url._replace(netloc='i.fixupx.com'))
    if parsed_url.hostname in ['bilibili.com', 'm.bilibili.com']:
        # 把 bilibili 的链接转换为桌面端的 www.bilibili.com
        return urlunparse(parsed_url._replace(netloc='www.bilibili.com'))
    return url


async def handle_links(message: Message):
    if not config.is_feature_enabled('link', message.chat.id):
        return
    # URL regex pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

    # Extract URLs from message text
    if message.text:
        urls = re.findall(url_pattern, message.text)
        final_urls = []
        for url in urls:
            # 首先清理跟踪参数
            cleaned_url = remove_tracking_params(url)
            # 扩展短链接
            extended_url = extend_short_urls(cleaned_url)
            # 对于一些网站，只保留白名单中的参数
            if urlparse(extended_url).hostname in ['item.taobao.com','detail.tmall.com','h5.m.goofish.com','music.163.com','www.bilibili.com','m.bilibili.com','bilibili.com','mall.bilibili.com','space.bilibili.com','live.bilibili.com']:
                final_url = reserve_whitelisted_params(extended_url)
                if urlparse(extended_url).hostname in ['bilibili.com', 'm.bilibili.com']:
                    final_url = transform_into_fixed_url(final_url)
            elif urlparse(extended_url).hostname in ['x.com', 'twitter.com']:
                # 对于 Twitter 链接，转换为 fixupx.com
                removed_tracking_url = remove_tracking_params(extended_url)
                final_url = transform_into_fixed_url(removed_tracking_url)
            else:
                # 对于其他链接，直接对其进行跟踪参数清理
                final_url = remove_tracking_params(extended_url)
            final_urls.append(final_url)

        # 回复处理后的链接
        if final_urls:
            await message.reply(f"{"\n".join(final_urls)}\n消息里有包含跟踪参数的链接，已经帮你转换了哦")