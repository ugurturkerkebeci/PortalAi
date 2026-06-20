import http.server
import socketserver
import webbrowser
import json
import sys
import time
import g4f
from g4f.client import Client

if sys.platform.startswith('win'):
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)
    kernel32.SetConsoleOutputCP(65001)

PORT        = 5000
WAKE_WORD   = "portal"
SLEEP_CMD   = "sağırlaş"   # Bu komutu duyunca uyku moduna geç
MAX_RETRIES = 3
RETRY_DELAY = 1.0

PERSONA_PREFIX = (
    "Sen 'Portal' adında bir yapay zeka asistanısın. "
    "Sadece Türkçe konuş. Emoji kullanma. Kısa ve doğal cevap ver.\n\n"
    "Kullanıcı sorusu: "
)

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Portal AI</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --c-bg:#020a12;
  --c-cyan:#00e5ff;
  --c-blue:#4facfe;
  --c-purple:#9b51e0;
  --c-green:#00ff88;
  --c-dim:#0a1825;
  --c-line:rgba(0,229,255,0.08);
  --c-text:#7ab8cc;
}

body{
  font-family:'Share Tech Mono',monospace;
  background:var(--c-bg);
  color:var(--c-text);
  min-height:100vh;
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  overflow:hidden;
  position:relative;
}

/* ── scan lines ── */
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:repeating-linear-gradient(0deg,
    transparent,transparent 2px,
    rgba(0,229,255,0.012) 2px,rgba(0,229,255,0.012) 4px);
}

/* ── grid ── */
body::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    linear-gradient(var(--c-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--c-line) 1px, transparent 1px);
  background-size:60px 60px;
}

/* ── corner brackets ── */
.corner{position:fixed;width:60px;height:60px;z-index:2;}
.corner svg{width:100%;height:100%}
.corner.tl{top:16px;left:16px}
.corner.tr{top:16px;right:16px;transform:scaleX(-1)}
.corner.bl{bottom:16px;left:16px;transform:scaleY(-1)}
.corner.br{bottom:16px;right:16px;transform:scale(-1)}

/* ── BAŞLAT EKRANI ── */
#start-screen{
  position:fixed;inset:0;background:var(--c-bg);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:32px;z-index:100;
}
#start-screen h2{
  font-family:'Share Tech Mono',monospace;
  font-size:2.5em;letter-spacing:10px;text-transform:uppercase;
  color:var(--c-cyan);text-shadow:0 0 30px var(--c-cyan);
}
#start-screen p{color:#334455;font-size:0.85em;letter-spacing:2px;text-align:center}
#start-btn{
  background:transparent;border:1px solid var(--c-cyan);
  color:var(--c-cyan);padding:14px 52px;
  font-family:'Share Tech Mono',monospace;font-size:1em;letter-spacing:4px;
  cursor:pointer;text-transform:uppercase;
  transition:all 0.3s;
  box-shadow:0 0 20px rgba(0,229,255,0.2), inset 0 0 20px rgba(0,229,255,0.03);
}
#start-btn:hover{
  background:rgba(0,229,255,0.08);
  box-shadow:0 0 40px rgba(0,229,255,0.4), inset 0 0 20px rgba(0,229,255,0.08);
}

/* ── ANA LAYOUT ── */
.hud{
  position:relative;z-index:1;
  display:grid;
  grid-template-columns:220px 1fr 220px;
  grid-template-rows:auto 1fr auto;
  gap:16px;
  width:min(1000px,96vw);
  min-height:min(640px,92vh);
  padding:12px;
}

/* ── PANEL ── */
.panel{
  background:rgba(0,15,30,0.7);
  border:1px solid rgba(0,229,255,0.1);
  border-radius:4px;
  padding:14px;
  backdrop-filter:blur(4px);
  position:relative;
  overflow:hidden;
}
.panel::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--c-cyan),transparent);
  opacity:0.4;
}
.panel-title{
  font-size:0.62em;letter-spacing:3px;color:rgba(0,229,255,0.5);
  text-transform:uppercase;margin-bottom:12px;border-bottom:1px solid rgba(0,229,255,0.07);
  padding-bottom:6px;
}

