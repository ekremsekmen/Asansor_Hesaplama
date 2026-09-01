# -*- coding: utf-8 -*-
"""
PDF DIŞA AKTARIM  —  baskıya hazır pafta / hesap raporu

Sayfa düzeni Excel'deki PAFTA ve "n NOLU ASANSÖR" sayfalarının işlem
akışını birebir izler:  başlık → girdi satırları → denklem → sayıların
yerine konmuş hâli → sonuç → kontrol → notlar.
"""
import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

from engine.steps import tr, trn, sayi_mi

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

# ----------------------------------------------------------------- yazı tipi
def _fontlari_yukle():
    try:
        pdfmetrics.getFont("Gov")
        return "Gov", "Gov-Bold"
    except Exception:
        pass
    adaylar = [
        (os.path.join(FONT_DIR, "DejaVuSans.ttf"), os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ]
    for normal, bold in adaylar:
        if os.path.exists(normal) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Gov", normal))
            pdfmetrics.registerFont(TTFont("Gov-Bold", bold))
            return "Gov", "Gov-Bold"
    return "Helvetica", "Helvetica-Bold"


F, FB = _fontlari_yukle()

# ------------------------------------------------------------------ renkler
MAVI = colors.HexColor("#123E6B")
MAVI_AC = colors.HexColor("#EAF1F8")
GRI = colors.HexColor("#666666")
GRI_AC = colors.HexColor("#F4F5F7")
CIZGI = colors.HexColor("#C9D3DE")
YESIL = colors.HexColor("#1B6B37")
KIRMIZI = colors.HexColor("#A8231F")
SARI_AC = colors.HexColor("#FFF8E1")

#  TABLO GENİŞLİK ÇARPANI
#  Pafta küçültülerek basıldığında ( bkz. _Belge.olcek ) çerçeve 1/olcek
#  büyüklüğünde kurulur.  Tablolar sabit mm genişlikte olduğu için, çarpan
#  uygulanmazsa ortada dar bir sütun hâlinde kalır ve sayfanın iki yanı boş
#  gider.  Bu çarpan tabloları da aynı oranda genişletir; ölçekten sonra
#  tam A4 yazı alanına otururlar.
_GEN = 1.0


def _w(x):
    return x * _GEN


S = {
    "h1": ParagraphStyle("h1", fontName=FB, fontSize=13.5, leading=17, textColor=MAVI,
                         alignment=TA_CENTER, spaceAfter=1),
    "h2": ParagraphStyle("h2", fontName=FB, fontSize=9.5, leading=13, textColor=colors.white),
    "h2k": ParagraphStyle("h2k", fontName=F, fontSize=7.4, leading=9.5, textColor=colors.white,
                          alignment=2),
    "alt": ParagraphStyle("alt", fontName=F, fontSize=7.6, leading=10, textColor=GRI,
                          alignment=TA_CENTER),
    "n": ParagraphStyle("n", fontName=F, fontSize=8.2, leading=11.2),
    "nb": ParagraphStyle("nb", fontName=FB, fontSize=8.2, leading=11.2),
    "sag": ParagraphStyle("sag", fontName=FB, fontSize=8.6, leading=11.2, alignment=2),
    "kaynak": ParagraphStyle("kaynak", fontName=F, fontSize=6.9, leading=9, textColor=GRI),
    "formul": ParagraphStyle("formul", fontName=FB, fontSize=8.4, leading=11.5, textColor=MAVI),
    "islem": ParagraphStyle("islem", fontName=F, fontSize=8.2, leading=11.5, textColor=colors.HexColor("#333")),
    "not": ParagraphStyle("not", fontName=F, fontSize=7.2, leading=9.6, textColor=GRI),
    "sonuc": ParagraphStyle("sonuc", fontName=FB, fontSize=9, leading=12.5, textColor=colors.white),
}


_IZINLI = (("<b>", "\x01"), ("</b>", "\x02"), ("<br/>", "\x03"), ("<i>", "\x04"), ("</i>", "\x05"))


def _p(metin, stil="n"):
    """XML kaçışı yapar ama <b>, </b>, <br/>, <i>, </i> etiketlerini korur."""
    if metin is None:
        metin = ""
    s = str(metin)
    for etiket, yer in _IZINLI:
        s = s.replace(etiket, yer)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for etiket, yer in _IZINLI:
        s = s.replace(yer, etiket)
    return Paragraph(s, S[stil])


# ---------------------------------------------------------------- belge iskeleti
class _Belge(BaseDocTemplate):
    """
    `olcek` < 1 ise içerik KÜÇÜLTÜLEREK sayfaya sığdırılır.

    Kâğıt yine A4'tür; yalnız iç çerçeve 1/olcek büyüklüğünde kurulur ve
    çizim anında olcek ile küçültülür.  Böylece dizgi daha geniş bir alana
    yapılır ( satırlar daha az kırılır ), sonra tamamı orantılı olarak
    A4 yazı alanına oturur.  Üst bant ve alt bilgi ölçekten etkilenmez —
    onlar gerçek A4 koordinatlarında çizilir.
    """

    def __init__(self, buf, ust_baslik, alt_baslik, olcek=1.0, **kw):
        # Pafta PDF'leri proje antedi taşımaz; bu bilgiler yalnız kapaktadır.
        baslik = ust_baslik
        super().__init__(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                         topMargin=22 * mm, bottomMargin=16 * mm,
                         title=baslik, author="",
                         subject=alt_baslik, creator="Asansör Avan Hesaplama Programı", **kw)
        self.ust_baslik, self.alt_baslik = ust_baslik, alt_baslik
        self.olcek = k = float(olcek) if olcek else 1.0
        cerceve = Frame(self.leftMargin / k, self.bottomMargin / k,
                        self.width / k, self.height / k, id="ana")
        self.addPageTemplates([PageTemplate(id="std", frames=cerceve, onPage=self._sayfa)])

    def _sayfa(self, cnv, doc):
        cnv.saveState()
        w, h = A4
        cnv.setFillColor(MAVI)
        cnv.rect(0, h - 14 * mm, w, 14 * mm, stroke=0, fill=1)
        cnv.setFillColor(colors.white)
        cnv.setFont(FB, 9.5)
        cnv.drawString(15 * mm, h - 9.6 * mm, self.ust_baslik)
        cnv.setFont(F, 7.6)
        cnv.setStrokeColor(CIZGI)
        cnv.setLineWidth(0.5)
        cnv.line(15 * mm, 12.5 * mm, w - 15 * mm, 12.5 * mm)
        cnv.setFillColor(GRI)
        cnv.setFont(F, 6.4)
        sag_metin = f"Sayfa {cnv.getPageNumber()}"
        sag_gen = cnv.stringWidth(sag_metin, F, 6.4)
        kalan = w - 30 * mm - sag_gen - 6 * mm
        sol = self.alt_baslik
        if cnv.stringWidth(sol, F, 6.4) > kalan:
            # kelime ortasından değil, ayraçtan kırp
            parcalar = sol.split("   ·   ")
            while len(parcalar) > 1 and \
                    cnv.stringWidth("   ·   ".join(parcalar) + " …", F, 6.4) > kalan:
                parcalar.pop()
            sol = "   ·   ".join(parcalar) + (" …" if len(parcalar) < len(self.alt_baslik.split("   ·   ")) else "")
        cnv.drawString(15 * mm, 9 * mm, sol)
        cnv.drawRightString(w - 15 * mm, 9 * mm, sag_metin)
        cnv.restoreState()
        #  Çerçeve içeriği bundan sonra çizilir; ölçek yalnız ONU etkiler.
        #  Sayfa değişiminde çizim durumu sıfırlandığı için her sayfada
        #  yeniden uygulanır.
        if self.olcek != 1.0:
            cnv.scale(self.olcek, self.olcek)


def _baslik_seridi(metin, kaynak=""):
    #  Yükseklik SABİT DEĞİLDİR: uzun bir bölüm başlığı iki satıra düştüğünde
    #  şerit de büyür, yoksa ikinci satır mavi bandın dışına taşıyordu.
    t = Table([[_p(metin, "h2"), _p(kaynak, "h2k")]],
              colWidths=[_w(108 * mm), _w(72 * mm)])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), MAVI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, 0), 5), ("RIGHTPADDING", (1, 0), (1, 0), 5),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    return t


