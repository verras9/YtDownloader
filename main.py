import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pytube import YouTube
from pytube.exceptions import RegexMatchError, VideoUnavailable, PytubeError
import os
import threading
import time
import random
from urllib.error import HTTPError
from fake_useragent import UserAgent

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Ultra")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        self.user_agent = UserAgent()
        self.max_retries = 3
        self.retry_delay = 5
        
        self.video_url = ""
        self.save_path = os.path.expanduser("~/Downloads")
        self.downloading = False
        self.yt = None
        
        self.setup_styles()
        self.create_widgets()
        self.create_menu()
    
    def setup_styles(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, font=('Arial', 10))
        style.configure("TLabel", font=('Arial', 10))
        style.configure("Title.TLabel", font=('Arial', 14, 'bold'))
        style.configure("Status.TLabel", font=('Arial', 9))
        style.configure("Info.TFrame", background="#f0f0f0")
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Mudar User-Agent", command=self.set_user_agent)
        config_menu.add_command(label="Configurar Tentativas", command=self.set_retries)
        menubar.add_cascade(label="Configurações", menu=config_menu)
        
        self.root.config(menu=menubar)
    
    def set_user_agent(self):
        new_agent = simpledialog.askstring(
            "User-Agent",
            "Digite um User-Agent personalizado (ou deixe em branco para aleatório):",
            parent=self.root
        )
        if new_agent:
            self.user_agent = lambda: new_agent
            messagebox.showinfo("Sucesso", f"User-Agent definido como:\n{new_agent}")
    
    def set_retries(self):
        retries = simpledialog.askinteger(
            "Tentativas",
            "Número máximo de tentativas (3-10):",
            parent=self.root,
            minvalue=3,
            maxvalue=10
        )
        if retries:
            self.max_retries = retries
            messagebox.showinfo("Sucesso", f"Máximo de tentativas: {retries}")
    
    def create_widgets(self):

        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        ttk.Label(
            title_frame,
            text="YouTube Downloader Ultra",
            style="Title.TLabel"
        ).pack()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="URL do YouTube:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_frame, text="Pasta de destino:").pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(folder_frame, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.folder_entry.insert(0, self.save_path)
        ttk.Button(
            folder_frame,
            text="Procurar",
            command=self.browse_folder
        ).pack(side=tk.LEFT)
        
        self.info_frame = ttk.LabelFrame(main_frame, text="Informações do Vídeo", style="Info.TFrame")
        self.info_frame.pack(fill=tk.BOTH, pady=10, expand=True)
        
        self.info_text = tk.Text(
            self.info_frame,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Arial', 9),
            padx=5,
            pady=5
        )
        scrollbar = ttk.Scrollbar(self.info_frame, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        self.progress = ttk.Progressbar(
            main_frame,
            orient=tk.HORIZONTAL,
            length=550,
            mode='determinate'
        )
        self.progress.pack(pady=10)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.fetch_button = ttk.Button(
            button_frame,
            text="Obter Informações",
            command=self.get_video_info_threaded
        )
        self.fetch_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(
            button_frame,
            text="Baixar MP4",
            state=tk.DISABLED,
            command=self.start_download
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(
            self.root,
            text="Pronto para começar",
            style="Status.TLabel",
            foreground="blue"
        )
        self.status_label.pack(pady=5)
    
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
                messagebox.showerror("Erro", "Por favor, insira uma URL do YouTube")
                return
            
            thread = threading.Thread(target=self.get_video_info_with_retry, daemon=True)
            thread.start()
    
    def get_video_info_with_retry(self, attempt=1):
        try:
            self.toggle_buttons(False)
            self.update_status(f"Conectando... (Tentativa {attempt}/{self.max_retries})", "orange")
            
            time.sleep(random.uniform(1.0, 3.0))
            
            self.yt = YouTube(
                self.video_url,
                on_progress_callback=self.progress_function,
                on_complete_callback=self.complete_function,
                use_oauth=False,
                allow_oauth_cache=False
            )
            
            self.yt.bypass_age_gate()
            
            if not self.yt.vid_info:
                raise PytubeError("Resposta vazia do YouTube")
            
            self.update_video_info()
            self.update_status("Informações obtidas com sucesso!", "green")
            self.download_button.config(state=tk.NORMAL)
            
        except (HTTPError, ConnectionError) as e:
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt
                self.update_status(f"Erro 403. Tentando novamente em {wait_time}s...", "orange")
                time.sleep(wait_time)
                self.get_video_info_with_retry(attempt + 1)
            else:
                self.handle_403_error(e)
        except Exception as e:
            self.handle_error(e)
        finally:
            self.toggle_buttons(True)
    
    def update_video_info(self):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info = f"▶ Título: {self.yt.title}\n"
        info += f"⏱ Duração: {self.yt.length // 60}:{self.yt.length % 60:02d}\n"
        info += f"👤 Autor: {self.yt.author}\n"
        info += f"👀 Visualizações: {self.yt.views:,}\n"
        info += f"\n📦 Formatos disponíveis:\n"
        
        streams = self.yt.streams.filter(
            progressive=True,
            file_extension='mp4'
        ).order_by('resolution').desc()
        
        for stream in streams:
            info += f"- {stream.resolution} ({stream.filesize_mb:.1f} MB)\n"
        
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)
    
    def start_download(self):
        if not self.downloading and self.yt:
            self.downloading = True
            thread = threading.Thread(target=self.download_video, daemon=True)
            thread.start()
    
    def download_video(self):
        try:
            self.update_status("Preparando download...", "orange")
            
            stream = self.yt.streams.filter(
                progressive=True,
                file_extension='mp4'
            ).order_by('resolution').desc().first()
            
            if not stream:
                raise PytubeError("Nenhum formato MP4 disponível")
            
            self.update_status(f"Baixando: {stream.resolution}...", "orange")
            
            temp_path = os.path.join(self.save_path, f"temp_{time.time()}")
            os.makedirs(temp_path, exist_ok=True)
            
            stream.download(
                output_path=temp_path,
                skip_existing=False,
                timeout=30
            )
            
            downloaded_file = os.listdir(temp_path)[0]
            final_path = os.path.join(self.save_path, downloaded_file)
            os.rename(os.path.join(temp_path, downloaded_file), final_path)
            os.rmdir(temp_path)
            
            self.complete_function(stream, final_path)
            
        except HTTPError as e:
            if e.code == 403:
                self.handle_403_error(e)
            else:
                self.handle_error(e)
        except Exception as e:
            self.handle_error(e)
        finally:
            self.downloading = False
            self.toggle_buttons(True)
    
    def progress_function(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        
        self.progress['value'] = percentage
        self.update_status(
            f"Baixando: {percentage:.1f}% | "
            f"{bytes_downloaded/1024/1024:.1f}MB de {total_size/1024/1024:.1f}MB",
            "orange"
        )
    
    def complete_function(self, stream, file_path):
        self.progress['value'] = 100
        self.update_status(
            f"✅ Download completo!\n{os.path.basename(file_path)}",
            "green"
        )
        messagebox.showinfo("Sucesso", f"Vídeo salvo em:\n{file_path}")
    
    def update_status(self, message, color="black"):
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()
    
    def toggle_buttons(self, enable):
        state = tk.NORMAL if enable else tk.DISABLED
        self.fetch_button.config(state=state)
        self.download_button.config(state=state if self.yt else tk.DISABLED)
        self.root.update_idletasks()
    
    def handle_403_error(self, error):
        error_msg = (
            "Erro 403: Acesso negado pelo YouTube.\n\n"
            "Possíveis soluções:\n"
            "1. Tente novamente mais tarde\n"
            "2. Use uma VPN\n"
            "3. Mude o User-Agent nas configurações\n"
            "4. Atualize o pytube (pip install pytube --upgrade)\n"
            "5. Reinicie o programa"
        )
        self.update_status("Erro 403: Acesso negado", "red")
        messagebox.showerror("Erro de Acesso", error_msg)
        self.reset_interface()
    
    def handle_error(self, error):
        error_msg = str(error)
        if "HTTP Error 403" in error_msg:
            self.handle_403_error(error)
        else:
            self.update_status(f"Erro: {error_msg}", "red")
            messagebox.showerror("Erro", error_msg)
            self.reset_interface()
    
    def reset_interface(self):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        self.progress['value'] = 0

if __name__ == "__main__":
    try:
        from pytube import __main__
        __main__.main()
    except:
        pass
    
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
