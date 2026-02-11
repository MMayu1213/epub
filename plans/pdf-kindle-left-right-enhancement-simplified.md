# PDF Kindle Optimizerの開き方対応拡張計画（簡易版）

## 概要
PDFの開き方（縦開き/横開き）を指定するだけで、左右ページの余白特性に応じた最適なクロップ処理を自動的に行う機能を実装する。

## 現状の課題
現在のPDF Kindle Optimizerは、すべてのページに対して均一の余白除去ロジックを適用しています。しかし実際の書籍PDFでは開き方によって左右ページで余白の特性が異なります：

- **縦開き**：
  - 右ページ：右側の余白が大きい（外側）
  - 左ページ：左側の余白が大きい（外側）

- **横開き**：
  - 左ページ：上側の余白が大きい（外側）
  - 右ページ：下側の余白が大きい（外側）

## 簡易実装計画

### 1. 左右ページを判定する機能の追加

```python
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

### 2. 開き方に基づいた自動余白処理の実装

開き方に応じて、左右ページそれぞれに適切な余白処理パラメータを自動的に適用します：

```python
def get_page_crop_settings(self, page_type: str, binding: str, base_settings: dict) -> dict:
    """
    ページタイプと開き方に基づいて適切なクロップ設定を返す
    
    Args:
        page_type: ページタイプ ('left' または 'right')
        binding: 開き方 ('vertical'=縦開き, 'horizontal'=横開き)
        base_settings: 基本クロップ設定 (%)
        
    Returns:
        調整されたクロップ設定 (%)
    """
    settings = base_settings.copy()
    
    # 縦開きの場合
    if binding == 'vertical':
        if page_type == 'right':
            # 右ページ: 右側の余白を多めに
            settings['right'] = max(settings['right'], 15)
        else:  # left
            # 左ページ: 左側の余白を多めに
            settings['left'] = max(settings['left'], 15)
    
    # 横開きの場合
    elif binding == 'horizontal':
        if page_type == 'left':
            # 左ページ: 上側の余白を多めに
            settings['top'] = max(settings['top'], 15)
        else:  # right
            # 右ページ: 下側の余白を多めに
            settings['bottom'] = max(settings['bottom'], 15)
    
    return settings
```

### 3. シンプルなユーザーインターフェース（CLI）

```python
@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
# 既存のオプション...
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
    '--page-aware',
    is_flag=True,
    default=True,
    help='左右ページに応じた最適化を行う（デフォルト）'
)
def crop(input_pdf, output, device, left, right, top, bottom, verbose,
         binding, first_page_right, page_aware):
    """
    指定した割合でPDFをクロップします。
    
    開き方（縦開き/横開き）を指定すると、左右ページに応じた最適なクロップを自動的に適用します。
    
    例:
      pdf-kindle crop input/book.pdf --left 10 --right 15 --top 5 --bottom 5 --binding vertical
    """
    # 実装詳細
```

同様に `auto` コマンドも拡張：

```python
@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True), required=False)
# 既存のオプション...
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
    '--page-aware',
    is_flag=True,
    default=True,
    help='左右ページに応じた最適化を行う（デフォルト）'
)
def auto(input_pdf, output, device, threshold, margin, no_uniform, verbose,
          input_dir, output_dir, scan, edge_threshold, min_char_size, max_char_size, 
          auto_threshold, binding, first_page_right, page_aware):
    """
    自動検出でPDFの余白を除去します。
    
    開き方（縦開き/横開き）を指定すると、左右ページに応じた最適なクロップを自動的に適用します。
    
    例:
      pdf-kindle auto input/book.pdf --binding vertical
      pdf-kindle auto --binding horizontal  # inputフォルダの全PDFを処理
    """
```

### 4. 自動検出機能の強化（オプション）

必要に応じて、PDFの内容から開き方を自動判定する機能を追加できます：

```python
def auto_detect_binding(self) -> str:
    """
    PDFの内容から開き方（縦開き/横開き）を自動判定
    
    Returns:
        'vertical'（縦開き）または'horizontal'（横開き）
    """
    # 実装詳細（縦書きテキストの検出など）
```

### 5. 処理フローの修正

`KindleOptimizer` クラスの `optimize_for_kindle` メソッドを修正して、ページタイプに応じた処理を組み込みます：

```python
def optimize_for_kindle(
    self,
    output_path: str,
    device: str = 'paperwhite',
    binding: str = 'vertical',
    first_page_right: bool = True,
    page_aware: bool = True,
    # 他の既存パラメータ
):
    """
    Kindle向けに最適化して保存（開き方に応じた左右ページ最適化対応）
    
    Args:
        output_path: 出力ファイルパス
        device: Kindleデバイス種類
        binding: 開き方 ('vertical'=縦開き, 'horizontal'=横開き)
        first_page_right: 最初のページが右ページかどうか
        page_aware: 左右ページに応じた最適化を行うか
        # 他の既存パラメータ
    """
    # 実装詳細
```

## メリット

1. **シンプルなユーザーインターフェース**
   - 開き方を指定するだけで適切な処理が行われる
   - 複雑なパラメータ設定が不要

2. **自動的な最適化**
   - 左右ページの特性に応じた処理が自動的に行われる
   - ユーザーが個別にクロップ設定を考える必要がない

3. **既存コードとの互換性維持**
   - 従来の均一処理もオプションで維持
   - 既存ユーザーへの影響を最小化

## 実装ステップ

1. ページタイプ判定機能の実装
2. 開き方に基づく最適化処理の追加
3. CLIインターフェースの拡張
4. テストとチューニング

## 将来の拡張可能性

1. 開き方の自動検出機能
2. より高度な余白パターン分析
3. マンガや雑誌などの特殊なレイアウト対応