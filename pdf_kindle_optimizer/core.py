"""
PDF処理のコアモジュール
"""

import fitz  # PyMuPDF
from PIL import Image
import io
from dataclasses import dataclass
from typing import Tuple, Optional, List
import numpy as np


@dataclass
class CropBox:
    """クロップ領域を表すデータクラス"""
    x0: float
    y0: float
    x1: float
    y1: float
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    def to_rect(self) -> fitz.Rect:
        """fitz.Rectに変換"""
        return fitz.Rect(self.x0, self.y0, self.x1, self.y1)


@dataclass
class PageInfo:
    """ページ情報を表すデータクラス"""
    page_number: int
    original_size: Tuple[float, float]
    crop_box: CropBox
    content_ratio: float  # コンテンツ領域の割合


class PDFProcessor:
    """PDF処理クラス"""
    
    def __init__(self, input_path: str):
        """
        PDFプロセッサを初期化
        
        Args:
            input_path: 入力PDFファイルのパス
        """
        self.input_path = input_path
        self.doc = fitz.open(input_path)
        self.page_infos: List[PageInfo] = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """ドキュメントを閉じる"""
        if self.doc:
            self.doc.close()
    
    @property
    def page_count(self) -> int:
        """ページ数を取得"""
        return len(self.doc)
    
    def get_page_as_image(self, page_num: int, dpi: int = 150) -> Image.Image:
        """
        指定ページを画像として取得
        
        Args:
            page_num: ページ番号（0始まり）
            dpi: 解像度
            
        Returns:
            PIL Image オブジェクト
        """
        page = self.doc[page_num]
        # DPIに応じたズーム率を計算
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # PIL Imageに変換
        img_data = pix.tobytes("png")
        return Image.open(io.BytesIO(img_data))
    
    def detect_content_bounds_by_text(
        self,
        page_num: int,
        margin_percent: float = 0.01
    ) -> Optional[CropBox]:
        """
        PDFのテキスト情報から直接コンテンツ領域を検出（最も正確）
        
        Args:
            page_num: ページ番号（0始まり）
            margin_percent: 追加するマージン（割合）
            
        Returns:
            検出されたコンテンツ領域のCropBox、またはテキストがない場合はNone
        """
        page = self.doc[page_num]
        original_rect = page.rect
        
        # テキストブロックの位置を取得
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        
        x0_min = original_rect.x1
        y0_min = original_rect.y1
        x1_max = original_rect.x0
        y1_max = original_rect.y0
        
        has_text = False
        
        for block in blocks:
            # テキストブロックのみ（画像は除外）
            if "lines" in block:  # テキストブロック
                for line in block["lines"]:
                    for span in line["spans"]:
                        bbox = span["bbox"]
                        text = span["text"].strip()
                        if text:  # 空でないテキストのみ
                            x0_min = min(x0_min, bbox[0])
                            y0_min = min(y0_min, bbox[1])
                            x1_max = max(x1_max, bbox[2])
                            y1_max = max(y1_max, bbox[3])
                            has_text = True
        
        if not has_text:
            # テキストが見つからない場合はNoneを返す（画像ベース検出にフォールバック）
            return None
        
        # マージンを追加
        margin_x = original_rect.width * margin_percent
        margin_y = original_rect.height * margin_percent
        
        x0 = max(original_rect.x0, x0_min - margin_x)
        y0 = max(original_rect.y0, y0_min - margin_y)
        x1 = min(original_rect.x1, x1_max + margin_x)
        y1 = min(original_rect.y1, y1_max + margin_y)
        
        return CropBox(x0=x0, y0=y0, x1=x1, y1=y1)
    
    def detect_content_bounds(
        self,
        page_num: int,
        threshold: int = 250,
        margin_percent: float = 0.02,
        dpi: int = 150,
        use_edge_detection: bool = True,
        edge_threshold: int = 30,
        min_content_pixels: int = 50,
        use_text_detection: bool = True,
        min_char_size: int = 8,
        max_char_size: int = 200,
        shadow_distance_ratio: float = 0.45
    ) -> CropBox:
        """
        ページのコンテンツ領域を検出
        
        Args:
            page_num: ページ番号（0始まり）
            threshold: 白とみなす閾値（0-255）- 0の場合はOtsu法で自動決定
            margin_percent: 追加するマージン（割合）
            dpi: 検出に使用する解像度
            use_edge_detection: エッジ検出を使用するか（文字検出に効果的）
            edge_threshold: エッジ検出の閾値（use_edge_detection=Trueの場合のみ使用）
            min_content_pixels: コンテンツとみなす最小ピクセル数（ノイズ除去）
            use_text_detection: PDFのテキスト情報を使用するか（最も正確）
            min_char_size: 文字として認識する最小サイズ（ピクセル）
            max_char_size: 文字として認識する最大サイズ（ピクセル）
            shadow_distance_ratio: 中心からの距離の割合（0.0-0.5）
                                   0.45 = 中心から45%以上離れた位置（端から10%以内）
                                   0.40 = 中心から40%以上離れた位置（端から20%以内）
            
        Returns:
            検出されたコンテンツ領域のCropBox
        """
        # テキスト検出モード（PDFから直接テキスト位置を取得）
        if use_text_detection:
            result = self.detect_content_bounds_by_text(page_num, margin_percent)
            if result is not None:
                return result
            # テキストが見つからない場合は画像ベース検出にフォールバック
        
        from scipy import ndimage
        
        page = self.doc[page_num]
        original_rect = page.rect
        
        # ページを画像に変換
        img = self.get_page_as_image(page_num, dpi)
        img_array = np.array(img.convert('L'))  # グレースケールに変換
        
        if use_edge_detection:
            # === 二値化 + 連結成分分析による文字検出 ===
            
            # 1. Otsu法による自動二値化（背景と文字を分離）
            # 文字は暗い（値が小さい）、背景は明るい（値が大きい）と仮定
            if threshold == 0:
                # Otsu法で最適な閾値を自動決定
                hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
                total_pixels = img_array.size
                
                sum_total = np.sum(np.arange(256) * hist)
                sum_bg = 0
                weight_bg = 0
                max_variance = 0
                optimal_threshold = 128
                
                for t in range(256):
                    weight_bg += hist[t]
                    if weight_bg == 0:
                        continue
                    weight_fg = total_pixels - weight_bg
                    if weight_fg == 0:
                        break
                    
                    sum_bg += t * hist[t]
                    mean_bg = sum_bg / weight_bg
                    mean_fg = (sum_total - sum_bg) / weight_fg
                    
                    variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
                    if variance > max_variance:
                        max_variance = variance
                        optimal_threshold = t
                
                binary_threshold = optimal_threshold
            else:
                binary_threshold = threshold
            
            # 二値化: 閾値より暗いピクセル = 文字候補
            binary_mask = img_array < binary_threshold
            
            # 2. 連結成分分析
            labeled, num_features = ndimage.label(binary_mask)
            
            img_height, img_width = img_array.shape
            
            if num_features > 0:
                # 各成分のサイズと境界ボックスを計算
                content_mask = np.zeros_like(binary_mask)
                
                # スライスを取得（各成分の境界ボックス）
                slices = ndimage.find_objects(labeled)
                
                # 端マージン: 画像端からこの距離以内に接する成分は影として除外
                edge_margin = int(5 * dpi / 150.0)  # 5ピクセル（150dpi基準）
                
                for i, slc in enumerate(slices):
                    if slc is None:
                        continue
                    
                    component_label = i + 1
                    component_mask_local = labeled[slc] == component_label
                    component_size = np.sum(component_mask_local)
                    
                    # 境界ボックスの位置とサイズを計算
                    y_start, y_end = slc[0].start, slc[0].stop
                    x_start, x_end = slc[1].start, slc[1].stop
                    height = y_end - y_start
                    width = x_end - x_start
                    
                    # DPIに基づいてサイズを調整（150dpiで約10-100ピクセルが文字）
                    dpi_scale = dpi / 150.0
                    min_size = int(min_char_size * dpi_scale)
                    max_size = int(max_char_size * dpi_scale)
                    
                    # *** 影フィルタ：画像端に接する大きな成分を除外 ***
                    touches_left = x_start <= edge_margin
                    touches_right = x_end >= img_width - edge_margin
                    touches_top = y_start <= edge_margin
                    touches_bottom = y_end >= img_height - edge_margin
                    
                    # 端に接していて、かつ長い成分は影として除外
                    # （ページ高さの30%以上の成分が端に接している場合）
                    is_edge_shadow = False
                    if touches_left or touches_right:
                        if height > img_height * 0.3:  # 高さがページの30%以上
                            is_edge_shadow = True
                    if touches_top or touches_bottom:
                        if width > img_width * 0.3:  # 幅がページの30%以上
                            is_edge_shadow = True
                    
                    if is_edge_shadow:
                        continue  # 影として除外
                    
                    # サイズフィルタリング: 文字サイズの範囲内かチェック
                    # - 小さすぎる = ノイズ
                    # - 大きすぎる = 背景パターンや枠線
                    is_valid_size = (
                        min_size <= height <= max_size * 3 and  # 縦書きなので高さは緩め
                        min_size <= width <= max_size and
                        component_size >= min_content_pixels
                    )
                    
                    # アスペクト比チェック: 極端に細長いものは除外（枠線等）
                    aspect_ratio = max(height, width) / max(min(height, width), 1)
                    is_valid_aspect = aspect_ratio < 30  # 30:1より細長いものは除外
                    
                    if is_valid_size and is_valid_aspect:
                        content_mask[slc][component_mask_local] = True
                
                # 3. 文字領域を膨張して近接した文字を繋げる
                structure = np.ones((3, 3))
                content_mask = ndimage.binary_dilation(content_mask, structure, iterations=2)
            else:
                content_mask = binary_mask
        else:
            # 従来の方式：単純な閾値処理
            content_mask = img_array < threshold
        
        # コンテンツがある行と列を見つける
        rows_with_content = np.any(content_mask, axis=1)
        cols_with_content = np.any(content_mask, axis=0)
        
        if not np.any(rows_with_content) or not np.any(cols_with_content):
            # コンテンツが見つからない場合は元のサイズを返す
            return CropBox(
                x0=original_rect.x0,
                y0=original_rect.y0,
                x1=original_rect.x1,
                y1=original_rect.y1
            )
        
        # コンテンツ領域の境界を取得
        y_indices = np.where(rows_with_content)[0]
        x_indices = np.where(cols_with_content)[0]
        
        img_height, img_width = img_array.shape
        
        # 画像座標からPDF座標に変換
        zoom = dpi / 72.0
        
        # マージンを追加
        margin_x = img_width * margin_percent
        margin_y = img_height * margin_percent
        
        x0_img = max(0, x_indices[0] - margin_x)
        y0_img = max(0, y_indices[0] - margin_y)
        x1_img = min(img_width, x_indices[-1] + margin_x)
        y1_img = min(img_height, y_indices[-1] + margin_y)
        
        # PDF座標に変換
        x0 = x0_img / zoom
        y0 = y0_img / zoom
        x1 = x1_img / zoom
        y1 = y1_img / zoom
        
        return CropBox(x0=x0, y0=y0, x1=x1, y1=y1)
    
    def analyze_all_pages(
        self,
        threshold: int = 250,
        margin_percent: float = 0.02,
        use_edge_detection: bool = True,
        edge_threshold: int = 30,
        use_text_detection: bool = True,
        min_char_size: int = 8,
        max_char_size: int = 200,
        progress_callback=None
    ) -> List[PageInfo]:
        """
        全ページを分析してコンテンツ領域を検出
        
        Args:
            threshold: 白とみなす閾値（0の場合はOtsu法で自動決定）
            margin_percent: 追加するマージン
            use_edge_detection: エッジ検出を使用するか
            edge_threshold: エッジ検出の閾値
            use_text_detection: PDFのテキスト情報から検出するか（最も正確）
            min_char_size: 文字として認識する最小サイズ（ピクセル）
            max_char_size: 文字として認識する最大サイズ（ピクセル）
            progress_callback: 進捗コールバック関数
            
        Returns:
            各ページのPageInfoリスト
        """
        self.page_infos = []
        
        for i in range(self.page_count):
            page = self.doc[i]
            original_rect = page.rect
            crop_box = self.detect_content_bounds(
                i, threshold, margin_percent,
                use_edge_detection=use_edge_detection,
                edge_threshold=edge_threshold,
                use_text_detection=use_text_detection,
                min_char_size=min_char_size,
                max_char_size=max_char_size
            )
            
            original_area = original_rect.width * original_rect.height
            content_area = crop_box.width * crop_box.height
            content_ratio = content_area / original_area if original_area > 0 else 1.0
            
            page_info = PageInfo(
                page_number=i,
                original_size=(original_rect.width, original_rect.height),
                crop_box=crop_box,
                content_ratio=content_ratio
            )
            self.page_infos.append(page_info)
            
            if progress_callback:
                progress_callback(i + 1, self.page_count)
        
        return self.page_infos
    
    def get_uniform_crop_box(self) -> Optional[CropBox]:
        """
        全ページで統一されたクロップ領域を計算
        
        Returns:
            統一されたCropBox、またはページ情報がない場合はNone
        """
        if not self.page_infos:
            return None
        
        # 全ページのクロップ領域の外接矩形を計算
        x0 = min(p.crop_box.x0 for p in self.page_infos)
        y0 = min(p.crop_box.y0 for p in self.page_infos)
        x1 = max(p.crop_box.x1 for p in self.page_infos)
        y1 = max(p.crop_box.y1 for p in self.page_infos)
        
        return CropBox(x0=x0, y0=y0, x1=x1, y1=y1)
    
    def crop_and_save(
        self,
        output_path: str,
        uniform_crop: bool = True,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        progress_callback=None
    ):
        """
        PDFをクロップして保存
        
        Args:
            output_path: 出力ファイルパス
            uniform_crop: 全ページで統一したクロップを使用するか
            target_width: 目標幅（ピクセル）
            target_height: 目標高さ（ピクセル）
            progress_callback: 進捗コールバック関数
        """
        if not self.page_infos:
            self.analyze_all_pages()
        
        # 新しいPDFドキュメントを作成
        output_doc = fitz.open()
        
        # 統一クロップの場合は事前に計算
        uniform_box = self.get_uniform_crop_box() if uniform_crop else None
        
        for i, page_info in enumerate(self.page_infos):
            src_page = self.doc[i]
            
            # クロップ領域を決定
            crop_box = uniform_box if uniform_crop else page_info.crop_box
            crop_rect = crop_box.to_rect()
            
            # 新しいページサイズを計算
            new_width = crop_box.width
            new_height = crop_box.height
            
            # ターゲットサイズが指定されている場合はスケール
            if target_width and target_height:
                # アスペクト比を維持してフィット
                scale_w = target_width / new_width
                scale_h = target_height / new_height
                scale = min(scale_w, scale_h)
                new_width *= scale
                new_height *= scale
            
            # 新しいページを作成
            new_page = output_doc.new_page(
                width=new_width,
                height=new_height
            )
            
            # ソースページの指定領域を新しいページにコピー
            new_page.show_pdf_page(
                fitz.Rect(0, 0, new_width, new_height),
                self.doc,
                i,
                clip=crop_rect
            )
            
            if progress_callback:
                progress_callback(i + 1, len(self.page_infos))
        
        # 保存
        output_doc.save(output_path, garbage=4, deflate=True)
        output_doc.close()


