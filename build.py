# -*- coding: utf-8 -*-
"""
ほあんペディア ビルドシステム v1.0
Markdown/JSONからHTMLを生成するメインスクリプト
"""
import os
import sys
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# ビルドツールのインポート
from lib.template_engine import TemplateEngine
from lib.markdown_parser import MarkdownParser
from lib.auto_linker import AutoLinker
from lib.standards_parser import StandardsParser

# 設定
BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR / "docs"
IMAGES_DIR = BASE_DIR / "images"

class HoanPediaBuilder:
    """ほあんペディアビルダー"""
    
    def __init__(self, clean=False):
        self.clean = clean
        self.warnings = []
        self.errors = []
        self.generated_files = 0
        self.start_time = None
        
        # コンポーネント初期化
        self.template_engine = None
        self.markdown_parser = None
        self.auto_linker = None
        self.standards_parser = None
        self.site_config = {}
        self.terms = []
    
    def log(self, message, level="INFO"):
        """ログ出力"""
        if level == "WARNING":
            self.warnings.append(message)
            print(f"[警告] {message}")
        elif level == "ERROR":
            self.errors.append(message)
            print(f"[エラー] {message}")
        else:
            print(f"      → {message}")
    
    def log_step(self, step, total, message):
        """ステップログ"""
        print(f"\n[{step}/{total}] {message}")
    
    def load_json(self, filepath):
        """JSONファイルを読み込む"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.log(f"{filepath} が見つかりません", "WARNING")
            return {}
        except json.JSONDecodeError as e:
            self.log(f"{filepath}: JSON構文エラー（{e}）", "ERROR")
            return None
    
    def build(self):
        """メインビルド処理"""
        self.start_time = datetime.now()
        
        print("=" * 60)
        print("ほあんペディア ビルドシステム v1.0")
        print("=" * 60)
        
        # クリーンビルド
        if self.clean:
            self.clean_docs()
        
        # Step 1: 設定読み込み
        self.log_step(1, 7, "設定を読み込み中...")
        if not self.load_config():
            return False
        
        # Step 2: 用語辞書読み込み
        self.log_step(2, 7, "用語辞書を読み込み中...")
        if not self.load_terms():
            return False
        
        # Step 3: テンプレート読み込み
        self.log_step(3, 7, "テンプレートを読み込み中...")
        if not self.load_templates():
            return False
        
        # Step 4: Markdownファイル処理
        self.log_step(4, 7, "Markdownファイルを処理中...")
        self.process_markdown_files()
        
        # Step 5: 法令ページ生成
        self.log_step(5, 7, "法令ページを生成中...")
        self.generate_standards_pages()
        
        # Step 6: トップページ生成
        self.log_step(6, 7, "トップページを生成中...")
        self.generate_top_page()
        
        # Step 7: 静的ファイルコピー
        self.log_step(7, 7, "静的ファイルをコピー中...")
        self.copy_static_files()
        
        # 完了メッセージ
        self.print_summary()
        
        return len(self.errors) == 0
    
    def clean_docs(self):
        """docs/フォルダをクリーン"""
        print("\n[準備] docs/ フォルダをクリーン中...")
        # 重要: coming-soon.html等の静的ファイルは保持
        # 動的生成ファイルのみ削除する設計
        self.log("クリーンビルドは現在未実装（既存ファイルを保持）")
    
    def load_config(self):
        """サイト設定を読み込む"""
        config_path = DATA_DIR / "site.json"
        self.site_config = self.load_json(config_path)
        
        if self.site_config is None:
            return False
        
        if not self.site_config:
            # デフォルト値を使用
            self.site_config = {
                "site_name": "ほあんペディア",
                "description": "電気保安に関する知識を集約した情報サイト",
                "version": "2.0.0"
            }
            self.log("site.json が見つからないため、デフォルト値を使用")
        else:
            self.log("site.json を読み込みました")
        
        return True
    
    def load_terms(self):
        """用語辞書を読み込む"""
        terms_path = DATA_DIR / "terms.json"
        data = self.load_json(terms_path)
        
        if data is None:
            return False
        
        if data and "terms" in data:
            self.terms = data["terms"]
            self.auto_linker = AutoLinker(self.terms)
            self.log(f"{len(self.terms)} 件の用語を登録しました")
        else:
            self.terms = []
            self.auto_linker = AutoLinker([])
            self.log("terms.json が見つからないため、自動リンクは無効")
        
        return True
    
    def load_templates(self):
        """テンプレートを読み込む"""
        self.template_engine = TemplateEngine(TEMPLATES_DIR, self.site_config)
        template_count = self.template_engine.load_all()
        
        if template_count > 0:
            self.log(f"{template_count} 件のテンプレートを読み込みました")
        else:
            self.log("テンプレートが見つかりません", "WARNING")
        
        return True
    
    def process_markdown_files(self):
        """Markdownファイルを処理"""
        self.markdown_parser = MarkdownParser()
        
        # content/ 内の全 .md ファイルを処理
        md_files = list(CONTENT_DIR.rglob("*.md"))
        
        if not md_files:
            self.log("Markdownファイルが見つかりません")
            return
        
        for md_file in md_files:
            try:
                self.process_single_markdown(md_file)
            except Exception as e:
                self.log(f"{md_file.name}: 処理エラー（{e}）", "WARNING")
        
        self.log(f"{len(md_files)} ファイルを処理しました")
    
    def process_single_markdown(self, md_file):
        """単一のMarkdownファイルを処理"""
        # フロントマター解析とHTML変換
        frontmatter, html_content = self.markdown_parser.parse_file(md_file)
        
        # 自動リンク適用
        output_path = self.get_output_path(md_file)
        html_content = self.auto_linker.apply(html_content, str(output_path))
        
        # テンプレート適用
        template_name = frontmatter.get("template", "article")
        context = {
            "page_title": frontmatter.get("title", md_file.stem),
            "page_description": frontmatter.get("description", ""),
            "content": html_content,
            "breadcrumb": self.generate_breadcrumb(md_file, frontmatter)
        }
        
        final_html = self.template_engine.render(template_name, context)
        
        # 出力
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)
        
        self.generated_files += 1
        self.log(f"{md_file.name} ... 完了")
    
    def get_output_path(self, md_file):
        """Markdownファイルの出力先パスを取得"""
        relative = md_file.relative_to(CONTENT_DIR)
        return DOCS_DIR / relative.with_suffix(".html")
    
    def generate_breadcrumb(self, md_file, frontmatter):
        """パンくずナビゲーションを生成"""
        # 簡易実装：後で拡張可能
        return ""
    
    def generate_standards_pages(self):
        """法令ページを生成"""
        self.standards_parser = StandardsParser()
        standards_dir = CONTENT_DIR / "standards" / "dengi"
        
        if not standards_dir.exists():
            self.log("法令テキストフォルダが見つかりません")
            return
        
        # 電気設備技術基準の生成
        txt_files = list(standards_dir.glob("*.txt"))
        if txt_files:
            article_count = self.standards_parser.generate(
                txt_files,
                DOCS_DIR / "standards" / "index.html",
                self.template_engine,
                self.auto_linker,
                self.site_config
            )
            self.log(f"電気設備技術基準 ... {article_count}条を生成しました")
            self.generated_files += 1
    
    def generate_top_page(self):
        """トップページを生成"""
        # news.json と updates.json を読み込み
        news_data = self.load_json(DATA_DIR / "news.json") or {"news": []}
        updates_data = self.load_json(DATA_DIR / "updates.json") or {"updates": []}
        
        # 現在のトップページは既存のindex.htmlを使用
        # Phase 2 完了後にテンプレートから生成に切り替え
        self.log("index.html は既存ファイルを使用（将来テンプレート化予定）")
    
    def copy_static_files(self):
        """静的ファイルをコピー"""
        # 画像ファイルをコピー
        if IMAGES_DIR.exists():
            dest_images = DOCS_DIR / "images"
            if dest_images.exists():
                shutil.rmtree(dest_images)
            shutil.copytree(IMAGES_DIR, dest_images)
            image_count = len(list(dest_images.rglob("*.*")))
            self.log(f"画像: {image_count} ファイル")
        else:
            self.log("画像フォルダが見つかりません（スキップ）")
        
        # CSSは既存のものを維持
        self.log("CSS: 既存ファイルを維持")
    
    def print_summary(self):
        """ビルド結果サマリーを表示"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 60)
        
        if self.errors:
            print("ビルド失敗")
            print(f"エラー: {len(self.errors)} 件")
            print("エラー内容を確認し、修正後に再実行してください。")
        elif self.warnings:
            print("ビルド完了（警告あり）")
            print(f"警告: {len(self.warnings)} 件")
        else:
            print("ビルド完了！")
        
        print(f"出力先: {DOCS_DIR}")
        print(f"生成ファイル数: {self.generated_files}")
        print(f"ビルド時間: {elapsed:.1f} 秒")
        print("=" * 60)


def main():
    """エントリーポイント"""
    parser = argparse.ArgumentParser(description="ほあんペディア ビルドシステム")
    parser.add_argument("--clean", action="store_true", help="クリーンビルドを実行")
    args = parser.parse_args()
    
    builder = HoanPediaBuilder(clean=args.clean)
    success = builder.build()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