/* ── SAAT ── */
#clock{
  font-size:2.4em;letter-spacing:4px;color:var(--c-cyan);
  text-shadow:0 0 20px rgba(0,229,255,0.5);
  text-align:center;margin-bottom:4px;
}
#date-str{font-size:0.7em;letter-spacing:2px;color:#334d5c;text-align:center}

/* ── HAVA DURUMU ── */
#weather-temp{font-size:2em;color:var(--c-cyan);text-shadow:0 0 16px rgba(0,229,255,0.4);text-align:center;margin:8px 0 4px}
#weather-desc{font-size:0.68em;letter-spacing:2px;color:#334d5c;text-align:center;text-transform:uppercase}
#weather-detail{font-size:0.65em;color:#223344;margin-top:8px;text-align:center;line-height:1.8}
.weather-loc{font-size:0.62em;letter-spacing:3px;color:rgba(0,229,255,0.35);text-align:center;margin-top:6px}

/* ── ORTA SÜTUN ── */
.center-col{
  grid-column:2;grid-row:1/4;
  display:flex;flex-direction:column;align-items:center;gap:14px;
  padding:8px 0;
}

/* ── ORB ── */
.orb-area{
  position:relative;width:220px;height:220px;
  cursor:pointer;flex-shrink:0;
}
/* dönen yaylar */
.arc{
  position:absolute;border-radius:50%;border:1.5px solid transparent;
}
.arc1{
  inset:0;border-top-color:rgba(0,229,255,0.6);border-right-color:rgba(0,229,255,0.2);
  animation:spin1 4s linear infinite;
  transition:border-color 0.5s;
}
.arc2{
  inset:12px;border-bottom-color:rgba(79,172,254,0.5);border-left-color:rgba(79,172,254,0.15);
  animation:spin2 6s linear infinite;
  transition:border-color 0.5s;
}
.arc3{
  inset:24px;border-top-color:rgba(155,81,224,0.3);
  animation:spin1 9s linear infinite reverse;
  transition:border-color 0.5s;
}
@keyframes spin1{to{transform:rotate(360deg)}}
@keyframes spin2{to{transform:rotate(-360deg)}}

body.state-wake     .arc1{border-top-color:rgba(0,229,255,1);animation-duration:2s}
body.state-wake     .arc2{border-bottom-color:rgba(79,172,254,0.9);animation-duration:3s}
body.state-thinking .arc1{border-top-color:rgba(155,81,224,0.9);animation-duration:1.5s}
body.state-thinking .arc2{border-bottom-color:rgba(155,81,224,0.6);animation-duration:2.5s}
body.state-speaking .arc1{border-top-color:rgba(0,255,136,0.9);animation-duration:1s}
body.state-speaking .arc2{border-bottom-color:rgba(0,255,136,0.6);animation-duration:1.8s}

.orb-core{
  position:absolute;inset:36px;border-radius:50%;
  background:radial-gradient(circle at 38% 36%, #0d2035, #020a12);
  box-shadow:0 0 30px rgba(0,229,255,0.1),inset 0 0 30px rgba(0,0,0,0.8);
  display:flex;align-items:center;justify-content:center;
  transition:box-shadow 0.6s;
}
body.state-wake .orb-core{
  box-shadow:0 0 60px rgba(0,229,255,0.6),0 0 100px rgba(0,229,255,0.15),inset 0 0 20px rgba(0,229,255,0.05);
}
body.state-thinking .orb-core{
  box-shadow:0 0 60px rgba(155,81,224,0.6),0 0 100px rgba(155,81,224,0.15),inset 0 0 20px rgba(155,81,224,0.05);
  animation:core-pulse 1.1s ease-in-out infinite;
}
body.state-speaking .orb-core{
  box-shadow:0 0 60px rgba(0,255,136,0.6),0 0 100px rgba(0,255,136,0.15),inset 0 0 20px rgba(0,255,136,0.05);
  animation:core-pulse 0.5s ease-in-out infinite;
}
@keyframes core-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}