class KindleOptimizer:
    """Kindle向けに最適化するクラス"""
    
    # Kindle端末のディスプレイサイズ（ポイント単位）
    KINDLE_PROFILES = {
        'paperwhite': {'width': 1236, 'height': 1648},  # Kindle Paperwhite
        'oasis': {'width': 1264, 'height': 1680},        # Kindle Oasis
        'basic': {'width': 1072, 'height': 1448},        # Kindle Basic
        'scribe': {'width': 1860, 'height': 2480},       # Kindle Scribe
    }
    
    def __init__(self, processor: PDFProcessor):
        """
        Kindleオプティマイザを初期化
        
        Args:
            processor: PDFProcessorインスタンス
        """
        self.processor = processor
    
    def optimize_for_kindle(
        self,
        output_path: str,
        device: str = 'paperwhite',
        uniform_crop: bool = True,
        threshold: int = 250,
        margin_percent: float = 0.02,
        use_edge_detection: bool = True,
        edge_threshold: int = 30,
        use_text_detection: bool = True,
        min_char_size: int = 8,
        max_char_size: int = 200,
        progress_callback=None
    ):
        """
        Kindle向けに最適化して保存
        
        Args:
            output_path: 出力ファイルパス
            device: Kindleデバイス種類
            uniform_crop: 全ページで統一したクロップを使用するか
            threshold: 白とみなす閾値（0の場合はOtsu法で自動決定）
            margin_percent: 追加するマージン
            use_edge_detection: エッジ検出を使用するか
            edge_threshold: エッジ検出の閾値
            use_text_detection: PDFのテキスト情報から検出するか（最も正確）
            min_char_size: 文字として認識する最小サイズ（ピクセル）
            max_char_size: 文字として認識する最大サイズ（ピクセル）
            progress_callback: 進捗コールバック関数
        """
        # プロファイルを取得
        profile = self.KINDLE_PROFILES.get(device, self.KINDLE_PROFILES['paperwhite'])
        
        # ページを分析
        def analyze_progress(current, total):
            if progress_callback:
                progress_callback(current, total * 2, "分析中")
        
        self.processor.analyze_all_pages(
            threshold=threshold,
            margin_percent=margin_percent,
            use_edge_detection=use_edge_detection,
            edge_threshold=edge_threshold,
            use_text_detection=use_text_detection,
            min_char_size=min_char_size,
            max_char_size=max_char_size,
            progress_callback=analyze_progress
        )
        
        # クロップして保存
        def save_progress(current, total):
            if progress_callback:
                progress_callback(current + total, total * 2, "保存中")
        
        self.processor.crop_and_save(
            output_path=output_path,
            uniform_crop=uniform_crop,
            target_width=profile['width'],
            target_height=profile['height'],
            progress_callback=save_progress
        )
