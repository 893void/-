# ほあんペディア 機器ページ配置指示書

対象：antigravity  
作成日：2026年1月15日

---

## 概要

Claude Opusが作成した機器ページのMarkdownファイルを、プロジェクトに配置してください。

---

## 配置先

すべてのファイルを以下のディレクトリに配置：

```
hoan-pedia/content/equipment/
```

---

## 配置するファイル一覧

| ファイル名 | 内容 | 配置先 |
|-----------|------|--------|
| `_index.md` | 機器ページ目次（更新版） | `content/equipment/_index.md` |
| `transformer.md` | 変圧器 | `content/equipment/transformer.md` |
| `vcb.md` | VCB（真空遮断器） | `content/equipment/vcb.md` |
| `pas.md` | PAS（高圧気中開閉器） | `content/equipment/pas.md` |
| `lbs.md` | LBS（高圧負荷開閉器） | `content/equipment/lbs.md` |
| `ds.md` | DS（断路器） | `content/equipment/ds.md` |
| `ct.md` | CT（変流器） | `content/equipment/ct.md` |
| `vt.md` | VT（計器用変圧器） | `content/equipment/vt.md` |
| `zct.md` | ZCT（零相変流器） | `content/equipment/zct.md` |
| `zpd.md` | ZPD（零相電圧検出器） | `content/equipment/zpd.md` |
| `la.md` | LA（避雷器） | `content/equipment/la.md` |
| `sc.md` | SC（進相コンデンサ） | `content/equipment/sc.md` |
| `vct.md` | VCT（計器用変成器） | `content/equipment/vct.md` |

合計：13ファイル

---

## 配置後の作業

1. `python build.py` を実行してHTMLを生成
2. ブラウザで動作確認
3. 各ページのリンクが正常に動作するか確認

---

## 確認ポイント

- [ ] `equipment/` 配下に13ファイルが配置されているか
- [ ] `build.py` が正常に完了するか
- [ ] 機器一覧ページ（`equipment/index.html`）が表示されるか
- [ ] 各機器ページが表示されるか
- [ ] ページ間のリンクが正常に動作するか
- [ ] 保護継電器ページ（`relay/`）へのリンクが動作するか

---

## 注意事項

- `_index.md` は既存ファイルを **上書き** する（更新版）
- その他のファイルは **新規追加**
- build.py が equipment/ フォルダを処理できることを確認

---

## フォルダ構成（配置後）

```
hoan-pedia/
└── content/
    ├── relay/              # 保護継電器（既存）
    ├── equipment/          # 機器ページ ← ここに配置
    │   ├── _index.md       # 目次
    │   ├── transformer.md  # 変圧器
    │   ├── vcb.md          # VCB
    │   ├── pas.md          # PAS
    │   ├── lbs.md          # LBS
    │   ├── ds.md           # DS
    │   ├── ct.md           # CT
    │   ├── vt.md           # VT
    │   ├── zct.md          # ZCT
    │   ├── zpd.md          # ZPD
    │   ├── la.md           # LA
    │   ├── sc.md           # SC
    │   └── vct.md          # VCT
    ├── sld/                # 単線結線図（既に配置済み）
    ├── guide/              # 学習ガイド（既に配置済み）
    └── standards/          # 法令（既存）
```

---

**配置指示書 終了**
