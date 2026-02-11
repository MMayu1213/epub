# PDF Kindle Optimizer - AIアシスト型ワークフロー強化計画

## 概要
現在のAIアシスト型ワークフローを強化し、左右ページの違いに対応した最適なPDF処理を実現する。ユーザーが開き方を指定し、AIが左右ページそれぞれに最適な余白設定を提案、それに基づいてクロップを実行する。

## 現状のワークフロー
現在のAIアシスト型ワークフローは以下の流れ：
1. ユーザーがプレビュー画像を生成
2. AIにプレビュー画像を見せて余白の切り方を判断してもらう
3. AIの提案に基づいてクロップコマンドを実行

## 課題
現状では左右ページの違いを考慮していないため、すべてのページに同一の余白設定が適用され、最適な結果が得られない。

## 改善計画

### 1. AIアシスト型ワークフローの強化

#### 1.1 開き方情報の追加
ユーザーが開き方（縦開き/横開き）を指定できるようにし、これをプレビュー画像の生成時に含める。

```
pdf-kindle preview input/book.pdf --binding vertical
```

または

```
pdf-kindle preview input/book.pdf --binding horizontal
```

#### 1.2 ページタイプ情報の表示
プレビュー画像生成時に、各ページが左ページか右ページかの情報を明示的に表示する。

```
ページ 1 (右ページ) → output/preview_page1.png
ページ 2 (左ページ) → output/preview_page2.png
```

#### 1.3 AIへの質問フォーマットの改善
AIに対する質問例を改善し、左右ページ別の余白設定を提案してもらうようにする。

```
このPDFの余白を除去するための最適なクロップ位置を左右ページ別に%で教えてください。
- 左ページ: 左からX%、右からY%、上からZ%、下からW%
- 右ページ: 左からA%、右からB%、上からC%、下からD%
```

### 2. プレビュー機能の拡張

#### 2.1 `preview` コマンドの拡張
```python
@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
# 既存のオプション
@click.option(
    '--binding',
    type=click.Choice(['vertical', 'horizontal']),
    default='vertical',
    help='開き方 (vertical=縦開き, horizontal=横開き)'
)
@click.option(
    '--first-page-right',
    is_flag=True,
    default=True,
    help='最初のページを右ページとして扱う（デフォルト）'
)
def preview(input_pdf, output_dir, pages, num_pages, dpi, binding, first_page_right):
    """
    PDFのサンプルページを画像として出力します。
    
    出力された画像をAIに見せて、左右ページ別にどこでカットすべきか判断してもらうために使用します。
    開き方（縦開き/横開き）を指定することで、左右ページ情報が追加されます。
    
    例:
      pdf-kindle preview input/book.pdf --binding vertical           # 縦開きPDF
      pdf-kindle preview input/book.pdf --binding horizontal         # 横開きPDF
    """
```

#### 2.2 ページタイプの判定と表示
```python
# PDFProcessor クラスに追加
def determine_page_type(self, page_idx: int, first_page_is_right: bool = True) -> str:
    """
    ページの種類（左/右）を判定する
    
    Args:
        page_idx: ページインデックス（0始まり）
        first_page_is_right: 最初のページが右ページかどうか
        
    Returns:
        'left' または 'right'
    """
    is_even = (page_idx % 2 == 0)
    
    if first_page_is_right:
        return 'left' if is_even else 'right'
    else:
        return 'right' if is_even else 'left'
```

```python
# preview コマンド内の処理に追加
page_type = processor.determine_page_type(
    page_idx, first_page_is_right=first_page_right
)
page_type_jp = "右ページ" if page_type == "right" else "左ページ"
click.echo(f"✓ ページ {page_num} ({page_type_jp}) → {output_file}")
```

#### 2.3 メタデータの画像への埋め込み
プレビュー画像に直接ページタイプ情報を埋め込む：

```python
# 画像にページタイプ情報を埋め込む
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("Arial.ttf", 24)
text = f"ページ {page_num} ({page_type_jp})"
draw.text((10, 10), text, fill="black", font=font)
```

### 3. クロップコマンドの拡張

#### 3.1 `crop` コマンドの拡張
```python
@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
# 既存のオプション
@click.option(
    '--binding',
    type=click.Choice(['vertical', 'horizontal']),
    default='vertical',
    help='開き方 (vertical=縦開き, horizontal=横開き)'
)
@click.option(
    '--first-page-right',
    is_flag=True,
    default=True,
    help='最初のページを右ページとして扱う（デフォルト）'
)
@click.option(
    '--left-left',
    type=float,
    default=None,
    help='左ページの左からカットする割合（%）'
)
@click.option(
    '--left-right',
    type=float,
    default=None,
    help='左ページの右からカットする割合（%）'
)
@click.option(
    '--left-top',
    type=float,
    default=None,
    help='左ページの上からカットする割合（%）'
)
@click.option(
    '--left-bottom',
    type=float,
    default=None,
    help='左ページの下からカットする割合（%）'
)
@click.option(
    '--right-left',
    type=float,
    default=None,
    help='右ページの左からカットする割合（%）'
)
@click.option(
    '--right-right',
    type=float,
    default=None,
    help='右ページの右からカットする割合（%）'
)
@click.option(
    '--right-top',
    type=float,
    default=None,
    help='右ページの上からカットする割合（%）'
)
@click.option(
    '--right-bottom',
    type=float,
    default=None,
    help='右ページの下からカットする割合（%）'
)
def crop(input_pdf, output, device, left, right, top, bottom, verbose,
         binding, first_page_right, 
         left_left, left_right, left_top, left_bottom,
         right_left, right_right, right_top, right_bottom):
    """
    指定した割合でPDFをクロップします。
    
    AIが提案した左右ページ別のクロップ位置を指定して実行できます。
    左右ページでそれぞれ異なる設定が可能です。
    
    例:
      # 従来の方法（すべてのページに同じ設定）
      pdf-kindle crop input/book.pdf --left 10 --right 15 --top 5 --bottom 5
      
      # 左右ページ別設定
      pdf-kindle crop input/book.pdf --binding vertical --left-left 15 --left-right 5 --right-left 5 --right-right 15
    """
```

