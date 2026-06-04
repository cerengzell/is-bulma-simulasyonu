// 1. Bölüm Tanımlamaları (TÜİK 2024 ve Temmuz 2025 Güncellemesi Bazlı)
const DEPARTMENTS = [
    { id: 'tip', name: 'Tıp', baseline: 4.1, group: 'Sağlık' },
    { id: 'ozel_egitim', name: 'Özel Eğitim Öğretmenliği', baseline: 4.3, group: 'Eğitim' },
    { id: 'eczacilik', name: 'Eczacılık', baseline: 5.1, group: 'Sağlık' },
    { id: 'dis_hekimligi', name: 'Diş Hekimliği', baseline: 5.5, group: 'Sağlık' },
    { id: 'hemsirelik', name: 'Hemşirelik', baseline: 7.5, group: 'Sağlık' },
    { id: 'endustri_muh', name: 'Endüstri Mühendisliği', baseline: 11.0, group: 'Mühendislik' },
    { id: 'elk_elek_muh', name: 'Elektrik-Elektronik Mühendisliği', baseline: 11.2, group: 'Mühendislik' },
    { id: 'bilgisayar_muh', name: 'Bilgisayar/Yazılım Mühendisliği', baseline: 11.8, group: 'BİT' },
    { id: 'makine_muh', name: 'Makine Mühendisliği', baseline: 12.2, group: 'Mühendislik' },
    { id: 'sinif_ogretmenligi', name: 'Sınıf Öğretmenliği', baseline: 12.6, group: 'Eğitim' },
    { id: 'hukuk', name: 'Hukuk', baseline: 13.0, group: 'Hukuk' },
    { id: 'mimarlik', name: 'Mimarlık', baseline: 13.0, group: 'Mühendislik' },
    { id: 'insaat_muh', name: 'İnşaat Mühendisliği', baseline: 13.5, group: 'Mühendislik' },
    { id: 'isletme_iktisat', name: 'İşletme / İktisat', baseline: 14.0, group: 'İş-Yönetim' },
    { id: 'siyaset_kamu', name: 'Siyaset Bilimi ve Kamu Yönetimi', baseline: 15.5, group: 'İş-Yönetim' },
    { id: 'psikoloji_sosyoloji', name: 'Psikoloji / Sosyoloji', baseline: 16.5, group: 'Sosyal Bilimler' },
    { id: 'iletisim_gazete', name: 'İletişim / Gazetecilik', baseline: 17.0, group: 'Sosyal Bilimler' }
];

// Uygulama Durumu (State)
let chartProbCurve = null;

// Dışa Aktarım için son hesaplanan veri (export için global)
let lastExportData = null;

// Standart Normal Kümülatif Dağılım Fonksiyonu (CDF) Φ(x)
// Abramowitz and Stegun yaklaşımı (Hata Payı < 7.5e-8)
function normalCDF(x) {
    const a1 = 0.254829592;
    const a2 = -0.284496736;
    const a3 = 1.421413741;
    const a4 = -1.453152027;
    const a5 = 1.061405429;
    const p = 0.3275911;

    const sign = (x < 0) ? -1 : 1;
    const absX = Math.abs(x) / Math.sqrt(2.0);

    const t = 1.0 / (1.0 + p * absX);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-absX * absX);

    return 0.5 * (1.0 + sign * y);
}