# ------------------------------------------------------------ adım tabloları
def _adim_tablosu(adimlar):
    """
    veri  satırı : sembol | açıklama | = | değer | birim | kaynak
    hesap satırı : denklem (tam genişlik)  +  '= sayılar'  |  sonuç | birim | kaynak
    """
    veriler, stil, i = [], [], 0
    for a in adimlar:
        tip = a.get("tip")
        if tip == "metin":
            veriler.append([_p(f"<b>{a['deger']}</b>", "n"), "", "", "", "", ""])
            stil += [("SPAN", (0, i), (-1, i)),
                     ("BACKGROUND", (0, i), (-1, i), MAVI_AC),
                     ("TOPPADDING", (0, i), (-1, i), 4), ("BOTTOMPADDING", (0, i), (-1, i), 3)]
            i += 1
            continue
        if tip == "hesap":
            veriler.append([_p(a["formul"], "formul"), "", "", "", "", ""])
            stil += [("SPAN", (0, i), (-1, i)), ("TOPPADDING", (0, i), (-1, i), 5),
                     ("BOTTOMPADDING", (0, i), (-1, i), 0)]
            i += 1
            veriler.append(["", _p(a["islem"], "islem"), "",
                            _p(a["metin"], "sag"), _p(a["birim"], "n"), _p(a["kaynak"], "kaynak")])
            stil += [("SPAN", (1, i), (2, i)), ("BACKGROUND", (3, i), (3, i), GRI_AC),
                     ("BOTTOMPADDING", (0, i), (-1, i), 4),
                     ("LINEBELOW", (0, i), (-1, i), 0.4, CIZGI)]
            i += 1
            continue
        veriler.append([_p(f"<b>{a['sembol']}</b>", "n"), _p(a["aciklama"], "n"),
                        _p("=", "n") if a["sembol"] or a["aciklama"] else "",
                        _p(a["metin"], "sag"), _p(a["birim"], "n"), _p(a["kaynak"], "kaynak")])
        stil += [("LINEBELOW", (0, i), (-1, i), 0.25, colors.HexColor("#E6EAEF"))]
        i += 1

    t = Table(veriler, colWidths=[_w(13 * mm), _w(84 * mm), _w(5 * mm), _w(30 * mm), _w(18 * mm), _w(30 * mm)])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ] + stil))
    return t


