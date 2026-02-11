# クイックスタートガイド 🚀

## はじめに

PDF Kindle Optimizerは、PDFの余白を除去してKindle端末で読みやすく最適化するツールです。
AIアシスタント（Claude等）と一緒に使うことで、最適なクロップ位置を簡単に決定できます。

---

## セットアップ

```bash
pip install -e .
```

---

## 基本的な使い方

### ステップ1: PDFを配置

処理したいPDFファイルを `input/` フォルダに入れます。

### ステップ2: プレビュー画像を生成

```bash
pdf-kindle preview input/your-book.pdf
```

`preview/` フォルダにサンプルページの画像が出力されます。

### ステップ3: クロップを実行

```bash
pdf-kindle crop input/your-book.pdf --left 10 --right 10 --top 5 --bottom 5
```

`output/` フォルダに最適化されたPDFが出力されます。
処理完了後、previewフォルダは自動でクリーンアップされます。

---

## コマンド一覧

| コマンド | 説明 |
|----------|------|
| `pdf-kindle preview` | プレビュー画像を生成 |
| `pdf-kindle crop` | 指定した割合でクロップ |
| `pdf-kindle auto` | 自動検出でクロップ |
| `pdf-kindle reorder` | ページ順序を修正 |
| `pdf-kindle clean` | previewフォルダをクリーンアップ |

---

## AIアシスタントと使う場合

AIアシスタント（Claude等）に以下のように依頼するだけでOKです：

| やりたいこと | AIへの依頼例 |
|-------------|-------------|
| 余白を除去したい | 「input/にあるPDFの余白を除去して」 |
| プレビューを確認したい | 「まずプレビュー画像を見せて」 |
| スキャンPDFを処理 | 「スキャンPDFなので、それに合わせて処理して」 |
| 一括処理 | 「inputフォルダのPDFを全部処理して」 |

AIがコマンドを実行し、最適化されたPDFを `output/` フォルダに出力します。

---

## フォルダ構成

```
pdf-kindle-optimizer/
├── input/     ← PDFをここに入れる
├── output/    ← 処理済みPDFが出力される
├── preview/   ← プレビュー画像が出力される
└── ...
```

---

## 対応Kindleデバイス

| デバイス | オプション |
|----------|------------|
| Kindle Paperwhite（デフォルト） | `-d paperwhite` |
| Kindle Oasis | `-d oasis` |
| Kindle Basic | `-d basic` |
| Kindle Scribe | `-d scribe` |

---

## トラブルシューティング

### 「コマンドが見つからない」

```bash
pip install -e .
```

### 余白がうまく取れない

- 手動クロップ: `pdf-kindle crop` で値を調整
- 自動検出: `pdf-kindle auto -m 0` でマージンを0に

### スキャンPDFがうまく処理されない

```bash
pdf-kindle auto --scan --auto-threshold input/your-book.pdf
```

---

詳細は [README.md](README.md) を参照してください。
