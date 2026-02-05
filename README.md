# PDF Kindle Optimizer

縦書きPDFの余白を自動検出・除去し、Kindle端末で見やすく最適化するツールです。

## 特徴

- 📄 **自動余白検出**: 各ページのコンテンツ領域を自動で検出
- 🤖 **AI支援クロップ**: AIにページ画像を見せてクロップ位置を判断
- ✂️ **スマートクロップ**: 不要な余白を除去してコンテンツを最大化
- 📱 **Kindle最適化**: 各種Kindleデバイスの画面サイズに合わせて最適化
- 📚 **縦書き対応**: 日本語縦書きPDFに最適化
- 📁 **バッチ処理**: inputフォルダに入れたPDFを一括処理

## フォルダ構成

```
epub/
├── input/          # PDFファイルをここに配置
├── output/         # 処理済みファイルがここに出力
├── preview/        # プレビュー画像が出力される
├── pdf_kindle_optimizer/
│   ├── __init__.py
│   ├── core.py
│   └── cli.py
├── pyproject.toml
└── README.md
```

## 対応Kindleデバイス

- Kindle Paperwhite (1236 x 1648)
- Kindle Oasis (1264 x 1680)
- Kindle Basic (1072 x 1448)
- Kindle Scribe (1860 x 2480)

## インストール

### pipを使用

```bash
pip install -e .
```

### 依存関係のみインストール

```bash
pip install PyMuPDF Pillow numpy click
```

## 使い方

### 🤖 AI支援ワークフロー（推奨）

AIにページ画像を見せてクロップ位置を判断してもらうワークフローです。

#### ステップ1: プレビュー画像を出力

```bash
pdf-kindle preview input/book.pdf
```

これにより `preview/` フォルダにサンプルページの画像が出力されます。

**オプション:**
```bash
# 特定のページを出力
pdf-kindle preview input/book.pdf -p 1,10,20,50

# 高解像度で出力
pdf-kindle preview input/book.pdf --dpi 300
```

#### ステップ2: AIに画像を見せる

出力された画像をClaude等のAIに見せて質問します：

> 「このPDFページ画像を見て、余白を除去するためのクロップ位置を%で教えてください。
> 左からX%、右からY%、上からZ%、下からW%の形式で。」

AIが例えば「左から8%、右から12%、上から5%、下から5%」と回答したとします。

#### ステップ3: AIの提案でクロップ実行

```bash
pdf-kindle crop input/book.pdf --left 8 --right 12 --top 5 --bottom 5
```

これにより `output/book_kindle.pdf` が生成されます。

---

### 自動検出モード

AIを使わず自動でコンテンツ領域を検出する場合：

```bash
# 単一ファイル
pdf-kindle auto input/book.pdf

# inputフォルダの全PDFを一括処理
pdf-kindle auto
```

---

### コマンド一覧

| コマンド | 説明 |
|----------|------|
| `pdf-kindle preview` | サンプルページを画像として出力 |
| `pdf-kindle crop` | 指定した割合でクロップ |
| `pdf-kindle auto` | 自動検出でクロップ |

### previewコマンドのオプション

| オプション | 短縮形 | 説明 | デフォルト |
|------------|--------|------|------------|
| `--output-dir` | `-o` | 出力フォルダ | `preview` |
| `--pages` | `-p` | 出力ページ番号（カンマ区切り） | `1,5,10` |
| `--dpi` | - | 画像解像度 | `150` |

### cropコマンドのオプション

| オプション | 短縮形 | 説明 | デフォルト |
|------------|--------|------|------------|
| `--output` | `-o` | 出力ファイルパス | `output/{ファイル名}_kindle.pdf` |
| `--device` | `-d` | Kindleデバイス種類 | `paperwhite` |
| `--left` | - | 左からカット（%） | `0` |
| `--right` | - | 右からカット（%） | `0` |
| `--top` | - | 上からカット（%） | `0` |
| `--bottom` | - | 下からカット（%） | `0` |
| `--verbose` | `-v` | 詳細出力 | (オフ) |