def _sonuc_kutusu(sonuc):
    if not sonuc:
        return None
    renk = YESIL if sonuc.get("uygun", True) else KIRMIZI
    satirlar = [[_p(sonuc.get("baslik", "SONUÇ"), "sonuc"), _p(sonuc.get("metin", ""), "sonuc")]]
    t = Table(satirlar, colWidths=[_w(52 * mm), _w(128 * mm)])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), renk),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    ogeler = [Spacer(1, 1.5 * mm), t]
    for alt in sonuc.get("alt", []) or []:
        ogeler.append(_p(alt, "not"))
    return ogeler


def _notlar(notlar):
    if not notlar:
        return []
    o = [Spacer(1, 1.2 * mm)]
    for n in notlar:
        o.append(_p("▪  " + str(n), "not"))
    return o


def _bolum(b):
    o = [Spacer(1, 3.5 * mm), _baslik_seridi(b["baslik"], b.get("kaynak", "")), Spacer(1, 1.2 * mm)]
    if b.get("adimlar"):
        o.append(_adim_tablosu(b["adimlar"]))
    if b.get("cetvel"):
        o.append(_cetvel_tablosu(b["cetvel"]))
    sk = _sonuc_kutusu(b.get("sonuc"))
    if sk:
        o += sk
    #  Paftada iki liste de basılır: "notlar" bu bölümün sonucuna ait satırlar,
    #  "aciklamalar" yöntemi anlatan bilgi metinleri.  Ekranda ikincisi ⓘ
    #  simgesine toplanır; çıktıda hiçbir şey eksilmez.
    o += _notlar(list(b.get("notlar") or []) + list(b.get("aciklamalar") or []))
    return o


