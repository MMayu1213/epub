# PDF Kindle Optimizer

縦書きPDFの余白を自動検出・除去し、Kindle端末で見やすく最適化するツールです。

## AI アシスタント向けクイックガイド

このツールはAIアシスタント（Claude、ChatGPT等）と一緒に使うことを想定しています。
AIにPDFファイルを処理してもらう場合は、以下のように依頼してください。

### 使い方の例

```
「input/にあるPDFをKindle用に最適化して」
「このPDFの余白を除去して」
「スキャンPDFをKindle Paperwhiteで読みやすくして」
```

AIアシスタントが自動でコマンドを実行し、最適化されたPDFを `output/` フォルダに出力します。

---

## フォルダ構成

```
epub/
├── input/          # ← PDFファイルをここに配置
├── output/         # ← 処理済みファイルがここに出力される
├── preview/        # ← プレビュー画像が出力される
└── pdf_kindle_optimizer/
```

## セットアップ

```bash
pip install -e .
```

---

## AI アシスタント向け実行ガイド

### ワークフロー1: AI支援クロップ（推奨）

AIがプレビュー画像を確認してクロップ位置を判断するワークフローです。

**ステップ1: PDFファイルを確認**
```bash
ls input/
```

**ステップ2: プレビュー画像を生成**
```bash
pdf-kindle preview input/[ファイル名].pdf
```
→ `preview/` フォルダにサンプルページ画像が出力されます

**ステップ3: 画像を確認してクロップ位置を判断（Kindleサイズを考慮）**
出力された画像を確認し、余白をどれだけ除去すべきか判断します。

> **重要**: Kindleデバイスのアスペクト比（約0.75）を考慮してクロップ位置を決定してください。
> - コンテンツが縦長すぎる場合（比率 < 0.75）→ 上下を多めにカット
> - コンテンツが横長すぎる場合（比率 > 0.75）→ 左右を多めにカット

**ステップ4: クロップを実行**
```bash
pdf-kindle crop input/[ファイル名].pdf --left [X] --right [Y] --top [Z] --bottom [W]
```
→ `output/[ファイル名]_kindle.pdf` が生成されます

---

### ワークフロー2: 自動検出クロップ

テキスト位置からコンテンツ領域を自動検出します。

**単一ファイル処理:**
```bash
pdf-kindle auto input/[ファイル名].pdf
```

**inputフォルダ全体を一括処理:**
```bash
pdf-kindle auto
```

---

### ワークフロー3: スキャンPDF処理

画像ベースのPDF（テキストが埋め込まれていない）の場合：

```bash
pdf-kindle auto --scan --auto-threshold -m 0 input/[ファイル名].pdf
```

---

## コマンドリファレンス

### preview - プレビュー画像生成

```bash
pdf-kindle preview input/book.pdf
pdf-kindle preview input/book.pdf -p 1,10,20,50    # 特定ページを出力
pdf-kindle preview input/book.pdf --dpi 300        # 高解像度で出力
pdf-kindle preview input/book.pdf -n 10            # ランダムに10ページ出力
```

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output-dir` | 出力フォルダ | `preview` |
| `-p, --pages` | 出力ページ番号（カンマ区切り） | `1,5,10` |
| `-n, --num-pages` | ランダム選択数 | - |
| `--dpi` | 画像解像度 | `150` |

---

### crop - 手動クロップ

```bash
pdf-kindle crop input/book.pdf --left 10 --right 10 --top 5 --bottom 5
```

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output` | 出力ファイルパス | `output/{ファイル名}_kindle.pdf` |
| `-d, --device` | Kindleデバイス種類 | `paperwhite` |
| `--left` | 左からカット（%） | `0` |
| `--right` | 右からカット（%） | `0` |
| `--top` | 上からカット（%） | `0` |
| `--bottom` | 下からカット（%） | `0` |
| `-v, --verbose` | 詳細出力 | オフ |

---

### auto - 自動検出クロップ

```bash
# 通常PDF
pdf-kindle auto input/book.pdf

# スキャンPDF（Otsu法で自動閾値）
pdf-kindle auto --scan --auto-threshold -m 0 input/book.pdf

# 閾値を手動指定
pdf-kindle auto -t 230 input/book.pdf
```

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `-o, --output` | 出力ファイルパス | `output/{ファイル名}_kindle.pdf` |
| `-d, --device` | Kindleデバイス種類 | `paperwhite` |
| `-t, --threshold` | 余白検出の閾値 (0-255) | `250` |
| `-m, --margin` | 追加マージン (割合) | `0.005` |
| `--no-uniform` | ページ個別クロップ | 統一クロップ |
| `--scan` | スキャンPDF用モード | オフ |
| `--auto-threshold` | Otsu法で自動閾値 | オフ |
| `-i, --input-dir` | 入力フォルダ | `input` |
| `--output-dir` | 出力フォルダ | `output` |
| `-v, --verbose` | 詳細出力 | オフ |

---

## 対応Kindleデバイス

| デバイス | 解像度 | アスペクト比 | オプション |
|----------|--------|--------------|------------|
| Kindle Paperwhite | 1236 x 1648 | 約 0.75 | `-d paperwhite`（デフォルト）|
| Kindle Oasis | 1264 x 1680 | 約 0.75 | `-d oasis` |
| Kindle Basic | 1072 x 1448 | 約 0.74 | `-d basic` |
| Kindle Scribe | 1860 x 2480 | 約 0.75 | `-d scribe` |

> **ヒント**: クロップ後のコンテンツがKindle画面を最大限活用できるよう、アスペクト比（約0.75）を意識してクロップ位置を決定すると、より読みやすい表示になります。

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
        threshold=250,
        margin_percent=0.02
    )
```

### エクスポートされるクラス

| クラス | 説明 |
|--------|------|
| `PDFProcessor` | PDF処理のメインクラス |
| `KindleOptimizer` | Kindle向け最適化クラス |
| `CropBox` | クロップ領域を表すデータクラス |
| `PageInfo` | ページ情報を表すデータクラス |

---

## 動作要件

- Python 3.8以上
- PyMuPDF 1.23.0以上
- Pillow 9.0.0以上
- NumPy 1.20.0以上
- SciPy 1.10.0以上
- Click 8.0.0以上

## ライセンス

MIT License
