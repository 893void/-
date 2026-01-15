# -*- coding: utf-8 -*-
"""
テンプレートエンジン
HTMLテンプレートの変数置換とレンダリングを担当
"""
import os
import re
from pathlib import Path
from datetime import datetime


class TemplateEngine:
    """シンプルなテンプレートエンジン"""
    
    def __init__(self, templates_dir, site_config=None):
        self.templates_dir = Path(templates_dir)
        self.site_config = site_config or {}
        self.templates = {}
    
    def load_all(self):
        """全テンプレートを読み込む"""
        if not self.templates_dir.exists():
            return 0
        
        for html_file in self.templates_dir.glob("*.html"):
            template_name = html_file.stem
            with open(html_file, "r", encoding="utf-8") as f:
                self.templates[template_name] = f.read()
        
        return len(self.templates)
    
    def render(self, template_name, context=None):
        """テンプレートをレンダリング"""
        context = context or {}
        
        # テンプレートが存在しない場合はデフォルトを使用
        if template_name not in self.templates:
            if "base" in self.templates:
                template_name = "base"
            else:
                # テンプレートがない場合はコンテンツをそのまま返す
                return context.get("content", "")
        
        template = self.templates[template_name]
        
        # テンプレート継承の処理
        template = self._process_extends(template)
        
        # 変数を展開
        html = self._replace_variables(template, context)
        
        return html
    
    def _process_extends(self, template):
        """テンプレート継承を処理"""
        # {{extends base.html}} パターンを検出
        extends_match = re.search(r'\{\{extends\s+(\w+)\.html\}\}', template)
        
        if not extends_match:
            return template
        
        parent_name = extends_match.group(1)
        
        if parent_name not in self.templates:
            # 継承元がない場合はそのまま
            return template
        
        parent_template = self.templates[parent_name]
        
        # {{block content}}...{{endblock}} を抽出
        block_match = re.search(
            r'\{\{block\s+content\}\}(.*?)\{\{endblock\}\}',
            template,
            re.DOTALL
        )
        
        if block_match:
            block_content = block_match.group(1).strip()
            # 親テンプレートの {{content}} を置換
            return parent_template.replace("{{content}}", block_content)
        
        return parent_template
    
    def _replace_variables(self, template, context):
        """テンプレート変数を置換"""
        # サイト設定の変数
        site_vars = {
            "site_name": self.site_config.get("site_name", "ほあんペディア"),
            "site_description": self.site_config.get("description", ""),
            "current_year": str(datetime.now().year),
        }
        
        # コンテキスト変数とマージ
        all_vars = {**site_vars, **context}
        
        # 特殊パス変数は後で処理するのでスキップ
        special_vars = {"css_path", "home_path"}
        
        # {{変数名}} パターンを置換
        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name in special_vars:
                return match.group(0)  # そのまま残す
            return str(all_vars.get(var_name, ""))
        
        result = re.sub(r'\{\{(\w+)\}\}', replace_var, template)
        
        # CSSパスの自動調整（特殊変数を処理）
        result = self._adjust_paths(result, context)
        
        return result
    
    def _adjust_paths(self, html, context):
        """相対パスを調整"""
        # {{css_path}} を適切な相対パスに置換
        depth = context.get("depth", 0)
        prefix = "../" * depth if depth > 0 else ""
        
        html = html.replace("{{css_path}}", f"{prefix}css/style.css")
        html = html.replace("{{home_path}}", f"{prefix}index.html")
        
        return html