def _cetvel_tablosu(cetvel):
    basliklar = ["Lin", "Sorti", "", "Gücü", "Birim", "Sigorta A"]
    veriler = [[_p(f"<b>{x}</b>", "n") for x in basliklar]]
    toplam = 0
    for c in cetvel:
        toplam += c["guc"]
        veriler.append([_p(str(c["lin"]), "n"), _p(c["sorti"], "n"), _p("=", "n"),
                        _p(trn(c["guc"], 0), "sag"), _p(c["birim"], "n"), _p(c["sigorta"], "n")])
    veriler.append(["", _p("<b>ASANSÖRÜN KURULU GÜCÜ</b>", "n"), _p("=", "n"),
                    _p(trn(toplam, 0), "sag"), _p("W", "n"), ""])
    t = Table(veriler, colWidths=[_w(13 * mm), _w(84 * mm), _w(5 * mm), _w(30 * mm), _w(18 * mm), _w(30 * mm)])
    n = len(veriler) - 1
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), MAVI_AC),
        ("BACKGROUND", (0, n), (-1, n), GRI_AC),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, CIZGI),
    ]))
    return t


def _uyari_kutusu(metinler, hata=False):
    if not metinler:
        return []
    #  Motor iletileri zaten "⚠ " ile başlayabilir; kutu kendi simgesini
    #  çizdiği için baştaki tekrarı temizliyoruz (çift ⚠ görünmesin).
    def _sadelestir(m):
        m = str(m).lstrip()
        while m[:1] in ("⚠", "✕", "!", "ℹ"):
            m = m[1:].lstrip()
        return m

    def _simge(m):
        if hata:
            return "✕  "
        return "ℹ  " if str(m).lstrip()[:1] == "ℹ" else "⚠  "

    satirlar = [[_p(_simge(m) + _sadelestir(m), "n")] for m in metinler]
    t = Table(satirlar, colWidths=[_w(180 * mm)])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SARI_AC if not hata else colors.HexColor("#FDECEA")),
        ("BOX", (0, 0), (-1, -1), 0.6, KIRMIZI if hata else colors.HexColor("#E0B84C")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [Spacer(1, 2 * mm), t]


def _kv_tablo(satirlar, genislikler=(70 * mm, 110 * mm), vurgu_son=False):
    veriler = [[_p(f"<b>{a}</b>", "n"), _p(b, "n")] for a, b in satirlar]
    t = Table(veriler, colWidths=[_w(x) for x in genislikler])
    stil = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.3, CIZGI),
            ("BACKGROUND", (0, 0), (0, -1), GRI_AC)]
    if vurgu_son:
        stil.append(("BACKGROUND", (0, len(veriler) - 1), (-1, len(veriler) - 1), MAVI_AC))
    t.setStyle(TableStyle(stil))
    return t


# =====================================================================
#  TRAFİK HESABI PDF   (PAFTA / PAFTA-COKLU karşılığı)
# =====================================================================
#  Trafik paftası TEK SAYFA olmalıdır.  İçerik sığmazsa küçültülür.
#  Ölçek büyükten küçüğe denenir ve SIĞAN İLK ( yani en büyük ) ölçek
#  seçilir — yazı gereğinden fazla küçülmesin diye adım 0,02'dir.
#  Alt sınır 0,40: bunun altında okunmaz olurdu, orada iki sayfaya izin verilir.
TRAFIK_OLCEKLERI = tuple(round(1.0 - 0.02 * i, 2) for i in range(31))


def trafik_pdf(sonuc: dict, proje: dict = None) -> bytes:
    """
    ASANSÖR TRAFİK HESABI paftası  —  her zaman TEK SAYFA.

    Pafta SONUÇ ile biter.  İçerik A4'e sığmazsa yazı ve tablolar orantılı
    olarak küçültülür; hiçbir satır atılmaz, ikinci sayfaya taşma olmaz.
    """
    for _olcek in TRAFIK_OLCEKLERI:
        cikti, sayfa = _trafik_bas(sonuc, _olcek)
        if sayfa <= 1:
            return cikti
    return cikti


