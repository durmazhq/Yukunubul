from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
import random
import re

app = Flask(__name__)
app.secret_key = 'durmaz_tech_holding_master_premium_key_2026'
app.permanent_session_lifetime = timedelta(days=365)

# Boş liste olarak başlattık. O inatçı Aslan Lojistik ilanı tamamen silindi!
kullanicilar = []
ilanlar = []
holding_kasasi = 0.0 
ilan_id_sayaci = 101

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
    
    tasiyici_sayisi = sum(1 for k in kullanicilar if 'Taşıyıcı' in k['tip']) + 18
    sirket_sayisi = sum(1 for k in kullanicilar if 'Şirket' in k['tip']) + 6
    sefer_sayisi = 54 + sum(1 for i in ilanlar if i.get('durum') == 'Tamamlandı')
    
    aktif_ilanlar = [i for i in ilanlar if i.get('durum', 'Bekliyor') == 'Bekliyor']
    
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
        yeni_kullanici = {
            "isim": request.form.get('isim'),
            "email": request.form.get('email'),        # E-posta alanı eklendi
            "telefon": request.form.get('telefon'),
            "tip": request.form.get('tip'),
            "detay": request.form.get('detay'),
            "sifre": request.form.get('sifre'),
            "kimlik_no": request.form.get('kimlik_no'),
            "onayli_mi": True,
            "bakiye": 0.0
        }
        kullanicilar.append(yeni_kullanici)
        return redirect(url_for('giriş_yap'))
    return render_template('kayit.html')

@app.route('/giris', methods=['GET', 'POST'])
def giriş_yap():
    hata_mesaji = None
    if request.method == 'POST':
        giris_verisi = request.form.get('telefon_veya_email') # Hem tel hem mail kabul edecek alan
        sifre = request.form.get('sifre')
        
        # Admin kontrolü
        if giris_verisi == ADMIN_USER and sifre == ADMIN_PASS:
            session.permanent = True
            session['kullanici_adi'] = "Mertcan Durmaz"
            session['kullanici_tipi'] = "Kurucu Lider"
            session['kullanici_detay'] = "Durmaz Holding"
            session['kullanici_telefon'] = "Gizli"
            session['kullanici_email'] = "Gizli"
            return redirect(url_for('admin_paneli'))
            
        # Kullanıcı kontrolü (İster e-posta ister telefon eşleşsin)
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
    return render_template('giris.html', hata=hata_mesaji)

@app.route('/admin')
def admin_paneli():
    if session.get('kullanici_adi') != "Mertcan Durmaz": 
        return redirect(url_for('ana_sayfa'))
    return render_template('admin.html', kullanicilar=kullanicilar, ilanlar=ilanlar, kasa=holding_kasasi)

@app.route('/ilan-ver', methods=['GET', 'POST'])
def ilan_ver():
    global ilan_id_sayaci
    if 'kullanici_adi' not in session: return redirect(url_for('giriş_yap'))
        
    if request.method == 'POST':
        fiyat_ham = request.form.get('fiyat')
        fiyat = float(fiyat_ham) if fiyat_ham else 0.0
        nereden = request.form.get('nereden')
        nereye = request.form.get('nereye')
        
        yeni_ilan = {
            "id": ilan_id_sayaci,
            "nereden": nereden,
            "nereye": nereye,
            "yuk": request.form.get('yuk'),
            "arac": request.form.get('arac'),
            "fiyat": fiyat,
            "acıklama": aciklama_sansurle(request.form.get('acıklama')),
            "veren_firma": session.get('kullanici_detay'),
            "durum": "Bekliyor",
            "irsaliye": e_irsaliye_olustur(nereden, nereye)
        }
        ilan_id_sayaci += 1
        ilanlar.append(yeni_ilan)
        return redirect(url_for('ana_sayfa'))
    return render_template('ilan_ver.html')

@app.route('/islem-tamamla/<int:ilan_id>')
def islem_tamamla(ilan_id):
    global holding_kasasi
    if session.get('kullanici_adi') != "Mertcan Durmaz": return redirect(url_for('ana_sayfa'))
    for i in ilanlar:
        if i['id'] == ilan_id and i['durum'] == 'Bekliyor':
            i['durum'] = 'Tamamlandı'
            holding_kasasi += (i['fiyat'] * 0.05)
    return redirect(url_for('admin_paneli'))

@app.route('/ilan-sil/<int:ilan_id>')
def ilan_sil(ilan_id):
    global ilanlar
    if session.get('kullanici_adi') != "Mertcan Durmaz": return redirect(url_for('ana_sayfa'))
    ilanlar = [i for i in ilanlar if i['id'] != ilan_id]
    return redirect(url_for('admin_paneli'))

@app.route('/profil')
def profil_sayfası():
    if 'kullanici_adi' not in session: return redirect(url_for('giriş_yap'))
    
    kullanici_adi = session.get('kullanici_adi')
    kullanici_detay = session.get('kullanici_detay')
    aktif_kullanici = next((k for k in kullanicilar if k['isim'] == kullanici_adi), None)
    
    kullanici_ilanlari = [i for i in ilanlar if i['veren_firma'] == kullanici_detay or i['veren_firma'] == kullanici_adi]
    
    return render_template('profil.html', ilanlar=kullanici_ilanlari, kullanici=aktif_kullanici, kasa=holding_kasasi)

@app.route('/cikis')
def cikis_yap():
    session.clear()
    return redirect(url_for('ana_sayfa'))

if __name__ == '__main__':
    app.run(debug=True)