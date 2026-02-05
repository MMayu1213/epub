"""
PDF Kindle Optimizer - 縦書きPDFの余白除去ツール
Kindle端末で見やすくするためにPDFの余白を自動検出・除去します
"""

__version__ = "1.0.0"
__author__ = "PDF Kindle Optimizer"

from .core import PDFProcessor, KindleOptimizer, CropBox, PageInfo

__all__ = ["PDFProcessor", "KindleOptimizer", "CropBox", "PageInfo"]