// Bireysel Tahmin Hesaplayıcı Mantığı
function updatePrediction() {
    const deptId = document.getElementById('calc-dept').value;
    const gpa = parseFloat(document.getElementById('calc-gpa').value);
    const internship = parseInt(document.getElementById('calc-internship').value);

    const dept = DEPARTMENTS.find(d => d.id === deptId);
    if (!dept) return;

    // Akademik ve ampirik çalışmalardan elde edilen sabitleştirilmiş katsayılar
    const coefGPA = -0.25;       // GPA artışı etkisi
    const coefStaj = -0.04;      // Staj süresi (ay) etkisi
    const noiseSigma = 0.35;     // Standart sapma (belirsizlik katsayısı)

    // AFT Katsayı Hesaplaması
    // Log-normal ortalama E[T] = exp(mu + sigma^2/2) olduğu için, 
    // baseline değerine tam uyması için mu_base = ln(baseline) - sigma^2/2 yaparız.
    const sigmaSq = noiseSigma * noiseSigma;
    const muBase = Math.log(dept.baseline) - sigmaSq / 2;

    // Bağımsız değişkenlerin etkisi (Referans noktası: GPA = 2.8, Staj = 0)
    const gpaEffect = coefGPA * (gpa - 2.8);
    const internshipEffect = coefStaj * internship;

    // Baert et al. (ScienceDirect, 2021) & NACE Job Outlook 2021 Etkisi:
    // Staj tecrübesi olanlar (staj > 0) için Baert et al. referanslı 
    // mülakat olasılığı artışı nedeniyle ekstra %12.6 daha hızlı işe yerleşme (hazarda çarpanı)
    // NACE Job Outlook 2021 etkisi: Stajı olmayanlar (staj === 0) için %15 gecikme cezası (işverenlerin stajı belirleyici görmesi)
    let academicRefMultiplier = 0.0;
    if (internship > 0) {
        academicRefMultiplier = -0.12; 
    } else {
        academicRefMultiplier = 0.14; 
    }

    // Toplam mu parametresi
    const mu = muBase + gpaEffect + internshipEffect + academicRefMultiplier;

    // Beklenen değer (Beklenti E[T] = exp(mu + sigma^2/2))
    const expectedTime = Math.exp(mu + sigmaSq / 2);
    const finalExpectedTime = Math.max(0.5, parseFloat(expectedTime.toFixed(1)));

    // 95% Güven Aralığı Hesaplama (Log-normal için exp(mu +- 1.96 * sigma))
    const ciLower = Math.max(0.2, Math.exp(mu - 1.96 * noiseSigma));
    const ciUpper = Math.exp(mu + 1.96 * noiseSigma);
    
    // UI Güncelleme - Ortalama Süre ve Güven Aralığı
    document.getElementById('calc-result-val').innerText = finalExpectedTime.toFixed(1) + ' Ay';
    document.getElementById('calc-ci-val').innerText = `En Olası Aralık: ${ciLower.toFixed(1)} - ${ciUpper.toFixed(1)} Ay (%95 Güven)`;

    // TÜİK Kıyaslama İlerleme Çubuğu (TÜİK ortalaması 14.4 aydır)
    const maxVal = 24.0; // Grafik ölçeği maksimum ay
    const expectedPct = Math.min(100, (finalExpectedTime / maxVal) * 100);
    const fillEl = document.getElementById('calc-compare-fill');
    
    fillEl.style.width = expectedPct + '%';
    document.getElementById('compare-text-val').innerText = `${finalExpectedTime.toFixed(1)} Ay`;
    
    // TÜİK Oran Karşılaştırması ve Renk Yönetimi
    const badgeEl = document.getElementById('compare-pct-badge');
    const diffPct = ((14.4 - finalExpectedTime) / 14.4) * 100;

    if (finalExpectedTime < 10.0) {
        // Hızlı (Yeşil)
        fillEl.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)'; 
        badgeEl.style.color = '#10b981';
        badgeEl.innerText = `TÜİK Ortalamasından %${Math.abs(diffPct).toFixed(0)} Daha Hızlı`;
    } else if (finalExpectedTime <= 14.4) {
        // Normal (Mavi/Indigo)
        fillEl.style.background = 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)';
        badgeEl.style.color = '#4f46e5';
        badgeEl.innerText = `TÜİK Ortalamasından %${Math.abs(diffPct).toFixed(0)} Daha Hızlı`;
    } else {
        // Yavaş (Kırmızı/Turuncu)
        fillEl.style.background = 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)';
        badgeEl.style.color = '#ef4444';
        badgeEl.innerText = `TÜİK Ortalamasından %${Math.abs(diffPct).toFixed(0)} Daha Yavaş`;
    }

    // İşe Yerleşme Olasılık Eğrisi Grafik Güncellemesi
    let timeLabels = [];
    let probData = [];
    for (let t = 1; t <= 24; t += 1) {
        timeLabels.push(t + '. Ay');
        // P(T <= t) = Φ((ln(t) - mu) / sigma)
        const p = normalCDF((Math.log(t) - mu) / noiseSigma);
        probData.push(parseFloat((p * 100).toFixed(1)));
    }

    // Dışa aktarım için hesaplanan verileri global değişkene kaydet
    lastExportData = {
        inputs: {
            bolum: dept.name,
            bolum_grubu: dept.group,
            gpa: gpa,
            staj_ay: internship
        },
        model: {
            mu: parseFloat(mu.toFixed(6)),
            sigma: noiseSigma,
            beklenen_sure_ay: finalExpectedTime,
            ci_alt_ay: parseFloat(ciLower.toFixed(2)),
            ci_ust_ay: parseFloat(ciUpper.toFixed(2))
        },
        kumulatif_ihtimal: timeLabels.map((label, i) => ({
            ay: i + 1,
            etiket: label,
            kumulatif_ihtimal_yuzde: probData[i]
        }))
    };

    if (chartProbCurve) {
        chartProbCurve.data.labels = timeLabels;
        chartProbCurve.data.datasets[0].data = probData;
        chartProbCurve.update();
    }
}

