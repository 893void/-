# -*- coding: utf-8 -*-
"""
Markdown パーサー
フロントマター解析とMarkdown→HTML変換を担当
"""
import re
from pathlib import Path

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class MarkdownParser:
    """Markdownファイルのパーサー"""
    
    def __init__(self):
        if MARKDOWN_AVAILABLE:
            self.md = markdown.Markdown(
                extensions=[
                    'tables',
                    'fenced_code',
                    'codehilite',
                    'toc',
                ]
            )
        else:
            self.md = None
    
    def parse_file(self, filepath):
        """ファイルを解析してフロントマターとHTMLを返す"""
        filepath = Path(filepath)
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content):
        """コンテンツを解析してフロントマターとHTMLを返す"""
        frontmatter = {}
        body = content
        
        # フロントマター（YAML）の抽出
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        
        if fm_match:
            fm_text = fm_match.group(1)
            frontmatter = self._parse_yaml_simple(fm_text)
            body = content[fm_match.end():]
        
        # カスタム記法の処理（:::info, :::warning等）
        body = self._process_custom_blocks(body)
        
        # Markdown → HTML 変換
        if self.md:
            self.md.reset()
            html = self.md.convert(body)
        else:
            # markdownライブラリがない場合は簡易変換
            html = self._simple_markdown(body)
        
        return frontmatter, html
    
    def _parse_yaml_simple(self, yaml_text):
        """シンプルなYAML解析（ネストなし）"""
        result = {}
        
        for line in yaml_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                # 文字列のクォートを削除
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # 数値変換
                if value.isdigit():
                    value = int(value)
                
                result[key] = value
        
        return result
    
    def _process_custom_blocks(self, text):
        """カスタムブロック記法を処理"""
        # :::info, :::warning, :::danger を変換
        def replace_block(match):
            block_type = match.group(1)
            block_content = match.group(2).strip()
            return f'<div class="notice notice-{block_type}">\n<p>{block_content}</p>\n</div>'
        
        pattern = r':::(\w+)\n(.*?)\n:::'
        text = re.sub(pattern, replace_block, text, flags=re.DOTALL)
        
        return text
    
    def _simple_markdown(self, text):
        """シンプルなMarkdown変換（フォールバック用）"""
        lines = text.split("\n")
        html_lines = []
        in_list = False
        
        for line in lines:
            # 見出し
            if line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            # リスト
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{line[2:]}</li>")
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                
                if line.strip():
                    # 太字
                    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    # 斜体
                    line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                    # リンク
                    line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
                    html_lines.append(f"<p>{line}</p>")
        
        if in_list:
            html_lines.append("</ul>")
        
        return "\n".join(html_lines)