.orb-icon{font-size:40px;user-select:none;transition:opacity 0.3s}

/* ── BAŞLIK ── */
.portal-title{
  font-family:'Share Tech Mono',monospace;
  font-size:2.2em;letter-spacing:8px;text-transform:uppercase;
  color:var(--c-cyan);text-shadow:0 0 20px rgba(0,229,255,0.5);
  text-align:center;
}
#status{
  font-size:0.72em;letter-spacing:3px;text-transform:uppercase;
  color:#1e3344;transition:color 0.4s;text-align:center;min-height:16px;
}
body.state-wake     #status{color:var(--c-cyan);text-shadow:0 0 8px rgba(0,229,255,0.4)}
body.state-thinking #status{color:var(--c-purple);text-shadow:0 0 8px rgba(155,81,224,0.4)}
body.state-speaking #status{color:var(--c-green);text-shadow:0 0 8px rgba(0,255,136,0.4)}

/* ── CHAT ── */
#chat-box{
  width:100%;flex:1;min-height:0;
  background:rgba(0,5,12,0.6);
  border:1px solid rgba(0,229,255,0.07);
  border-radius:4px;padding:12px;
  overflow-y:auto;
  display:flex;flex-direction:column;gap:10px;
  font-family:'Share Tech Mono',monospace;
}
.msg{
  padding:8px 12px;border-radius:2px;max-width:90%;
  font-size:0.82em;line-height:1.6;word-wrap:break-word;
  animation:fadeUp 0.22s ease forwards;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
.msg.user{
  align-self:flex-end;
  background:rgba(0,229,255,0.06);
  color:var(--c-cyan);border:1px solid rgba(0,229,255,0.2);
  border-right:3px solid var(--c-cyan);
}
.msg.user::before{content:'> ';color:rgba(0,229,255,0.5)}
.msg.ai{
  align-self:flex-start;
  background:rgba(155,81,224,0.05);
  color:#8899aa;border:1px solid rgba(155,81,224,0.12);
  border-left:3px solid rgba(155,81,224,0.5);
}
.msg.ai::before{content:'PORTAL: ';color:rgba(155,81,224,0.6);font-size:0.85em}
.msg.system{align-self:center;background:transparent;color:#1e3344;font-size:0.75em;font-style:italic}
.msg.thinking{
  align-self:flex-start;background:rgba(155,81,224,0.06);
  color:rgba(155,81,224,0.6);border:1px solid rgba(155,81,224,0.1);
  border-left:3px solid rgba(155,81,224,0.3);font-style:italic;font-size:0.8em;
}

/* ── SES SEÇİCİ ── */
.voice-row{display:flex;align-items:center;gap:8px;width:100%}
.voice-row label{font-size:0.65em;color:#1e3344;letter-spacing:2px;white-space:nowrap;text-transform:uppercase}
#voice-select{
  flex:1;background:rgba(0,229,255,0.03);border:1px solid rgba(0,229,255,0.1);
  color:#3d6070;padding:6px 10px;border-radius:2px;outline:none;font-size:0.75em;
  font-family:'Share Tech Mono',monospace;cursor:pointer;
}
#voice-select option{background:#020a12}

/* ── TEXT INPUT ── */
.input-row{display:flex;gap:8px;width:100%}
#text-input{
  flex:1;background:rgba(0,229,255,0.03);border:1px solid rgba(0,229,255,0.1);
  color:var(--c-cyan);padding:9px 12px;border-radius:2px;
  outline:none;font-size:0.82em;font-family:'Share Tech Mono',monospace;
  transition:border-color 0.2s;
}
#text-input::placeholder{color:#0d1e2a}
#text-input:focus{border-color:rgba(0,229,255,0.4);box-shadow:0 0 12px rgba(0,229,255,0.08)}
#send-btn{
  background:transparent;border:1px solid rgba(0,229,255,0.3);color:var(--c-cyan);
  padding:9px 16px;border-radius:2px;font-family:'Share Tech Mono',monospace;
  font-size:0.8em;letter-spacing:2px;cursor:pointer;white-space:nowrap;
  transition:all 0.2s;text-transform:uppercase;
}
#send-btn:hover{background:rgba(0,229,255,0.08);box-shadow:0 0 16px rgba(0,229,255,0.2)}

