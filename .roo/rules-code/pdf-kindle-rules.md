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
