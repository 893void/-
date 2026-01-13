#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
電気設備技術基準の解釈 HTML生成スクリプト
解釈テキストファイルからHTMLページを生成する
電技省令と同じ2カラムレイアウト（左:目次、右:本文）を使用
"""

import re
import os
from pathlib import Path

def parse_kaishaku_text(text):
    """解釈テキストを解析して構造化データを返す"""
    articles = []
    lines = text.split('\n')
    
    current_article = None
    current_title = None
    current_content = []
    current_chapter = None
    current_section = None
    in_toc = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line:
            if current_article and current_content:
                current_content.append('')
            continue
        
        # 目次部分の開始検出
        if line.startswith('目 次') or line.startswith('目次'):
            in_toc = True
            continue
        
        # 目次中は章タイトルをスキップ、「第1章 総則」で目次終了
        if in_toc:
            if re.match(r'^第1章\s+総則', line):
                in_toc = False
            else:
                continue
        
        # 章の検出（アラビア数字: 第1章、第2章...）
        chapter_match = re.match(r'^(第\d+章)\s*(.*)$', line)
        if chapter_match:
            if current_article and current_content:
                articles.append({
                    'type': 'article',
                    'number': current_article,
                    'title': current_title,
                    'content': current_content[:],
                    'chapter': current_chapter,
                    'section': current_section
                })
                current_content = []
            
            current_chapter = chapter_match.group(1)
            chapter_title = chapter_match.group(2).strip()
            articles.append({
                'type': 'chapter',
                'number': current_chapter,
                'title': chapter_title
            })
            current_section = None
            current_article = None
            current_title = None
            continue
        
        # 節の検出（アラビア数字: 第1節、第2節...）
        section_match = re.match(r'^(第\d+節)\s*(.*)$', line)
        if section_match:
            if current_article and current_content:
                articles.append({
                    'type': 'article',
                    'number': current_article,
                    'title': current_title,
                    'content': current_content[:],
                    'chapter': current_chapter,
                    'section': current_section
                })
                current_content = []
            
            current_section = section_match.group(1)
            section_title = section_match.group(2).strip()
            articles.append({
                'type': 'section',
                'number': current_section,
                'title': section_title,
                'chapter': current_chapter
            })
            current_article = None
            current_title = None
            continue
        
        # 条文タイトルの検出（【タイトル】パターン）
        title_match = re.match(r'^【(.+?)】', line)
        if title_match:
            if current_article and current_content:
                articles.append({
                    'type': 'article',
                    'number': current_article,
                    'title': current_title,
                    'content': current_content[:],
                    'chapter': current_chapter,
                    'section': current_section
                })
                current_content = []
            current_title = title_match.group(1)
            current_article = None
            continue
        
        # 条番号の検出（アラビア数字: 第1条、第37条の2 など）
        article_num_match = re.match(r'^(第\d+条(?:の\d+)?)\s*(.*)$', line)
        if article_num_match:
            if current_article and current_content:
                articles.append({
                    'type': 'article',
                    'number': current_article,
                    'title': current_title,
                    'content': current_content[:],
                    'chapter': current_chapter,
                    'section': current_section
                })
                current_content = []
            
            current_article = article_num_match.group(1)
            remaining = article_num_match.group(2).strip()
            if remaining:
                current_content.append(remaining)
            continue
        
        # 現在の条文のコンテンツに追加
        if current_article:
            current_content.append(line)
    
    # 最後の条文を保存
    if current_article and current_content:
        articles.append({
            'type': 'article',
            'number': current_article,
            'title': current_title,
            'content': current_content[:],
            'chapter': current_chapter,
            'section': current_section
        })
    
    return articles

def format_content(content_lines):
    """コンテンツ行をHTML形式に整形"""
    html_parts = []
    in_table = False
    table_rows = []
    
    for line in content_lines:
        line = line.strip()
        if not line:
            if in_table and table_rows:
                html_parts.append(format_table(table_rows))
                table_rows = []
                in_table = False
            html_parts.append('<br>')
            continue
        
        # 表の検出（タブで区切られた行）
        if '\t' in line:
            in_table = True
            table_rows.append(line)
            continue
        
        # 表の終了
        if in_table and table_rows and '\t' not in line:
            html_parts.append(format_table(table_rows))
            table_rows = []
            in_table = False
        
        # 号の検出（一、二、三...）
        if re.match(r'^[一二三四五六七八九十]+\s', line):
            html_parts.append(f'<p class="item-major">{escape_html(line)}</p>')
        # 細分号の検出（イ、ロ、ハ...）
        elif re.match(r'^[イロハニホヘトチリヌ]\s', line):
            html_parts.append(f'<p class="item-sub">{escape_html(line)}</p>')
        # さらに細かい号（(イ)、(ロ)...）
        elif re.match(r'^\([イロハニホヘトチリヌ]\)', line):
            html_parts.append(f'<p class="item-detail">{escape_html(line)}</p>')
        # (1)、(2) などの号
        elif re.match(r'^\(\d+\)', line):
            html_parts.append(f'<p class="item-detail">{escape_html(line)}</p>')
        # 備考
        elif line.startswith('(備考)') or line.startswith('※'):
            html_parts.append(f'<p class="note">{escape_html(line)}</p>')
        else:
            html_parts.append(f'<p>{escape_html(line)}</p>')
    
    # 残りの表を処理
    if table_rows:
        html_parts.append(format_table(table_rows))
    
    return '\n'.join(html_parts)

def format_table(rows):
    """表データをHTMLテーブルに変換"""
    if not rows:
        return ''
    
    html = ['<div class="table-container"><table class="spec-table">']
    for i, row in enumerate(rows):
        cells = row.split('\t')
        tag = 'th' if i == 0 else 'td'
        html.append('<tr>')
        for cell in cells:
            html.append(f'<{tag}>{escape_html(cell.strip())}</{tag}>')
        html.append('</tr>')
    html.append('</table></div>')
    return '\n'.join(html)

def escape_html(text):
    """HTMLエスケープ"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def generate_html(articles):
    """HTML全体を生成（電技省令と同じ2カラムレイアウト）"""
    
    # 目次の生成
    toc_items = []
    for item in articles:
        if item['type'] == 'chapter':
            num = item['number'].replace('第', '').replace('章', '')
            toc_items.append(f'<li class="sidebar-chapter">{item["number"]} {item["title"]}</li>')
        elif item['type'] == 'section':
            num = item['number'].replace('第', '').replace('節', '')
            chapter_num = (item.get('chapter') or '').replace('第', '').replace('章', '')
            toc_items.append(f'<li><a href="#section{chapter_num}_{num}">{item["number"]} {item["title"]}</a></li>')
        elif item['type'] == 'article':
            article_num = item['number'].replace('第', '').replace('条', '').replace('の', '_')
            title_text = item.get('title', '')
            if title_text:
                toc_items.append(f'<li><a href="#article{article_num}">{item["number"]}（{title_text}）</a></li>')
            else:
                toc_items.append(f'<li><a href="#article{article_num}">{item["number"]}</a></li>')
    
    # 本文の生成
    content_items = []
    for item in articles:
        if item['type'] == 'chapter':
            num = item['number'].replace('第', '').replace('章', '')
            content_items.append(f'''
                <article class="article" id="chapter{num}">
                    <h2 class="chapter-title">{item['number']} {item['title']}</h2>
                </article>
            ''')
        elif item['type'] == 'section':
            num = item['number'].replace('第', '').replace('節', '')
            chapter_num = (item.get('chapter') or '').replace('第', '').replace('章', '')
            content_items.append(f'''
                <article class="article" id="section{chapter_num}_{num}">
                    <h3 class="section-title">{item['number']} {item['title']}</h3>
                </article>
            ''')
        elif item['type'] == 'article':
            article_num = item['number'].replace('第', '').replace('条', '').replace('の', '_')
            title_text = f'（{item["title"]}）' if item.get('title') else ''
            content_html = format_content(item['content'])
            content_items.append(f'''
                <article class="article" id="article{article_num}">
                    <h3 class="article-title">
                        <a href="../coming-soon.html">{item['number']}{title_text}</a>
                    </h3>
                    <div class="article-content">
                        {content_html}
                    </div>
                </article>
            ''')
    
    # 完全なHTML（電技省令と同じ構造）
    html = f'''<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>電気設備技術基準の解釈 - ほあんペディア</title>
    <meta name="description" content="電気設備に関する技術基準を定める省令に定める技術的要件を満たすと認められる技術的内容">
    <link rel="stylesheet" href="../../css/style.css">
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
        <h1 class="page-title">電気設備技術基準の解釈</h1>

        <div class="two-column-layout">
            <!-- 左カラム：目次 -->
            <aside class="sidebar">
                <h2 class="sidebar-title">目次</h2>
                <ul class="sidebar-list">
                    {''.join(toc_items)}
                </ul>
            </aside>

            <!-- 右カラム：条文本文 -->
            <div class="content-area">
                {''.join(content_items)}
            </div>
        </div>
    </main>

    <!-- フッター -->
    <footer class="site-footer">
        <p>&copy; 2026 ほあんペディア - 保安・電気技術の百科事典</p>
    </footer>
</body>
</html>
'''
    return html

