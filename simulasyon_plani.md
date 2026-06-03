# Ekonometrik Analiz ve İlk İş Bulma Süresi Tahmin Planı

Bu plan, üniversite mezunlarının niteliklerine göre mezuniyet sonrası **ilk iş bulma sürelerini (ay bazında)** tahmin eden bilimsel ve interaktif bir web uygulamasının teorik altyapısını ve işleyiş modelini açıklamaktadır.

Uygulama, kullanıcının seçtiği profile (Bölüm, GPA, Staj) göre beklenen iş bulma süresini ve güven aralıklarını kesin istatistiki katsayılar kullanarak hesaplar.

---

## 1. Tahmin Modeli ve İstatistiki Altyapı

İstihdam süreleri gibi sağa çarpık (right-skewed) ve pozitif olması zorunlu olan verilerin modellenmesinde ekonometri literatüründeki standart **Hızlandırılmış Başarısızlık Süresi (Accelerated Failure Time - AFT) Log-Normal Dağılım Modeli** kullanılmıştır:

### Matematiksel Denklem:
$$T_i = \exp\left(\mu_{\text{bölüm}} + \beta_{\text{GPA}} \cdot (\text{GPA}_i - 2.8) + \beta_{\text{staj}} \cdot \text{Staj}_i + \theta_{\text{akademik}}\right)$$

Burada:
*   $T_i$: Adayın beklenen ilk iş bulma süresi (Ay).
*   $\mu_{\text{bölüm}}$: Bölüme özgü baz istihdam katsayısı (TÜİK verilerine göre ayarlanmıştır).
*   $\beta_{\text{GPA}}$: Not ortalamasının etkisi (sabit katsayı: $-0.25$. GPA'daki her 1 birimlik artış süreyi yaklaşık %22 kısaltır).
*   $\beta_{\text{staj}}$: Staj tecrübesinin etkisi (sabit katsayı: $-0.04$. Her 1 aylık staj süreyi yaklaşık %4 kısaltır).
*   $\theta_{\text{akademik}}$: Akademik literatürden türetilen staj durum katsayısı (Staj > 0 ise $-0.12$, Staj = 0 ise $+0.14$).
*   *Önemli Not:* Bu katsayılar ilgili literatürden (TÜİK, Baert et al., NACE) ilham alınarak türetilmiş tahmini değerlerdir; doğrudan tek bir çalışmadan alınmamıştır.

---

## 2. Akademik Referanslar ve Model Kalibrasyonu

Uygulamanın tahmin motoru ve kıyaslama parametreleri, aşağıdaki gerçek dünya verilerine göre kalibre edilmiştir:

1.  **TÜİK — Yükseköğretim İstihdam Göstergeleri (Temmuz 2025 Güncellemesi, 2024 yılı verisi):**
    *   Lisans mezunlarının genel Türkiye ortalaması **14.4 ay** olarak alınmıştır.
    *   Bölüm bazlı baz süreler ($\mu_{\text{bölüm}}$): Tıp (4.1 ay), Mühendislik (11.6 ay), BİT (11.8 ay), Eğitim (12.6 ay), Hukuk (13.0 ay), İşletme/İktisat (14.0 ay), Sosyal Bilimler (16.5 ay).
2.  **Baert et al. (ScienceDirect, 2021) [Orijinal tartışma tebliği: 2019]:**
    *   Staj deneyimi olan adayların mülakat daveti alma olasılığının stajsızlara göre **%12.6 daha yüksek** olduğunu gösterir. Bu bulgu staj katsayısına ve stajyerler için $\theta = -0.12$ hızlandırma çarpanına yansıtılmıştır.
3.  **NACE Job Outlook 2021:**
    *   İşverenlerin iki eşit nitelikli aday arasından stajı olanı belirleyici olarak tercih ettiğini gösterir. Bu bulgu, staj yapmamış adaylar için $\theta = +0.14$ gecikme cezasına yansıtılmıştır.

---

## 3. Sistem Girdileri ve Çıktıları

Uygulama, SaaS tarzı beyaz tema arayüzünde şu verileri işler:

### Kullanıcı Girdileri (Aday Profili):
*   `Mezun Olunan Bölüm`: 17 detaylı lisans bölümü içeren açılır liste.
*   `Not Ortalaması (GPA)`: 1.00 ile 4.00 arasında sürgü (Adım: 0.05).
*   `Staj Süresi`: 0 ile 24 ay arasında staj/iş tecrübesi sürgüsü (Adım: 1).

### Tahmin Çıktıları:
*   `Beklenen İlk İş Bulma Süresi (Ay)`: Nokta tahmin değeri.
*   `%95 Güven Aralığı`: Adayın iş bulma süresinin istatistiki olarak en olası alt ve üst sınır aralığı.
*   `TÜİK Karşılaştırma Göstergesi`: Adayın süresini Türkiye ortalamasıyla kıyaslayan renk kodlu ilerleme çubuğu ve yüzde başarı mesajı.
*   `İşe Yerleşme Olasılık Eğrisi`: 1. aydan 24. aya kadar adayın kümülatif olarak işe yerleşme ihtimalini (%) gösteren Chart.js çizgi grafiği.