/* ── SOL / SAĞ PANEL İÇİ ── */
.stat-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid rgba(0,229,255,0.05)}
.stat-row:last-child{border-bottom:none}
.stat-label{font-size:0.62em;letter-spacing:2px;color:#1e3344;text-transform:uppercase}
.stat-val{font-size:0.75em;color:rgba(0,229,255,0.55);letter-spacing:1px}

.bar-wrap{height:3px;background:rgba(0,229,255,0.06);border-radius:2px;margin-top:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:2px;background:linear-gradient(90deg,rgba(0,229,255,0.3),rgba(0,229,255,0.7));width:0%;transition:width 1s ease}

/* ── SAĞIR MODU BADGE ── */
#deaf-badge{
  display:none;position:fixed;top:20px;left:50%;transform:translateX(-50%);
  background:rgba(155,81,224,0.15);border:1px solid rgba(155,81,224,0.4);
  color:rgba(155,81,224,0.9);padding:6px 20px;border-radius:2px;
  font-size:0.7em;letter-spacing:3px;text-transform:uppercase;z-index:50;
}

/* scrollbar */
#chat-box::-webkit-scrollbar{width:3px}
#chat-box::-webkit-scrollbar-track{background:transparent}
#chat-box::-webkit-scrollbar-thumb{background:rgba(0,229,255,0.1);border-radius:2px}
</style>
</head>

<body class="state-sleep">

<!-- Köşe süslemeleri -->
<div class="corner tl"><svg viewBox="0 0 60 60"><path d="M0 60 L0 0 L60 0" fill="none" stroke="rgba(0,229,255,0.35)" stroke-width="1.5"/><path d="M0 45 L0 0 L45 0" fill="none" stroke="rgba(0,229,255,0.15)" stroke-width="1"/></svg></div>
<div class="corner tr"><svg viewBox="0 0 60 60"><path d="M0 60 L0 0 L60 0" fill="none" stroke="rgba(0,229,255,0.35)" stroke-width="1.5"/><path d="M0 45 L0 0 L45 0" fill="none" stroke="rgba(0,229,255,0.15)" stroke-width="1"/></svg></div>
<div class="corner bl"><svg viewBox="0 0 60 60"><path d="M0 60 L0 0 L60 0" fill="none" stroke="rgba(0,229,255,0.35)" stroke-width="1.5"/><path d="M0 45 L0 0 L45 0" fill="none" stroke="rgba(0,229,255,0.15)" stroke-width="1"/></svg></div>
<div class="corner br"><svg viewBox="0 0 60 60"><path d="M0 60 L0 0 L60 0" fill="none" stroke="rgba(0,229,255,0.35)" stroke-width="1.5"/><path d="M0 45 L0 0 L45 0" fill="none" stroke="rgba(0,229,255,0.15)" stroke-width="1"/></svg></div>

<!-- Sağır modu badge -->
<div id="deaf-badge">SAĞIR MOD — "Portal" ile uyandır</div>

<!-- Başlat Ekranı -->
<div id="start-screen">
  <h2>Portal</h2>
  <p>Yapay Zeka Asistan Sistemi<br><br>Mikrofon ve ses izni gerekiyor.</p>
  <button id="start-btn" onclick="initPortal()">Sistemi Başlat</button>
</div>

