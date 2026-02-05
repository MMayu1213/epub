"""
コマンドラインインターフェース
"""

import click
import os
import sys
import glob
import random
from pathlib import Path
from .core import PDFProcessor, KindleOptimizer

# デフォルトのフォルダパス
DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_PREVIEW_DIR = "preview"


def print_progress(current: int, total: int, stage: str = ""):
    """進捗バーを表示"""
    percent = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    stage_text = f" ({stage})" if stage else ""
    sys.stdout.write(f'\r進捗: [{bar}] {percent:.1f}%{stage_text}')
    sys.stdout.flush()
    if current == total:
        print()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    縦書きPDFの余白を除去してKindle向けに最適化します。
    
    【推奨】AI判断モード（ベースオプション）:
    
      1. サンプル画像を出力
         pdf-kindle preview input/book.pdf
      
      2. 出力画像をAI（Claude等）に見せて最適なクロップ位置を判断してもらう
      
      3. AIが提案したクロップ位置で処理
         pdf-kindle crop input/book.pdf --left 10 --right 15 --top 5 --bottom 5
    
    【代替】自動検出モード:
    
      テキスト位置から自動検出（AI判断より精度が劣る場合あり）
         pdf-kindle auto input/book.pdf
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
@click.option(
    '-o', '--output-dir',
    type=click.Path(),
    default=DEFAULT_PREVIEW_DIR,
    help=f'プレビュー画像の出力フォルダ（デフォルト: {DEFAULT_PREVIEW_DIR}）'
)
@click.option(
    '-p', '--pages',
    type=str,
    default=None,
    help='出力するページ番号（カンマ区切り、例: 1,10,50）。省略時はランダム選択'
)
@click.option(
    '-n', '--num-pages',
    type=int,
    default=5,
    help='ランダム選択するページ数（デフォルト: 5）'
)
@click.option(
    '--dpi',
    type=int,
    default=150,
    help='画像の解像度（デフォルト: 150）'
)
def preview(input_pdf, output_dir, pages, num_pages, dpi):
    """
    PDFのサンプルページを画像として出力します。
    
    出力された画像をAIに見せて、どこでカットすべきか判断してもらうために使用します。
    デフォルトではランダムに複数ページを選択します。
    
    例:
      pdf-kindle preview input/book.pdf           # ランダムに5ページ選択
      pdf-kindle preview input/book.pdf -n 10    # ランダムに10ページ選択
      pdf-kindle preview input/book.pdf -p 1,10,50  # 指定ページを出力
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    input_name = Path(input_pdf).stem
    
    try:
        with PDFProcessor(input_pdf) as processor:
            total_pages = processor.page_count
            click.echo(f"PDF: {input_pdf}")
            click.echo(f"総ページ数: {total_pages}")
            click.echo()
            
            # ページ番号を決定
            if pages:
                # 手動指定
                try:
                    page_nums = [int(p.strip()) for p in pages.split(',')]
                except ValueError:
                    click.echo(click.style("エラー: ページ番号は数字で指定してください", fg='red'), err=True)
                    sys.exit(1)
                click.echo(f"指定ページ: {page_nums}")
            else:
                # ランダム選択（最初と最後のページも含める可能性あり）
                # ただし、最初の数ページ（表紙等）と最後の数ページは除外
                start_page = min(5, total_pages)  # 最初の5ページは除外
                end_page = max(start_page + 1, total_pages - 3)  # 最後の3ページは除外
                
                available_pages = list(range(start_page, end_page + 1))
                
                # 選択数を調整
                actual_num = min(num_pages, len(available_pages))
                
                if actual_num > 0:
                    page_nums = sorted(random.sample(available_pages, actual_num))
                else:
                    # ページ数が少ない場合は全ページ
                    page_nums = list(range(1, total_pages + 1))
                
                click.echo(f"ランダム選択: {page_nums}")
            
            click.echo()
            
            exported_files = []
            
            for page_num in page_nums:
                if page_num < 1 or page_num > total_pages:
                    click.echo(f"警告: ページ {page_num} は範囲外です（1-{total_pages}）")
                    continue
                
                # 0始まりに変換
                page_idx = page_num - 1
                
                # 画像を取得
                img = processor.get_page_as_image(page_idx, dpi=dpi)
                
                # 保存
                output_file = output_path / f"{input_name}_page{page_num}.png"
                img.save(str(output_file))
                exported_files.append(str(output_file))
                
                click.echo(f"✓ ページ {page_num} → {output_file}")
            
            click.echo()
            click.echo(click.style("プレビュー画像を出力しました！", fg='green', bold=True))
            click.echo()
            click.echo("次のステップ:")
            click.echo("  1. 出力された画像をAI（Claude等）に見せる")
            click.echo("  2. 「この画像のどこでカットすべきか教えて」と質問")
            click.echo("  3. AIが提案した値で crop コマンドを実行:")
            click.echo()
            click.echo(f"     pdf-kindle crop {input_pdf} --left 10 --right 10 --top 5 --bottom 5")
            click.echo()
            
            # 画像サイズ情報を表示
            if exported_files:
                first_img = processor.get_page_as_image(page_nums[0] - 1, dpi=dpi)
                width, height = first_img.size
                click.echo(f"画像サイズ: {width} x {height} px")
                click.echo()
                click.echo("AIへの質問例:")
                click.echo("  「このPDFページ画像を見て、余白を除去するための")
                click.echo("   クロップ位置を%で教えてください。")
                click.echo("   左からX%、右からY%、上からZ%、下からW%の形式で。」")
                
    except Exception as e:
        click.echo(click.style(f"エラー: {e}", fg='red'), err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='出力ファイルパス（指定しない場合はoutputフォルダに出力）'
)
@click.option(
    '-d', '--device',
    type=click.Choice(['paperwhite', 'oasis', 'basic', 'scribe']),
    default='paperwhite',
    help='Kindleデバイス種類（デフォルト: paperwhite）'
)
@click.option(
    '--left',
    type=float,
    default=0,
    help='左からカットする割合（%、デフォルト: 0）'
)
@click.option(
    '--right',
    type=float,
    default=0,
    help='右からカットする割合（%、デフォルト: 0）'
)
@click.option(
    '--top',
    type=float,
    default=0,
    help='上からカットする割合（%、デフォルト: 0）'
)
@click.option(
    '--bottom',
    type=float,
    default=0,
    help='下からカットする割合（%、デフォルト: 0）'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='詳細な出力を表示'
)
def crop(input_pdf, output, device, left, right, top, bottom, verbose):
    """
    指定した割合でPDFをクロップします。
    
    AIが提案したクロップ位置を指定して実行します。
    
    例:
      pdf-kindle crop input/book.pdf --left 10 --right 15 --top 5 --bottom 5
    """
    import fitz
    
    if not output:
        output_dir = Path(DEFAULT_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = Path(input_pdf)
        output = str(output_dir / f"{input_path.stem}_kindle.pdf")
    
    click.echo(f"入力ファイル: {input_pdf}")
    click.echo(f"出力ファイル: {output}")
    click.echo(f"対象デバイス: {device}")
    click.echo(f"クロップ設定: 左{left}%, 右{right}%, 上{top}%, 下{bottom}%")
    click.echo()
    
    try:
        # デバイスプロファイル
        profiles = {
            'paperwhite': {'width': 1236, 'height': 1648},
            'oasis': {'width': 1264, 'height': 1680},
            'basic': {'width': 1072, 'height': 1448},
            'scribe': {'width': 1860, 'height': 2480},
        }
        profile = profiles.get(device, profiles['paperwhite'])
        
        src_doc = fitz.open(input_pdf)
        output_doc = fitz.open()
        
        total_pages = len(src_doc)
        
        for i in range(total_pages):
            page = src_doc[i]
            rect = page.rect
            
            # クロップ領域を計算
            crop_x0 = rect.x0 + rect.width * (left / 100)
            crop_x1 = rect.x1 - rect.width * (right / 100)
            crop_y0 = rect.y0 + rect.height * (top / 100)
            crop_y1 = rect.y1 - rect.height * (bottom / 100)
            
            crop_rect = fitz.Rect(crop_x0, crop_y0, crop_x1, crop_y1)
            
            # 新しいページサイズを計算
            new_width = crop_rect.width
            new_height = crop_rect.height
            
            # ターゲットサイズにスケール
            scale_w = profile['width'] / new_width
            scale_h = profile['height'] / new_height
            scale = min(scale_w, scale_h)
            new_width *= scale
            new_height *= scale
            
            # 新しいページを作成
            new_page = output_doc.new_page(width=new_width, height=new_height)
            new_page.show_pdf_page(
                fitz.Rect(0, 0, new_width, new_height),
                src_doc,
                i,
                clip=crop_rect
            )
            
            print_progress(i + 1, total_pages)
        
        output_doc.save(output, garbage=4, deflate=True)
        output_doc.close()
        src_doc.close()
        
        click.echo()
        click.echo(click.style("✓ 処理完了！", fg='green', bold=True))
        
        if verbose:
            input_size = os.path.getsize(input_pdf)
            output_size = os.path.getsize(output)
            click.echo(f"入力ファイルサイズ: {input_size / 1024:.1f} KB")
            click.echo(f"出力ファイルサイズ: {output_size / 1024:.1f} KB")
            
    except Exception as e:
        click.echo(click.style(f"エラー: {e}", fg='red'), err=True)
        import traceback
        if verbose:
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('input_pdf', type=click.Path(exists=True), required=False)
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='出力ファイルパス（指定しない場合はoutputフォルダに出力）'
)
@click.option(
    '-d', '--device',
    type=click.Choice(['paperwhite', 'oasis', 'basic', 'scribe']),
    default='paperwhite',
    help='Kindleデバイス種類（デフォルト: paperwhite）'
)
@click.option(
    '-t', '--threshold',
    type=int,
    default=250,
    help='余白検出の閾値（0-255、デフォルト: 250）- --scan使用時のみ'
)
@click.option(
    '-m', '--margin',
    type=float,
    default=0.005,
    help='追加マージン（割合、デフォルト: 0.005 = 0.5%）'
)
@click.option(
    '--no-uniform',
    is_flag=True,
    help='ページごとに個別にクロップする（デフォルトは統一クロップ）'
)
@click.option(
    '-v', '--verbose',
    is_flag=True,
    help='詳細な出力を表示'
)
@click.option(
    '-i', '--input-dir',
    type=click.Path(),
    default=DEFAULT_INPUT_DIR,
    help=f'入力フォルダ（デフォルト: {DEFAULT_INPUT_DIR}）'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default=DEFAULT_OUTPUT_DIR,
    help=f'出力フォルダ（デフォルト: {DEFAULT_OUTPUT_DIR}）'
)
@click.option(
    '--scan',
    is_flag=True,
    help='スキャンPDF用：画像ベースのエッジ検出を使用'
)
@click.option(
    '-e', '--edge-threshold',
    type=int,
    default=30,
    help='エッジ検出の閾値（デフォルト: 30）- --scan使用時のみ'
)
@click.option(
    '--min-char-size',
    type=int,
    default=8,
    help='文字として認識する最小サイズ（ピクセル、デフォルト: 8）'
)
@click.option(
    '--max-char-size',
    type=int,
    default=200,
    help='文字として認識する最大サイズ（ピクセル、デフォルト: 200）'
)
@click.option(
    '--auto-threshold',
    is_flag=True,
    help='Otsu法で二値化閾値を自動決定（--scan使用時のみ）'
)
def auto(input_pdf, output, device, threshold, margin, no_uniform, verbose,
         input_dir, output_dir, scan, edge_threshold, min_char_size, max_char_size, auto_threshold):
    """
    自動検出でPDFの余白を除去します。
    
    テキスト位置から自動的にコンテンツ領域を検出してクロップします。
    
    例:
      pdf-kindle auto input/book.pdf
      pdf-kindle auto  # inputフォルダの全PDFを処理
    """
    # デフォルトはテキスト検出（文字位置から検出）
    use_text_detection = not scan
    use_edge_detection = scan
    
    # 出力フォルダを確認・作成
    output_dir_path = Path(output_dir)
    if not output_dir_path.exists():
        output_dir_path.mkdir(parents=True)
        click.echo(f"出力フォルダを作成しました: {output_dir}")
    
    # 単一ファイルが指定された場合
    if input_pdf:
        # 出力パスを設定
        if not output:
            input_path = Path(input_pdf)
            output = str(output_dir_path / f"{input_path.stem}_kindle.pdf")
        
        success = process_single_pdf(
            input_pdf, output, device, threshold, margin, no_uniform, verbose,
            use_edge_detection, edge_threshold, use_text_detection,
            min_char_size, max_char_size, auto_threshold
        )
        if not success:
            sys.exit(1)
        return
    
    # inputフォルダから全PDFを処理
    input_dir_path = Path(input_dir)
    if not input_dir_path.exists():
        input_dir_path.mkdir(parents=True)
        click.echo(f"入力フォルダを作成しました: {input_dir}")
        click.echo("PDFファイルを入力フォルダに配置して再実行してください。")
        return
    
    # PDFファイルを検索
    pdf_files = list(input_dir_path.glob("*.pdf")) + list(input_dir_path.glob("*.PDF"))
    
    if not pdf_files:
        click.echo(f"入力フォルダにPDFファイルが見つかりません: {input_dir}")
        click.echo("PDFファイルを入力フォルダに配置して再実行してください。")
        return
    
    click.echo(f"処理対象: {len(pdf_files)}個のPDFファイル")
    click.echo(f"入力フォルダ: {input_dir}")
    click.echo(f"出力フォルダ: {output_dir}")
    click.echo("=" * 50)
    click.echo()
    
    success_count = 0
    fail_count = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        click.echo(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
        click.echo("-" * 40)
        
        output_path = str(output_dir_path / f"{pdf_file.stem}_kindle.pdf")
        
        success = process_single_pdf(
            str(pdf_file), output_path, device, threshold, margin, no_uniform, verbose,
            use_edge_detection, edge_threshold, use_text_detection,
            min_char_size, max_char_size, auto_threshold
        )
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        click.echo()
    
    # 結果サマリー
    click.echo("=" * 50)
    click.echo(f"処理完了: 成功 {success_count}件, 失敗 {fail_count}件")
    
    if fail_count > 0:
        sys.exit(1)


def process_single_pdf(
    input_pdf: str,
    output: str,
    device: str,
    threshold: int,
    margin: float,
    no_uniform: bool,
    verbose: bool,
    use_edge_detection: bool,
    edge_threshold: int,
    use_text_detection: bool,
    min_char_size: int = 8,
    max_char_size: int = 200,
    auto_threshold: bool = False
):
    """単一のPDFファイルを処理"""
    click.echo(f"入力ファイル: {input_pdf}")
    click.echo(f"出力ファイル: {output}")
    click.echo(f"対象デバイス: {device}")
    if use_text_detection:
        click.echo(f"検出方式: テキスト検出（文字位置から検出）")
    elif use_edge_detection:
        click.echo(f"検出方式: 二値化+連結成分分析（文字検出）")
        if auto_threshold:
            click.echo(f"二値化: Otsu法（自動閾値）")
        else:
            click.echo(f"二値化閾値: {threshold}")
        click.echo(f"文字サイズ範囲: {min_char_size}-{max_char_size}px")
    else:
        click.echo(f"検出方式: 閾値検出")
        click.echo(f"余白閾値: {threshold}")
    click.echo(f"マージン: {margin * 100:.1f}%")
    click.echo(f"クロップモード: {'ページ個別' if no_uniform else '統一'}")
    click.echo()
    
    try:
        with PDFProcessor(input_pdf) as processor:
            click.echo(f"ページ数: {processor.page_count}")
            click.echo()
            
            optimizer = KindleOptimizer(processor)
            
            def progress_callback(current, total, stage=""):
                print_progress(current, total, stage)
            
            # auto_thresholdの場合、threshold=0でOtsu法を使用
            effective_threshold = 0 if auto_threshold else threshold
            
            optimizer.optimize_for_kindle(
                output_path=output,
                device=device,
                uniform_crop=not no_uniform,
                threshold=effective_threshold,
                margin_percent=margin,
                use_edge_detection=use_edge_detection,
                edge_threshold=edge_threshold,
                use_text_detection=use_text_detection,
                min_char_size=min_char_size,
                max_char_size=max_char_size,
                progress_callback=progress_callback
            )
            
            click.echo()
            click.echo(click.style("✓ 処理完了！", fg='green', bold=True))
            
            # 統計情報を表示
            if verbose and processor.page_infos:
                click.echo()
                click.echo("=== 処理統計 ===")
                avg_ratio = sum(p.content_ratio for p in processor.page_infos) / len(processor.page_infos)
                click.echo(f"平均コンテンツ比率: {avg_ratio * 100:.1f}%")
                click.echo(f"削減率: {(1 - avg_ratio) * 100:.1f}%")
                
                # ファイルサイズ比較
                input_size = os.path.getsize(input_pdf)
                output_size = os.path.getsize(output)
                click.echo(f"入力ファイルサイズ: {input_size / 1024:.1f} KB")
                click.echo(f"出力ファイルサイズ: {output_size / 1024:.1f} KB")
            
            return True
                
    except Exception as e:
        click.echo(click.style(f"エラー: {e}", fg='red'), err=True)
        import traceback
        if verbose:
            traceback.print_exc()
        return False


# 後方互換性のためのエイリアス
main = cli


if __name__ == '__main__':
    cli()
