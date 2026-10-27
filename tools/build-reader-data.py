from __future__ import annotations

import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


AD_PATTERNS = re.compile(
    r'欢迎关注微信公众号|小书呆读书纪|海量电子书|听读学社|多种格式方便你阅读',
    re.I,
)


def plain_text(html: str) -> str:
    return re.sub(r'<[^>]+>', ' ', html).replace('&nbsp;', ' ').strip()


def remove_ad_nodes(html: str) -> str:
    # 只删除独立的短广告节点，绝不删除外层 div、section 或正文容器。
    for tag in ('p', 'li', 'aside'):
        node_pattern = re.compile(rf'<(?P<tag>{tag})\b[^>]*>.*?</(?P=tag)>', re.I | re.S)
        while True:
            removed = False
            for match in list(node_pattern.finditer(html)):
                node_text = plain_text(match.group(0))
                if AD_PATTERNS.search(node_text) and len(node_text) <= 300:
                    html = html[:match.start()] + html[match.end():]
                    removed = True
                    break
            if not removed:
                break
    if AD_PATTERNS.search(plain_text(html)) and len(plain_text(html)) <= 300:
        return ''
    html = re.sub(r'<p\b[^>]*class=["\'][^"\']*picture[^"\']*["\'][^>]*>\s*</p>', '', html, flags=re.I)
    html = re.sub(r'<p\b[^>]*>\s*</p>', '', html, flags=re.I)
    return html.strip()

def local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def resolve(base: str, href: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), href.split('#', 1)[0]))


def text_from_xhtml(raw: bytes) -> str:
    text = raw.decode('utf-8', errors='replace')
    text = re.sub(r'<script\b[^>]*>.*?</script>', '', text, flags=re.I | re.S)
    text = re.sub(r'<style\b[^>]*>.*?</style>', '', text, flags=re.I | re.S)
    body = re.search(r'<body\b[^>]*>(.*?)</body>', text, flags=re.I | re.S)
    if body:
        text = body.group(1)
    text = re.sub(r'\s+(?:src|srcset)\s*=\s*(?:"[^"]*"|\'[^\']*\')', '', text, flags=re.I)
    text = re.sub(r'<img\b[^>]*>', '', text, flags=re.I)
    text = re.sub(r'\s+style\s*=\s*(?:"[^"]*"|\'[^\']*\')', '', text, flags=re.I)
    return text.strip()


def rewrite_internal_links(html: str, source: str, chapter_map: dict[str, int]) -> str:
    def replace(match: re.Match[str]) -> str:
        href = match.group(2)
        if href.startswith(('#', 'http://', 'https://', 'mailto:')):
            return match.group(0)
        target = resolve(source, href)
        chapter = chapter_map.get(target) or chapter_map.get(posixpath.basename(target))
        if chapter is None:
            return 'href="#"'
        return f'href="#reader-chapter-{chapter}"'

    return re.sub(r'href\s*=\s*(["\'])([^"\']+)\1', replace, html, flags=re.I)


def build(epub: Path, output: Path) -> dict:
    with zipfile.ZipFile(epub) as archive:
        container = ET.fromstring(archive.read('META-INF/container.xml'))
        rootfile = next(e for e in container.iter() if local_name(e.tag) == 'rootfile')
        opf_path = rootfile.attrib['full-path']
        opf = ET.fromstring(archive.read(opf_path))
        manifest = {}
        for item in opf.iter():
            if local_name(item.tag) == 'item':
                manifest[item.attrib['id']] = item.attrib
        spine = []
        for itemref in opf.iter():
            if local_name(itemref.tag) == 'itemref':
                item = manifest.get(itemref.attrib.get('idref'))
                if item and item.get('media-type', '').lower() in {'application/xhtml+xml', 'text/html'}:
                    spine.append(item)
        chapter_map = {}
        for number, item in enumerate(spine):
            path = resolve(opf_path, item['href'])
            chapter_map[path] = number + 1
            chapter_map[posixpath.basename(path)] = number + 1
        chapters = []
        for number, item in enumerate(spine, 1):
            path = resolve(opf_path, item['href'])
            if path not in archive.namelist():
                continue
            html = remove_ad_nodes(text_from_xhtml(archive.read(path)))
            html = rewrite_internal_links(html, path, chapter_map)
            if html:
                chapters.append({'number': number, 'html': html})
        result = {'title': epub.stem, 'chapters': chapters}
        output.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        return {'file': epub.name, 'chapters': len(chapters), 'bytes': output.stat().st_size}


def main() -> None:
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for epub in sorted(source.glob('*.epub')):
        target = destination / f'{epub.stem}.json'
        results.append(build(epub, target))
    print(json.dumps({'books': len(results), 'results': results}, ensure_ascii=False))


if __name__ == '__main__':
    main()
