# -*- coding: utf-8 -*-
"""
ASANSÖR AVAN HESAPLAMA PROGRAMI
=================================
Yerel sunucu + tarayıcı arayüzü.  Çalıştırmak için:

    python3 main.py

Tarayıcı kendiliğinden açılır (http://127.0.0.1:8760).
Program tümüyle bilgisayarınızda çalışır, internet gerektirmez.
"""
import json
import math
import os
import re
import sys
import threading
import webbrowser
from datetime import date

from fastapi import Body, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

#  CAD çıktısı ezdxf + pdfminer.six ister.  Bunlar kurulu değilse PROGRAM
#  YİNE AÇILIR — yalnız CAD düğmeleri anlaşılır bir hata verir.
#  ( Kitaplık denetimi artık uç dosyalarında:  api/avan.py · api/uygulama.py )
_BASLATICI = "baslat.bat" if os.name == "nt" else "baslat.command"

SURUM = "3.0"
KOK = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("AVAN_PORT", "8760"))

app = FastAPI(title="Asansör Proje Programı", version=SURUM,
              docs_url=None, redoc_url=None)


# ------------------------------------------------------------------ yardımcı
#  BELİRSİZ SAYI  —  "1.200" bin iki yüz mü, bir nokta iki mi?
#  Program ondalık ayracı olarak hem virgülü hem noktayı kabul ediyor; bu da
#  TEK ayraçlı ve ardından TAM ÜÇ RAKAM gelen yazımları belirsiz bırakır:
#  Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki.  Program bunu
#  tahmin ETMEZ — reddeder ve kullanıcıya nasıl yazması gerektiğini söyler.
#  Sessizce 1,2 okumak 1.200 daireli bir binada asansör adedini 41'den 2'ye
#  düşürüyordu.
#  Tam sayı kısmı SIFIRLA BAŞLAMAMALI: "0,075" ( = %7,5 ) belirsiz değildir,
#  çünkü binlik ayracı sıfırdan sonra gelmez.  Belirsiz olan "1.200" gibi
#  1-3 basamaklı, sıfırla başlamayan bir sayıdan sonra tam üç rakam gelmesidir.
BELIRSIZ_SAYI = re.compile(r"^[+-]?[1-9]\d{0,2}[.,]\d{3}$")



from api import avan as UC_AVAN
from api import uygulama as UC_UYGULAMA
from api.ortak import (_BELIRSIZ, _RED, _sayi, belirsiz_sayi_mi)   # noqa: F401
from exports import mukavemet_xlsx as X_MXLS
from exports import xlsx_import as X_IMP
from engine.uygulama import girdi as E_UGR
from engine.uygulama import mukavemet_girdi as E_MGR

#  UÇLAR İKİ PAKETTE:  avan projesi ve uygulama projesi ayrı dosyalarda
#  ( bkz. api/avan.py · api/uygulama.py ).  Ortak yardımcılar api/ortak.py.
app.include_router(UC_AVAN.router)
app.include_router(UC_UYGULAMA.router)