<!-- HUD -->
<div class="hud" id="hud">

  <!-- SOL PANEL: SAAT + Komutlar -->
  <div style="grid-column:1;grid-row:1/3;display:flex;flex-direction:column;gap:12px">
    <div class="panel">
      <div class="panel-title">Sistem Saati</div>
      <div id="clock">00:00:00</div>
      <div id="date-str">---</div>
    </div>
    <div class="panel" style="flex:1">
      <div class="panel-title">Sesli Komutlar</div>
      <div class="stat-row"><span class="stat-label">Uyandır</span><span class="stat-val">"Portal"</span></div>
      <div class="stat-row"><span class="stat-label">Kapat</span><span class="stat-val">"Sağırlaş"</span></div>
      <div class="stat-row"><span class="stat-label">Manuel</span><span class="stat-val">Orba tıkla</span></div>
      <div style="margin-top:14px">
        <div class="panel-title">Dinleme Durumu</div>
        <div class="stat-row"><span class="stat-label">Mod</span><span class="stat-val" id="listen-mode-label">Uyku</span></div>
        <div class="stat-row"><span class="stat-label">Sağlayıcı</span><span class="stat-val">Yqcloud</span></div>
      </div>
    </div>
  </div>

  <!-- ORTA: ORB + Chat -->
  <div class="center-col">
    <div class="orb-area" onclick="orbClick()" title="Tıkla: uyandır/kapat">
      <div class="arc arc1"></div>
      <div class="arc arc2"></div>
      <div class="arc arc3"></div>
      <div class="orb-core"><span class="orb-icon" id="orb-icon">💤</span></div>
    </div>

    <div class="portal-title">Portal</div>
    <div id="status">Sistem Bekleniyor</div>

    <div id="chat-box" style="width:100%;flex:1">
      <div class="msg system">Sistem aktif. "Portal" diyerek başlayın.</div>
    </div>

    <div class="voice-row">
      <label>Ses</label>
      <select id="voice-select"><option value="">Varsayılan</option></select>
    </div>

    <div class="input-row">
      <input type="text" id="text-input" placeholder="Komut girin..." autocomplete="off"
             onkeydown="if(event.key==='Enter') sendText()">
      <button id="send-btn" onclick="sendText()">Gönder</button>
    </div>
  </div>

  <!-- SAĞ PANEL: HAVA DURUMU -->
  <div style="grid-column:3;grid-row:1/3;display:flex;flex-direction:column;gap:12px">
    <div class="panel">
      <div class="panel-title">Hava — Safranbolu</div>
      <div id="weather-temp">--°C</div>
      <div id="weather-desc">Yükleniyor...</div>
      <div id="weather-detail"></div>
      <div class="weather-loc">KARABÜK / TÜRKİYE</div>
    </div>
    <div class="panel" style="flex:1">
      <div class="panel-title">Konum Bilgisi</div>
      <div class="stat-row"><span class="stat-label">Şehir</span><span class="stat-val">Karabük</span></div>
      <div class="stat-row"><span class="stat-label">İlçe</span><span class="stat-val">Safranbolu</span></div>
      <div class="stat-row"><span class="stat-label">Enlem</span><span class="stat-val">41.25°N</span></div>
      <div class="stat-row"><span class="stat-label">Boylam</span><span class="stat-val">32.69°E</span></div>
      <div style="margin-top:14px">
        <div class="panel-title">Sistem Metrikleri</div>
        <div class="stat-row"><span class="stat-label">Motor</span><span class="stat-val">GPT-4</span></div>
        <div class="stat-row"><span class="stat-label">STT</span><span class="stat-val">Web API</span></div>
        <div class="stat-row"><span class="stat-label">TTS</span><span class="stat-val">Ahmet</span></div>
      </div>
    </div>
  </div>

</div><!-- /hud -->

<script>
/* ═══════════════ PORTAL AI — HUD ═══════════════ */
const WAKE_WORDS  = ['portal','portel','portalım','hey portal'];
const SLEEP_WORDS = ['sağırlaş','sağırlas','sağır ol','sus portal'];
const WAKE_REPLY  = 'Dinliyorum efendim!';
const SLEEP_REPLY = 'Anlıyorum, sizi dinlemeyeceğim.';

let appState    = 'sleep';
let isBusy      = false;
let isDeaf      = true;     // başlangıçta uyku: true = sadece wake word bekle
let listenMode  = 'wake';
let recognition = null;
let trVoices    = [];
let thinkEl     = null;
let started     = false;

const body       = document.body;
const statusDiv  = document.getElementById('status');
const chatBox    = document.getElementById('chat-box');
const voiceSel   = document.getElementById('voice-select');
const textInput  = document.getElementById('text-input');
const orbIcon    = document.getElementById('orb-icon');
const deafBadge  = document.getElementById('deaf-badge');
const listenLbl  = document.getElementById('listen-mode-label');

