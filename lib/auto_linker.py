# -*- coding: utf-8 -*-
"""
自動リンク処理
用語辞書に基づいて本文中のキーワードを自動リンク化
"""
import re
from html.parser import HTMLParser


class TagPositionFinder(HTMLParser):
    """HTMLタグの位置を特定するパーサー"""
    
    def __init__(self):
        super().__init__()
        self.tag_positions = []  # (start, end) のリスト
        self.current_pos = 0
    
    def handle_starttag(self, tag, attrs):
        # タグ開始位置を記録
        pass
    
    def handle_data(self, data):
        # テキストデータの位置を記録
        pass


class AutoLinker:
    """自動リンク処理クラス"""
    
    def __init__(self, terms):
        """
        Args:
            terms: 用語辞書のリスト
                   [{"word": "過電流継電器", "link": "relay/ocr.html", ...}, ...]
        """
        # 長い単語順にソート（長い方を優先マッチ）
        self.terms = sorted(terms, key=lambda t: len(t.get("word", "")), reverse=True)
    
    def apply(self, html_content, current_page=""):
        """
        HTML本文に自動リンクを適用
        
        Args:
            html_content: HTML文字列
            current_page: 現在のページパス（自己参照防止用）
        
        Returns:
            リンク適用後のHTML文字列
        """
        if not self.terms:
            return html_content
        
        # 現在のページの階層を計算
        current_depth = self._get_depth(current_page)
        
        # 既にリンク済みの単語を記録
        linked_words = set()
        
        for term in self.terms:
            word = term.get("word", "")
            link = term.get("link", "")
            
            if not word or not link:
                continue
            
            # 自分自身へのリンクはスキップ
            if self._is_same_page(link, current_page):
                continue
            
            # 既にリンク済みならスキップ
            if word in linked_words:
                continue
            
            # 現在のページからの相対パスを計算
            relative_link = self._make_relative_link(link, current_depth)
            
            # 初出のみ置換
            html_content = self._replace_first_outside_tags(
                html_content,
                word,
                relative_link
            )
            
            linked_words.add(word)
        
        return html_content
    
    def _get_depth(self, page_path):
        """ページパスの階層深度を取得"""
        if not page_path:
            return 0
        
        # パスを正規化
        normalized = page_path.replace("\\", "/")
        
        # docs/ を除去
        if "docs/" in normalized:
            normalized = normalized.split("docs/", 1)[1]
        
        # ディレクトリ部分のみ取得（ファイル名を除く）
        parts = normalized.split("/")
        return len(parts) - 1  # ファイル名を除く
    
    def _make_relative_link(self, link, depth):
        """現在の階層から相対パスを作成"""
        if depth == 0:
            return link
        
        # 上位階層への移動を計算
        prefix = "../" * depth
        return prefix + link
    
    def _is_same_page(self, link, current_page):
        """同一ページかどうか判定"""
        if not current_page:
            return False
        
        # パスの正規化
        link_normalized = link.replace("\\", "/").lstrip("/")
        current_normalized = current_page.replace("\\", "/").lstrip("/")
        
        # docs/ を除去して比較
        if link_normalized.startswith("docs/"):
            link_normalized = link_normalized[5:]
        if current_normalized.startswith("docs/"):
            current_normalized = current_normalized[5:]
        
        return link_normalized == current_normalized
    
    def _replace_first_outside_tags(self, html, word, link):
        """
        HTMLタグ外で最初に出現する単語のみを置換
        
        - タグ内（href="..."等）は置換しない
        - 既存の<a>タグ内は置換しない
        """
        # 正規表現でHTMLタグをマッチ
        # パターン: タグ全体 OR テキストノード
        pattern = r'(<[^>]+>)|([^<]+)'
        
        replaced = False
        result = []
        
        for match in re.finditer(pattern, html):
            tag = match.group(1)
            text = match.group(2)
            
            if tag:
                # HTMLタグはそのまま
                result.append(tag)
            elif text and not replaced:
                # テキストノード：初出の単語を置換
                if word in text:
                    # <a>タグ内でないか確認
                    if not self._is_inside_anchor(html, match.start()):
                        replacement = f'<a href="{link}" class="auto-link">{word}</a>'
                        text = text.replace(word, replacement, 1)
                        replaced = True
                result.append(text)
            else:
                result.append(text or "")
        
        return "".join(result)
    
    def _is_inside_anchor(self, html, position):
        """指定位置が<a>タグ内かどうか判定"""
        # 簡易判定：直前の<a>と</a>の位置を確認
        before = html[:position]
        
        last_a_open = before.rfind("<a ")
        if last_a_open == -1:
            last_a_open = before.rfind("<a>")
        
        last_a_close = before.rfind("</a>")
        
        # <a>が開いていて、まだ閉じていなければタグ内
        return last_a_open > last_a_close