#### 3.2 クロップ処理の修正
ページタイプに応じた個別のクロップ設定を適用：

```python
# crop コマンド内の処理を修正
for i in range(total_pages):
    page = src_doc[i]
    rect = page.rect
    
    # ページタイプを判定
    page_type = processor.determine_page_type(i, first_page_is_right=first_page_right)
    
    # ページタイプに応じたクロップ設定を適用
    if page_type == 'left' and all(v is not None for v in [left_left, left_right, left_top, left_bottom]):
        # 左ページ用設定を使用
        crop_x0 = rect.x0 + rect.width * (left_left / 100)
        crop_x1 = rect.x1 - rect.width * (left_right / 100)
        crop_y0 = rect.y0 + rect.height * (left_top / 100)
        crop_y1 = rect.y1 - rect.height * (left_bottom / 100)
    elif page_type == 'right' and all(v is not None for v in [right_left, right_right, right_top, right_bottom]):
        # 右ページ用設定を使用
        crop_x0 = rect.x0 + rect.width * (right_left / 100)
        crop_x1 = rect.x1 - rect.width * (right_right / 100)
        crop_y0 = rect.y0 + rect.height * (right_top / 100)
        crop_y1 = rect.y1 - rect.height * (right_bottom / 100)
    else:
        # 従来の共通設定を使用
        crop_x0 = rect.x0 + rect.width * (left / 100)
        crop_x1 = rect.x1 - rect.width * (right / 100)
        crop_y0 = rect.y0 + rect.height * (top / 100)
        crop_y1 = rect.y1 - rect.height * (bottom / 100)
    
    crop_rect = fitz.Rect(crop_x0, crop_y0, crop_x1, crop_y1)
    
    # 以下は既存の処理と同様
```

### 4. ドキュメント（README.md）の更新

READMEに左右ページ対応のワークフローを追加：

```markdown
## 左右ページ対応ワークフロー

縦開きや横開きの書籍PDFでは、左右ページで余白の特性が異なります。
本ツールは左右ページを区別した最適な処理に対応しています。

### 基本的な使い方

1. 開き方を指定してプレビュー画像を生成
   ```
   pdf-kindle preview input/book.pdf --binding vertical
   ```

2. AIに左右ページ別の最適なクロップ位置を判断してもらう
   - 生成された画像をAIに見せて、以下のように質問してください:
   ```
   このPDFの余白を除去するための最適なクロップ位置を左右ページ別に%で教えてください。
   - 左ページ: 左からX%、右からY%、上からZ%、下からW%
   - 右ページ: 左からA%、右からB%、上からC%、下からD%
   ```

3. AIの提案に基づいて左右ページ別のクロップを実行
   ```
   pdf-kindle crop input/book.pdf --binding vertical \
     --left-left 15 --left-right 5 --left-top 5 --left-bottom 5 \
     --right-left 5 --right-right 15 --right-top 5 --right-bottom 5
   ```
```

### 5. AIプロンプト（.roo）の改善

.rooファイルに左右ページ対応の質問と回答例を追加：

```
## 左右ページ別の余白除去

【質問例】
「このPDF画像を見て、左右ページ別の最適なクロップ位置を%で教えてください。」

【回答例】
PDFのプレビュー画像を分析しました。縦開きの書籍PDFで、左右ページで余白パターンが異なります。

最適なクロップ設定は:

**左ページ**:
- 左から: 15%（ページ外側の余白が大きい）
- 右から: 5%（本の綴じ側は余白が小さい）
- 上から: 5%
- 下から: 5%

**右ページ**:
- 左から: 5%（本の綴じ側は余白が小さい）
- 右から: 15%（ページ外側の余白が大きい）
- 上から: 5%
- 下から: 5%

次のコマンドで処理できます:
```
pdf-kindle crop input/book.pdf --binding vertical \
  --left-left 15 --left-right 5 --left-top 5 --left-bottom 5 \
  --right-left 5 --right-right 15 --right-top 5 --right-bottom 5
```

これにより、Kindle画面でより多くのコンテンツが表示され、読みやすさが向上します。
```

## 実装ステップ

1. ページタイプ判定機能の実装
2. プレビュー機能の拡張
3. クロップコマンドの拡張
4. ドキュメント類の更新

## メリット

1. **ページに応じた最適化**
   - 左右ページそれぞれに最適な余白設定を適用できる
   - 綴じ側と外側で異なる余白特性に対応

2. **AIアシストの活用**
   - AIの画像認識能力を活かした余白判断
   - 左右ページの違いをAIが認識し最適な提案を得られる

3. **使いやすさの維持**
   - 従来のシンプルなワークフローを維持しつつ機能を拡張
   - 単一設定と左右別設定の両方に対応