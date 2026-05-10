import os
import sys
import shlex
import pdf_core

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    import rich
except ImportError:
    print("richライブラリがインストールされていません。pip install -r requirements.txt を実行してください。")
    sys.exit(1)

console = Console()

def print_menu():
    menu_text = (
        "[cyan]1.[/cyan] PDFをパスワードで暗号化する（手動／環境変数）\n"
        "[cyan]2.[/cyan] PDFをランダムパスワードで暗号化する\n"
        "[cyan]3.[/cyan] PDFのパスワードを解除する（復号）\n"
        "[cyan]4.[/cyan] PDFから特定のページを抽出する\n"
        "[cyan]5.[/cyan] PDFを分割する\n"
        "[cyan]6.[/cyan] PDFのページを逆順に並び替える\n"
        "[cyan]7.[/cyan] 複数のPDFを1つに結合する\n"
        "[cyan]8.[/cyan] PDFを画像に変換する\n"
        "[cyan]9.[/cyan] 複数の画像を1つのPDFに変換する\n"
        "[red]Q.[/red] 終了"
    )
    console.print()
    console.print(Panel(menu_text, title="[bold white on blue] PDFツールキット メニュー [/bold white on blue]", border_style="blue", expand=False))

def parse_paths(input_str: str) -> list[str]:
    """D&Dなどで入力された複数パスの文字列をリストに変換する"""
    try:
        paths = shlex.split(input_str, posix=False)
        clean_paths = [p.strip('"\'') for p in paths]
        return clean_paths
    except ValueError:
        return [input_str.strip('"\'')]

def get_output_path(input_path: str, suffix: str) -> str:
    """入力ファイル名にサフィックスを付与した出力パスを生成する"""
    base, ext = os.path.splitext(input_path)
    return f"{base}_{suffix}{ext}"

def confirm_overwrite(out_path: str) -> bool:
    """出力ファイルが既に存在する場合、上書きするかどうかを確認する"""
    if os.path.exists(out_path):
        ans = Prompt.ask(f"[bold red]警告: ファイル '{os.path.basename(out_path)}' は既に存在します。上書きしますか？[/bold red] [y/N]", choices=["y", "n"], default="n").strip().lower()
        if ans != 'y':
            console.print("[yellow]処理をキャンセルしました。[/yellow]")
            return False
    return True

def check_multiple_overwrite(out_dir: str, base_name: str, ext: str = None) -> bool:
    """複数ファイル出力時に、同名になりうるファイルが存在するかチェックする"""
    if not os.path.exists(out_dir): return True
    for f in os.listdir(out_dir):
        if f.startswith(base_name):
            if ext and not f.lower().endswith(ext.lower()):
                continue
            ans = Prompt.ask(f"[bold red]警告: 出力先ディレクトリに、出力ファイル名と前方一致するファイル（{f} など）が存在するようです。上書きされる可能性があります。続行しますか？[/bold red] [y/N]", choices=["y", "n"], default="n").strip().lower()
            if ans != 'y':
                console.print("[yellow]処理をキャンセルしました。[/yellow]")
                return False
            return True
    return True

def get_single_file_input(prompt: str) -> str:
    while True:
        user_input = Prompt.ask(f"[bold yellow]{prompt}[/bold yellow]").strip()
        if not user_input:
            console.print("[yellow]入力がキャンセルされました。[/yellow]")
            return ""
        paths = parse_paths(user_input)
        if not paths:
            continue
        path = paths[0]
        if os.path.exists(path) and os.path.isfile(path):
            return path
        else:
            console.print(f"[bold red]ファイルが存在しません: {path}[/bold red]")

def get_multiple_files_input(prompt: str) -> list[str]:
    while True:
        user_input = Prompt.ask(f"[bold yellow]{prompt}[/bold yellow]").strip()
        if not user_input:
            console.print("[yellow]入力がキャンセルされました。[/yellow]")
            return []
        paths = parse_paths(user_input)
        valid_paths = []
        for p in paths:
            if os.path.exists(p) and os.path.isfile(p):
                valid_paths.append(p)
            else:
                console.print(f"[bold red]警告: ファイルが存在しません - {p}[/bold red]")
        if valid_paths:
            return valid_paths