const STATES = {
  sleep:    {icon:'💤', label:'Beklemede — "Portal" deyin'},
  wake:     {icon:'🎤', label:'Dinliyorum...'},
  thinking: {icon:'⏳', label:'İşleniyor...'},
  speaking: {icon:'📢', label:'Yanıt veriliyor...'},
};
function setState(s){
  appState = s;
  body.className = 'state-'+s;
  orbIcon.textContent   = STATES[s]?.icon  ?? '💤';
  statusDiv.textContent = STATES[s]?.label ?? '';
  listenLbl.textContent = isDeaf
    ? (s==='sleep'?'Sağır Mod':'Aktif')
    : {sleep:'Uyku',wake:'Aktif',thinking:'İşleniyor',speaking:'Konuşuyor'}[s]??'--';
}

/* ── SAAT ── */
const DAYS=['Pazar','Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi'];
const MONTHS=['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
function tickClock(){
  const n=new Date();
  const hh=String(n.getHours()).padStart(2,'0');
  const mm=String(n.getMinutes()).padStart(2,'0');
  const ss=String(n.getSeconds()).padStart(2,'0');
  document.getElementById('clock').textContent=`${hh}:${mm}:${ss}`;
  document.getElementById('date-str').textContent=
    `${DAYS[n.getDay()]} ${n.getDate()} ${MONTHS[n.getMonth()]} ${n.getFullYear()}`;
}
setInterval(tickClock,1000); tickClock();

/* ── HAVA DURUMU (Open-Meteo, ücretsiz, key yok) ── */
const WMO_CODES = {
  0:'Açık',1:'Az Bulutlu',2:'Parçalı Bulutlu',3:'Bulutlu',
  45:'Sisli',48:'Dondurucu Sis',
  51:'Hafif Çisenti',53:'Orta Çisenti',55:'Yoğun Çisenti',
  61:'Hafif Yağmur',63:'Orta Yağmur',65:'Kuvvetli Yağmur',
  71:'Hafif Kar',73:'Orta Kar',75:'Yoğun Kar',
  80:'Sağanak',81:'Kuvvetli Sağanak',82:'Şiddetli Sağanak',
  95:'Fırtına',96:'Dolu İle Fırtına',
};
function fetchWeather(){
  fetch('https://api.open-meteo.com/v1/forecast?latitude=41.25&longitude=32.69&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m&timezone=Europe%2FIstanbul')
  .then(r=>r.json())
  .then(d=>{
    const c=d.current;
    document.getElementById('weather-temp').textContent = `${Math.round(c.temperature_2m)}°C`;
    document.getElementById('weather-desc').textContent = WMO_CODES[c.weather_code]??'Bilinmiyor';
    document.getElementById('weather-detail').innerHTML =
      `Hissedilen: ${Math.round(c.apparent_temperature)}°C<br>`+
      `Nem: %${c.relative_humidity_2m}<br>`+
      `Rüzgar: ${Math.round(c.wind_speed_10m)} km/s`;
  })
  .catch(()=>{ document.getElementById('weather-desc').textContent='Bağlanılamadı'; });
}
fetchWeather();
setInterval(fetchWeather, 10*60*1000);

/* ── SES LİSTESİ ── */
function loadVoices(){
  if(!('speechSynthesis' in window))return;
  trVoices=window.speechSynthesis.getVoices().filter(v=>v.lang.toLowerCase().startsWith('tr'));
  voiceSel.innerHTML='<option value="">Varsayılan</option>';
  trVoices.forEach((v,i)=>{
    const o=document.createElement('option');
    o.value=i; o.textContent=v.name+(!v.localService?' ✨':'');
    if(v.name.toLowerCase().includes('ahmet'))o.selected=true;
    voiceSel.appendChild(o);
  });
}
if('speechSynthesis' in window){window.speechSynthesis.onvoiceschanged=loadVoices;loadVoices();}

/* ── TTS ── */
function speak(text, onEnd){
  if(!('speechSynthesis' in window)){onEnd?.();return;}
  window.speechSynthesis.cancel();
  const clean = text
    .replace(/[*#_`~>]/g,'')
    .replace(/[\u{1F000}-\u{1FFFF}]/gu,'')
    .replace(/[\u{2600}-\u{27BF}]/gu,'')
    .replace(/[\u{1F300}-\u{1F9FF}]/gu,'')
    .replace(/[\u{FE00}-\u{FEFF}]/gu,'')
    .replace(/\s{2,}/g,' ').trim();
  if(!clean){onEnd?.();return;}

  const utt=new SpeechSynthesisUtterance(clean);
  utt.lang='tr-TR';
  const idx=voiceSel.value;
  if(idx!==''&&trVoices[idx]) utt.voice=trVoices[idx];
  else { const a=trVoices.find(v=>v.name.toLowerCase().includes('ahmet')); if(a)utt.voice=a; }

  let fired=false;
  const done=()=>{if(!fired){fired=true;onEnd?.();}};
  utt.onend=done; utt.onerror=done;
  setTimeout(done, 30000);

  setState('speaking');
  window.speechSynthesis.speak(utt);
}
function stopSpeaking(){window.speechSynthesis?.cancel();}

/* ── CHAT ── */
function appendMsg(cls,text){
  document.querySelectorAll('.msg.system').forEach(m=>m.remove());
  const d=document.createElement('div');
  d.className='msg '+cls; d.textContent=text;
  chatBox.appendChild(d); chatBox.scrollTop=chatBox.scrollHeight;
  return d;
}

/* ── AI İSTEĞİ ── */
function askAI(userText){
  if(isBusy)return;
  isBusy=true; stopSpeaking();
  try{recognition?.stop();}catch(e){}
  appendMsg('user',userText);
  thinkEl=appendMsg('thinking','Portal işliyor...');
  setState('thinking');

  fetch('/transcribe',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:userText})
  })
  .then(r=>r.json())
  .then(data=>{
    thinkEl?.remove(); thinkEl=null;
    if(data.response){
      appendMsg('ai',data.response);
      speak(data.response,()=>{
        isBusy=false;
        // Sağır değilse (isDeaf=false) → otomatik tekrar dinle (wake word beklemeden)
        if(!isDeaf){
          setState('wake');
          listenMode='query';
          setTimeout(tryStartListen, 700);
        } else {
          setState('sleep');
          listenMode='wake';
          tryStartListen();
        }
      });
    } else {
      isBusy=false; setState('sleep'); listenMode='wake'; tryStartListen();
    }
  })
  .catch(()=>{
    thinkEl?.remove(); thinkEl=null;
    isBusy=false; setState('sleep'); listenMode='wake'; tryStartListen();
  });
}

