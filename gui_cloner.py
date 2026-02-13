import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import asyncio
import os
import sys
import json
import logging
from colorama import Fore, Style, init
from tqdm import tqdm

# --- AYARLAR ---
# Logging
logging.getLogger('discord').setLevel(logging.CRITICAL)
logging.getLogger('discord.http').setLevel(logging.CRITICAL)
logging.getLogger('discord.client').setLevel(logging.CRITICAL)
logging.getLogger('discord.gateway').setLevel(logging.CRITICAL)

# Console Output'u yönlendirmek için
class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str):
        self.text_widget.after(0, self._insert, str)

    def _insert(self, str):
        self.text_widget.configure(state='normal')
        
        # Renk Belirleme (Basit Gradyan Simülasyonu)
        # Satır sayısına göre renk değiştir
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        colors = ["#00FF00", "#00FFFF", "#00BFFF", "#FF00FF", "#FFD700"]
        color = colors[line_count % len(colors)]
        
        tag_name = f"color_{line_count}"
        self.text_widget.tag_config(tag_name, foreground=color)
        
        self.text_widget.insert(tk.END, str, (tag_name,))
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass

# --- MONKEY PATCHES (Aynı kalacak) ---
try:
    from discord.enums import FriendFlags
    original_from_dict = FriendFlags._from_dict
    @classmethod
    def patched_from_dict(cls, data):
        if data is None: data = {}
        return original_from_dict.__func__(cls, data)
    FriendFlags._from_dict = patched_from_dict
except: pass

try:
    from discord.settings import Settings
    original_settings_init = Settings.__init__
    def patched_settings_init(self, *args, **kwargs): pass
    Settings.__init__ = patched_settings_init
except: pass

import discord

# --- CUSTOM WIDGETS ---
class CustomCheckbox(tk.Label):
    def __init__(self, parent, text, variable, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.variable = variable
        self.text_label = text
        self.variable.trace_add('write', self.update_view)
        self.bind("<Button-1>", self.toggle)
        self.cursor = "hand2"
        self.configure(cursor=self.cursor, font=("Segoe UI", 11))
        self.update_view()

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())

    def update_view(self, *args):
        state = self.variable.get()
        symbol = "✅" if state else "❌"
        # Green for checked, Red for unchecked
        color = "#3BA55C" if state else "#ED4245" 
        self.config(text=f"{symbol} {self.text_label}", fg=color)