// Grafik Oluşturma
function initializeChart() {
    const ctxProb = document.getElementById('chart-individual-prob').getContext('2d');
    
    // Light-theme professional Chart configuration
    chartProbCurve = new Chart(ctxProb, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Kümülatif İşe Yerleşme İhtimali (%)',
                data: [],
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.06)',
                borderWidth: 3,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#4f46e5',
                pointHoverBackgroundColor: '#4f46e5',
                pointHoverRadius: 6,
                pointRadius: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0f172a',
                    titleFont: { family: 'Plus Jakarta Sans', size: 12, weight: 'bold' },
                    bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
                    padding: 10,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) { return ` İşe Yerleşme İhtimali: %${context.parsed.y}`; }
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: '#f1f5f9' },
                    ticks: { 
                        color: '#64748b', 
                        font: { family: 'Plus Jakarta Sans', size: 11 },
                        callback: value => '%' + value 
                    }
                },
                x: {
                    grid: { color: '#f1f5f9' },
                    ticks: { 
                        color: '#64748b',
                        font: { family: 'Plus Jakarta Sans', size: 11 }
                    }
                }
            }
        }
    });
}

// Başlangıç Kurulumları
document.addEventListener('DOMContentLoaded', () => {
    // Grafik Başlat
    initializeChart();

    // Bölüm Seçim Dropdown'ını Doldur
    const calcDeptSelect = document.getElementById('calc-dept');
    DEPARTMENTS.forEach(dept => {
        const opt = document.createElement('option');
        opt.value = dept.id;
        opt.text = `${dept.name} (${dept.group})`;
        calcDeptSelect.appendChild(opt);
    });

    // İlk Hesaplamayı Çalıştır
    updatePrediction();

    // --- EVENT LISTENERS ---
    
    // Değer değişimlerini dinle
    document.getElementById('calc-dept').addEventListener('change', updatePrediction);
    
    document.getElementById('calc-gpa').addEventListener('input', (e) => {
        document.getElementById('calc-gpa-val').innerText = parseFloat(e.target.value).toFixed(2);
        updatePrediction();
    });

    document.getElementById('calc-internship').addEventListener('input', (e) => {
        document.getElementById('calc-internship-val').innerText = e.target.value + ' Ay';
        updatePrediction();
    });

    // Akademik Detaylar Collapsible Panel Aç/Kapat
    const refToggleBtn = document.getElementById('ref-toggle-btn');
    const refContentPanel = document.getElementById('ref-content-panel');

    refToggleBtn.addEventListener('click', () => {
        refToggleBtn.classList.toggle('active');
        refContentPanel.classList.toggle('open');

        if (refContentPanel.classList.contains('open')) {
            refContentPanel.style.maxHeight = refContentPanel.scrollHeight + 'px';
        } else {
            refContentPanel.style.maxHeight = '0px';
        }
    });
});

// =============================================
// VERİ DIŞA AKTARIM FONKSİYONLARI
// =============================================

/**
 * Kümülatif olasılık verilerini CSV formatında indirir.
 * Sütunlar: Ay | Etiket | Kumulatif_Ihtimal_Yuzde
 * Ek satırlar: Kullanıcı girdileri ve model parametreleri
 */
