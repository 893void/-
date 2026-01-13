# -*- coding: utf-8 -*-
"""
法令テキストパーサー
電気設備技術基準等のテキストファイルからHTMLを生成
"""
import re
from pathlib import Path


class StandardsParser:
    """法令テキストパーサー"""
    
    def __init__(self):
        self.kanji_nums = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100
        }
    
    def generate(self, txt_files, output_path, template_engine, auto_linker, site_config):
        """
        テキストファイルからHTMLを生成
        
        Args:
            txt_files: テキストファイルのリスト
            output_path: 出力先HTMLパス
            template_engine: テンプレートエンジン
            auto_linker: 自動リンカー
            site_config: サイト設定
        
        Returns:
            生成した条文数
        """
        # 全テキストを読み込み
        full_text = self._read_all_files(txt_files)
        
        # 条文を解析
        articles = self._parse_articles(full_text)
        
        # 条文数をカウント
        article_count = len([a for a in articles if a['type'] == 'article'])
        
        # HTMLを生成
        html_content = self._generate_html(articles, auto_linker, str(output_path))
        
        # テンプレートなしで直接出力（既存形式を維持）
        final_html = self._wrap_in_template(html_content, articles, site_config)
        
        # ファイル出力
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)
        
        return article_count
    
    def _read_all_files(self, txt_files):
        """複数のテキストファイルを結合して読み込む"""
        contents = []
        
        for txt_file in sorted(txt_files):
            try:
                with open(txt_file, "r", encoding="utf-8-sig") as f:
                    contents.append(f.read())
            except Exception as e:
                print(f"[警告] {txt_file}: 読み込みエラー（{e}）")
        
        return "\n".join(contents)
    
    def _kanji_to_number(self, kanji):
        """漢数字を数字に変換"""
        # 第X条の二のパターン
        if 'の二' in kanji:
            base = kanji.replace('第', '').replace('条の二', '')
            return str(self._kanji_to_number('第' + base + '条')) + '_2'
        
        # 第X条のパターン
        num_part = kanji.replace('第', '').replace('条', '').replace('章', '')
        
        result = 0
        current = 0
        
        for char in num_part:
            if char == '十':
                if current == 0:
                    current = 1
                result += current * 10
                current = 0
            elif char == '百':
                if current == 0:
                    current = 1
                result += current * 100
                current = 0
            elif char in self.kanji_nums:
                current = self.kanji_nums[char]
            else:
                current = 0
        
        result += current
        return str(result)
    
    def _parse_articles(self, text):
        """条文を解析してリストを返す"""
        articles = []
        lines = text.split('\n')
        
        current_article = None
        current_title = None
        current_content = []
        current_chapter = None
        
        # 目次部分をスキップするフラグ
        in_toc = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # ページ番号をスキップ
            if re.match(r'^\d+$', line):
                continue
            
            # 目次開始を検出
            if line == '目次':
                in_toc = True
                continue
            
            # 目次内の行をスキップ
            if in_toc:
                if line.startswith('附則') and len(line) < 5:
                    in_toc = False
                continue
            
            # 節・款をスキップ
            if re.match(r'^第[一二三四五六七八九十]+節', line):
                continue
            if re.match(r'^第[一二三四五六七八九十]+款', line):
                continue
            
            # 法令名や制定文をスキップ
            if '省令' in line and len(line) < 30 and '条' not in line:
                continue
            if '電気事業法' in line and '第' not in line[:5]:
                continue
            
            # 章の検出
            chapter_match = re.match(r'^(第[一二三]章)\s+(.+)$', line)
            if chapter_match:
                # 前の条文を保存
                if current_article and current_content:
                    articles.append({
                        'type': 'article',
                        'number': current_article,
                        'title': current_title,
                        'content': current_content[:],
                        'chapter': current_chapter
                    })
                    current_content = []
                    current_article = None
                
                current_chapter = chapter_match.group(1)
                chapter_title = chapter_match.group(2)
                articles.append({
                    'type': 'chapter',
                    'number': current_chapter,
                    'title': chapter_title
                })
                continue
            
            # 条文タイトルの検出
            title_match = re.match(r'^（(.+)）$', line)
            if title_match:
                # 前の条文を保存
                if current_article and current_content:
                    articles.append({
                        'type': 'article',
                        'number': current_article,
                        'title': current_title,
                        'content': current_content[:],
                        'chapter': current_chapter
                    })
                    current_content = []
                    current_article = None
                current_title = title_match.group(1)
                continue
            
            # 条文番号の検出
            article_match = re.match(r'^(第[一二三四五六七八九十百]+条(?:の二)?)\s+(.+)$', line)
            if article_match:
                # 前の条文を保存
                if current_article and current_content:
                    articles.append({
                        'type': 'article',
                        'number': current_article,
                        'title': current_title,
                        'content': current_content[:],
                        'chapter': current_chapter
                    })
                current_article = article_match.group(1)
                current_content = [article_match.group(2)]
                continue
            
            # 通常の内容行
            if current_article:
                current_content.append(line)
        
        # 最後の条文を保存
        if current_article and current_content:
            articles.append({
                'type': 'article',
                'number': current_article,
                'title': current_title,
                'content': current_content[:],
                'chapter': current_chapter
            })
        
        return articles
    
    def _generate_html(self, articles, auto_linker, current_page):
        """条文HTMLを生成"""
        content_html = []
        
        for item in articles:
            if item['type'] == 'chapter':
                num = self._kanji_to_number(item['number'])
                content_html.append(f'''
                <!-- {item["number"]} -->
                <article class="article" id="chapter{num}">
                    <h2 class="chapter-title">{item["number"]} {item["title"]}</h2>
                </article>''')
            
            elif item['type'] == 'article':
                num = self._kanji_to_number(item['number'])
                article_id = f'article{num}'
                
                # 内容をパラグラフに変換
                paragraphs = []
                for line in item['content']:
                    escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    paragraphs.append(f'                        <p>{escaped}</p>')
                
                content_str = '\n'.join(paragraphs)
                
                content_html.append(f'''
                <article class="article" id="{article_id}">
                    <h3 class="article-title">
                        <a href="../coming-soon.html">{item["number"]}（{item["title"]}）</a>
                    </h3>
                    <div class="article-content">
{content_str}
                    </div>
                </article>''')
        
        html = ''.join(content_html)
        
        # 自動リンク適用
        if auto_linker:
            html = auto_linker.apply(html, current_page)
        
        return html
    
    def _generate_toc(self, articles):
        """目次HTMLを生成"""
        sidebar_html = []
        
        for item in articles:
            if item['type'] == 'chapter':
                sidebar_html.append(
                    f'                    <li class="sidebar-chapter">{item["number"]} {item["title"]}</li>'
                )
            elif item['type'] == 'article':
                num = self._kanji_to_number(item['number'])
                article_id = f'article{num}'
                sidebar_html.append(
                    f'                    <li><a href="#{article_id}">{item["number"]} {item["title"]}</a></li>'
                )
        
        return '\n'.join(sidebar_html)
    
    def _wrap_in_template(self, content, articles, site_config):
        """完全なHTMLを生成"""
        toc = self._generate_toc(articles)
        site_name = site_config.get("site_name", "ほあんペディア")
        
        return f'''<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>電気設備技術基準 - {site_name}</title>
    <meta name="description" content="電気設備の技術的要件を定めた経済産業省令（平成九年通商産業省令第五十二号）">
    <link rel="stylesheet" href="../css/style.css">
</head>

<body>
    <!-- 共通ヘッダー -->
    <header class="site-header">
        <a href="../index.html">
            <span class="home-icon">🏠</span>
            <span>{site_name}</span>
        </a>
    </header>

    <!-- メインコンテンツ -->
    <main class="main-content">
        <h1 class="page-title">電気設備技術基準</h1>

        <div class="two-column-layout">
            <!-- 左カラム：目次 -->
            <aside class="sidebar">
                <h2 class="sidebar-title">目次</h2>
                <ul class="sidebar-list">
{toc}
                </ul>
            </aside>

            <!-- 右カラム：条文本文 -->
            <div class="content-area">
{content}
            </div>
        </div>
    </main>

    <!-- スクロール機能 -->
    <script>
        document.querySelectorAll('.sidebar-list a').forEach(link => {{
            link.addEventListener('click', function (e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>

</html>'''
