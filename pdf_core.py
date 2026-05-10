import fitz  # PyMuPDF
import os
import random
import string

def encrypt_pdf(input_path: str, output_path: str, password: str):
    """PDFをパスワードで暗号化する"""
    doc = fitz.open(input_path)
    if doc.is_encrypted or doc.needs_pass:
        doc.close()
        raise ValueError("このファイルは既に暗号化されています。先にパスワードを解除（復号）してください。")
    doc.save(output_path, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
    doc.close()

def generate_random_password(length=12) -> str:
    """ランダムなパスワードを生成する"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def decrypt_pdf(input_path: str, output_path: str, password: str) -> bool:
    """PDFのパスワードを解除する"""
    doc = fitz.open(input_path)
    if doc.needs_pass:
        if not doc.authenticate(password):
            doc.close()
            return False # パスワードエラー
    doc.save(output_path)
    doc.close()
    return True

def parse_page_ranges(range_str: str, max_pages: int) -> list[int]:
    """1,3,5-7 のような文字列から0オリジンのページ番号リストを生成する"""
    pages = set()
    if not range_str.strip():
        return list(range(max_pages))
    
    parts = range_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            start_idx = max(0, int(start) - 1)
            end_idx = min(max_pages - 1, int(end) - 1)
            for i in range(start_idx, end_idx + 1):
                pages.add(i)
        else:
            idx = int(part) - 1
            if 0 <= idx < max_pages:
                pages.add(idx)
    return sorted(list(pages))

def extract_pages(input_path: str, output_path: str, page_ranges_str: str):
    """特定のページを抽出する"""
    doc = fitz.open(input_path)
    pages_to_keep = parse_page_ranges(page_ranges_str, doc.page_count)
    
    new_doc = fitz.open()
    for page_num in pages_to_keep:
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
    new_doc.save(output_path)
    new_doc.close()
    doc.close()

def split_pdf(input_path: str, output_dir: str, split_spec: str):
    """
    PDFを分割する。
    split_spec が空なら1ページずつ。
    "3,5" の場合は 1-3, 4-5, 6-末尾 の3ファイルに分割。
    """
    doc = fitz.open(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    total_pages = doc.page_count
    
    if not split_spec.strip():
        # 1ページずつ分割
        for i in range(total_pages):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            out_name = f"{base_name}_page_{i+1}.pdf"
            new_doc.save(os.path.join(output_dir, out_name))
            new_doc.close()
    else:
        # 指定ページで分割
        breakpoints = []
        for p in split_spec.split(','):
            try:
                bp = int(p.strip())
                if 0 < bp < total_pages:
                    breakpoints.append(bp)
            except ValueError:
                pass
        
        breakpoints = sorted(list(set(breakpoints)))
        
        start_page = 0
        part_num = 1
        for bp in breakpoints:
            end_page = bp - 1
            if start_page <= end_page:
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
                out_name = f"{base_name}_part{part_num}.pdf"
                new_doc.save(os.path.join(output_dir, out_name))
                new_doc.close()
                part_num += 1
            start_page = bp
            
        # 最後の部分
        if start_page < total_pages:
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start_page, to_page=total_pages - 1)
            out_name = f"{base_name}_part{part_num}.pdf"
            new_doc.save(os.path.join(output_dir, out_name))
            new_doc.close()
            
    doc.close()

def reverse_pdf(input_path: str, output_path: str):
    """ページを逆順に並び替える"""
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    for i in range(doc.page_count - 1, -1, -1):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(output_path)
    new_doc.close()
    doc.close()

def merge_pdfs(input_paths: list[str], output_path: str):
    """複数のPDFを1つに結合する"""
    new_doc = fitz.open()
    for path in input_paths:
        doc = fitz.open(path)
        new_doc.insert_pdf(doc)
        doc.close()
    new_doc.save(output_path)
    new_doc.close()

def pdf_to_images(input_path: str, output_dir: str, fmt="png", dpi=150):
    """PDFを画像に変換する"""
    doc = fitz.open(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        out_name = f"{base_name}_page_{i+1}.{fmt}"
        pix.save(os.path.join(output_dir, out_name))
    doc.close()

def images_to_pdf(input_paths: list[str], output_path: str):
    """複数の画像を1つのPDFに変換する"""
    new_doc = fitz.open()
    for path in input_paths:
        img_doc = fitz.open(path)
        pdf_bytes = img_doc.convert_to_pdf()
        pdf_doc = fitz.open("pdf", pdf_bytes)
        new_doc.insert_pdf(pdf_doc)
        pdf_doc.close()
        img_doc.close()
    new_doc.save(output_path)
    new_doc.close()

def get_page_count(input_path: str) -> int:
    """PDFの総ページ数を取得する"""
    doc = fitz.open(input_path)
    count = doc.page_count
    doc.close()
    return count