def main():
    while True:
        print_menu()
        choice = Prompt.ask("[bold]番号を選んでください[/bold]").strip().lower()
        
        if choice == 'q':
            console.print("[bold green]終了します。お疲れ様でした！[/bold green]")
            break
            
        elif choice == '1':
            in_path = get_single_file_input("暗号化するPDFのパスを入力（またはD&D）")
            if not in_path: continue
            
            pwd = Prompt.ask("[bold yellow]設定するパスワードを入力（空欄で環境変数 PDF_DEFAULT_PASSWORD を使用）[/bold yellow]", password=True).strip()
            if not pwd:
                pwd = os.environ.get("PDF_DEFAULT_PASSWORD", "")
                if not pwd:
                    console.print("[bold red]環境変数 PDF_DEFAULT_PASSWORD が設定されていません。処理を中止します。[/bold red]")
                    continue
                else:
                    console.print("[cyan]環境変数からパスワードを取得しました。[/cyan]")
            
            uncrypted_path = get_output_path(in_path, "uncrypted")
            if not confirm_overwrite(uncrypted_path):
                continue
            
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    temp_out = in_path + ".tmp"
                    pdf_core.encrypt_pdf(in_path, temp_out, pwd)
                    if os.path.exists(uncrypted_path):
                        os.remove(uncrypted_path)
                    os.rename(in_path, uncrypted_path)
                    os.rename(temp_out, in_path)
                    console.print(f"[bold green]✔ 完了:[/bold green] {in_path}\n  [dim](元のファイルは {uncrypted_path} に保存されました)[/dim]")
                except Exception as e:
                    if os.path.exists(temp_out):
                        os.remove(temp_out)
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '2':
            in_path = get_single_file_input("暗号化するPDFのパスを入力（またはD&D）")
            if not in_path: continue
            
            pwd = pdf_core.generate_random_password()
            console.print(f"🔑 [bold magenta]生成されたパスワード:[/bold magenta] [bold white on magenta] {pwd} [/bold white on magenta]")
            
            uncrypted_path = get_output_path(in_path, "uncrypted")
            if not confirm_overwrite(uncrypted_path):
                continue
            
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    temp_out = in_path + ".tmp"
                    pdf_core.encrypt_pdf(in_path, temp_out, pwd)
                    if os.path.exists(uncrypted_path):
                        os.remove(uncrypted_path)
                    os.rename(in_path, uncrypted_path)
                    os.rename(temp_out, in_path)
                    console.print(f"[bold green]✔ 完了:[/bold green] {in_path}\n  [dim](元のファイルは {uncrypted_path} に保存されました)[/dim]")
                except Exception as e:
                    if os.path.exists(temp_out):
                        os.remove(temp_out)
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '3':
            in_path = get_single_file_input("復号するPDFのパスを入力（またはD&D）")
            if not in_path: continue
            
            pwd = Prompt.ask("[bold yellow]現在のパスワードを入力[/bold yellow]", password=True).strip()
            out_path = get_output_path(in_path, "decrypted")
            
            if not confirm_overwrite(out_path):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    success = pdf_core.decrypt_pdf(in_path, out_path, pwd)
                    if success:
                        console.print(f"[bold green]✔ 完了:[/bold green] {out_path}")
                    else:
                        console.print("[bold red]✖ パスワードが違います、または復号に失敗しました。[/bold red]")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '4':
            in_path = get_single_file_input("抽出元PDFのパスを入力（またはD&D）")
            if not in_path: continue
            
            try:
                total_pages = pdf_core.get_page_count(in_path)
                console.print(f"📄 [cyan]対象PDFの総ページ数: {total_pages} ページ[/cyan]")
            except Exception:
                pass
                
            ranges = Prompt.ask("[bold yellow]抽出するページを指定（例: 1,3,5-7）未指定で全ページ[/bold yellow]").strip()
            out_path = get_output_path(in_path, "extracted")
            
            if not confirm_overwrite(out_path):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    pdf_core.extract_pages(in_path, out_path, ranges)
                    console.print(f"[bold green]✔ 完了:[/bold green] {out_path}")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '5':
            in_path = get_single_file_input("分割するPDFのパスを入力（またはD&D）")
            if not in_path: continue
            
            try:
                total_pages = pdf_core.get_page_count(in_path)
                console.print(f"📄 [cyan]対象PDFの総ページ数: {total_pages} ページ[/cyan]")
            except Exception:
                pass
                
            spec = Prompt.ask("[bold yellow]分割するページ番号をカンマ区切りで指定（例: 3,5 / 空欄で1ページずつバラバラに分割）[/bold yellow]").strip()
            out_dir = os.path.dirname(in_path) or "."
            
            base_name = os.path.splitext(os.path.basename(in_path))[0]
            if not check_multiple_overwrite(out_dir, base_name, ".pdf"):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    pdf_core.split_pdf(in_path, out_dir, spec)
                    console.print(f"[bold green]✔ 分割完了:[/bold green] 出力先ディレクトリ {out_dir}")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '6':
            in_path = get_single_file_input("逆順にするPDFのパスを入力（またはD&D）")
            if not in_path: continue
            out_path = get_output_path(in_path, "reversed")
            
            if not confirm_overwrite(out_path):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    pdf_core.reverse_pdf(in_path, out_path)
                    console.print(f"[bold green]✔ 完了:[/bold green] {out_path}")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '7':
            console.print("[cyan]結合する複数のPDFファイルを指定してください。[/cyan]")
            in_paths = get_multiple_files_input("パスを入力（または複数ファイルをD&D）")
            if not in_paths: continue
            if len(in_paths) < 2:
                console.print("[bold red]結合には2つ以上のファイルが必要です。[/bold red]")
                continue
            
            out_dir = os.path.dirname(in_paths[0]) or "."
            out_path = os.path.join(out_dir, "merged_output.pdf")
            
            if not confirm_overwrite(out_path):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    pdf_core.merge_pdfs(in_paths, out_path)
                    console.print(f"[bold green]✔ 完了:[/bold green] {out_path}")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '8':
            in_path = get_single_file_input("画像に変換するPDFのパスを入力（またはD&D）")
            if not in_path: continue
            
            fmt = Prompt.ask("[bold yellow]出力フォーマットを入力 (png または jpg, デフォルトはpng)[/bold yellow]").strip().lower()
            if fmt not in ['png', 'jpg', 'jpeg']:
                fmt = 'png'
            if fmt == 'jpeg': fmt = 'jpg'
            
            out_dir = os.path.dirname(in_path) or "."
            
            base_name = os.path.splitext(os.path.basename(in_path))[0]
            if not check_multiple_overwrite(out_dir, base_name, "." + fmt):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    pdf_core.pdf_to_images(in_path, out_dir, fmt=fmt)
                    console.print(f"[bold green]✔ 画像変換完了:[/bold green] 出力先ディレクトリ {out_dir}")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
                
        elif choice == '9':
            console.print("[cyan]PDFに変換する複数の画像ファイルを指定してください。[/cyan]")
            in_paths = get_multiple_files_input("パスを入力（または複数ファイルをD&D）")
            if not in_paths: continue
            
            out_dir = os.path.dirname(in_paths[0]) or "."
            out_path = os.path.join(out_dir, "images_to_pdf_output.pdf")
            
            if not confirm_overwrite(out_path):
                continue
                
            with console.status("[bold green]処理中...[/bold green]"):
                try:
                    pdf_core.images_to_pdf(in_paths, out_path)
                    console.print(f"[bold green]✔ 完了:[/bold green] {out_path}")
                except Exception as e:
                    console.print(f"[bold red]✖ エラーが発生しました:[/bold red] {e}")
        else:
            console.print("[bold red]無効な選択です。[/bold red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]強制終了します。[/bold red]")
        sys.exit(0)