def _trafik_bas(sonuc: dict, olcek: float):
    """Paftayı verilen ölçekle basar; ( bayt, sayfa adedi ) döner."""
    global _GEN
    _GEN = 1.0 / (olcek or 1.0)
    try:
        return _trafik_bas_ic(sonuc, olcek)
    finally:
        _GEN = 1.0


def _trafik_bas_ic(sonuc: dict, olcek: float):
    coklu = sonuc.get("tip") == "coklu"
    # Başlıklar Excel'deki çıktı sayfalarının A1 hücreleriyle birebir aynıdır:
    #   PAFTA        -> "ASANSÖR TRAFİK HESABI"
    #   PAFTA-COKLU  -> "ÇOKLU ASANSÖR TRAFİK HESABI"
    baslik = "ÇOKLU ASANSÖR TRAFİK HESABI" if coklu else "ASANSÖR TRAFİK HESABI"
    alt = ("Farklı kapasitede asansör grubu  —  MMO/697 s.12   ( Excel : PAFTA-COKLU sayfası )"
           if coklu else
           "Tek asansör  —  MMO/697 s.11-17   ( Excel : PAFTA sayfası )")
    buf = io.BytesIO()
    doc = _Belge(buf, baslik,
                 "MMO / 697  “Asansör Avan Projesi Hazırlama Teknik Esasları”, 2. Baskı, Ocak 2020, s.11-17"
                 "   ·   ISO 8100-32:2020   ·   BYKHY md.4",
                 olcek=olcek)
    # Hesap tamamlanamadıysa da geçerli bir belge üretilir; hata paftaya yazılır.
    o = sonuc.get("ozet") or {}
    ic = [_p(baslik, "h1"), _p(alt, "alt"), Spacer(1, 3 * mm)]

    if sonuc.get("hata"):
        ic += _uyari_kutusu([sonuc["hata"]], hata=True)
    if sonuc.get("uyarilar"):
        ic += _uyari_kutusu(sonuc["uyarilar"])

    for b in (sonuc.get("bolumler") or []):
        ic += _bolum(b)

    # çoklu: asansör bazında tablo
    if coklu and sonuc.get("asansorler"):
        ic += [Spacer(1, 3.5 * mm), _baslik_seridi("ASANSÖR BAZINDA HESAP", "MMO/697 s.11-12"),
               Spacer(1, 1.2 * mm), _coklu_tablo(sonuc["asansorler"])]

    #  NÜFUS DÖKÜMÜ PAFTAYA BASILMAZ.  b = Σc değeri ve nasıl bulunduğu
    #  zaten ilk bölümde ( "BİNADA BULUNAN İNSAN SAYISININ TESPİTİ" ) satır
    #  satır yazılı; kalem kalem döküm ekranda durur.  Pafta tek sayfadır.
    # sonuç
    ic += [Spacer(1, 4 * mm)]
    _sonuc_metni = (o.get("sonuc") or sonuc.get("hata")
                    or "Hesap tamamlanamadı — girdileri kontrol edin.")
    sk = _sonuc_kutusu({"baslik": "SONUÇ", "metin": _sonuc_metni,
                        "uygun": not str(_sonuc_metni).startswith(("Kabul", "YETERSİZ", "HESAP"))})
    ic += sk
    if o.get("sonuc_cumlesi"):
        ic += [Spacer(1, 1.5 * mm), _p(o["sonuc_cumlesi"], "nb")]
    elif o.get("pafta_satiri"):
        ic += [Spacer(1, 1.5 * mm), _p(o["pafta_satiri"], "nb")]

    #  TRAFİK PAFTASI TEK SAYFADIR.  Pafta SONUÇ ile biter: otomatik öneri
    #  tablosu ( bilgi amaçlıydı ) ve imza kutusu paftadan çıkarıldı — öneri
    #  ekranda duruyor, imza bilgisi kapak sayfasındadır.
    doc.build(ic)
    buf.seek(0)
    return buf.read(), doc.page