# --- ANA GUI SINIFI ---
class ClonerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Server Cloner (Self-Bot)")
        self.root.geometry("650x550")
        self.root.configure(bg="#1E1E1E") # Daha koyu, modern siyah
        
        # Stil Ayarları
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern Stil Tanımlamaları
        style.configure("TLabel", background="#1E1E1E", foreground="#CCCCCC", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#FFFFFF")
        
        # Buton Stili (Modern)
        style.configure("TButton", 
                        background="#5865F2", # Discord Mavisi
                        foreground="white", 
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        focuscolor="none")
        style.map("TButton", background=[("active", "#4752C4")]) # Hover rengi
        
        # Progress Bar Stili
        style.configure("TProgressbar", 
                        thickness=25, 
                        troughcolor="#2F3136", 
                        background="#3BA55C") # Yeşil

        # --- ARAYÜZ ELEMANLARI ---
        
        # Ana Frame (Padding için)
        main_frame = tk.Frame(root, bg="#1E1E1E")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Credits (EN ÜSTTE)
        tk.Label(main_frame, text="ThrustHUB - Berkaycimh", bg="#1E1E1E", fg="#5865F2", font=("Segoe UI", 10, "bold")).pack(pady=(0, 15))

        # 1. Token Girişi
        tk.Label(main_frame, text="USER TOKEN", bg="#1E1E1E", fg="#99AAB5", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.token_entry = tk.Entry(main_frame, width=60, show="•", bg="#2F3136", fg="white", bd=0, insertbackground="white", font=("Consolas", 10))
        self.token_entry.pack(fill="x", pady=(5, 15), ipady=8)
        
        # 2. Seçenekler (Checkboxlar)
        self.options_frame = tk.Frame(main_frame, bg="#1E1E1E")
        self.options_frame.pack(fill="x", pady=(0, 10))

        # Değişkenler
        self.var_settings = tk.BooleanVar(value=True)
        self.var_roles = tk.BooleanVar(value=True)
        self.var_channels = tk.BooleanVar(value=True)
        self.var_emojis = tk.BooleanVar(value=True)

        # Checkbox Stili
        style.configure("TCheckbutton", background="#1E1E1E", foreground="#CCCCCC", font=("Segoe UI", 9))

        # Checkboxları Yan Yana Dizme
        # Checkboxları Yan Yana Dizme
        # CustomCheckbox(parent, text, variable)
        
        cb_settings = CustomCheckbox(self.options_frame, text="Ayarlar & İkon", variable=self.var_settings, bg="#1E1E1E")
        cb_settings.pack(side="left", padx=10)
        
        cb_roles = CustomCheckbox(self.options_frame, text="Roller", variable=self.var_roles, bg="#1E1E1E")
        cb_roles.pack(side="left", padx=10)
        
        cb_channels = CustomCheckbox(self.options_frame, text="Kanallar", variable=self.var_channels, bg="#1E1E1E")
        cb_channels.pack(side="left", padx=10)
        
        cb_emojis = CustomCheckbox(self.options_frame, text="Emojiler", variable=self.var_emojis, bg="#1E1E1E")
        cb_emojis.pack(side="left", padx=10)

        # 3. Bağlan Butonu
        self.connect_btn = ttk.Button(main_frame, text="BAĞLAN VE BAŞLA", command=self.start_login_thread)
        self.connect_btn.pack(fill="x", pady=5)

        # 3. Nuke Butonu (Yeni)
        self.nuke_btn = tk.Button(main_frame, text="☢️ SUNUCUYU SIFIRLA (NUKE)", bg="#ED4245", fg="white", 
                                  font=("Segoe UI", 9, "bold"), bd=0, activebackground="#C03537", 
                                  activeforeground="white", cursor="hand2", command=self.start_nuke_thread)
        self.nuke_btn.pack(fill="x", pady=(0, 10))

        # 4. Durum / Log Penceresi
        tk.Label(main_frame, text="İŞLEM GÜNLÜĞÜ", bg="#1E1E1E", fg="#99AAB5", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5, 5))
        self.log_text = tk.Text(main_frame, height=12, bg="#000000", fg="#00FF00", 
                                font=("Consolas", 9), bd=0, padx=10, pady=10, state='disabled')
        self.log_text.pack(fill="both", expand=True)
        
        # Console Yönlendirme
        sys.stdout = ConsoleRedirector(self.log_text)
        sys.stderr = ConsoleRedirector(self.log_text)

        # 4. Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(15, 5))
        
        self.status_label = tk.Label(main_frame, text="Hazır", bg="#1E1E1E", fg="#FFFFFF", font=("Segoe UI", 9))
        self.status_label.pack()
        
        # 5. Tamamlanan İşlemler Tablosu (Sol Alt)
        self.status_frame = tk.Frame(main_frame, bg="#2F3136", bd=0)
        self.status_frame.pack(fill="x", pady=15)

        self.status_items = {
            "AYARLAR": tk.Label(self.status_frame, text="BEKLİYOR", bg="#2F3136", fg="#72767D", font=("Segoe UI", 8)),
            "ROLLER": tk.Label(self.status_frame, text="BEKLİYOR", bg="#2F3136", fg="#72767D", font=("Segoe UI", 8)),
            "KANALLAR": tk.Label(self.status_frame, text="BEKLİYOR", bg="#2F3136", fg="#72767D", font=("Segoe UI", 8)),
            "EMOJİLER": tk.Label(self.status_frame, text="BEKLİYOR", bg="#2F3136", fg="#72767D", font=("Segoe UI", 8))
        }

        # Grid Layout (Daha düzenli)
        col = 0
        for name, widget in self.status_items.items():
            # Başlık (Gradyan yerine renkli)
            # Renkler: Cyan -> Blue -> Purple -> Pink (Manuel gradyan efekti)
            colors = ["#00FFFF", "#00BFFF", "#BF00FF", "#FF00FF"]
            tk.Label(self.status_frame, text=name, bg="#2F3136", fg=colors[col], font=("Segoe UI", 9, "bold")).grid(row=0, column=col, padx=10, pady=5, sticky="ew")
            widget.grid(row=1, column=col, padx=10, pady=(0, 5), sticky="ew")
            self.status_frame.grid_columnconfigure(col, weight=1)
            col += 1

        # Değişkenler
        self.client = None
        self.loop = None

    def mark_completed(self, item):
        if item in self.status_items:
             self.status_items[item].config(text="TAMAMLANDI", fg="#3BA55C", font=("Segoe UI", 8, "bold"))

    def log(self, message):
        # Konsola (ve log_text'e) yaz
        print(message)
        
        # Log Text'e renkli (gradyan) ekleme yapabilmek için özel işlem
        # Ancak sys.stdout yönlendirildiği için print otomatik oraya gidiyor.
        # Bu yüzden burada gradyan yaparsak, print'in çıktısını ezmemiz veya print yerine bunu kullanmamız lazım.
        # En iyisi stdout yönlendirmesini iptal edip, bu fonksiyonu kullanmak.
        pass

    def _insert_gradient(self, text):
        # Basit bir gradyan efekti (Yeşil -> Mavi -> Mor)
        # Tkinter'da her karaktere tag atamak performansı öldürür.
        # Satır bazlı renk değişimi daha mantıklı.
        
        # Renk Paleti (RGB)
        colors = ["#00FF00", "#00FFFF", "#0000FF", "#FF00FF"]
        # Rastgele veya sırayla renk seç
        import random
        color = colors[len(self.log_text.get("1.0", tk.END).splitlines()) % len(colors)]
        
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, text + "\n", ("gradient",))
        # Tag'e renk ata (Her satır aynı renk olacak ama satırlar farklı renk)
        # Maalesef tkinter tag sistemi biraz karışık.
        # En basiti: Tek renk (Cyan/Yeşil) yerine, belirli anahtar kelimelere göre renk verelim.
        
        # Log text varsayılan rengi zaten yeşil (#00FF00).
        # Biz sadece belirli kısımları renklendirelim.
        pass

    def start_login_thread(self):
        token = self.token_entry.get().strip().replace('"', '')
        if not token:
            messagebox.showerror("Hata", "Lütfen token girin!")
            return
        
        self.connect_btn.config(state='disabled')
        self.log("Giriş yapılıyor...")
        
        # Thread içinde asyncio loop başlat
        threading.Thread(target=self.run_bot, args=(token,), daemon=True).start()

    def start_nuke_thread(self):
        token = self.token_entry.get().strip().replace('"', '')
        if not token:
            messagebox.showerror("Hata", "Lütfen token girin!")
            return
        
        # Onay İste
        if not messagebox.askyesno("DİKKAT", "Bu işlem hedef sunucudaki HER ŞEYİ (Kanallar, Roller, Emojiler) SİLECEK!\n\nEmin misiniz?"):
            return

        self.connect_btn.config(state='disabled')
        self.nuke_btn.config(state='disabled')
        self.log("Nuke işlemi başlatılıyor...")
        
        threading.Thread(target=self.run_nuke, args=(token,), daemon=True).start()

    def run_nuke(self, token):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        client = GUIClonerClient(token, self)
        client.is_nuke_mode = True # Nuke modu bayrağı
        
        try:
            self.loop.run_until_complete(client.start(token))
        except discord.errors.LoginFailure:
            self.log("HATA: Token geçersiz!")
            self.root.after(0, lambda: self.connect_btn.config(state='normal'))
            self.root.after(0, lambda: self.nuke_btn.config(state='normal'))
        except Exception as e:
            self.log(f"HATA: {e}")
            self.root.after(0, lambda: self.connect_btn.config(state='normal'))
            self.root.after(0, lambda: self.nuke_btn.config(state='normal'))

    def run_bot(self, token):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.client = GUIClonerClient(token, self)
        try:
            self.loop.run_until_complete(self.client.start(token))
        except discord.errors.LoginFailure:
            self.log("HATA: Token geçersiz!")
            self.root.after(0, lambda: self.connect_btn.config(state='normal'))
        except Exception as e:
            self.log(f"HATA: {e}")
            self.root.after(0, lambda: self.connect_btn.config(state='normal'))

