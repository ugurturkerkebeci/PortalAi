# Portal AI - Sesli Asistan HUD 🤖🎙️

Portal, tarayıcı tabanlı konuşma tanıma (Speech-to-Text) ve metin okuma (Text-to-Speech) teknolojilerini kullanarak çalışan, fütüristik bir arayüze (HUD) sahip yapay zeka asistanıdır. Gücünü Python, yerleşik HTTP sunucusu ve `g4f` kütüphanesi üzerinden sağlanan GPT-4 modelinden alır.

Geliştirici: [@ugurturkerkebeci](https://github.com/ugurturkerkebeci)

## Özellikler

* **Sesli Etkileşim:** Tarayıcının Web Speech API'sini kullanarak ortam dinlemesi yapar ve Türkçe yanıtları sesli olarak okur.
* **Cyberpunk HUD Arayüzü:** Animasyonlu orb, scan-line efektleri ve reaktif durum göstergeleri ile şık bir deneyim sunar.
* **Uyku/Uyanıklık Modu:** Özel sesli komutlarla asistanı dinleme moduna alabilir veya tamamen sağırlaştırabilirsiniz.
* **Gerçek Zamanlı Veri:** Open-Meteo API kullanılarak entegre edilmiş anlık hava durumu ve sistem saati takibi.
* **Ücretsiz LLM Entegrasyonu:** `g4f` (GPT4Free) kütüphanesinin Yqcloud sağlayıcısı üzerinden GPT-4 tabanlı doğal dil işleme.

## Teknoloji Yığını

* **Backend:** Python 3, `http.server`, `g4f`
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
* **API'ler:** Web Speech API (STT & TTS), Open-Meteo (Hava Durumu)

## Kurulum

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1. Depoyu bilgisayarınıza klonlayın.
2. Gerekli Python kütüphanesini yükleyin:
   `pip install g4f`
3. Proje dizininde terminali açıp scripti çalıştırın:
   `python transcribe.py`
4. Tarayıcınız otomatik olarak `http://localhost:5000` adresinde açılacaktır. (Mikrofon izni vermeyi unutmayın).

## Sesli Komutlar

Sistemi yönetmek için aşağıdaki anahtar kelimeleri kullanabilirsiniz:

| İşlem | Komutlar | Açıklama |
| :--- | :--- | :--- |
| **Uyandır** | `portal`, `portel`, `portalım`, `hey portal` | Asistanı uyku modundan çıkarır ve dinlemeye başlar. |
| **Uyut (Sağır Mod)** | `sağırlaş`, `sağırlas`, `sağır ol`, `sus portal` | Asistanı dinlemeyi bırakmaya zorlar. Sadece uyandırma komutuna tepki verir. |
| **Manuel Tetikleme** | *Arayüzdeki animasyonlu küreye tıklamak* | Uyku ve aktif dinleme modları arasında manuel geçiş yapar. |

## Notlar ve Uyarılar

* **Tarayıcı Uyumluluğu:** Konuşma tanıma (SpeechRecognition) özelliği en kararlı şekilde Google Chrome ve Chromium tabanlı tarayıcılarda çalışmaktadır.
* **Hava Durumu Konumu:** Mevcut sürümde hava durumu verisi Safranbolu/Karabük koordinatlarına göre sabitlenmiştir. İhtiyaca göre `transcribe.py` içindeki HTML şablonundan enlem ve boylam ayarlanabilir.
* **API Limitleri:** Proje `g4f` üzerinden Yqcloud sağlayıcısını kullandığı için zaman zaman bağlantı gecikmeleri veya sağlayıcı kaynaklı hatalar yaşanabilir. Sistem bu durumlarda otomatik yeniden deneme (retry) mekanizmasına sahiptir.

## Lisans

Bu proje kişisel kullanım ve geliştirme amacıyla açık kaynak olarak paylaşılmıştır.