function exportCSV() {
    if (!lastExportData) {
        alert('Henüz hesaplanmış veri yok. Lütfen önce parametreleri ayarlayın.');
        return;
    }

    const btn = document.getElementById('btn-export-csv');
    btn.classList.add('downloading');
    setTimeout(() => btn.classList.remove('downloading'), 400);

    const d = lastExportData;
    const lines = [];

    // ---- Başlık Bloğu ----
    lines.push('# İş Bulma Süresi Tahmincisi - Kümülatif Olasılık Verisi (CSV Dışa Aktarımı)');
    lines.push('# Oluşturulma Zamanı:,' + new Date().toLocaleString('tr-TR'));
    lines.push('');

    // ---- Girdi Parametreleri ----
    lines.push('## GİRDİ PARAMETRELERİ');
    lines.push('Bölüm,' + d.inputs.bolum);
    lines.push('Bölüm Grubu,' + d.inputs.bolum_grubu);
    lines.push('Not Ortalaması (GPA),' + d.inputs.gpa.toFixed(2));
    lines.push('Staj Tecrübesi (Ay),' + d.inputs.staj_ay);
    lines.push('');

    // ---- Model Çıktıları ----
    lines.push('## MODEL ÇIKTILARI (AFT Log-Normal)');
    lines.push('Beklenen İş Bulma Süresi (Ay),' + d.model.beklenen_sure_ay);
    lines.push('%95 Güven Aralığı Alt Sınır (Ay),' + d.model.ci_alt_ay);
    lines.push('%95 Güven Aralığı Üst Sınır (Ay),' + d.model.ci_ust_ay);
    lines.push('Log-Normal μ (mu) Parametresi,' + d.model.mu);
    lines.push('Log-Normal σ (sigma) Parametresi,' + d.model.sigma);
    lines.push('');

    // ---- Kümülatif Olasılık Tablosu ----
    lines.push('## KÜMÜLATİF İŞE YERLEŞİM İHTİMALİ TABLOSU');
    lines.push('Ay,Etiket,Kumulatif Ihtimal (%)');
    d.kumulatif_ihtimal.forEach(row => {
        lines.push(`${row.ay},${row.etiket},${row.kumulatif_ihtimal_yuzde}`);
    });

    // ---- BOM + İndirme ----
    const csvContent = '\uFEFF' + lines.join('\r\n'); // UTF-8 BOM (Excel uyumluluğu)
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const safeName = d.inputs.bolum.replace(/[^a-zA-Z0-9ığüşöçIĞÜŞÖÇ]/g, '_');
    const filename = `is_bulma_suresi_${safeName}_${Date.now()}.csv`;
    _triggerDownload(url, filename);
}

/**
 * Kümülatif olasılık verilerini JSON formatında indirir.
 * Girdi parametreleri, model çıktıları ve tam olasılık dizisini içerir.
 */
function exportJSON() {
    if (!lastExportData) {
        alert('Henüz hesaplanmış veri yok. Lütfen önce parametreleri ayarlayın.');
        return;
    }

    const btn = document.getElementById('btn-export-json');
    btn.classList.add('downloading');
    setTimeout(() => btn.classList.remove('downloading'), 400);

    const exportObj = {
        meta: {
            baslik: 'İş Bulma Süresi Tahmincisi – Kümülatif Olasılık Dışa Aktarımı',
            model: 'AFT Log-Normal Dağılım (Hızlandırılmış Başarısızlık Süresi)',
            kaynaklar: [
                'TÜİK Yükseköğretim İstihdam Göstergeleri (Temmuz 2025 Güncellemesi, 2024 yılı verisi)',
                'Baert et al. (ScienceDirect, 2021)',
                'NACE Job Outlook 2021'
            ],
            olusturulma: new Date().toISOString()
        },
        girdiler: lastExportData.inputs,
        model_ciktilari: lastExportData.model,
        kumulatif_ihtimal_serisi: lastExportData.kumulatif_ihtimal
    };

    const jsonContent = JSON.stringify(exportObj, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const safeName = lastExportData.inputs.bolum.replace(/[^a-zA-Z0-9ığüşöçIĞÜŞÖÇ]/g, '_');
    const filename = `is_bulma_suresi_${safeName}_${Date.now()}.json`;
    _triggerDownload(url, filename);
}

/**
 * Verilen URL'i gizli bir <a> etiketi ile tetikleyerek dosyayı indirir.
 * @param {string} url - Blob URL
 * @param {string} filename - İndirilecek dosya adı
 */
function _triggerDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 5000);
}