def main():
    # 入力ファイルのパス
    input_dir = Path('content/standards/kaishaku')
    output_dir = Path('docs/standards/kaishaku')
    
    # 出力ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 入力ファイルを読み込み（条文番号順）
    all_text = ''
    # ファイルを正しい順序で読み込む（第1条から始まる順）
    file_order = [
        'chapters_1_2.txt',        # 第1条〜第48条（第1章、第2章）
        '第3章61条まで 電線路.txt', # 第49条〜第61条（第3章前半）
        '106条まで.txt',           # 第62条〜第106条
        '153条まで.txt',           # 第107条〜第153条
        '183条まで.txt',           # 第154条〜第183条
        '198条まで.txt',           # 第184条〜第198条
        '217条まで.txt',           # 第199条〜第217条
        '226条まで.txt',           # 第218条〜第226条
        '最後.txt',                # 第227条〜第234条、別表、附則
    ]
    
    for filename in file_order:
        txt_file = input_dir / filename
        if txt_file.exists():
            print(f'読み込み中: {txt_file.name}')
            with open(txt_file, 'r', encoding='utf-8') as f:
                all_text += f.read() + '\n'
        else:
            print(f'警告: {filename} が見つかりません')
    
    if not all_text:
        print('エラー: テキストファイルが見つかりません')
        return
    
    # テキストを解析
    print('テキストを解析中...')
    articles = parse_kaishaku_text(all_text)
    
    # 統計情報
    chapters = sum(1 for a in articles if a['type'] == 'chapter')
    sections = sum(1 for a in articles if a['type'] == 'section')
    article_count = sum(1 for a in articles if a['type'] == 'article')
    print(f'解析完了: {chapters}章, {sections}節, {article_count}条文')
    
    # HTMLを生成
    print('HTMLを生成中...')
    html = generate_html(articles)
    
    # 出力
    output_file = output_dir / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # ファイルサイズ
    size_kb = output_file.stat().st_size / 1024
    print(f'出力完了: {output_file} ({size_kb:.1f} KB)')

if __name__ == '__main__':
    main()