def _coklu_tablo(asansorler):
    satirlar = [
        ("P — Kabin kapasitesi (kişi)", lambda a: trn(a["P"], 0)),
        ("Beyan yükü (kg)", lambda a: trn(a["yuk_kg"], 0)),
        ("Kapı genişliği (mm) / tipi", lambda a: f"{trn(a['kapi_genisligi'],0)} / {a['kapi_tipi']}"),
        ("Durak adedi (ana giriş dâhil)", lambda a: trn(a["durak"], 0)),
        ("V — Kabin hızı (m/s)", lambda a: tr(a["V"])),
        ("h — Katlar arası mesafe (m)", lambda a: tr(a["h"])),
        ("p = 0,8·P", lambda a: tr(a["p"], 1)),
        ("H — Ort. en yüksek dönüş katı", lambda a: tr(a["H"], 4)),
        ("S — Ortalama durak adedi", lambda a: tr(a["S"], 4)),
        ("ta / tk  (kapı aç / kapa) (s)", lambda a: f"{tr(a['ta'],1)} / {tr(a['tk'],1)}"),
        ("tg / tp  (geçiş / transfer) (s)", lambda a: f"{tr(a['tg'],1)} / {tr(a['tp'],1)}"),
        ("tv = h / V  (s)", lambda a: tr(a["tv"], 3)),
        ("ts = ta+tk+tg−tv  (s)", lambda a: tr(a["ts"], 3)),
        ("TR = 2·H·tv+(S+1)·ts+2·p·tp  (s)", lambda a: tr(a["TR"], 2)),
        ("R = 5·60·p / TR  (kişi/5dk)", lambda a: tr(a["R"], 2)),
    ]
    basliklar = [_p("<b>Büyüklük</b>", "n")] + [_p(f"<b>{a['ad']}</b>", "sag") for a in asansorler]
    veriler = [basliklar]
    for etiket, fn in satirlar:
        veriler.append([_p(etiket, "n")] + [_p(fn(a), "sag") for a in asansorler])
    gen = [72 * mm] + [(108 / len(asansorler)) * mm] * len(asansorler)
    t = Table(veriler, colWidths=[_w(x) for x in gen], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), MAVI_AC),
        ("BACKGROUND", (0, 1), (0, -1), GRI_AC),
        ("GRID", (0, 0), (-1, -1), 0.3, CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _nufus_tablo(nufus, b):
    veriler = [[_p("<b>Grup / açıklama</b>", "n"), _p("<b>Miktar</b>", "n"),
                _p("<b>Tablo-1 kalemi</b>", "n"), _p("<b>Birim</b>", "n"),
                _p("<b>Katsayı</b>", "n"), _p("<b>c (kişi)</b>", "n")]]
    for s in nufus:
        veriler.append([_p(s["aciklama"], "n"), _p(trn(s["miktar"], 2), "sag"),
                        _p(s["kalem"], "n"), _p(s["birim"], "n"),
                        _p(trn(s["katsayi"], 4), "sag"), _p(trn(s["c"], 2), "sag")])
    veriler.append([_p("<b>TOPLAM  b = Σc</b>", "n"), "", "", "", "", _p(trn(b, 2), "sag")])
    t = Table(veriler, colWidths=[_w(58 * mm), _w(20 * mm), _w(48 * mm), _w(16 * mm), _w(18 * mm), _w(20 * mm)], repeatRows=1)
    n = len(veriler) - 1
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), MAVI_AC),
        ("BACKGROUND", (0, n), (-1, n), GRI_AC),
        ("SPAN", (0, n), (4, n)),
        ("GRID", (0, 0), (-1, -1), 0.3, CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _oneri_tablo(oneriler):
    veriler = [[_p("<b>Seçenek (kabin — hız)</b>", "n"), _p("<b>Adet</b>", "n"),
                _p("<b>Bekleme (sn)</b>", "n"), _p("<b>Sınıf</b>", "n"),
                _p("<b>TR (sn)</b>", "n"), _p("<b>R (kişi/5dk)</b>", "n")]]
    stil = []
    for i, s in enumerate(oneriler, 1):
        veriler.append([_p(s["secenek"], "n"), _p(str(s["adet"]), "sag"),
                        _p(tr(s["Ieer"], 1), "sag"), _p(s["sinif"], "n"),
                        _p(tr(s["TR"], 1), "sag"), _p(tr(s["R"], 1), "sag")])
        if s.get("onerilen"):
            stil.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#E4F3E8")))
    t = Table(veriler, colWidths=[_w(74 * mm), _w(14 * mm), _w(24 * mm), _w(30 * mm), _w(19 * mm), _w(19 * mm)], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), MAVI_AC),
        ("GRID", (0, 0), (-1, -1), 0.3, CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 7.6),
    ] + stil))
    return t