/* ── SES TANIMA ── */
function buildRecognition(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR)return null;
  const r=new SR();
  r.continuous=false; r.interimResults=false; r.lang='tr-TR';

  r.onresult=(e)=>{
    let text='';
    for(let i=e.resultIndex;i<e.results.length;i++)
      if(e.results[i].isFinal)text+=e.results[i][0].transcript;
    text=text.toLowerCase().trim();
    console.log('[Portal] duyulan:',text,'| mod:',listenMode,'| deaf:',isDeaf);

    // ── SAĞIRLAŞ komutu her modda çalışır ──
    if(SLEEP_WORDS.some(w=>text.includes(w))){
      isDeaf=true; listenMode='wake';
      try{recognition.stop();}catch(ex){}
      speak(SLEEP_REPLY,()=>{
        setState('sleep');
        deafBadge.style.display='block';
        listenMode='wake';
        setTimeout(tryStartListen,700);
      });
      return;
    }

    if(listenMode==='wake'){
      const woke=WAKE_WORDS.some(w=>text.includes(w));
      if(woke){
        isDeaf=false;
        deafBadge.style.display='none';
        setState('wake');
        try{recognition.stop();}catch(ex){}
        speak(WAKE_REPLY,()=>{
          listenMode='query';
          setState('wake');
          setTimeout(tryStartListen,700);
        });
      } else {
        tryStartListen();
      }
    } else {
      // query modu
      if(text.length>1){
        askAI(text);
      } else {
        tryStartListen();
      }
    }
  };

  r.onend=()=>{ if(!isBusy&&!window.speechSynthesis?.speaking) tryStartListen(); };
  r.onerror=(e)=>{ if(!isBusy) setTimeout(tryStartListen,600); };
  return r;
}

