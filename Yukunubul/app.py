from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
import random
import re
import requests
import json
import os

app = Flask(__name__)
app.secret_key = 'durmaz_tech_holding_master_premium_key_2026'
app.permanent_session_lifetime = timedelta(days=365)

# --- 📂 GÜVENLİ VE KALICI DOSYA VERİTABANI SİSTEMİ ---
KULLANICI_DOSYASI = "kullanicilar.json"
ILAN_DOSYASI = "ilanlar.json"

def verileri_oku(dosya_adi):
    if not os.path.exists(dosya_adi):
        return []
    try:
        with open(dosya_adi, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def verileri_yaz(dosya_adi, veri):
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# --- 👑 GOOGLE GİRİŞ YAPILANDIRMASI ---
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"

# --- 👑 ÜST DÜZEY GÜVENLİK ANAHTARLARI 👑 ---
ADMIN_USER = "durmaz_tech_admin"
ADMIN_PASS = "DurmazHold.2026!x"

def e_irsaliye_olustur(nereden, nereye):
    return f"IRS-{random.randint(10000, 99999)}-{nereden[:3].upper()}-{nereye[:3].upper()}"

def aciklama_sansurle(metin):
    return re.sub(r'(\d[\s\-]?){10,11}', '[TELEFON GİZLENDİ - KOMİSYON İHLALİ]', metin)

@app.route('/')
def ana_sayfa():
    giriş_yapan = session.get('kullanici_adi')
    kullanici_tipi = session.get('kullanici_tipi')
    
    kullanicilar = verileri_oku(KULLANICI_DOSYASI)
    ilanlar = verileri_oku(ILAN_DOSYASI)
    
    tasiyici_sayisi = sum(1 for k in kullanicilar if k.get('tip') and 'Taşıyıcı' in k['tip'])
    sirket_sayisi = sum(1 for k in kullanicilar if k.get('tip') and 'Şirket' in k['tip'])
    sefer_sayisi = sum(1 for i in ilanlar if i.get('durum') == 'Tamamlandı')
    
    # Sadece tamamlanmamış ilanlar ana sayfada dönsün
    aktif_ilanlar = [i for i in ilanlar if i.get('durum') != 'Tamamlandı']
    
    return render_template('index.html', 
                           ilanlar=aktif_ilanlar, 
                           giriş_yapan=giriş_yapan,
                           kullanici_tipi=kullanici_tipi,
                           tasiyici_sayisi=tasiyici_sayisi,
                           sirket_sayisi=sirket_sayisi,
                           sefer_sayisi=sefer_sayisi)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit_ol():
    if request.method == 'POST':
        kullanicilar = verileri_oku(KULLANICI_DOSYASI)
        sms_pazarlama = True if request.form.get('sms_izin') == 'on' else False
        
        yeni_kullanici = {
            "isim": request.form.get('isim'),
            "email": request.form.get('email'),        
            "telefon": request.form.get('telefon'),    
            "tip": request.form.get('tip'),
            "detay": request.form.get('detay'),
            "sifre": request.form.get('sifre'),
            "kimlik_no": request.form.get('kimlik_no'),
            "sms_eposta_izin": sms_pazarlama,
            "onayli_mi": True,
            "bakiye": 0.0
        }
        
        kullanicilar.append(yeni_kullanici)
        verileri_yaz(KULLANICI_DOSYASI, kullanicilar)
        return redirect(url_for('giriş_yap'))
    return render_template('kayit.html')

@app.route('/giris', methods=['GET', 'POST'])
def giriş_yap():
    hata_mesaji = None
    if request.method == 'POST':
        giris_verisi = request.form.get('telefon_veya_email') 
        sifre = request.form.get('sifre')
        
        if giris_verisi == ADMIN_USER and sifre == ADMIN_PASS:
            session.permanent = True
            session['kullanici_adi'] = "Mertcan Durmaz"
            session['kullanici_tipi'] = "Kurucu"
            session['kullanici_detay'] = "Durmaz Tech"
            return redirect(url_for('admin_paneli'))
            
        kullanicilar = verileri_oku(KULLANICI_DOSYASI)
        for k in kullanicilar:
            if (k['telefon'] == giris_verisi or k.get('email') == giris_verisi) and k['sifre'] == sifre:
                session.permanent = True
                session['kullanici_adi'] = k['isim']
                session['kullanici_tipi'] = k['tip']
                session['kullanici_detay'] = k['detay']
                session['kullanici_telefon'] = k['telefon']
                session['kullanici_email'] = k.get('email', '')
                return redirect(url_for('ana_sayfa'))
        hata_mesaji = "Giriş bilgileri hatalı."
    return render_template('giris.html', hata=hata_mesaji, google_client_id=GOOGLE_CLIENT_ID)

@app.route('/login-with-google', methods=['POST'])
def login_with_google():
    token = request.json.get('id_token')
    if not token: return {"success": False, "message": "Token eksik"}, 400
    try:
        google_verify = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}").json()
        if "error_description" in google_verify: return {"success": False, "message": "Geçersiz Token"}, 400
        
        google_email = google_verify.get('email')
        google_name = google_verify.get('name', 'Google Kullanıcısı')
        
        kullanicilar = verileri_oku(KULLANICI_DOSYASI)
        mevcut_kullanici = next((k for k in kullanicilar if k.get('email') == google_email), None)
        
        if mevcut_kullanici:
            session.permanent = True
            session['kullanici_adi'] = mevcut_kullanici['isim']
            session['kullanici_tipi'] = mevcut_kullanici['tip']
            session['kullanici_detay'] = mevcut_kullanici['detay']
            session['kullanici_telefon'] = mevcut_kullanici['telefon']
            session['kullanici_email'] = mevcut_kullanici['email']
            return {"success": True, "redirect": url_for('ana_sayfa')}
        else:
            session['temp_google_email'] = google_email
            session['temp_google_name'] = google_name
            return {"success": True, "redirect": url_for('google_tamamla')}
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/google-kayit-tamamla', methods=['GET', 'POST'])
def google_tamamla():
    if 'temp_google_email' not in session: return redirect(url_for('giriş_yap'))
    if request.method == 'POST':
        kullanicilar = verileri_oku(KULLANICI_DOSYASI)
        sms_pazarlama = True if request.form.get('sms_izin') == 'on' else False
        
        yeni_kullanici = {
            "isim": session.get('temp_google_name'),
            "email": session.get('temp_google_email'),
            "telefon": request.form.get('telefon'),
            "tip": request.form.get('tip'),
            "detay": request.form.get('detay'),
            "sifre": "GoogleAuthAccount",
            "kimlik_no": request.form.get('kimlik_no'),
            "sms_eposta_izin": sms_pazarlama,
            "onayli_mi": True,
            "bakiye": 0.0
        }
        kullanicilar.append(yeni_kullanici)
        verileri_yaz(KULLANICI_DOSYASI, kullanicilar)
        
        session.permanent = True
        session['kullanici_adi'] = yeni_kullanici['isim']
        session['kullanici_tipi'] = yeni_kullanici['tip']
        session['kullanici_detay'] = yeni_kullanici['detay']
        session['kullanici_telefon'] = yeni_kullanici['telefon']
        session['kullanici_email'] = yeni_kullanici['email']
        session.pop('temp_google_email', None)
        session.pop('temp_google_name', None)
        return redirect(url_for('ana_sayfa'))
    return render_template('google_tamamla.html', email=session.get('temp_google_email'), name=session.get('temp_google_name'))

