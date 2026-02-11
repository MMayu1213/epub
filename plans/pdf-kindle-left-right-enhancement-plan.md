# PDF Kindle Optimizerの左右ページ対応拡張計画

## 概要
PDFの左右ページ（綴じ方向に依存する余白の違い）に応じた最適なクロップ処理を実装し、より良いKindle向け最適化を実現する。

## 現状分析
現在のPDF Kindle Optimizerは、すべてのページに対して同一の余白除去ロジックを適用しています。しかし、実際の書籍PDFでは左右ページで余白の特性が異なります：

- **縦開きの場合**：右ページは右側の余白が大きく、左ページは左側の余白が大きい
- **横開きの場合**：左ページは上側の余白が大きく、右ページは下側の余白が大きい

これにより、すべてのページに同じクロップ設定を適用すると、片側のページで過剰にクロップされたり、逆に余白が残ってしまう問題があります。

## 詳細実装計画

### 1. 左右ページを判定する機能の追加

#### 1.1 ページ位置判定ロジック
- 基本的にはページ番号の偶数/奇数で左右を判定
- 綴じ方向（縦開き/横開き）の設定に基づいて左右判定を調整
- 開始ページが左か右かの設定をサポート（デフォルトは右始まり）

#### 1.2 判定機能の実装箇所
`PDFProcessor`クラスに以下のメソッドを追加:
```python
def determine_page_type(self, page_idx: int, binding: str = 'vertical', 
                        first_page_is_right: bool = True) -> str:
    """
    ページの種類（左/右）を判定する
    
    Args:
        page_idx: ページインデックス（0始まり）
        binding: 綴じ方向 ('vertical'=縦開き, 'horizontal'=横開き)
        first_page_is_right: 最初のページが右ページかどうか
        
    Returns:
        'left' または 'right'
    """
    # 最初のページが右ページの場合、偶数ページは左、奇数ページは右
    # 最初のページが左ページの場合、偶数ページは右、奇数ページは左
    is_even = (page_idx % 2 == 0)
    
    if first_page_is_right:
        return 'left' if is_even else 'right'
    else:
        return 'right' if is_even else 'left'
```

#### 1.3 `PageInfo` クラスの拡張
```python
@dataclass
class PageInfo:
    """ページ情報を表すデータクラス"""
    page_number: int
    original_size: Tuple[float, float]
    crop_box: CropBox
    content_ratio: float  # コンテンツ領域の割合
    page_type: str = 'unknown'  # 'left', 'right', 'unknown'
```

### 2. ページタイプに基づいた異なるクロップ設定を適用する仕組みの実装

#### 2.1 クロップ設定の分離
- 左ページと右ページで個別のクロップパラメータを適用できるよう拡張
- 統一クロップの場合でも左右ページでパラメータを分離

#### 2.2 `CropSettings` クラスの追加
```python
@dataclass
class CropSettings:
    """クロップ設定を表すデータクラス"""
    left_margin: float = 0.0  # 左からのマージン(%)
    right_margin: float = 0.0  # 右からのマージン(%)
    top_margin: float = 0.0  # 上からのマージン(%)
    bottom_margin: float = 0.0  # 下からのマージン(%)
    
    @classmethod
    def from_percent(cls, left: float, right: float, top: float, bottom: float):
        """パーセント値からインスタンスを作成"""
        return cls(left, right, top, bottom)
```

#### 2.3 クロップ処理の拡張
`crop_and_save` メソッドを修正して左右ページで異なる設定を適用:
```python
def crop_and_save(
    self,
    output_path: str,
    left_page_settings: CropSettings,
    right_page_settings: CropSettings,
    binding: str = 'vertical',
    first_page_is_right: bool = True,
    uniform_crop: bool = True,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    progress_callback=None
):
    """
    PDFをクロップして保存（左右ページで異なる設定を適用）
    
    Args:
        output_path: 出力ファイルパス
        left_page_settings: 左ページのクロップ設定
        right_page_settings: 右ページのクロップ設定
        binding: 綴じ方向 ('vertical'=縦開き, 'horizontal'=横開き)
        first_page_is_right: 最初のページが右ページかどうか
        uniform_crop: 全ページで統一したクロップを使用するか
        target_width: 目標幅（ピクセル）
        target_height: 目標高さ（ピクセル）
        progress_callback: 進捗コールバック関数
    """
    # 実装詳細
```

### 3. ユーザーインターフェース（CLI）の拡張

#### 3.1 `crop` コマンドの拡張
```python
@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
# 既存のオプション...
@click.option(
    '--binding',
    type=click.Choice(['vertical', 'horizontal']),
    default='vertical',
    help='綴じ方向 (vertical=縦開き, horizontal=横開き)'
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
    
    AIが提案したクロップ位置を指定して実行します。
    左右ページで異なるクロップ設定が可能です。
    
    例:
      pdf-kindle crop input/book.pdf --left 10 --right 15 --top 5 --bottom 5
      
    左右ページ個別設定の例:
      pdf-kindle crop input/book.pdf --binding vertical --left-left 20 --left-right 5 --right-left 5 --right-right 20
    """
    # 実装詳細
```

#### 3.2 `auto` コマンドの拡張
- 綴じ方向と左右ページ検出のオプション追加
- 左右ページで個別の余白検出をサポート

#### 3.3 `preview` コマンドの拡張
- ページタイプ（左/右）の表示追加
- AIへの質問例に左右ページの区別を追加

### 4. 自動検出機能の強化

#### 4.1 左右ページの自動判別
- テキスト位置からページタイプを推定する機能
- 余白パターンによる左右ページのクラスタリング
- 適切なアルゴリズムの選択

#### 4.2 実装案
```python
def auto_detect_binding_and_page_types(self):
    """
    PDFの綴じ方向と左右ページパターンを自動検出
    
    Returns:
        (binding, first_page_is_right): 綴じ方向と最初のページが右ページかどうか
    """
    # 実装詳細
```

#### 4.3 最適な余白検出
- 左右ページタイプに応じた余白検出の最適化
- ノド（本の内側）と外側で異なる余白処理

### 5. テストと検証

#### 5.1 テスト方法
- 様々な縦書き/横書きPDFでのテスト
- 異なる綴じ方向のPDFでのテスト
- 自動検出精度の評価

#### 5.2 評価指標
- 視認性の向上（主観評価）
- 余白除去の精度（定量評価）
- 処理速度の変化

## 実装スケジュール
1. まずは基本的な左右ページ判定と個別クロップ設定を実装
2. CLIインターフェースの拡張
3. 自動検出機能の追加
4. テストと調整

## 将来の拡張可能性
- ページの傾き自動補正
- 複雑なレイアウト（雑誌など）への対応
- マンガ向け最適化オプション