@app.get("/", response_class=HTMLResponse)
def anasayfa():
    with open(os.path.join(KOK, "static", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/xlsx-yukle")
def api_xlsx_yukle(veri: dict = Body(...)):
    """
    Programın ürettiği bir XLSX dosyasından girdileri geri yükler.

    Revizyon akışı:  proje klasöründeki Excel'i yükle → değişen girdiyi
    düzelt → güncel PDF ve XLSX'i yeniden indir.

    Dosya, arayüz tarafından base64 olarak gönderilir; böylece programın
    ek bir Python paketine ( multipart ) ihtiyacı olmaz.
    """
    import base64
    try:
        ham = (veri or {}).get("icerik") or ""
        if isinstance(ham, str) and "," in ham[:80] and ham.strip().startswith("data:"):
            ham = ham.split(",", 1)[1]              # data: URL başlığını at
        icerik = base64.b64decode(ham, validate=False)
    except Exception:                                         # noqa: BLE001
        return JSONResponse({"hata": "Dosya içeriği okunamadı."}, status_code=422)
    if len(icerik) < 1000:
        return JSONResponse({"hata": "Dosya boş veya çok küçük."}, status_code=422)
    if len(icerik) > 25 * 1024 * 1024:
        return JSONResponse({"hata": "Dosya çok büyük (en fazla 25 MB)."}, status_code=422)
    #  MUKAVEMET ÇALIŞMA KİTABI  ( uygulama projesi ).  Avan içe aktarıcısı
    #  bu dosyayı tanımaz;  önce o denetlenir, yoksa "tanınmayan dosya"
    #  hatası verirdi.  Dönen yapı avanınkiyle aynıdır — arayüzün uygula()
    #  işlevi ikisini de aynı yoldan işler.
    try:
        if X_MXLS.mukavemet_dosyasi_mi(icerik):
            g = X_MXLS.xlsx_oku(icerik)
            alanlar, durak = {}, []
            for anahtar, _h, _e, _b, tur, _s2, _v in E_MGR.ALANLAR:
                if anahtar not in g:
                    continue
                if tur == "liste":
                    durak = [str(x) for x in g[anahtar]]
                    continue
                alanlar[f"m_{anahtar}"] = g[anahtar]
            return JSONResponse({
                "tur": "mukavemet", "alanlar": alanlar, "muk_durak": durak,
                "proje": {}, "ozet": f"Mukavemet hesabı — {len(durak)} durak, "
                                     f"{len(alanlar)} girdi geri yüklendi."})
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"hata": f"Mukavemet dosyası okunamadı: {e}"},
                            status_code=422)
    try:
        return JSONResponse(X_IMP.xlsx_oku(icerik))
    except X_IMP.YuklemeHatasi as e:
        return JSONResponse({"hata": str(e)}, status_code=422)
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"hata": f"Dosya yüklenemedi: {e}"}, status_code=422)


@app.get("/api/saglik")
def saglik():
    return {"durum": "calisiyor", "surum": SURUM}


app.mount("/static", StaticFiles(directory=os.path.join(KOK, "static")), name="static")


# ------------------------------------------------------------------ başlat
def _bos_port(ilk, deneme=20):
    """İlk boş portu bulur — program zaten açıksa ikinci kopya çakışmasın."""
    import socket
    for p in range(ilk, ilk + deneme):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return None


def _zaten_calisiyor(port):
    """Bu portta bizim programımız mı çalışıyor?"""
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/saglik", timeout=2) as c:
            return json.loads(c.read()).get("durum") == "calisiyor"
    except Exception:                                         # noqa: BLE001
        return False


def calistir():
    import uvicorn
    port = PORT
    if _zaten_calisiyor(port):
        url = f"http://127.0.0.1:{port}"
        print(f"\n  Program zaten açık  →  {url}\n  Tarayıcı yönlendiriliyor…\n")
        webbrowser.open(url)
        return
    if _bos_port(port, 1) is None:
        yeni = _bos_port(port + 1)
        if yeni is None:
            print(f"\n  {port} ve sonraki portlar dolu. Başka bir program bu portları "
                  "kullanıyor olabilir.\n  Bilgisayarı yeniden başlatıp tekrar deneyin.\n")
            return
        print(f"\n  {port} portu başka bir program tarafından kullanılıyor — "
              f"{yeni} portuna geçildi.")
        port = yeni

    url = f"http://127.0.0.1:{port}"
    print("\n" + "═" * 62)
    print(f"  ASANSÖR AVAN HESAPLAMA PROGRAMI   ·   sürüm {SURUM}")
    print("═" * 62)
    print(f"  Program çalışıyor :  {url}")
    print("  Tarayıcı kendiliğinden açılmazsa bu adresi yapıştırın.")
    print("  Kapatmak için bu pencerede  Ctrl + C  tuşlayın.")
    print("═" * 62 + "\n")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        print("\n  Program kapatıldı.\n")


if __name__ == "__main__":
    calistir()