@app.route('/admin')
def admin_paneli():
    if session.get('kullanici_adi') != "Mertcan Durmaz": return redirect(url_for('ana_sayfa'))
    kullanicilar = verileri_oku(KULLANICI_DOSYASI)
    ilanlar = verileri_oku(ILAN_DOSYASI)
    
    kasa = sum(i.get('fiyat', 0) * 0.05 for i in ilanlar if i.get('durum') == 'Tamamlandı')
    return render_template('admin.html', kullanicilar=kullanicilar, ilanlar=ilanlar, kasa=kasa)

@app.route('/ilan-ver', methods=['GET', 'POST'])
def ilan_ver():
    if 'kullanici_adi' not in session: return redirect(url_for('giriş_yap'))
    if request.method == 'POST':
        ilanlar = verileri_oku(ILAN_DOSYASI)
        fiyat_ham = request.form.get('fiyat')
        fiyat = float(fiyat_ham) if fiyat_ham else 0.0
        nereden = request.form.get('nereden')
        nereye = request.form.get('nereye')
        
        yeni_id = random.randint(10000, 99999)
        
        yeni_ilan = {
            "id": yeni_id, "nereden": nereden, "nereye": nereye,
            "yuk": request.form.get('yuk'), "arac": request.form.get('arac'), "fiyat": fiyat,
            "acıklama": aciklama_sansurle(request.form.get('acıklama')),
            "veren_firma": session.get('kullanici_detay'), "durum": "Bekliyor",
            "irsaliye": e_irsaliye_olustur(nereden, nereye)
        }
        ilanlar.append(yeni_ilan)
        verileri_yaz(ILAN_DOSYASI, ilanlar)
        return redirect(url_for('ana_sayfa'))
    return render_template('ilan_ver.html')

