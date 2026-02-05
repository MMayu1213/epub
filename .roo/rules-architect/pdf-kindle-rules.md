# PDF Kindle Optimizer - アーキテクトモードルール

## プロジェクト概要
縦書きPDFの余白を自動検出・除去し、Kindle端末で見やすく最適化するPythonツール。

## アーキテクチャ

### コアモジュール (`pdf_kindle_optimizer/core.py`)
- `PDFProcessor`: PDF処理のメインクラス
  - コンテンツ領域検出（テキストベース / 画像ベース）
  - ページ分析
  - クロップ＆保存
- `KindleOptimizer`: Kindle向け最適化
  - デバイスプロファイル管理
  - 最適化処理の統合

### CLI (`pdf_kindle_optimizer/cli.py`)
- `preview`: プレビュー画像生成
- `crop`: 手動クロップ
- `auto`: 自動検出クロップ

## 技術スタック
- PyMuPDF (fitz): PDF処理
- Pillow: 画像処理
- NumPy: 配列処理
- SciPy: 連結成分分析
- Click: CLI フレームワーク

## 設計原則
1. シンプルなCLIインターフェース
2. AI支援ワークフローのサポート
3. 縦書き日本語PDFへの最適化
4. 複数Kindleデバイスへの対応