function tryStartListen(){
  if(!recognition||isBusy)return;
  if(window.speechSynthesis?.speaking)return;
  try{recognition.start();}catch(e){}
}

/* ── ORB CLICK ── */
function orbClick(){
  if(!started)return;
  stopSpeaking();
  if(isBusy)return;
  if(appState==='sleep'||isDeaf){
    isDeaf=false; deafBadge.style.display='none';
    setState('wake'); listenMode='query';
    try{recognition?.stop();}catch(e){}
    setTimeout(tryStartListen,250);
  } else if(appState==='wake'){
    isDeaf=true; deafBadge.style.display='block';
    setState('sleep'); listenMode='wake';
  }
}

/* ── YAZILI GİRİŞ ── */
function sendText(){
  const msg=textInput.value.trim();
  if(!msg||isBusy)return;
  textInput.value='';
  isDeaf=false; deafBadge.style.display='none';
  askAI(msg);
}

/* ── BAŞLAT ── */
function initPortal(){
  document.getElementById('start-screen').style.display='none';
  started=true;
  loadVoices(); setTimeout(loadVoices,500);
  recognition=buildRecognition();
  if(recognition){
    setState('sleep'); listenMode='wake';
    deafBadge.style.display='block';
    tryStartListen();
  } else {
    statusDiv.textContent='Tarayıcı mikrofonu desteklemiyor!';
  }
}
</script>
</body>
</html>"""

# ── Python backend ─────────────────────────────────────────────────────────

_g4f_client = None

def get_client():
    global _g4f_client
    if _g4f_client is None:
        _g4f_client = Client()
    return _g4f_client


def get_ai_response(user_text):
    delay = RETRY_DELAY
    full_prompt = PERSONA_PREFIX + user_text

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            label = f"({attempt}/{MAX_RETRIES})" if attempt > 1 else ""
            print(f"[Sistem]: Yqcloud istek {label}...", flush=True)
            response = get_client().chat.completions.create(
                model="gpt-4",
                provider=g4f.Provider.Yqcloud,
                messages=[{"role": "user", "content": full_prompt}],
            )
            ans = response.choices[0].message.content.strip()
            if ans:
                print(f"[Portal]: {ans}\n", flush=True)
                return ans
            raise ValueError("Boş yanıt")
        except Exception as e:
            print(f"[Sistem]: Hata ({attempt}/{MAX_RETRIES}) → {str(e)[:80]}", flush=True)
            if attempt < MAX_RETRIES:
                time.sleep(delay); delay *= 2
                global _g4f_client; _g4f_client = None

    return "Şu an bağlanamıyorum, lütfen biraz sonra tekrar deneyin."


class ChatServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/transcribe':
            raw  = self.rfile.read(int(self.headers['Content-Length']))
            text = ""
            try: text = json.loads(raw.decode('utf-8')).get('text','').strip()
            except Exception: pass
            resp = ""
            if text:
                print(f"\n[Siz]: {text}", flush=True)
                resp = get_ai_response(text)
            self.send_response(200)
            self.send_header('Content-type','application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status":"ok","response":resp},ensure_ascii=False).encode())
        else:
            self.send_error(404)


def main():
    print("=" * 55)
    print(f"  PORTAL AI HUD")
    print(f"  Wake: '{WAKE_WORD.upper()}' | Sleep: '{SLEEP_CMD.upper()}'")
    print("=" * 55)
    print(f"→ http://localhost:{PORT}")
    print("→ Safranbolu hava durumu: Open-Meteo (ücretsiz)\n")

    with socketserver.TCPServer(("", PORT), ChatServer) as httpd:
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nPortal kapatıldı.")


if __name__ == "__main__":
    main()