# --- 🚀 YENİ: AKILLI DURUM GÜNCELLEME MOTORU ---
@app.route('/durum-guncelle/<int:ilan_id>', methods=['POST'])
def durum_guncelle(ilan_id):
    if session.get('kullanici_adi') != "Mertcan Durmaz": 
        return redirect(url_for('ana_sayfa'))
        
    ilanlar = verileri_oku(ILAN_DOSYASI)
    yeni_durum = request.form.get('yeni_durum')
    
    for i in ilanlar:
        if i['id'] == ilan_id:
            i['durum'] = yeni_durum
            
    verileri_yaz(ILAN_DOSYASI, ilanlar)
    return redirect(url_for('admin_paneli'))

@app.route('/ilan-sil/<int:ilan_id>')
def ilan_sil(ilan_id):
    if session.get('kullanici_adi') != "Mertcan Durmaz": return redirect(url_for('ana_sayfa'))
    ilanlar = verileri_oku(ILAN_DOSYASI)
    ilanlar = [i for i in ilanlar if i['id'] != ilan_id]
    verileri_yaz(ILAN_DOSYASI, ilanlar)
    return redirect(url_for('admin_paneli'))

@app.route('/profil')
def profil_sayfası():
    if 'kullanici_adi' not in session: return redirect(url_for('giriş_yap'))
    kullanici_adi = session.get('kullanici_adi')
    kullanici_detay = session.get('kullanici_detay')
    
    kullanicilar = verileri_oku(KULLANICI_DOSYASI)
    ilanlar = verileri_oku(ILAN_DOSYASI)
    
    aktif_kullanici = next((k for k in kullanicilar if k['isim'] == kullanici_adi), None)
    kullanici_ilanlari = [i for i in ilanlar if i['veren_firma'] == kullanici_detay or i['veren_firma'] == kullanici_adi]
    
    kasa = sum(i.get('fiyat', 0) * 0.05 for i in ilanlar if i.get('durum') == 'Tamamlandı')
    return render_template('profil.html', ilanlar=kullanici_ilanlari, kullanici=aktif_kullanici, kasa=kasa)

@app.route('/cikis')
def cikis_yap():
    session.clear()
    return redirect(url_for('ana_sayfa'))

if __name__ == '__main__':
    app.run(debug=True)