# PDF Kindle Optimizer - コードモードルール

## プロジェクトの目的
縦書きPDFの余白を自動検出・除去し、Kindle端末で見やすく最適化するツール。

## フォルダ構成
- `input/` - 入力PDFファイル
- `output/` - 出力PDFファイル
- `preview/` - プレビュー画像
- `pdf_kindle_optimizer/` - ソースコード

## CLI ツール

`pdf-kindle` コマンドが利用可能です：

```bash
# プレビュー画像を生成
pdf-kindle preview input/[file].pdf

# 手動クロップ
pdf-kindle crop input/[file].pdf --left 10 --right 10 --top 5 --bottom 5

# 自動検出クロップ
pdf-kindle auto input/[file].pdf

# スキャンPDF
pdf-kindle auto --scan --auto-threshold -m 0 input/[file].pdf
```

## ユーザー支援時の注意

1. ユーザーがCLIに詳しくない可能性があります。コマンドは代わりに実行してあげてください
2. プレビュー画像を確認してからクロップ位置を決定するフローを推奨
3. スキャンPDFと通常PDFで処理方法が異なることを説明
4. 結果が良くない場合はパラメータ調整を提案
5. **Kindleデバイスのアスペクト比（約0.75）を考慮してクロップ位置を決定**
6. **画像は一枚ずつ表示して処理してください（複数画像を同時表示するとAPI errorの原因になります）**

## Kindleサイズを考慮したクロップ

クロップ位置を決定する際は、Kindleデバイスのアスペクト比を考慮してください：

| デバイス | 解像度 | アスペクト比 |
|----------|--------|--------------|
| `paperwhite` | 1236 x 1648 | 約 0.75 |
| `oasis` | 1264 x 1680 | 約 0.75 |
| `basic` | 1072 x 1448 | 約 0.74 |
| `scribe` | 1860 x 2480 | 約 0.75 |

**クロップ位置決定の考え方：**
- コンテンツ領域が縦長すぎる場合（比率 < 0.75）→ 上下を多めにカット
- コンテンツ領域が横長すぎる場合（比率 > 0.75）→ 左右を多めにカット
- 理想的にはクロップ後のアスペクト比が0.70〜0.80になるよう調整

## 左右ページ対応

縦書きPDFでは左右ページで余白の特性が異なります。開き方を指定して、左右ページ別のクロップ設定を使用してください。

### プレビュー生成時に開き方を指定

```bash
# 縦開き（右綴じ）の場合
pdf-kindle preview input/[file].pdf --binding vertical

# 横開き（左綴じ）の場合
pdf-kindle preview input/[file].pdf --binding horizontal
```

### 左右ページ別クロップ

```bash
# 縦開きの場合の例
pdf-kindle crop input/[file].pdf --binding vertical \
  --left-left 15 --left-right 5 --left-top 5 --left-bottom 5 \
  --right-left 5 --right-right 15 --right-top 5 --right-bottom 5
```

### 左右ページの余白パターン（縦開きの場合）

- **左ページ**: 左側（外側）の余白が大きく、右側（綴じ側）の余白が小さい
- **右ページ**: 右側（外側）の余白が大きく、左側（綴じ側）の余白が小さい
