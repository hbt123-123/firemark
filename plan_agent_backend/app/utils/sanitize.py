import re
import html
from typing import Optional


def sanitize_html(text: str) -> str:
    if not text:
        return text
    
    text = html.escape(text)
    
    dangerous_patterns = [
        (r'javascript:', ''),
        (r'on\w+\s*=', ''),
        (r'<script[^>]*>.*?</script>', '', re.IGNORECASE | re.DOTALL),
        (r'<iframe[^>]*>.*?</iframe>', '', re.IGNORECASE | re.DOTALL),
        (r'<object[^>]*>.*?</object>', '', re.IGNORECASE | re.DOTALL),
        (r'<embed[^>]*>', '', re.IGNORECASE),
        (r'<link[^>]*>', '', re.IGNORECASE),
        (r'<meta[^>]*>', '', re.IGNORECASE),
        (r'<style[^>]*>.*?</style>', '', re.IGNORECASE | re.DOTALL),
        (r'<base[^>]*>', '', re.IGNORECASE),
        (r'expression\s*\(', '', re.IGNORECASE),
        (r'vbscript:', '', re.IGNORECASE),
        (r'data:text/html', '', re.IGNORECASE),
    ]
    
    for pattern in dangerous_patterns:
        if len(pattern) == 2:
            text = re.sub(pattern[0], pattern[1], text)
        else:
            text = re.sub(pattern[0], pattern[1], text, flags=pattern[2])
    
    return text


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    if not text:
        return text
    
    text = sanitize_html(text)
    
    text = text.strip()
    
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def strip_tags(text: str) -> str:
    if not text:
        return text
    
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def is_safe_url(url: str) -> bool:
    if not url:
        return False
    
    safe_schemes = ['http', 'https']
    
    dangerous_patterns = [
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'file:',
    ]
    
    url_lower = url.lower()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, url_lower):
            return False
    
    if '://' in url:
        scheme = url.split('://')[0].lower()
        if scheme not in safe_schemes:
            return False
    
    return True