def _imza_kutusu():
    t = Table([[_p("<b>Hesabı yapan</b><br/><br/><br/>", "n"),
                _p("<b>Kontrol eden</b><br/><br/><br/>", "n"),
                _p("<b>Onay</b><br/><br/><br/>", "n")]],
              colWidths=[_w(60 * mm), _w(60 * mm), _w(60 * mm)])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, CIZGI), ("INNERGRID", (0, 0), (-1, -1), 0.4, CIZGI),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# =====================================================================
#  AVAN HESAPLARI PDF
# =====================================================================
def avan_pdf(sonuc: dict, proje: dict = None) -> bytes:
    # ``proje`` eski çağrılarla uyumluluk için kabul edilir, paftaya yazılmaz.
    buf = io.BytesIO()
    doc = _Belge(buf, "ASANSÖR AVAN PROJE HESAPLARI",
                 "MMO / 697  “Asansör Avan Projesi Hazırlama Teknik Esasları”, 2. Baskı, Ocak 2020, s.18-21"
                 "   ·   TS EN 81-20   ·   IEEE Std 80   ·   IEC 60364-5-52")
    ic = [_p("ASANSÖR AVAN PROJE HESAPLARI", "h1"),
          _p("Motor · kuvvetler · aydınlatma · kurulu güç · topraklama  —  MMO/697 s.18-21"
             "   ( Excel : ÖZET ve NOLU ASANSÖR sayfaları )", "alt"),
          Spacer(1, 3 * mm)]
    if sonuc.get("hata"):
        ic += _uyari_kutusu([sonuc["hata"]], hata=True)
    if sonuc.get("uyarilar"):
        ic += _uyari_kutusu(sonuc["uyarilar"])

    # ---- ÖZET
    ic += [Spacer(1, 3.5 * mm), _baslik_seridi("SONUÇ ÖZETİ", "tüm asansörler"), Spacer(1, 1.2 * mm),
           _avan_ozet_tablo(sonuc)]

    # ---- her asansör
    for a in (sonuc.get("asansorler") or []):
        if not a.get("aktif"):
            continue
        ic += [Spacer(1, 6 * mm),
               _baslik_seridi(f"{a['baslik']}" + (f"   —   {a['tanim']}" if a["tanim"] else ""),
                              "AVAN PROJE HESAPLARI")]
        for b in a["bolumler"]:
            ic += _bolum(b)

    # ---- makine dairesi
    mk = sonuc.get("makine_dairesi") or {}
    ic += [Spacer(1, 6 * mm), _baslik_seridi("MAKİNE DAİRESİ AYDINLATMASI", "TS EN 81-20")]
    if mk.get("aktif"):
        ic += _bolum(mk["bolum"])
    else:
        ic += [Spacer(1, 1.5 * mm), _p(mk.get("uyari", ""), "nb")]

    # ---- topraklama
    tp = sonuc.get("topraklama") or {}
    ic += [Spacer(1, 6 * mm), _baslik_seridi("TEMEL TOPRAKLAMA HESABI",
                                             "Temel ( ızgara ) + paralel çubuk topraklayıcı")]
    if tp.get("aktif"):
        for b in tp["bolumler"]:
            ic += _bolum(b)
    else:
        ic += _uyari_kutusu([tp.get("uyari", "")], hata=True)

    ic += [Spacer(1, 5 * mm), _imza_kutusu()]
    doc.build(ic)
    buf.seek(0)
    return buf.read()


