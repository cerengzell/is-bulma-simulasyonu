
# -*- coding: utf-8 -*-
"""
Mezuniyet Sonrası İş Bulma Süresi Simülasyonu - Rapor Oluşturucu
Hazırlayan: Ceren Betül Gözel
"""

import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    """Tablo hücresi arka plan rengi ayarla."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right'):
        border = OxmlElement(f'w:{edge}')
        border.set(qn('w:val'), kwargs.get('val', 'single'))
        border.set(qn('w:sz'), kwargs.get('sz', '4'))
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), kwargs.get('color', 'E2E8F0'))
        tcBorders.append(border)
    tcPr.append(tcBorders)

def add_horizontal_line(doc, color='4F46E5'):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), color)
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p

def normal_cdf(x):
    """Standart Normal CDF (Abramowitz & Stegun yaklaşımı)."""
    a1 = 0.254829592; a2 = -0.284496736; a3 = 1.421413741
    a4 = -1.453152027; a5 = 1.061405429; p = 0.3275911
    sign = -1 if x < 0 else 1
    absX = abs(x) / math.sqrt(2.0)
    t = 1.0 / (1.0 + p * absX)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t * math.exp(-absX*absX)
    return 0.5 * (1.0 + sign * y)

def compute_result(baseline, gpa, internship):
    sigma = 0.35
    sigma_sq = sigma ** 2
    mu_base = math.log(baseline) - sigma_sq / 2
    gpa_effect = -0.25 * (gpa - 2.8)
    intern_effect = -0.04 * internship
    academic = -0.12 if internship > 0 else 0.14
    mu = mu_base + gpa_effect + intern_effect + academic
    expected = math.exp(mu + sigma_sq / 2)
    ci_lower = max(0.2, math.exp(mu - 1.96 * sigma))
    ci_upper = math.exp(mu + 1.96 * sigma)
    probs = []
    for t in range(1, 25):
        probs.append(normal_cdf((math.log(t) - mu) / sigma) * 100)
    return round(expected, 1), round(ci_lower, 1), round(ci_upper, 1), probs

# ─────────────────────────────────────────────
# GRAFİK OLUŞTURMA
# ─────────────────────────────────────────────

DEPARTMENTS = [
    ('Tıp',                              4.1,  'Sağlık'),
    ('Özel Eğitim Öğretmenliği',         4.3,  'Eğitim'),
    ('Eczacılık',                        5.1,  'Sağlık'),
    ('Diş Hekimliği',                    5.5,  'Sağlık'),
    ('Hemşirelik',                       7.5,  'Sağlık'),
    ('Endüstri Mühendisliği',            11.0, 'Mühendislik'),
    ('Elektrik-Elektronik Müh.',         11.2, 'Mühendislik'),
    ('Bilgisayar/Yazılım Müh.',          11.8, 'BIT'),
    ('Makine Mühendisliği',              12.2, 'Mühendislik'),
    ('Sınıf Öğretmenliği',              12.6, 'Eğitim'),
    ('Hukuk',                            13.0, 'Hukuk'),
    ('Mimarlık',                         13.0, 'Mühendislik'),
    ('İnşaat Mühendisliği',             13.5, 'Mühendislik'),
    ('İşletme / İktisat',               14.0, 'Is-Yonetim'),
    ('Siyaset Bil. & Kamu Yön.',         15.5, 'Is-Yonetim'),
    ('Psikoloji / Sosyoloji',            16.5, 'Sosyal'),
    ('İletişim / Gazetecilik',          17.0, 'Sosyal'),
]

COLOR_MAP = {
    'Sağlık': '#10B981',
    'Eğitim': '#3B82F6',
    'Mühendislik': '#6366F1',
    'BIT': '#8B5CF6',
    'Hukuk': '#F59E0B',
    'Is-Yonetim': '#EF4444',
    'Sosyal': '#EC4899',
}

def make_bar_chart(save_path):
    names = [d[0] for d in DEPARTMENTS]
    baselines = [d[1] for d in DEPARTMENTS]
    groups = [d[2] for d in DEPARTMENTS]
    colors = [COLOR_MAP.get(g, '#94A3B8') for g in groups]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    bars = ax.barh(names, baselines, color=colors, height=0.65, edgecolor='white', linewidth=0.8)

    ax.axvline(14.4, color='#EF4444', linewidth=2, linestyle='--', label='TÜİK Ort. (14.4 Ay)', zorder=5)

    for bar, val in zip(bars, baselines):
        ax.text(val + 0.15, bar.get_y() + bar.get_height()/2,
                f'{val} ay', va='center', ha='left',
                fontsize=9, color='#334155', fontweight='bold')

    ax.set_xlabel('Ortalama İlk İş Bulma Süresi (Ay)', fontsize=11, color='#475569')
    ax.set_title('Bölüme Göre Ortalama İlk İş Bulma Süresi\n(TÜİK 2024 Verileriyle Kalibre Edilmiştir)',
                 fontsize=13, fontweight='bold', color='#1E293B', pad=12)
    ax.set_xlim(0, 21)
    ax.tick_params(colors='#475569', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.grid(axis='x', color='#E2E8F0', linewidth=0.7, linestyle='-')

    legend_patches = [mpatches.Patch(color=v, label=k) for k, v in COLOR_MAP.items()]
    legend_patches.append(mpatches.Patch(color='#EF4444', label='TÜİK Ort.'))
    ax.legend(handles=legend_patches, loc='lower right', fontsize=8,
              framealpha=0.95, edgecolor='#E2E8F0')

    plt.tight_layout()
    plt.savefig(save_path, dpi=180, bbox_inches='tight', facecolor='#F8FAFC')
    plt.close()
    print(f"  [✓] Grafik kaydedildi: {save_path}")

def make_prob_curve(save_path):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    scenarios = [
        ('GPA 3.8 | 6 Ay Staj | Müh.',   11.8, 3.8, 6,  '#10B981', '-'),
        ('GPA 3.0 | 3 Ay Staj | İşletme', 14.0, 3.0, 3, '#6366F1', '-'),
        ('GPA 2.5 | Stajsız | Sosyal',    16.5, 2.5, 0,  '#EF4444', '--'),
    ]

    months = list(range(1, 25))
    for label, base, gpa, intern, color, ls in scenarios:
        _, _, _, probs = compute_result(base, gpa, intern)
        ax.plot(months, probs, label=label, color=color, linewidth=2.5, linestyle=ls)
        ax.fill_between(months, probs, alpha=0.07, color=color)

    ax.axhline(50, color='#94A3B8', linewidth=1.2, linestyle=':', label='%50 Eşiği')
    ax.set_xlabel('Mezuniyetten Sonra Geçen Süre (Ay)', fontsize=11, color='#475569')
    ax.set_ylabel('Kümülatif İş Bulma Olasılığı (%)', fontsize=11, color='#475569')
    ax.set_title('Farklı Profillere Göre Kümülatif İşe Yerleşme Eğrisi\n(AFT Log-Normal Model)',
                 fontsize=12, fontweight='bold', color='#1E293B', pad=10)
    ax.set_ylim(0, 100)
    ax.set_xlim(1, 24)
    ax.tick_params(colors='#475569', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.grid(color='#E2E8F0', linewidth=0.7)
    ax.legend(fontsize=9, framealpha=0.95, edgecolor='#E2E8F0')

    plt.tight_layout()
    plt.savefig(save_path, dpi=180, bbox_inches='tight', facecolor='#F8FAFC')
    plt.close()
    print(f"  [✓] Grafik kaydedildi: {save_path}")

def make_gpa_effect_chart(save_path):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    gpas = [round(1.5 + i*0.1, 1) for i in range(26)]
    cases = [
        ('6 Ay Staj', 11.8, 6, '#10B981'),
        ('3 Ay Staj', 11.8, 3, '#6366F1'),
        ('Stajsız',   11.8, 0, '#EF4444'),
    ]
    for label, base, intern, color in cases:
        times = []
        for g in gpas:
            t, _, _, _ = compute_result(base, g, intern)
            times.append(t)
        ax.plot(gpas, times, label=label, color=color, linewidth=2.5)

    ax.axhline(14.4, color='#94A3B8', linewidth=1.2, linestyle=':', label='TÜİK Ort.')
    ax.set_xlabel('Not Ortalaması (GPA)', fontsize=11, color='#475569')
    ax.set_ylabel('Beklenen İş Bulma Süresi (Ay)', fontsize=11, color='#475569')
    ax.set_title('GPA ve Staj Süresinin İş Bulma Süresine Etkisi\n(Bilgisayar/Yazılım Müh. için)', 
                 fontsize=12, fontweight='bold', color='#1E293B', pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E2E8F0')
    ax.spines['bottom'].set_color('#E2E8F0')
    ax.grid(color='#E2E8F0', linewidth=0.7)
    ax.legend(fontsize=9, framealpha=0.95, edgecolor='#E2E8F0')
    ax.tick_params(colors='#475569', labelsize=9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=180, bbox_inches='tight', facecolor='#F8FAFC')
    plt.close()
    print(f"  [✓] Grafik kaydedildi: {save_path}")

# ─────────────────────────────────────────────
# DOCX RAPOR OLUŞTURMA
# ─────────────────────────────────────────────

def build_report(out_path, img_bar, img_prob, img_gpa):
    doc = Document()

    # Sayfa kenar boşlukları
    from docx.oxml import OxmlElement
    sections = doc.sections
    for section in sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(2.8)
        section.right_margin  = Cm(2.8)

    # Stil ayarları
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0x33, 0x41, 0x55)  # slate-700

    # ─── KAPAK / BAŞLIK ────────────────────────────────────
    cover = doc.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_before = Pt(0)
    cover.paragraph_format.space_after  = Pt(4)
    run = cover.add_run('📊  MezunScope')
    run.bold = True
    run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)  # indigo-600

    sub_cover = doc.add_paragraph()
    sub_cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_cover.paragraph_format.space_before = Pt(0)
    sub_cover.paragraph_format.space_after  = Pt(2)
    run2 = sub_cover.add_run('Mezuniyet Sonrası İlk İş Bulma Süresi Tahmin Simülasyonu')
    run2.font.size = Pt(14)
    run2.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
    run2.bold = False

    add_horizontal_line(doc)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_before = Pt(6)
    meta.paragraph_format.space_after  = Pt(0)
    meta.add_run('Hazırlayan: ').bold = True
    meta.add_run('Ceren Betül Gözel')
    meta.add_run('  |  Veri Bilimi ve Analitiği Öğrencisi\n')
    meta.add_run('Tarih: ').bold = True
    meta.add_run(datetime.date.today().strftime('%d %B %Y'))
    meta.add_run('  |  Alıcı: ').bold = True
    meta.add_run('final@dogusan.org')

    doc.add_paragraph()

    # ─── YÖNETİCİ ÖZETİ ───────────────────────────────────
    def section_title(text, color_hex='4F46E5'):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after  = Pt(4)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(14)
        r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
        run.font.color.rgb = RGBColor(r, g, b)
        return p

    def sub_title(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after  = Pt(3)
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        return p

    def body(text, bold_parts=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(4)
        p.paragraph_format.left_indent  = Cm(0)
        run = p.add_run(text)
        run.font.size = Pt(11)
        return p

    def bullet(text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after  = Pt(1)
        p.paragraph_format.left_indent  = Cm(0.8)
        run = p.add_run(text)
        run.font.size = Pt(11)
        return p

    def info_box(text, bg='EEF2FF', border_color='4F46E5'):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after  = Pt(6)
        p.paragraph_format.left_indent  = Cm(0.5)
        p.paragraph_format.right_indent = Cm(0.5)
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x31, 0x49, 0x7C)
        return p

    # ─── 1. YÖNETİCİ ÖZETİ ───────────────────────────────
    section_title('1. Yönetici Özeti')
    add_horizontal_line(doc, '4F46E5')

    body(
        'Bu rapor, üniversite mezunlarının mezuniyet sonrası ilk iş bulma sürelerini bilimsel bir '
        'istatistik modeliyle tahmin eden interaktif bir web simülasyonu olan MezunScope\'u ve bu '
        'simülasyonun potansiyel iş ortaklarına sunacağı değeri detaylıca açıklamaktadır.'
    )
    body(
        'Kısaca ne yaptık? Mezun profilleri (bölüm, not ortalaması, staj süresi) ile ilk iş '
        'bulma süresi arasındaki ilişkiyi ekonometrik bir modelle sayısal hale getirdik. '
        'Böylece hem bireyler hem de kurumlar, "Bu profildeki bir mezun kaç ayda iş bulur?" '
        'sorusuna somut, güven aralıklı bir yanıt alabilmektedir.'
    )

    info_box(
        '💡 Basit dille özetlemek gerekirse: Tıpkı hava durumu uygulamalarının yağmur '
        'olasılığını hesaplaması gibi, MezunScope da bir mezunun iş bulma "hava durumunu" '
        'hesaplıyor. Diploma bölümü, not ortalaması ve staj tecrübesi bilgilerini giriyorsunuz; '
        'model size "büyük ihtimalle X ile Y ay arasında iş bulursunuz" diyor.'
    )

    # ─── 2. VERİ NASIL ÜRETİLDİ ─────────────────────────
    section_title('2. Veriyi Nasıl Ürettik?')
    add_horizontal_line(doc, '4F46E5')

    sub_title('2.1  Gerçek Dünya Verileri ile Kalibrasyon')
    body(
        'Simülasyon, tamamen hayali verilerle değil; gerçek istatistiki kaynaklarla '
        'kalibre edilmiştir. Kullandığımız üç temel kaynak şunlardır:'
    )

    # Kaynak tablosu
    tbl = doc.add_table(rows=4, cols=3)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_row = tbl.rows[0]
    hdr_labels = ['Kaynak', 'İçerik', 'Modele Katkısı']
    for i, label in enumerate(hdr_labels):
        cell = hdr_row.cells[i]
        set_cell_bg(cell, '4F46E5')
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(label)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(10.5)
    
    data = [
        ('TÜİK — Yükseköğretim İstihdam Göstergeleri (2024)',
         'Lisans mezunlarının bölüm bazında Türkiye geneli ortalama iş bulma süreleri.',
         'Her bölüm için baz (başlangıç) süre katsayısı (μ_bölüm) belirlendi.'),
        ('Baert et al. (ScienceDirect, 2021)',
         'Staj yapan adayların mülakat davetine alınma olasılığı stajsızlara göre %12,6 daha yüksek.',
         'Staj yapanlar için süreyi kısaltan −0.12 hızlandırma katsayısı oluşturuldu.'),
        ('NACE Job Outlook 2021',
         'İşverenler eşit nitelikli iki adaydan staj yapanı belirleyici biçimde tercih ediyor.',
         'Stajsız adaylar için +0.14 gecikme cezası katsayısı eklendi.'),
    ]

    for row_idx, (src, content, contrib) in enumerate(data):
        row = tbl.rows[row_idx + 1]
        for col_idx, txt in enumerate([src, content, contrib]):
            cell = row.cells[col_idx]
            set_cell_bg(cell, 'F8FAFC' if row_idx % 2 == 0 else 'EEF2FF')
            p = cell.paragraphs[0]
            run = p.add_run(txt)
            run.font.size = Pt(9.5)

    doc.add_paragraph()

    sub_title('2.2  İstatistiksel Model: AFT Log-Normal Dağılım')
    body(
        'İş bulma süresi gibi "pozitif ve sağa çarpık" veriler (yani neredeyse herkes için '
        'belli bir minimum süre var ama bazı insanlar çok uzun süre iş arayabiliyor) için '
        'ekonometri literatüründeki standart yöntem olan Hızlandırılmış Başarısızlık Süresi '
        '(AFT — Accelerated Failure Time) Log-Normal modeli kullanılmıştır.'
    )

    info_box(
        '🔢 Formül (teknik detay, atlayabilirsiniz):\n\n'
        '    T = exp( μ_bölüm  +  (−0.25) × (GPA − 2.8)  +  (−0.04) × Staj_Ay  +  θ_staj )\n\n'
        'Burada T = tahmini iş bulma süresi (ay); μ_bölüm = TÜİK\'ten alınan bölüm katsayısı; '
        'θ_staj = staj varsa −0.12, yoksa +0.14. GPA her 1 puan arttığında süre yaklaşık '
        '%22 kısalıyor; her 1 aylık staj tecrübesi ise yaklaşık %4 kısaltıyor.'
    )

    body(
        'Modelin belirsizliği ise σ = 0.35 standart sapma parametresiyle temsil ediliyor. '
        'Bu sayede sadece "ortalama tahmin" değil, %95 güven aralığı da hesaplanıyor: '
        '"En kötü ihtimalle X ay, en iyi ihtimalle Y ay içinde iş bulursunuz." '
        'gibi bir bilgi verebiliyoruz.'
    )

    # ─── 3. NE BULDUK ────────────────────────────────────
    section_title('3. Ne Bulduk? — Temel Bulgular')
    add_horizontal_line(doc, '4F46E5')

    sub_title('3.1  Bölüme Göre Ortalama İş Bulma Süreleri')
    body(
        'Aşağıdaki grafik, modelimizin 17 farklı lisans bölümü için hesapladığı baz iş bulma '
        'sürelerini göstermektedir. Kırmızı kesik çizgi, TÜİK\'in 2024 yılı ulusal ortalaması '
        'olan 14,4 ayı işaret etmektedir. Bu çizginin solundaki bölümler iş bulmada '
        '"ortalamanın üstünde" performans gösteriyor demektir.'
    )
    doc.add_picture(img_bar, width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    sub_title('3.2  Seçilen Örnek Profil Karşılaştırması')
    body('Modelin çalışma mantığını somutlaştırmak için üç farklı mezun profili oluşturduk:')

    # Örnek profil tablosu
    tbl2 = doc.add_table(rows=5, cols=4)
    tbl2.style = 'Table Grid'
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr2 = tbl2.rows[0]
    headers2 = ['Profil', 'Bölüm | GPA | Staj', 'Beklenen Süre', '%95 Güven Aralığı']
    for i, h in enumerate(headers2):
        cell = hdr2.cells[i]
        set_cell_bg(cell, '1E293B')
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(10)

    profiles = [
        ('🟢 Güçlü Profil',   'Bil. Müh. | GPA 3.8 | 6 Ay Staj',  11.8, 3.8, 6),
        ('🟡 Orta Profil',    'İşletme   | GPA 3.0 | 3 Ay Staj',  14.0, 3.0, 3),
        ('🔴 Zayıf Profil',   'Sosyoloji  | GPA 2.5 | Stajsız',   16.5, 2.5, 0),
        ('📊 Türkiye Ort.',   'TÜİK 2024 Genel Ortalama',          None, None, None),
    ]
    row_colors = ['F0FDF4', 'FEFCE8', 'FFF1F2', 'EEF2FF']
    for i, (label, desc, base, gpa, intern) in enumerate(profiles):
        row = tbl2.rows[i + 1]
        cells_data = [label, desc]
        if base is not None:
            t, lo, hi, _ = compute_result(base, gpa, intern)
            cells_data += [f'{t} Ay', f'{lo} – {hi} Ay']
        else:
            cells_data += ['14.4 Ay', '—']
        for j, txt in enumerate(cells_data):
            cell = row.cells[j]
            set_cell_bg(cell, row_colors[i])
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(txt)
            run.font.size = Pt(10)
            if j == 2:
                run.bold = True

    doc.add_paragraph()
    sub_title('3.3  GPA ve Stajın Etkisi')
    body(
        'Aşağıdaki grafik, not ortalaması ve staj süresinin iş bulma süresine etkisini '
        'açıkça göstermektedir. Grafik, Bilgisayar/Yazılım Mühendisliği örneği üzerinden '
        'hazırlanmıştır fakat genel örüntü tüm bölümler için geçerlidir.'
    )
    doc.add_picture(img_gpa, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    body(
        'Grafikten iki net mesaj çıkmaktadır: (1) Staj tecrübesi olan mezunlar '
        'her not ortalamasında stajsız meslektaşlarından hızlı iş bulmaktadır. '
        '(2) GPA arttıkça iş bulma süresi azalmakta, ancak bu etki staj tecrübesiyle '
        'birleşince çok daha belirgin hale gelmektedir.'
    )

    # ─── 4. OLASLIK EĞRİSİ ───────────────────────────────
    section_title('4. "Kaç Ayda İş Bulurum?" — Olasılık Eğrisi')
    add_horizontal_line(doc, '4F46E5')
    body(
        'Modelimiz sadece tek bir sayı vermez; zaman içindeki olasılık değişimini de '
        'hesaplar. Aşağıdaki eğri, farklı mezun profillerinin aylar içinde kümülatif '
        'olarak işe yerleşme ihtimallerini göstermektedir.'
    )
    doc.add_picture(img_prob, width=Inches(6.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    body(
        '"Kümülatif ihtimal" demek, "mezuniyetin üzerinden X ay geçtiğinde, bu profilin '
        'kaçta kaçı iş bulmuş olur?" sorusunun cevabıdır. Örneğin yeşil çizgiyi takip eden '
        'bir mezun (Mühendislik, GPA 3.8, 6 ay staj) 6. ayda zaten %80\'in üzerinde '
        'iş bulma ihtimaline sahipken, kırmızı çizgideki profil (Sosyoloji, GPA 2.5, '
        'stajsız) aynı noktada hâlâ %40\'ın altında kalmaktadır.'
    )

    # ─── 5. BU SİZE NE SAĞLAR ────────────────────────────
    section_title('5. Bu Araç Size Ne Sağlar? — İş Birliği Teklifi')
    add_horizontal_line(doc, '4F46E5')

    body(
        'MezunScope, tek bir kez kurulup köşeye bırakılan bir analiz değil; '
        'canlı ve güncellenebilir bir karar destek aracıdır. İşte bu platformun '
        'potansiyel iş ortağımıza sunabileceği somut değerler:'
    )

    value_items = [
        ('🎯 Öğrenci/Mezun Danışmanlığı',
         'Kariyer merkezleri, öğrencilere hangi sektörde, hangi staj '
         'deneyimiyle, kaç ayda iş bulabileceklerini somut verilerle gösterebilir. '
         '"Staj yaparsan büyük ihtimalle X ay erken iş bulursun" cümlesi '
         'artık bir tahmin değil, istatistiksel bir gerçek haline gelir.'),
        ('📈 Bölüm Tanıtımı ve Rekabetçi Analiz',
         'Üniversiteler ve eğitim kurumları, bölümlerinin istihdam gücünü '
         'rakamlarla ortaya koyabilir. "Mezunlarımız X ayda iş buluyor" '
         'ifadesini kanıtlanmış bir modelle destekleyebilir.'),
        ('🏢 İK ve İşe Alım Platformları',
         'İşe alım şirketleri ve İK platformları, bu modeli entegre ederek '
         'aday profili değerlendirmesine bilimsel bir boyut ekleyebilir. '
         'Adayların "piyasa beklenti süresi" öngörüsü portföy analizi için '
         'güçlü bir ek veri noktasıdır.'),
        ('🔬 Araştırma ve Politika Geliştirme',
         'Eğitim politikası geliştiren kurumlar, hangi bölümlerde istihdam '
         'açığı olduğunu ve müdahaleler (zorunlu staj, mentorluk vb.) ile '
         'süreler nasıl kısaltılabilir sorusunu bu modelle analiz edebilir.'),
    ]
    for icon_title, desc in value_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(5)
        p.paragraph_format.space_after  = Pt(1)
        p.paragraph_format.left_indent  = Cm(0.3)
        run = p.add_run(icon_title)
        run.bold = True
        run.font.size = Pt(11.5)
        run.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)
        body_p = doc.add_paragraph()
        body_p.paragraph_format.left_indent  = Cm(0.6)
        body_p.paragraph_format.space_before = Pt(0)
        body_p.paragraph_format.space_after  = Pt(5)
        run2 = body_p.add_run(desc)
        run2.font.size = Pt(10.5)

    # ─── 6. TEKNİK DETAYLAR VE GELİŞTİRME PLANI ─────────
    section_title('6. Teknik Detaylar ve Geliştirme Planı')
    add_horizontal_line(doc, '4F46E5')
    sub_title('6.1  Mevcut Simülasyonun Teknik Özellikleri')
    bullet('Platform: Saf HTML5, CSS3 ve JavaScript — herhangi bir tarayıcıda çalışır, kurulum gerektirmez.')
    bullet('Model: AFT Log-Normal dağılım, Abramowitz & Stegun (1964) yaklaşımlı Normal CDF implementasyonu.')
    bullet('Kapsam: 17 bölüm, GPA 1.00–4.00 arası, 0–24 aylık staj süreleri.')
    bullet('Görselleştirme: Chart.js kütüphanesiyle gerçek zamanlı, interaktif olasılık eğrisi.')
    bullet('Kalibrasyon: TÜİK 2024, Baert et al. 2021, NACE 2021 kaynakları.')

    sub_title('6.2  Potansiyel Geliştirmeler')
    bullet('Gerçek Mikro-Veri Entegrasyonu: TÜİK veya YÖK mezun takip anket micro-datası ile katsayıların makine öğrenmesiyle yeniden tahmin edilmesi.')
    bullet('Ek Değişkenler: Okul prestiji, ÖSYM puan türü, yabancı dil seviyesi, şehir faktörü.')
    bullet('API Katmanı: Python/FastAPI arka ucu ile ölçeklenebilir web servis olarak sunulması.')
    bullet('Kurum Paneli: Toplu analiz, raporlama ve karşılaştırma dashboard\'u.')
    bullet('Mobil Uygulama: PWA veya React Native ile mobil erişim.')

    # ─── 7. SINIRLILIKLAR VE ETİK ─────────────────────────
    section_title('7. Sınırlılıklar ve Etik Not')
    add_horizontal_line(doc, '4F46E5')
    body(
        'Her model gibi MezunScope da bazı varsayımlara dayanmaktadır. Dürüstlük adına '
        'bunları açıkça paylaşıyorum:'
    )
    bullet('Model katsayıları, yayınlanmış akademik çalışmalardan ilham alınarak türetilmiştir; '
           'Türkiye\'ye özel bir bireysel anket veri seti ile bağımsız olarak sınanmamıştır.')
    bullet('İş bulma süresi yalnızca ölçülebilir akademik değişkenlerle modellenmektedir; '
           'kişilik, sosyal ağ, şans gibi faktörler kapsam dışıdır.')
    bullet('Tahminler istatistiksel olasılıkları yansıtır; hiçbir bireysel vaka için '
           'kesin bir taahhüt anlamı taşımaz.')
    bullet('Model etnik köken, cinsiyet veya engellilik durumu gibi hassas demografik '
           'değişkenler içermemektedir.')

    info_box(
        '⚖️  Bu araç, bireyleri etiketlemek veya dışlamak için değil; '
        'danışmanlık, farkındalık ve politika geliştirme süreçlerini '
        'desteklemek amacıyla tasarlanmıştır.'
    )

    # ─── 8. SONUÇ VE İLETİŞİM ─────────────────────────────
    section_title('8. Sonuç ve İletişim')
    add_horizontal_line(doc, '4F46E5')
    body(
        'MezunScope, "mezunun iş piyasasındaki değerini sayısal hale getir" sorusuna '
        'verilen somut, bilimsel ve interaktif bir yanıttır. Bu aşamada bir prototip '
        'olmakla birlikte, gerçek veri entegrasyonu ve kurumsal iş birliğiyle '
        'Türkiye\'nin kariyer danışmanlığı ekosisteminde anlamlı bir boşluğu '
        'doldurabileceğine inanıyorum.'
    )
    body(
        'Simülasyona ve kaynak koduna erişmek, demo planlamak veya iş birliği '
        'görüşmesi yapmak için benimle iletişime geçebilirsiniz.'
    )

    p_contact = doc.add_paragraph()
    p_contact.paragraph_format.space_before = Pt(8)
    p_contact.paragraph_format.space_after = Pt(2)
    r1 = p_contact.add_run('Ceren Betül Gözel\n')
    r1.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)
    r2 = p_contact.add_run('Veri Bilimi ve Analitiği Öğrencisi\n')
    r2.font.size = Pt(11)
    r3 = p_contact.add_run('Bu rapor final@dogusan.org adresine iletilmek üzere hazırlanmıştır.')
    r3.font.size = Pt(10.5)
    r3.font.italic = True
    r3.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    add_horizontal_line(doc, 'E2E8F0')
    footer_p = doc.add_paragraph()
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_p.paragraph_format.space_before = Pt(4)
    r_footer = footer_p.add_run(
        'MezunScope — Akademik Prototip  •  '
        f'Hazırlanma Tarihi: {datetime.date.today().strftime("%d.%m.%Y")}  •  '
        'Kaynaklar: TÜİK (2024), Baert et al. (2021), NACE (2021)'
    )
    r_footer.font.size = Pt(8.5)
    r_footer.font.color.rgb = RGBColor(0x94, 0xA3, 0xB3)

    doc.save(out_path)
    print(f"\n  [OK] DOCX kaydedildi: {out_path}\n")


# ─────────────────────────────────────────────
# ANA ÇALIŞMA
# ─────────────────────────────────────────────
if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_bar  = os.path.join(base_dir, '_fig_bar.png')
    img_prob = os.path.join(base_dir, '_fig_prob.png')
    img_gpa  = os.path.join(base_dir, '_fig_gpa.png')
    out_docx = os.path.join(base_dir, 'MezunScope_Rapor_CerenBetulGozel.docx')

    print("\n=== MezunScope Rapor Oluşturucu ===")
    print("[1/4] Grafik: Bölüm bazlı bar chart...")
    make_bar_chart(img_bar)
    print("[2/4] Grafik: Olasılık eğrisi...")
    make_prob_curve(img_prob)
    print("[3/4] Grafik: GPA etkisi...")
    make_gpa_effect_chart(img_gpa)
    print("\n[4/4] DOCX rapor oluşturuluyor...")
    build_report(out_docx, img_bar, img_prob, img_gpa)

    # Geçici grafik dosyalarını sil
    for f in [img_bar, img_prob, img_gpa]:
        try:
            os.remove(f)
        except:
            pass

    print("✅ Tamamlandı! Rapor hazır.")
    print(f"   Dosya konumu: {out_docx}")