# --- DISCORD CLIENT ---
class GUIClonerClient(discord.Client):
    def __init__(self, token, gui):
        super().__init__()
        self.token = token
        self.gui = gui
        self.source_guild = None
        self.target_guild = None
        self.total_steps = 0
        self.current_step = 0
        self.is_nuke_mode = False # Varsayılan: False
        self.role_mapping = {}

    async def on_ready(self):
        self.gui.log(f"Giriş Başarılı: {self.user}")
        
        # Nuke Modu Kontrolü
        if self.is_nuke_mode:
            # Sadece Hedef Sunucu Sor
            future_id = self.loop.create_future()
            self.gui.root.after(0, self.ask_target_id, future_id)
            target_id_str = await future_id
            
            if not target_id_str:
                self.gui.log("İşlem iptal edildi.")
                await self.close()
                return
                
            try:
                self.target_guild = self.get_guild(int(target_id_str))
                if not self.target_guild:
                    self.gui.log("HATA: Hedef sunucu bulunamadı.")
                    await self.close()
                    return
            except:
                 self.gui.log("HATA: Geçersiz ID.")
                 await self.close()
                 return

            self.gui.log(f"NUKE HEDEFİ: {self.target_guild.name}")
            await self.start_nuke()
            return

        # Normal Klonlama Modu (Devam ediyor...)
        # Sunucuları Listele ve Seçtir (GUI thread'inde popup aç)
        guilds = list(self.guilds)
        guild_names = [f"{g.name} ({g.id})" for g in guilds]
        
        # Seçim için GUI thread'ine dönmemiz lazım ama basit olması için 
        # burada bekleyen bir input mekanizması zor. 
        # En iyisi ayrı bir pencere açmak.
        
        # Asyncio içinde blocking GUI çağrısı yapamayız.
        # Bu yüzden seçimi ana thread'e yaptırıp sonucu bekleyeceğiz.
        
        future = self.loop.create_future()
        self.gui.root.after(0, self.ask_source_guild, guild_names, future)
        idx = await future
        
        if idx is None:
            self.gui.log("İşlem iptal edildi.")
            await self.close()
            return

        self.source_guild = guilds[idx]
        self.gui.log(f"Kaynak Seçildi: {self.source_guild.name}")
        
        # Hedef ID İste
        future_id = self.loop.create_future()
        self.gui.root.after(0, self.ask_target_id, future_id)
        target_id_str = await future_id
        
        if not target_id_str:
            self.gui.log("İşlem iptal edildi.")
            await self.close()
            return
            
        try:
            self.target_guild = self.get_guild(int(target_id_str))
            if not self.target_guild:
                self.gui.log("HATA: Hedef sunucu bulunamadı (ID yanlış veya sunucuda yoksunuz).")
                await self.close()
                return
        except:
             self.gui.log("HATA: Geçersiz ID formatı.")
             await self.close()
             return

        self.gui.log(f"Hedef Seçildi: {self.target_guild.name}")
        await self.start_cloning()

    def ask_source_guild(self, options, future):
        top = tk.Toplevel(self.gui.root)
        top.title("Kopyalanacak Sunucuyu Seç")
        top.geometry("350x450")
        top.configure(bg="#1E1E1E")

        tk.Label(top, text="Lütfen kopyalamak istediğiniz sunucuyu seçin:", bg="#1E1E1E", fg="#FFFFFF", font=("Segoe UI", 10)).pack(pady=10)

        lb = tk.Listbox(top, bg="#2F3136", fg="#FFFFFF", font=("Segoe UI", 10), selectbackground="#5865F2")
        lb.pack(fill="both", expand=True, padx=10, pady=5)

        for opt in options:
            lb.insert(tk.END, opt)

        def on_select():
            sel = lb.curselection()
            if sel:
                top.destroy()
                self.gui.root.after(0, lambda: self.safe_set_result(future, sel[0]))
            else:
                messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!", parent=top)

        btn = tk.Button(top, text="SEÇ", bg="#5865F2", fg="white", font=("Segoe UI", 10, "bold"), command=on_select)
        btn.pack(pady=10, fill="x", padx=10)

        def on_close():
             top.destroy()
             if not future.done():
                 self.gui.root.after(0, lambda: self.safe_set_result(future, None))
        top.protocol("WM_DELETE_WINDOW", on_close)

    def ask_target_id(self, future):
        title = "Hedef Sunucu (NUKE)" if self.is_nuke_mode else "Hedef Sunucu"
        msg = "SIFIRLANACAK (NUKE) sunucunun ID'sini girin:" if self.is_nuke_mode else "Lütfen boş bir sunucu kurun ve ID'sini girin:"
        
        ans = simpledialog.askstring(title, msg)
        # self.gui.loop.call_soon_threadsafe(future.set_result, ans)
        self.gui.root.after(0, lambda: self.safe_set_result(future, ans))

    def safe_set_result(self, future, result):
        if not future.done():
            self.loop.call_soon_threadsafe(future.set_result, result)

    async def start_nuke(self):
        self.gui.log("\n[☢️] NUKE İŞLEMİ BAŞLATILIYOR...")
        
        # İstatistikler
        items_to_delete = len(self.target_guild.channels) + len(self.target_guild.roles) + len(self.target_guild.emojis)
        self.total_steps = items_to_delete
        
        try:
            # Kanallar
            for ch in self.target_guild.channels:
                try:
                    await ch.delete()
                    self.gui.log(f"Silindi: {ch.name}")
                except Exception as e:
                    self.gui.log(f"Silinemedi ({ch.name}): {e}")
                await self.update_progress("Nuke: Kanallar")
                await asyncio.sleep(0.2)

            # Roller
            for role in self.target_guild.roles:
                if role.name != "@everyone" and not role.managed:
                    try:
                        await role.delete()
                        self.gui.log(f"Silindi: {role.name}")
                    except Exception as e:
                        self.gui.log(f"Silinemedi ({role.name}): {e}")
                    await self.update_progress("Nuke: Roller")
                    await asyncio.sleep(0.2)

            # Emojiler
            for emoji in self.target_guild.emojis:
                try:
                    await emoji.delete()
                    self.gui.log(f"Silindi: {emoji.name}")
                except Exception as e:
                    self.gui.log(f"Silinemedi ({emoji.name}): {e}")
                await self.update_progress("Nuke: Emojiler")
                await asyncio.sleep(0.2)

            self.gui.log("\n[SUCCESS] NUKE TAMAMLANDI! SUNUCU TERTEMİZ.")
            self.gui.root.after(0, lambda: messagebox.showinfo("Başarılı", "Sunucu başarıyla sıfırlandı!"))

        except Exception as e:
            self.gui.log(f"HATA: {e}")
        finally:
            await self.close()

    async def update_progress(self, step_name):
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        
        # GUI güncelleme (Thread-safe)
        self.gui.root.after(0, lambda: self.gui.progress_var.set(percentage))
        self.gui.root.after(0, lambda: self.gui.status_label.config(text=f"{step_name} ({int(percentage)}%)"))
        
        # Ufak bir delay
        await asyncio.sleep(0.01)

    async def start_cloning(self):
        self.gui.log("\n[+] Klonlama Başlıyor...")
        
        # Seçimleri Al (GUI thread'inden güvenli bir şekilde alınmalı, ancak BooleanVar thread-safe genelde sorun çıkarmaz, yine de dikkatli olalım)
        # Değerleri başlatma sırasında gui nesnesinden okuyacağız.
        
        do_settings = self.gui.var_settings.get()
        do_roles = self.gui.var_roles.get()
        do_channels = self.gui.var_channels.get()
        do_emojis = self.gui.var_emojis.get()

        channel_count = len(self.source_guild.channels) if do_channels else 0
        role_count = len([r for r in self.source_guild.roles if r.name != "@everyone" and not r.managed]) if do_roles else 0
        emoji_count = len(self.source_guild.emojis) if do_emojis else 0
        
        self.total_steps = channel_count + role_count + emoji_count + 5 
        
        self.gui.log(f"[*] Seçilen İşlemler: {'Ayarlar, ' if do_settings else ''}{'Roller, ' if do_roles else ''}{'Kanallar, ' if do_channels else ''}{'Emojiler' if do_emojis else ''}")

        try:
            # 1. Temizlik (Sadece seçilenleri temizle)
            await self.update_progress("Temizleniyor")
            if do_channels or do_roles:
                await self.cleanup_target(do_channels, do_roles)

            # 2. Ayarlar
            if do_settings:
                await self.update_progress("Ayarlar")
                await self.clone_server_settings()
                self.gui.root.after(0, lambda: self.gui.mark_completed("AYARLAR"))
            else:
                 self.gui.root.after(0, lambda: self.gui.status_items["AYARLAR"].config(text="ATLANDI", fg="#FAA61A"))

            # 3. Roller
            if do_roles:
                await self.update_progress("Roller")
                await self.clone_roles()
                self.gui.root.after(0, lambda: self.gui.mark_completed("ROLLER"))
            else:
                self.gui.root.after(0, lambda: self.gui.status_items["ROLLER"].config(text="ATLANDI", fg="#FAA61A"))

            # 4. Kanallar
            if do_channels:
                await self.update_progress("Kanallar")
                await self.clone_channels()
                self.gui.root.after(0, lambda: self.gui.mark_completed("KANALLAR"))
            else:
                self.gui.root.after(0, lambda: self.gui.status_items["KANALLAR"].config(text="ATLANDI", fg="#FAA61A"))

            # 5. Emojiler
            if do_emojis:
                await self.update_progress("Emojiler")
                await self.clone_emojis()
                self.gui.root.after(0, lambda: self.gui.mark_completed("EMOJİLER"))
            else:
                self.gui.root.after(0, lambda: self.gui.status_items["EMOJİLER"].config(text="ATLANDI", fg="#FAA61A"))

            self.gui.log("\n[SUCCESS] İŞLEM TAMAMLANDI!")
            self.gui.root.after(0, lambda: messagebox.showinfo("Başarılı", "Klonlama tamamlandı!"))
            
        except Exception as e:
            self.gui.log(f"HATA: {e}")
        finally:
            await self.close()

    # --- KLONLAMA FONKSİYONLARI (Progress Bar Entegreli) ---
    async def cleanup_target(self, do_channels=True, do_roles=True):
        # Kanallar
        if do_channels:
            self.gui.log("[*] Kanallar temizleniyor...")
            for ch in self.target_guild.channels:
                try:
                    await ch.delete()
                except Exception as e:
                     self.gui.log(f"[-] Kanal silinemedi ({ch.name}): {e}")
        # Roller
        if do_roles:
            self.gui.log("[*] Roller temizleniyor...")
            for role in self.target_guild.roles:
                if role.name != "@everyone" and not role.managed:
                    try:
                        await role.delete()
                    except discord.Forbidden:
                        self.gui.log(f"[-] Rol silinemedi ({role.name}): Yetki Yetersiz (Rol hiyerarşisini kontrol edin)")
                    except Exception as e:
                        self.gui.log(f"[-] Rol silinemedi ({role.name}): {e}")

    async def clone_server_settings(self):
        # İsim Değiştirme
        if self.target_guild.name != self.source_guild.name:
            await self.target_guild.edit(name=self.source_guild.name)
            self.gui.log(f"[+] Sunucu ismi güncellendi: {self.source_guild.name}")
        
        # İkon Değiştirme
        if self.source_guild.icon:
            self.gui.log("[*] Sunucu ikonu kopyalanıyor...")
            try:
                icon_data = await self.source_guild.icon.read()
                await self.target_guild.edit(icon=icon_data)
                self.gui.log("[+] İkon başarıyla güncellendi.")
            except Exception as e_read:
                self.gui.log(f"[-] İkon okuma hatası: {e_read}. HTTP yntemi deneniyor...")
                # Fallback http
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(str(self.source_guild.icon.url)) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                await self.target_guild.edit(icon=data)
                                self.gui.log("[+] İkon (HTTP) başarıyla güncellendi.")
                            else:
                                self.gui.log(f"[-] İkon indirilemedi. HTTP Status: {resp.status}")
                except Exception as e_http:
                     self.gui.log(f"[-] İkon yükleme hatası (HTTP): {e_http}")
        else:
             self.gui.log("[i] Kaynak sunucunun ikonu yok.")

    async def clone_roles(self):
        roles = [r for r in self.source_guild.roles if r.name != "@everyone" and not r.managed]
        roles.reverse()
        for role in roles:
            try:
                new_role = await self.target_guild.create_role(
                    name=role.name, permissions=role.permissions, colour=role.colour,
                    hoist=role.hoist, mentionable=role.mentionable
                )
                self.role_mapping[role.id] = new_role
            except: pass
            await self.update_progress(f"Rol: {role.name}")
            await asyncio.sleep(0.5)

    async def clone_channels(self):
        categories = sorted(self.source_guild.categories, key=lambda c: c.position)
        for category in categories:
            overwrites = self.get_overwrites(category.overwrites)
            try:
                new_cat = await self.target_guild.create_category(name=category.name, overwrites=overwrites, position=category.position)
                for ch in category.channels:
                    await self.clone_single_channel(ch, new_cat)
                    await self.update_progress(f"Kanal: {ch.name}")
            except: pass
        
        # Kategorisiz
        for ch in [c for c in self.source_guild.channels if c.category is None]:
            await self.clone_single_channel(ch, None)
            await self.update_progress(f"Kanal: {ch.name}")

    async def clone_single_channel(self, channel, category):
        overwrites = self.get_overwrites(channel.overwrites)
        try:
            if isinstance(channel, discord.TextChannel):
                await self.target_guild.create_text_channel(name=channel.name, category=category, overwrites=overwrites, topic=channel.topic, nsfw=channel.nsfw, position=channel.position)
            elif isinstance(channel, discord.VoiceChannel):
                await self.target_guild.create_voice_channel(name=channel.name, category=category, overwrites=overwrites, user_limit=channel.user_limit, position=channel.position)
        except: pass
        await asyncio.sleep(0.5)

    def get_overwrites(self, original):
        new = {}
        if not hasattr(self, 'role_mapping'): self.role_mapping = {}
        for t, o in original.items():
            if isinstance(t, discord.Role) and t.id in self.role_mapping:
                new[self.role_mapping[t.id]] = o
        return new

    async def clone_emojis(self):
        for emoji in self.source_guild.emojis:
            try:
                # Önce normal read dene
                try:
                    data = await emoji.read()
                except:
                    # Fallback http
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(str(emoji.url)) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                            else:
                                raise Exception("HTTP Error")
                
                await self.target_guild.create_custom_emoji(name=emoji.name, image=data)
            except Exception as e:
                 self.gui.log(f"Emoji Hatası ({emoji.name}): {e}")
            
            await self.update_progress(f"Emoji: {emoji.name}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClonerGUI(root)
    root.mainloop()