### autoコマンドのオプション

| オプション | 短縮形 | 説明 | デフォルト |
|------------|--------|------|------------|
| `--output` | `-o` | 出力ファイルパス | `output/{ファイル名}_kindle.pdf` |
| `--device` | `-d` | Kindleデバイス種類 | `paperwhite` |
| `--threshold` | `-t` | 余白検出の閾値 (0-255) | `250` |
| `--margin` | `-m` | 追加マージン (割合) | `0.005` |
| `--no-uniform` | - | ページ個別クロップ | (統一クロップ) |
| `--verbose` | `-v` | 詳細出力 | (オフ) |
| `--input-dir` | `-i` | 入力フォルダ | `input` |
| `--output-dir` | - | 出力フォルダ | `output` |
| `--scan` | - | スキャンPDF用モード | (オフ) |
| `--auto-threshold` | - | Otsu法で自動閾値 | (オフ) |

## Pythonライブラリとして使用

```python
from pdf_kindle_optimizer import PDFProcessor, KindleOptimizer

# PDFを処理
with PDFProcessor("input.pdf") as processor:
    print(f"ページ数: {processor.page_count}")
    
    # Kindle向けに最適化
    optimizer = KindleOptimizer(processor)
    optimizer.optimize_for_kindle(
        output_path="output.pdf",
        device="paperwhite",
        uniform_crop=True,
        threshold=250,
        margin_percent=0.02
    )
```

### 詳細な制御

```python
from pdf_kindle_optimizer import PDFProcessor

with PDFProcessor("input.pdf") as processor:
    # 全ページを分析
    page_infos = processor.analyze_all_pages(
        threshold=250,
        margin_percent=0.02
    )
    
    # 各ページの情報を確認
    for info in page_infos:
        print(f"ページ {info.page_number + 1}:")
        print(f"  元サイズ: {info.original_size}")
        print(f"  クロップ領域: {info.crop_box}")
        print(f"  コンテンツ比率: {info.content_ratio:.1%}")
    
    # 統一クロップ領域を取得
    uniform_box = processor.get_uniform_crop_box()
    print(f"統一クロップ領域: {uniform_box}")
    
    # カスタム設定で保存
    processor.crop_and_save(
        output_path="output.pdf",
        uniform_crop=True
    )
```

## ヒント

### AI支援モードのコツ

1. **複数ページを確認**: ページによって余白が異なる場合があるので、複数ページの画像をAIに見せる
2. **見開きページに注意**: 見開きの左右で余白が異なる場合は、それぞれ別に処理するか平均値を使う
3. **少し余裕を持たせる**: AIの提案より1-2%少なめにカットすると安全

### 余白がうまく検出されない場合（autoモード）

1. **文字が薄い場合**: `--threshold` を下げてみてください（例: `-t 230`）
2. **余白が残りすぎる場合**: `--threshold` を上げてみてください（例: `-t 252`）
3. **文字が切れる場合**: `--margin` を増やしてください（例: `-m 0.05`）

### スキャンPDFの場合

スキャンPDF（画像ベース）の場合は `--scan` オプションを使用してください：

```bash
# 基本的な使用法（Otsu法で自動閾値決定）
pdf-kindle auto --scan --auto-threshold -m 0

# 二値化閾値を手動で指定
pdf-kindle auto --scan -t 200 -m 0
```

### 統一クロップ vs 個別クロップ

- **統一クロップ（デフォルト）**: 全ページで同じ領域をクロップ。ページ送り時の位置ずれが少ない
- **個別クロップ**: ページごとに最適なクロップ。余白が完全に除去される

## 動作要件

- Python 3.8以上
- PyMuPDF 1.23.0以上
- Pillow 9.0.0以上
- NumPy 1.20.0以上
- Click 8.0.0以上

## ライセンス

MIT License
