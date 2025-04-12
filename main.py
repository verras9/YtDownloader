import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
import json
import sys
import re
from pathlib import Path
import queue

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader by:verras")
        self.root.geometry("750x550")
        self.root.resizable(False, False)
        
       
        self.video_url = ""
        self.save_path = str(Path.home() / "Downloads")  
        self.downloading = False
        self.video_info = None
        self.process = None  
        self.update_queue = queue.Queue()  
        
        
        self.yt_dlp_path = self.find_yt_dlp()
        if not self.yt_dlp_path:
            self.show_installation_error()
            return
        
        
        self.setup_styles()
        self.create_widgets()
        
       
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        
        self.process_ui_updates()
    
    def find_yt_dlp(self):
        
        try:
            subprocess.run(["yt-dlp", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "yt-dlp"
        except (subprocess.CalledProcessError, FileNotFoundError):
            local_path = os.path.join(os.path.dirname(__file__), "yt-dlp")
            if os.path.isfile(local_path) and os.access(local_path, os.X_OK):
                return local_path
            return None
    
    def show_installation_error(self):
        error_msg = (
            "yt-dlp não está instalado ou não foi encontrado.\n\n"
            "Por favor instale usando um dos seguintes métodos:\n\n"
            "Windows (PowerShell):\n"
            "iwr https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe -OutFile yt-dlp.exe\n\n"
            "Mac/Linux:\n"
            "sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp\n"
            "sudo chmod a+rx /usr/local/bin/yt-dlp\n\n"
            "Ou visite: https://github.com/yt-dlp/yt-dlp"
        )
        messagebox.showerror("Erro de Instalação", error_msg)
        self.root.destroy()
        sys.exit(1)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, font=('Arial', 10), background='#4CAF50', foreground='white')
        style.configure("TLabel", font=('Arial', 10))
        style.configure("Title.TLabel", font=('Arial', 16, 'bold'), foreground='#333')
        style.configure("Status.TLabel", font=('Arial', 10))
        style.configure("Info.TFrame", background="#f5f5f5", borderwidth=2, relief="groove")
        style.map("TButton", background=[('active', '#45a049')])
    
    def create_widgets(self):
    
        title_frame = ttk.Frame(self.root, style="Info.TFrame")
        title_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(
            title_frame,
            text="YouTube Downloader Premium",
            style="Title.TLabel"
        ).pack(pady=5)
        

        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        

        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="URL do YouTube:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        

        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_frame, text="Pasta de destino:").pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(folder_frame, width=60)
        self.folder_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.folder_entry.insert(0, self.save_path)
        ttk.Button(
            folder_frame,
            text="Procurar",
            command=self.browse_folder,
            style="TButton"
        ).pack(side=tk.LEFT)
        
 
        self.info_frame = ttk.LabelFrame(main_frame, text="Informações do Vídeo", style="Info.TFrame")
        self.info_frame.pack(fill=tk.BOTH, pady=10, expand=True)
        
        self.info_text = tk.Text(
            self.info_frame,
            height=12,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Arial', 9),
            padx=5,
            pady=5,
            background="#f5f5f5"
        )
        scrollbar = ttk.Scrollbar(self.info_frame, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
  
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            text="Progresso:",
            font=('Arial', 9)
        )
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(
            self.progress_frame,
            orient=tk.HORIZONTAL,
            length=500,
            mode='determinate'
        )
        self.progress.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.fetch_button = ttk.Button(
            button_frame,
            text="Obter Informações",
            command=self.get_video_info_threaded,
            style="TButton"
        )
        self.fetch_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(
            button_frame,
            text="Baixar MP4 (Melhor Qualidade)",
            state=tk.DISABLED,
            command=self.start_download,
            style="TButton"
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancelar",
            state=tk.DISABLED,
            command=self.cancel_download,
            style="TButton"
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
    
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, pady=5, padx=10)
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Pronto para começar",
            style="Status.TLabel",
            foreground="blue",
            wraplength=700
        )
        self.status_label.pack(fill=tk.X)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_path)
        if folder:
            self.save_path = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, self.save_path)
    
    def get_video_info_threaded(self):
        if not self.downloading:
            self.video_url = self.url_entry.get().strip()
            if not self.video_url:
                messagebox.showerror("Erro", "Por favor, insira uma URL do YouTube válida")
                return
            
            self.toggle_buttons(False)
            self.clear_info()
            self.update_status("Obtendo informações do vídeo...", "blue")
            
            thread = threading.Thread(target=self.get_video_info, daemon=True)
            thread.start()
    
    def get_video_info(self):
        try:
            cmd = [
                self.yt_dlp_path,
                "--dump-json",
                "--no-warnings",
                "--no-check-certificate",
                self.video_url
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            self.video_info = json.loads(result.stdout)
            self.root.after(0, self.update_video_info)
            self.update_queue.put(("status", "Informações obtidas com sucesso! Clique em 'Baixar MP4' para continuar.", "green"))
            self.update_queue.put(("download_button", tk.NORMAL))
            
        except subprocess.CalledProcessError as e:
            error_msg = self.parse_error_message(e.stderr)
            self.handle_error(f"Erro ao obter informações:\n{error_msg}")
        except json.JSONDecodeError:
            self.handle_error("Erro ao processar informações do vídeo. URL pode ser inválida.")
        except Exception as e:
            self.handle_error(f"Erro inesperado: {str(e)}")
        finally:
            self.update_queue.put(("buttons", True))
    
    def parse_error_message(self, error_msg):
        if "This video is unavailable" in error_msg:
            return "Vídeo indisponível (pode ter sido removido ou é privado)"
        elif "Unable to download webpage" in error_msg:
            return "Não foi possível acessar o vídeo (verifique sua conexão)"
        elif "Unsupported URL" in error_msg:
            return "URL do YouTube inválida ou não suportada"
        elif error_msg.strip():
            return error_msg.strip()
        return "Erro desconhecido ao acessar o vídeo"
    
    def update_video_info(self):
        if not self.video_info:
            return
            
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info = f"📺 Título: {self.video_info.get('title', 'N/A')}\n"
        info += f"⏱ Duração: {self.format_duration(self.video_info.get('duration', 0))}\n"
        info += f"👤 Canal: {self.video_info.get('uploader', 'N/A')}\n"
        info += f"🔢 Visualizações: {self.video_info.get('view_count', 'N/A')}\n"
        
        best_format = self.get_best_mp4_format()
        if best_format:
            info += f"\n🎬 Melhor formato MP4 disponível:\n"
            info += f"📏 Resolução: {best_format.get('height', '?')}p\n"
            info += f"💾 Tamanho estimado: {self.format_size(best_format.get('filesize', 0))}\n"
            info += f"📦 Codec de vídeo: {best_format.get('vcodec', '?')}\n"
            info += f"🎵 Codec de áudio: {best_format.get('acodec', '?')}\n"
        else:
            info += "\n⚠️ Não foi possível determinar o melhor formato MP4\n"
        
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)
    
    def get_best_mp4_format(self):
        if not self.video_info or 'formats' not in self.video_info:
            return None
        
        mp4_formats = [
            f for f in self.video_info['formats'] 
            if f.get('vcodec') != 'none' 
            and f.get('acodec') != 'none'
            and f.get('ext', '').lower() == 'mp4'
        ]
        
        if not mp4_formats:
            return None
        
        return max(
            mp4_formats,
            key=lambda x: (
                x.get('height', 0),
                x.get('width', 0),
                x.get('tbr', 0)
            )
        )
    
    def format_duration(self, seconds):
        if not seconds:
            return "N/A"
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def format_size(self, bytes_size):
        if not bytes_size:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} GB"
    
    def start_download(self):
        if not self.downloading and self.video_info:
            self.downloading = True
            self.progress['value'] = 0
            self.cancel_button.config(state=tk.NORMAL)
            thread = threading.Thread(target=self.download_video, daemon=True)
            thread.start()
    
    def download_video(self):
        try:
            self.update_queue.put(("status", "Preparando download...", "blue"))
            os.makedirs(self.save_path, exist_ok=True)
            
            best_format = self.get_best_mp4_format()
            format_id = best_format['format_id'] if best_format else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
            
            cmd = [
                self.yt_dlp_path,
                "-f", format_id,
                "--merge-output-format", "mp4",
                "--no-part",
                "--no-check-certificate",
                "--newline",
                "-o", os.path.join(self.save_path, "%(title)s.%(ext)s"),
                self.video_url
            ]
            
            self.update_queue.put(("status", "Iniciando download...", "blue"))
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            progress_re = re.compile(r'\[download\]\s*(\d{1,3}\.\d)%')
            
            for line in self.process.stdout:
                if not self.downloading:  # Check for cancellation
                    self.process.terminate()
                    break
                
                progress_match = progress_re.search(line)
                if progress_match:
                    try:
                        progress = float(progress_match.group(1))
                        self.update_queue.put(("progress", progress))
                        self.update_queue.put(("status", f"Baixando: {progress:.1f}%", "blue"))
                    except ValueError:
                        pass
                elif "[download]" in line or "ETA" in line:
                    self.update_queue.put(("status", line.strip(), "blue"))
            
            self.process.wait()
            if self.process.returncode != 0 and self.downloading:
                raise subprocess.CalledProcessError(
                    self.process.returncode,
                    cmd,
                    output="Erro durante o download"
                )
            
            if self.downloading:
                self.update_queue.put(("status", "✅ Download concluído com sucesso!", "green"))
                self.update_queue.put(("messagebox", "Sucesso", f"Vídeo baixado e salvo em:\n{self.save_path}"))
        
        except subprocess.CalledProcessError as e:
            self.handle_error(f"Erro no download (código {e.returncode}):\n{e.output or 'Erro desconhecido'}")
        except Exception as e:
            self.handle_error(f"Erro inesperado: {str(e)}")
        finally:
            self.process = None
            self.downloading = False
            self.update_queue.put(("buttons", True))
            self.update_queue.put(("cancel_button", tk.DISABLED))
    
    def cancel_download(self):
        if self.downloading:
            self.downloading = False
            self.update_status("Cancelando download...", "red")
            if self.process:
                self.process.terminate()
    
    def clear_info(self):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.progress['value'] = 0
    
    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)
    
    def toggle_buttons(self, enable):
        state = tk.NORMAL if enable else tk.DISABLED
        self.fetch_button.config(state=state)
        self.download_button.config(state=state if self.video_info else tk.DISABLED)
        self.cancel_button.config(state=tk.DISABLED if not self.downloading else tk.NORMAL)
    
    def handle_error(self, error_msg):
        self.update_queue.put(("status", f"❌ {error_msg}", "red"))
        self.update_queue.put(("messagebox", "Erro", error_msg))
        self.update_queue.put(("clear_info",))
        self.downloading = False
        self.update_queue.put(("buttons", True))
    
    def process_ui_updates(self):
        try:
            while True:
                update = self.update_queue.get_nowait()
                action, *args = update
                if action == "status":
                    self.update_status(*args)
                elif action == "progress":
                    self.progress['value'] = args[0]
                elif action == "buttons":
                    self.toggle_buttons(args[0])
                elif action == "download_button":
                    self.download_button.config(state=args[0])
                elif action == "cancel_button":
                    self.cancel_button.config(state=args[0])
                elif action == "messagebox":
                    messagebox.showinfo(*args) if args[0] == "Sucesso" else messagebox.showerror(*args)
                elif action == "clear_info":
                    self.clear_info()
        except queue.Empty:
            pass
        self.root.after(100, self.process_ui_updates)
    
    def on_closing(self):
        if self.downloading:
            if messagebox.askyesno("Confirmar", "Um download está em andamento. Deseja cancelar e fechar?"):
                self.cancel_download()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    
    window_width = 750
    window_height = 550
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    app = YouTubeDownloader(root)
    root.mainloop()
