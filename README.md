# Discord Server Cloner (Self-Bot)

Bu araç, bir Discord sunucusunu (Roller, Kanallar, Emojiler, İsim ve İkon) başka bir sunucuya kopyalamanızı sağlar.

## ⚠️ Yasal Uyarı
Bu yazılım **eğitim amaçlıdır**. Self-bot kullanımı Discord Hizmet Koşulları'na (ToS) aykırıdır. Hesabınızın kapatılması gibi riskler tamamen **kullanıcı sorumluluğundadır**.

## 🚀 Özellikler
- Sunucu İsmi ve İkonu Kopyalama
- Rolleri (Renkler, İzinler, Hiyerarşi) Kopyalama
- Kategorileri ve Kanalları (İzinlerle) Kopyalama
- Emojileri Kopyalama
- **Otomatik Token Bulucu** (Kendi bilgisayarınızdaki tokeni bulmak için)

## 📦 Kurulum

1. Python'u yükleyin (3.8 veya üzeri).
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ Kullanım

### 1. Tokeninizi Bulun (Opsiyonel)
Eğer tokeninizi bilmiyorsanız, kendi bilgisayarınızdaki tokeni bulmak için:
```bash
python get_my_token.py
```
Bu komut size en güncel ve çalışan tokeninizi verecektir.

### 2. Kopyalayıcıyı Çalıştırın
```bash
python copyserver.py
```
Veya `DiscordServerCloner.exe` dosyasını çalıştırın.

Program sizden şunları isteyecektir:
- **User Token:** (1. adımda bulduğunuz veya bildiğiniz token)
- **Source ID:** Kopyalanacak sunucunun ID'si (Developer Mode açıkken sunucuya sağ tıklayıp "ID Kopyala" diyebilirsiniz).
- **Target ID:** Yapıştırılacak (boş) sunucunun ID'si.

## 📝 Notlar
- Hedef sunucudaki tüm kanallar ve roller silinecektir (Temiz kurulum için).
- Mesaj kopyalama özelliği, işlem süresini çok uzattığı ve riskli olduğu için kaldırılmıştır.
- Büyük sunucularda işlem birkaç dakika sürebilir, lütfen bekleyin.

**Made by Berkaycimh**
