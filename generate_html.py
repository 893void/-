# -*- coding: utf-8 -*-
"""
電気設備技術基準 HTML生成スクリプト v2
分割されたテキストファイルから完全なHTMLページを生成
（目次重複バグ修正版）
"""
import re
import os

# 設定
base_dir = r'c:\Users\sadan\OneDrive\ドキュメント\ほあんペディア'
output_file = os.path.join(base_dir, 'standards', 'index.html')

# 3つの分割ファイルを読み込む
files = [
    os.path.join(base_dir, '第１章.txt'),
    os.path.join(base_dir, '第２章.txt'),
    os.path.join(base_dir, '第３章.txt'),
]

all_content = []
for f in files:
    with open(f, 'r', encoding='utf-8-sig') as file:
        all_content.append(file.read())

full_text = '\n'.join(all_content)

def kanji_to_number(kanji):
    """漢数字を数字に変換"""
    kanji_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
                  '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                  '百': 100}
    
    # 第X条の二のパターン
    if 'の二' in kanji:
        base = kanji.replace('第', '').replace('条の二', '')
        return str(kanji_to_number('第' + base + '条')) + '_2'
    
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
        elif char in kanji_nums:
            current = kanji_nums[char]
        else:
            current = 0
    result += current
    return str(result)

def parse_articles(text):
    """条文を解析してリストを返す"""
    articles = []
    lines = text.split('\n')
    
    current_article = None
    current_title = None
    current_content = []
    current_chapter = None
    
    # 目次部分をスキップするフラグ
    in_toc = False
    toc_start_patterns = ['目次', '第一章　総則', '第一節　定義']
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line:
            continue
        
        # ページ番号をスキップ
        if re.match(r'^\d+$', line):
            continue
        
        # 目次開始を検出
        if line == '目次':
            in_toc = True
            continue
        
        # 目次内の行をスキップ（条文本体の開始まで）
        # 「第一章　総則」が2回目に現れたら本文開始
        if in_toc:
            if line.startswith('附則') and len(line) < 5:
                # 目次の附則は終わりマーカー、次に来る「第一章　総則」から本文
                in_toc = False
                continue
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
        
        # 章の検出（本文中）
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
        
        # 条文タイトルの検出 （用語の定義）
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

def generate_html(articles):
    """HTMLを生成"""
    
    # 目次を生成（章ごとに整理）
    sidebar_html = []
    current_chapter = None
    for item in articles:
        if item['type'] == 'chapter':
            sidebar_html.append(f'                    <li class="sidebar-chapter">{item["number"]} {item["title"]}</li>')
        elif item['type'] == 'article':
            num = kanji_to_number(item['number'])
            article_id = f'article{num}'
            sidebar_html.append(f'                    <li><a href="#{article_id}">{item["number"]} {item["title"]}</a></li>')
    
    # 本文を生成
    content_html = []
    for item in articles:
        if item['type'] == 'chapter':
            num = kanji_to_number(item['number'])
            content_html.append(f'''
                <!-- {item["number"]} -->
                <article class="article" id="chapter{num}">
                    <h2 class="chapter-title">{item["number"]} {item["title"]}</h2>
                </article>''')
        elif item['type'] == 'article':
            num = kanji_to_number(item['number'])
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
    
    # HTMLテンプレート
    html_template = f'''<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>電気設備技術基準 - ほあんペディア</title>
    <meta name="description" content="電気設備の技術的要件を定めた経済産業省令（平成九年通商産業省令第五十二号）">
    <link rel="stylesheet" href="../css/style.css">
</head>

<body>
    <!-- 共通ヘッダー -->
    <header class="site-header">
        <a href="../index.html">
            <span class="home-icon">🏠</span>
            <span>ほあんペディア</span>
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
{chr(10).join(sidebar_html)}
                </ul>
            </aside>

            <!-- 右カラム：条文本文 -->
            <div class="content-area">
{''.join(content_html)}
            </div>
        </div>
    </main>

    <!-- スクロール機能 -->
    <script>
        // 目次クリックで該当条文にスムーズスクロール
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
    
    return html_template

# メイン処理
print('条文を解析中...')
articles = parse_articles(full_text)

# 条文のみをカウント
article_count = len([a for a in articles if a['type'] == 'article'])
chapter_count = len([a for a in articles if a['type'] == 'chapter'])
print(f'章: {chapter_count}件, 条文: {article_count}件')

# HTMLを生成
print('HTMLを生成中...')
html_content = generate_html(articles)

# ファイルに書き込み
print(f'ファイルに書き込み中: {output_file}')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'完了！ファイルサイズ: {len(html_content):,} bytes')
print(f'第1条〜第78条 を含むHTMLを生成しました。')

# 確認用：最初と最後の条文を表示
article_items = [a for a in articles if a['type'] == 'article']
if article_items:
    print(f'最初の条文: {article_items[0]["number"]} ({article_items[0]["title"]})')
    print(f'最後の条文: {article_items[-1]["number"]} ({article_items[-1]["title"]})')
