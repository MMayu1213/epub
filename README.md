# PDF Kindle Optimizer

縦書きPDFの余白を自動検出・除去し、Kindle端末で見やすく最適化するCLIツールです。

## 特徴

- **AI支援クロップ**: プレビュー画像を生成し、AIアシスタント（Claude等）と協力して最適なクロップ位置を決定
- **左右ページ別設定**: 縦開き（右綴じ）・横開き（左綴じ）に対応、左右ページで異なる余白設定が可能
- **自動検出モード**: テキスト位置からコンテンツ領域を自動検出
- **スキャンPDF対応**: 画像ベースのPDFでも二値化+連結成分分析で文字領域を検出
- **複数デバイス対応**: Kindle Paperwhite, Oasis, Basic, Scribe のプロファイルを内蔵

## インストール

```bash
git clone https://github.com/yourusername/pdf-kindle-optimizer.git
cd pdf-kindle-optimizer
pip install -e .
```

## クイックスタート

### 1. PDFファイルを配置

```bash
cp your-book.pdf input/
```

### 2. プレビュー画像を生成

```bash
pdf-kindle preview input/your-book.pdf
```

`preview/` フォルダにサンプルページ画像が出力されます。

### 3. クロップを実行

```bash
# 全ページ共通設定
pdf-kindle crop input/your-book.pdf --left 10 --right 10 --top 5 --bottom 5

# 左右ページ別設定（縦開きの場合）
pdf-kindle crop input/your-book.pdf --binding vertical \
  --left-left 15 --left-right 5 --left-top 5 --left-bottom 5 \
  --right-left 5 --right-right 15 --right-top 5 --right-bottom 5
```

`output/` フォルダに最適化されたPDFが出力されます。

> **Note**: cropコマンド完了時にpreviewフォルダは自動でクリーンアップされます。

---

## コマンドリファレンス

### preview - プレビュー画像生成

PDFのサンプルページを画像として出力します。

```bash
pdf-kindle preview input/book.pdf                    # ランダムに5ページ選択
pdf-kindle preview input/book.pdf --binding vertical # 縦開き（左右ページ情報付き）
pdf-kindle preview input/book.pdf -p 1,10,20,50      # 特定ページを出力
pdf-kindle preview input/book.pdf --dpi 300          # 高解像度で出力
pdf-kindle preview input/book.pdf -n 10              # ランダムに10ページ出力
```

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output-dir` | 出力フォルダ | `preview` |
| `-p, --pages` | 出力ページ番号（カンマ区切り） | ランダム選択 |
| `-n, --num-pages` | ランダム選択数 | `5` |
| `--dpi` | 画像解像度 | `150` |
| `--binding` | 開き方 (`vertical`/`horizontal`) | `vertical` |
| `--first-page-right` | 最初のページを右ページとして扱う | オン |

### crop - 手動クロップ

指定した割合でPDFをクロップします。

```bash
# 全ページ共通設定
pdf-kindle crop input/book.pdf --left 10 --right 10 --top 5 --bottom 5

# 左右ページ別設定
pdf-kindle crop input/book.pdf --binding vertical \
  --left-left 15 --left-right 5 --left-top 5 --left-bottom 5 \
  --right-left 5 --right-right 15 --right-top 5 --right-bottom 5
```

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output` | 出力ファイルパス | `output/{name}_kindle.pdf` |
| `-d, --device` | Kindleデバイス種類 | `paperwhite` |
| `--left`, `--right`, `--top`, `--bottom` | 各辺からカット（%）- 全ページ共通 | `0` |
| `--binding` | 開き方 (`vertical`/`horizontal`) | `vertical` |
| `--left-*`, `--right-*` | 左右ページ別設定（%） | - |
| `--clean-preview` | 処理完了後にpreviewをクリーンアップ | オン |
| `-v, --verbose` | 詳細出力 | オフ |

### auto - 自動検出クロップ

テキスト位置からコンテンツ領域を自動検出してクロップします。

```bash
# 通常PDF
pdf-kindle auto input/book.pdf

# スキャンPDF（Otsu法で自動閾値）
pdf-kindle auto --scan --auto-threshold -m 0 input/book.pdf

# inputフォルダの全PDFを一括処理
pdf-kindle auto
```

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output` | 出力ファイルパス | `output/{name}_kindle.pdf` |
| `-d, --device` | Kindleデバイス種類 | `paperwhite` |
| `-t, --threshold` | 余白検出の閾値 (0-255) | `250` |
| `-m, --margin` | 追加マージン (割合) | `0.005` |
| `--no-uniform` | ページ個別クロップ | 統一クロップ |
| `--scan` | スキャンPDF用モード | オフ |
| `--auto-threshold` | Otsu法で自動閾値 | オフ |
| `-v, --verbose` | 詳細出力 | オフ |

### reorder - ページ順序修正

見開きPDF分割後のページ順序を修正します。

```bash
pdf-kindle reorder input/book.pdf
```

2,1,4,3,6,5... → 1,2,3,4,5,6... のように並び替えます。

### clean - プレビュークリーンアップ

previewフォルダ内の画像ファイルを削除します。

```bash
pdf-kindle clean
```

---

## フォルダ構成

```
pdf-kindle-optimizer/
├── input/          # PDFファイルを配置
├── output/         # 処理済みファイルが出力される
├── preview/        # プレビュー画像が出力される（自動クリーンアップ）
└── pdf_kindle_optimizer/
    ├── __init__.py
    ├── cli.py      # CLIコマンド
    └── core.py     # コア処理
```

---

## 対応Kindleデバイス

| デバイス | 解像度 | アスペクト比 | オプション |
|----------|--------|--------------|------------|
| Kindle Paperwhite | 1236 x 1648 | 約 0.75 | `-d paperwhite`（デフォルト）|
| Kindle Oasis | 1264 x 1680 | 約 0.75 | `-d oasis` |
| Kindle Basic | 1072 x 1448 | 約 0.74 | `-d basic` |
| Kindle Scribe | 1860 x 2480 | 約 0.75 | `-d scribe` |

> **Tip**: クロップ後のコンテンツがKindle画面を最大限活用できるよう、アスペクト比（約0.75）を意識してクロップ位置を決定すると、より読みやすい表示になります。

---

## Pythonライブラリとして使用

```python
from pdf_kindle_optimizer import PDFProcessor, KindleOptimizer

with PDFProcessor("input.pdf") as processor:
    print(f"ページ数: {processor.page_count}")
    
    optimizer = KindleOptimizer(processor)
    optimizer.optimize_for_kindle(
        output_path="output.pdf",
        device="paperwhite",
        uniform_crop=True,
        margin_percent=0.02
    )
```

---

## トラブルシューティング

### 余白が残る場合
- `--margin` を減らす（例: `-m 0`）
- 手動で `crop` コマンドを使用

### 文字が切れる場合
- `--margin` を増やす（例: `-m 0.05`）

### スキャンPDFで検出がうまくいかない場合
- `--threshold` 値を調整
  - 文字が薄い: `-t 230`
  - 余白が残る: `-t 252`

### コマンドが見つからない場合
```bash
pip install -e .
```

---

## 動作要件

- Python 3.8以上
- PyMuPDF 1.23.0以上
- Pillow 9.0.0以上
- NumPy 1.20.0以上
- SciPy 1.10.0以上
- Click 8.0.0以上

---

## ライセンス

MIT License