def _avan_ozet_tablo(sonuc):
    aktif = [a for a in (sonuc.get("asansorler") or []) if a.get("aktif")]
    if not aktif:
        return _p("Tanımlı asansör yok.", "n")
    satirlar = [
        ("Asansör tanımı", lambda o: o["tanim"] or "—", "—"),
        ("P — Kabin kapasitesi", lambda o: trn(o["kapasite"], 0), "kişi"),
        ("Q — Anma yükü", lambda o: trn(o["Q"], 0), "kg"),
        ("V — Kabin hızı", lambda o: tr(o["V"]), "m/s"),
        ("N — Hesaplanan motor gücü", lambda o: tr(o["N_hes"]), "kW"),
        ("Nsç — Seçilen motor gücü", lambda o: tr(o["Nsc"]), "kW"),
        ("Kontrol  ( Nsç ≥ N )", lambda o: "UYGUN" if o["motor_uygun"] else "UYGUN DEĞİL", ""),
        ("P1 — Kuyu alt boşluğu tabanına", lambda o: trn(o["P1"], 0), "N"),
        ("P2 — Karşı ağırlık tamponu altına", lambda o: trn(o["P2"], 0), "N"),
        ("PR — Bir kabin kılavuz rayına", lambda o: trn(o["PR"], 0), "N"),
        ("PK — Bir karşı ağırlık rayına", lambda o: trn(o["PK"], 0), "N"),
        ("Fs — Kuyu üstü betonuna", lambda o: trn(o["Fs"], 0), "N"),
        ("Kabin armatür sayısı", lambda o: trn(o["n_kabin"], 0), "adet"),
        ("Kuyu armatür sayısı", lambda o: trn(o["n_kuyu"], 0), "adet"),
        ("P — Asansörün kurulu gücü", lambda o: trn(o["P_kurulu"], 0), "W"),
        ("ε — Toplam gerilim düşümü", lambda o: tr(o["eps"], 3), "%"),
        ("Kontrol  ( ε ≤ εmax )", lambda o: "UYGUN" if o["eps_uygun"] else "UYGUN DEĞİL", ""),
        ("I — Hat akımı  /  Iz", lambda o: f"{tr(o['I'],1)} / {trn(o['Iz'],1)}", "A"),
    ]
    basliklar = [_p("<b>Büyüklük</b>", "n")] + \
                [_p(f"<b>{a['no']} NOLU</b>", "sag") for a in aktif] + [_p("<b>Birim</b>", "n")]
    veriler = [basliklar]
    for etiket, fn, birim in satirlar:
        veriler.append([_p(etiket, "n")] + [_p(fn(a["ozet"]), "sag") for a in aktif] + [_p(birim, "n")])
    oz = sonuc.get("ozet") or {"tesis_kurulu_guc": 0, "Re": None, "topraklama_uygun": None}
    veriler.append([_p("<b>Tesisin toplam kurulu gücü</b>", "n"),
                    _p(trn(oz["tesis_kurulu_guc"], 0), "sag")] +
                   [""] * (len(aktif) - 1) + [_p("W", "n")])
    veriler.append([_p("<b>Re — Temel topraklama direnci</b>", "n"),
                    _p(tr(oz["Re"], 3) if oz["Re"] is not None else "—", "sag")] +
                   [""] * (len(aktif) - 1) + [_p("Ω", "n")])
    veriler.append([_p("<b>Topraklama kontrolü  ( Re ≤ UL / IΔn )</b>", "n"),
                    _p("UYGUN" if oz["topraklama_uygun"] else "UYGUN DEĞİL", "sag")] +
                   [""] * (len(aktif) - 1) + [""])
    gen = [70 * mm] + [(94 / len(aktif)) * mm] * len(aktif) + [16 * mm]
    t = Table(veriler, colWidths=[_w(x) for x in gen], repeatRows=1)
    n = len(veriler)
    stil = [
        ("BACKGROUND", (0, 0), (-1, 0), MAVI_AC),
        ("BACKGROUND", (0, 1), (0, -1), GRI_AC),
        ("GRID", (0, 0), (-1, -1), 0.3, CIZGI),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 7.8),
    ]
    for r in (n - 3, n - 2, n - 1):
        stil.append(("BACKGROUND", (0, r), (-1, r), MAVI_AC))
        if len(aktif) > 1:
            stil.append(("SPAN", (1, r), (len(aktif), r)))
    t.setStyle(TableStyle(stil))
    return t
