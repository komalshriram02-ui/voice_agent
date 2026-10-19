from datetime import datetime
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .intent import detect_intent
from .ai import analyze_call, extract_booking
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice Agent")


class AppointmentCreate(BaseModel):
    customer_name: str
    phone: str
    appointment_time: datetime


class CallCreate(BaseModel):
    caller_phone: str
    transcript: str


@app.post("/appointments")
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    appointment = models.Appointment(
        customer_name=data.customer_name,
        phone=data.phone,
        appointment_time=data.appointment_time,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@app.get("/appointments")
def list_appointments(db: Session = Depends(get_db)):
    return db.query(models.Appointment).all()


@app.post("/calls")
def create_call(data: CallCreate, db: Session = Depends(get_db)):
    summary, sentiment = analyze_call(data.transcript)
    call = models.Call(
        caller_phone=data.caller_phone,
        transcript=data.transcript,
        intent=detect_intent(data.transcript),
        summary=summary,
        sentiment=sentiment,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@app.get("/calls")
def list_calls(db: Session = Depends(get_db)):
    return db.query(models.Call).all()

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_appointments = db.query(models.Appointment).count()
    total_calls = db.query(models.Call).count()

    intents = {}
    for call in db.query(models.Call).all():
        intents[call.intent] = intents.get(call.intent, 0) + 1

    return {
        "total_appointments": total_appointments,
        "total_calls": total_calls,
        "calls_by_intent": intents,
    }

from fastapi.responses import HTMLResponse


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Agent Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --primary: #4f46e5;
    --dark: #0f172a;
    --text: #334155;
    --muted: #64748b;
    --bg: #f1f5f9;
    --card: #ffffff;
    --gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Poppins', 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

  /* NAVBAR */
  nav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(10px);
    padding: 14px 6%; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  }
  nav .brand { color: #fff; font-weight: 700; font-size: 19px; margin-right: auto; display: flex; align-items: center; gap: 10px; }
  nav .brand .logo { width: 36px; height: 36px; border-radius: 10px; background: var(--gradient); display: flex; align-items: center; justify-content: center; font-size: 18px; }
  nav a.link { color: #cbd5e1; text-decoration: none; font-size: 14px; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: all 0.25s; }
  nav a.link:hover { background: rgba(255,255,255,0.1); color: #fff; }
  nav a.link.active { background: var(--gradient); color: #fff; }

  /* HEADER */
  .header { background: var(--gradient); color: #fff; text-align: center; padding: 50px 20px 100px; }
  .header h1 { font-size: clamp(26px, 4vw, 38px); font-weight: 700; margin-bottom: 8px; }
  .header p { opacity: 0.92; font-size: 15px; }

  /* STATS */
  .stats {
    max-width: 1100px; margin: -60px auto 0; padding: 0 20px;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 20px;
    position: relative; z-index: 2;
  }
  .stat {
    background: var(--card); border-radius: 18px; padding: 24px 22px;
    display: flex; align-items: center; gap: 18px;
    box-shadow: 0 10px 30px rgba(15,23,42,0.1); transition: transform 0.3s, box-shadow 0.3s;
  }
  .stat:hover { transform: translateY(-6px); box-shadow: 0 18px 40px rgba(79,70,229,0.2); }
  .icon { width: 54px; height: 54px; border-radius: 14px; font-size: 25px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .i1 { background: #e0e7ff; } .i2 { background: #dcfce7; } .i3 { background: #fee2e2; } .i4 { background: #cffafe; }
  .stat .num { font-size: 30px; font-weight: 700; color: var(--dark); line-height: 1.1; }
  .stat .label { font-size: 13px; color: var(--muted); margin-top: 2px; }

  /* PANELS */
  .grid { max-width: 1100px; margin: 36px auto 0; padding: 0 20px; display: grid; grid-template-columns: 1fr 1.6fr; gap: 24px; }
  .panel { background: var(--card); border-radius: 18px; padding: 24px; box-shadow: 0 6px 20px rgba(15,23,42,0.06); overflow-x: auto; }
  .panel h2 { font-size: 18px; color: var(--dark); margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--muted); padding: 10px 12px; border-bottom: 2px solid #e2e8f0; }
  td { padding: 13px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
  tr:hover td { background: #f8fafc; }
  .empty { text-align: center; color: var(--muted); padding: 24px 12px; }

  .bar { height: 8px; background: #e2e8f0; border-radius: 10px; overflow: hidden; margin-top: 6px; min-width: 80px; }
  .bar span { display: block; height: 100%; background: var(--gradient); border-radius: 10px; transition: width 0.5s; }

  .badge { display: inline-block; padding: 4px 12px; border-radius: 50px; font-size: 12px; font-weight: 600; }
  .b-green { background: #dcfce7; color: #166534; }
  .b-red { background: #fee2e2; color: #991b1b; }
  .b-gray { background: #e2e8f0; color: #334155; }

  #status { text-align: center; color: var(--muted); font-size: 13px; margin: 28px 0 10px; }
  footer { margin-top: 30px; background: var(--dark); color: #94a3b8; text-align: center; padding: 22px 20px; font-size: 14px; }
  footer span { color: #fff; font-weight: 600; }

  @media (max-width: 800px) {
    .grid { grid-template-columns: 1fr; }
    nav .brand { width: 100%; margin-bottom: 6px; }
  }
</style>
</head>
<body>

  <nav>
    <span class="brand"><span class="logo">🎙️</span> Voice Agent</span>
    <a class="link" href="/">Home</a>
    <a class="link" href="/voice">Voice Agent</a>
    <a class="link active" href="/dashboard">Dashboard</a>
    <a class="link" href="/docs">API Docs</a>
  </nav>

  <div class="header">
    <h1>Voice Agent Dashboard</h1>
    <p>Live overview of calls and appointments</p>
  </div>

  <section class="stats">
    <div class="stat"><div class="icon i1">📞</div><div><div class="num" id="calls">-</div><div class="label">Total Calls</div></div></div>
    <div class="stat"><div class="icon i2">✅</div><div><div class="num" id="book">-</div><div class="label">Bookings</div></div></div>
    <div class="stat"><div class="icon i3">❌</div><div><div class="num" id="cancel">-</div><div class="label">Cancellations</div></div></div>
    <div class="stat"><div class="icon i4">📅</div><div><div class="num" id="appts">-</div><div class="label">Active Appointments</div></div></div>
  </section>

  <section class="grid">
    <div class="panel">
      <h2>Calls by Intent</h2>
      <table>
        <thead><tr><th>Intent</th><th>Count</th></tr></thead>
        <tbody id="intents"><tr><td colspan="2" class="empty">Loading...</td></tr></tbody>
      </table>
    </div>
    <div class="panel">
      <h2>Appointments</h2>
      <table>
        <thead><tr><th>Name</th><th>Date and time</th><th>Status</th></tr></thead>
        <tbody id="apptRows"><tr><td colspan="3" class="empty">Loading...</td></tr></tbody>
      </table>
    </div>
  </section>

  <div id="status">Loading...</div>
  <footer>Built with ❤️ using <span>FastAPI</span> by <span>Komal Shriram</span></footer>

<script>
function esc(s) {
  return String(s === undefined || s === null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function loadStats() {
  try {
    const res = await fetch("/stats");
    const data = await res.json();
    const intents = data.calls_by_intent || {};
    document.getElementById("appts").textContent = data.total_appointments;
    document.getElementById("calls").textContent = data.total_calls;
    document.getElementById("book").textContent = intents.book_appointment || 0;
    document.getElementById("cancel").textContent = intents.cancel_appointment || 0;

    const body = document.getElementById("intents");
    const entries = Object.entries(intents);
    const max = Math.max(1, ...entries.map(e => e[1]));
    if (entries.length === 0) {
      body.innerHTML = '<tr><td colspan="2" class="empty">No calls yet</td></tr>';
    } else {
      body.innerHTML = entries.map(function(e) {
        const pct = Math.round((e[1] / max) * 100);
        return "<tr><td>" + esc(e[0]) + '<div class="bar"><span style="width:' + pct + '%"></span></div></td><td><b>' + esc(e[1]) + "</b></td></tr>";
      }).join("");
    }
    document.getElementById("status").textContent =
      "Last updated: " + new Date().toLocaleTimeString() + " (auto-refresh every 5 sec)";
  } catch (e) {
    document.getElementById("status").textContent = "Could not load stats.";
  }
}

function badgeClass(status) {
  const s = String(status || "").toLowerCase();
  if (s.indexOf("cancel") !== -1) return "b-red";
  if (s.indexOf("book") !== -1 || s.indexOf("confirm") !== -1 || s.indexOf("active") !== -1 || s.indexOf("schedul") !== -1) return "b-green";
  return "b-gray";
}

function loadAppts() {
  fetch("/appointments")
    .then(function(r) { return r.json(); })
    .then(function(list) {
      const body = document.getElementById("apptRows");
      if (!list.length) {
        body.innerHTML = '<tr><td colspan="3" class="empty">No appointments yet</td></tr>';
        return;
      }
      var html = "";
      list.reverse().forEach(function(a) {
        var when = String(a.appointment_time || "").replace("T", " ").slice(0, 16);
        html += "<tr><td>" + esc(a.customer_name || "-") + "</td><td>" + esc(when) +
          '</td><td><span class="badge ' + badgeClass(a.status) + '">' + esc(a.status) + "</span></td></tr>";
      });
      body.innerHTML = html;
    });
}

loadStats();
loadAppts();
setInterval(loadStats, 5000);
setInterval(loadAppts, 5000);
</script>
</body>
</html>
"""

@app.get("/voice", response_class=HTMLResponse)
def voice_page():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Agent</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --primary: #4f46e5;
    --dark: #0f172a;
    --text: #334155;
    --muted: #64748b;
    --bg: #f1f5f9;
    --card: #ffffff;
    --gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Poppins', 'Segoe UI', Arial, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }

  /* NAVBAR */
  nav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(10px);
    padding: 14px 6%; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  }
  nav .brand { color: #fff; font-weight: 700; font-size: 19px; margin-right: auto; display: flex; align-items: center; gap: 10px; }
  nav .brand .logo { width: 36px; height: 36px; border-radius: 10px; background: var(--gradient); display: flex; align-items: center; justify-content: center; font-size: 18px; }
  nav a.link { color: #cbd5e1; text-decoration: none; font-size: 14px; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: all 0.25s; }
  nav a.link:hover { background: rgba(255,255,255,0.1); color: #fff; }
  nav a.link.active { background: var(--gradient); color: #fff; }

  /* HEADER */
  .header { background: var(--gradient); color: #fff; text-align: center; padding: 50px 20px 110px; }
  .header h1 { font-size: clamp(26px, 4vw, 38px); font-weight: 700; margin-bottom: 8px; }
  .header p { opacity: 0.92; font-size: 15px; }

  /* MAIN CARD */
  .main {
    max-width: 560px; margin: -70px auto 0; padding: 0 20px; position: relative; z-index: 2;
  }
  .panel {
    background: var(--card); border-radius: 22px; padding: 34px 28px;
    box-shadow: 0 14px 40px rgba(15,23,42,0.12); text-align: center;
  }
  .lang-label { font-size: 13px; color: var(--muted); margin-bottom: 8px; display: block; }
  select {
    font-family: inherit; font-size: 16px; padding: 10px 18px; border-radius: 12px;
    border: 2px solid #e2e8f0; background: #f8fafc; color: var(--dark); cursor: pointer;
    outline: none; transition: border-color 0.2s;
  }
  select:focus { border-color: var(--primary); }

  .mic-wrap { margin: 34px 0 10px; }
  button.mic {
    width: 120px; height: 120px; border-radius: 50%; border: none; cursor: pointer;
    background: var(--gradient); color: #fff; font-size: 48px;
    box-shadow: 0 12px 30px rgba(79,70,229,0.4);
    transition: transform 0.25s, box-shadow 0.25s;
  }
  button.mic:hover { transform: scale(1.07); box-shadow: 0 16px 40px rgba(79,70,229,0.5); }
  button.mic.listening { animation: pulse 1.2s infinite; background: linear-gradient(135deg, #ef4444, #f97316); }
  @keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.55); }
    70% { box-shadow: 0 0 0 28px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
  }
  #state { margin-top: 14px; font-size: 14px; font-weight: 500; color: var(--muted); min-height: 20px; }
  #state.on { color: #ef4444; }

  .chat { margin-top: 26px; text-align: left; }
  .bubble { border-radius: 16px; padding: 16px 18px; margin-bottom: 14px; font-size: 15px; line-height: 1.6; }
  .bubble .who { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px; }
  .you { background: #eef2ff; border: 1px solid #c7d2fe; }
  .you .who { color: #4338ca; }
  .agent { background: #ecfeff; border: 1px solid #a5f3fc; }
  .agent .who { color: #0e7490; }
  .bubble b { color: var(--dark); font-weight: 500; }

  .tips { max-width: 560px; margin: 24px auto 0; padding: 0 20px; }
  .tips div { background: var(--card); border-radius: 16px; padding: 18px 22px; box-shadow: 0 6px 20px rgba(15,23,42,0.06); font-size: 13px; color: var(--muted); line-height: 1.8; }
  .tips strong { color: var(--dark); }

  footer { margin-top: 50px; background: var(--dark); color: #94a3b8; text-align: center; padding: 22px 20px; font-size: 14px; }
  footer span { color: #fff; font-weight: 600; }

  @media (max-width: 600px) {
    nav .brand { width: 100%; margin-bottom: 6px; }
    .panel { padding: 26px 18px; }
  }
</style>
</head>
<body>

  <nav>
    <span class="brand"><span class="logo">🎙️</span> Voice Agent</span>
    <a class="link" href="/">Home</a>
    <a class="link active" href="/voice">Voice Agent</a>
    <a class="link" href="/dashboard">Dashboard</a>
    <a class="link" href="/docs">API Docs</a>
  </nav>

  <div class="header">
    <h1>Talk to the Agent</h1>
    <p>Book or cancel an appointment just by speaking</p>
  </div>

  <div class="main">
    <div class="panel">
      <label class="lang-label" for="lang">Choose your language</label>
      <select id="lang" onchange="setLang()">
        <option value="en-IN">English</option>
        <option value="hi-IN">हिन्दी (Hindi)</option>
        <option value="mr-IN">मराठी (Marathi)</option>
      </select>

      <div class="mic-wrap">
        <button class="mic" id="micBtn" onclick="startListening()" title="Click and speak">🎤</button>
        <div id="state">Click the mic and speak</div>
      </div>

      <div class="chat">
        <div class="bubble you"><div class="who">You said</div><b id="said">-</b></div>
        <div class="bubble agent"><div class="who">Agent</div><b id="reply">-</b></div>
      </div>
    </div>
  </div>

  <div class="tips">
    <div>
      <strong>Try saying:</strong><br>
      "Book an appointment" &rarr; then your name &rarr; then "tomorrow at 5 PM"<br>
      "Cancel my appointment" &rarr; then your name<br>
      <strong>Tip:</strong> use Google Chrome and allow the microphone.
    </div>
  </div>

  <footer>Built with ❤️ using <span>FastAPI</span> by <span>Komal Shriram</span></footer>

<script>
var step = "start";
var custName = "";
var LANG = "en-IN";

var M = {
  "en-IN": {
    name: "Sure. What is your name?",
    noname: "Sorry, I did not catch your name. Please say your name.",
    time: function(n) { return "Thanks " + n + ". Which day and time? For example, tomorrow at 5 PM."; },
    badtime: "Sorry, please say it like tomorrow at 5 PM.",
    booked: function(n) { return "Done. Your appointment is booked, " + n + "."; },
    cancelq: "Sure. What name is the appointment under?",
    cancelled: function(n) { return "Done. Your appointment is cancelled, " + n + "."; },
    nocancel: "Sorry, I could not find a booked appointment under that name.",
    unknown: "Sorry, I did not understand.",
    error: "Sorry, something went wrong."
  },
  "hi-IN": {
    name: "ठीक है। आपका नाम क्या है?",
    noname: "माफ़ कीजिए, मैं नाम नहीं सुन पाई। कृपया अपना नाम बताइए।",
    time: function(n) { return "धन्यवाद " + n + "। कौन सा दिन और समय? जैसे, कल शाम 5 बजे।"; },
    badtime: "माफ़ कीजिए, कृपया ऐसे बोलिए: कल शाम 5 बजे।",
    booked: function(n) { return "हो गया। आपकी अपॉइंटमेंट बुक हो गई है, " + n + "।"; },
    cancelq: "ठीक है। अपॉइंटमेंट किस नाम से है?",
    cancelled: function(n) { return "हो गया। आपकी अपॉइंटमेंट रद्द हो गई है, " + n + "।"; },
    nocancel: "माफ़ कीजिए, इस नाम से कोई बुक अपॉइंटमेंट नहीं मिली।",
    unknown: "माफ़ कीजिए, मैं समझ नहीं पाई।",
    error: "माफ़ कीजिए, कुछ गड़बड़ हो गई।"
  },
  "mr-IN": {
    name: "ठीक आहे. तुमचे नाव काय आहे?",
    noname: "माफ करा, मला नाव ऐकू आले नाही. कृपया तुमचे नाव सांगा.",
    time: function(n) { return "धन्यवाद " + n + ". कोणता दिवस आणि वेळ? उदा. उद्या संध्याकाळी 5 वाजता."; },
    badtime: "माफ करा, कृपया असे सांगा: उद्या संध्याकाळी 5 वाजता.",
    booked: function(n) { return "झाले. तुमची अपॉइंटमेंट बुक झाली आहे, " + n + "."; },
    cancelq: "ठीक आहे. अपॉइंटमेंट कोणत्या नावाने आहे?",
    cancelled: function(n) { return "झाले. तुमची अपॉइंटमेंट रद्द झाली आहे, " + n + "."; },
    nocancel: "माफ करा, या नावाने बुक केलेली अपॉइंटमेंट सापडली नाही.",
    unknown: "माफ करा, मला समजले नाही.",
    error: "माफ करा, काहीतरी चुकले."
  }
};

function setLang() {
  LANG = document.getElementById("lang").value;
  step = "start";
}

function say(msg, listenAfter) {
document.getElementById("reply").innerText = msg;
  var u = new SpeechSynthesisUtterance(msg);
  u.lang = LANG;
  u.onend = function() { if (listenAfter) startListening(); };
  speechSynthesis.speak(u);
}

function pad(n) { return (n < 10 ? "0" : "") + n; }

function cleanName(text) {
  var t = text.replace(/my name is|i am|this is/gi, "");
  t = " " + t + " ";
  var phrases = ["मेरा नाम", "माझे नाव", "माझं नाव", "है", "आहे", "हूँ", "हूं"];
  for (var i = 0; i < phrases.length; i++) {
    t = t.split(" " + phrases[i] + " ").join(" ");
  }
  return t.trim();
}

function hasAny(t, list) {
  for (var i = 0; i < list.length; i++) {
    if (t.indexOf(list[i]) >= 0) return true;
  }
  return false;
}

function parseWhen(text) {
  var t = " " + text.toLowerCase().replace(/[.,]/g, " ") + " ";
  var dev = "०१२३४५६७८९";
  for (var i = 0; i < 10; i++) { t = t.split(dev.charAt(i)).join(String(i)); }
  var words = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7,
    "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12,
    "दोन": 2, "पाच": 5, "सहा": 6, "नऊ": 9, "दहा": 10, "अकरा": 11, "बारा": 12
  };
  for (var w in words) { t = t.split(" " + w + " ").join(" " + words[w] + " "); }
  var m = t.match(/([0-9]{1,2})(:([0-9]{2}))?/);
  if (!m) return null;
  var hour = parseInt(m[1]);
  var min = m[3] ? parseInt(m[3]) : 0;
  var isPM = /[0-9] *(p m|pm)/.test(t) || hasAny(t, ["शाम", "दोपहर", "रात", "संध्याकाळ", "सायंकाळ", "दुपार"]);
  var isAM = /[0-9] *(a m|am)/.test(t) || hasAny(t, ["सुबह", "सवेरे", "सकाळ"]);
  if (isPM && hour < 12) hour += 12;
  if (isAM && hour == 12) hour = 0;
  var d = new Date();
  if (hasAny(t, ["day after tomorrow", "परसों", "परसो", "परवा"])) d.setDate(d.getDate() + 2);
  else if (hasAny(t, ["tomorrow", "कल", "उद्या"])) d.setDate(d.getDate() + 1);
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + "T" + pad(hour) + ":" + pad(min) + ":00";
}
function handle(text) {
  var L = M[LANG];
  if (step == "start") {
    fetch("/calls", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({caller_phone: "browser", transcript: text})
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.intent == "book_appointment") {
        step = "name";
        say(L.name, true);
      } else if (d.intent == "cancel_appointment") {
        step = "cancelname";
        say(L.cancelq, true);
      } else {
        say(L.unknown, false);
      }
    });
  } else if (step == "name") {
    custName = cleanName(text);
    if (!custName) { say(L.noname, true); return; }
    step = "time";
    say(L.time(custName), true);
  } else if (step == "cancelname") {
    var cn = cleanName(text);
    fetch("/appointments/cancel-by-name", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({customer_name: cn})
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      step = "start";
      if (d.found) say(L.cancelled(cn), false);
      else say(L.nocancel, false);
    });
  } else if (step == "time") {
    var when = parseWhen(text);
    if (!when) { say(L.badtime, true); return; }
    fetch("/appointments", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({customer_name: custName, phone: "browser", appointment_time: when})
    })
    .then(function(r) {
      step = "start";
      if (r.ok) say(L.booked(custName), false);
      else say(L.error, false);
    });
  }
}

function startListening() {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alert("Use Chrome"); return; }
  var rec = new SR();
  rec.lang = LANG;
  var btn = document.getElementById("micBtn");
  var st = document.getElementById("state");
  rec.onstart = function() {
    btn.classList.add("listening");
    st.classList.add("on");
    st.innerText = "Listening... please speak";
  };
  rec.onend = function() {
    btn.classList.remove("listening");
    st.classList.remove("on");
    st.innerText = "Click the mic and speak";
  };
  rec.onresult = function(e) {
    var text = e.results[0][0].transcript;
    document.getElementById("said").innerText = text;
    handle(text);
  };
  rec.start();
}
</script>
</body>
</html>
"""
from datetime import datetime
from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    customer_name: str
    appointment_time: datetime
    phone: str = "browser"


@app.post("/appointments")
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    appt = models.Appointment(
        customer_name=data.customer_name,
        phone=data.phone,
        appointment_time=data.appointment_time,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt 

class CancelRequest(BaseModel):
    customer_name: str


@app.post("/appointments/cancel-by-name")
def cancel_by_name(data: CancelRequest, db: Session = Depends(get_db)):
    appt = (
        db.query(models.Appointment)
        .filter(models.Appointment.customer_name.ilike(data.customer_name.strip()))
        .filter(models.Appointment.status == "booked")
        .order_by(models.Appointment.id.desc())
        .first()
    )
    if not appt:
        return {"found": False}
    appt.status = "cancelled"
    db.commit()
    return {"found": True}


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Appointment Agent</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --primary: #4f46e5;
    --secondary: #06b6d4;
    --dark: #0f172a;
    --text: #334155;
    --muted: #64748b;
    --bg: #f1f5f9;
    --card: #ffffff;
    --gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    font-family: 'Poppins', 'Segoe UI', Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ---------- NAVBAR ---------- */
  nav {
    position: sticky; top: 0; z-index: 100;
    background: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(10px);
    padding: 14px 6%;
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  }
  nav .brand {
    color: #fff; font-weight: 700; font-size: 19px;
    margin-right: auto; display: flex; align-items: center; gap: 10px;
  }
  nav .brand .logo {
    width: 36px; height: 36px; border-radius: 10px;
    background: var(--gradient);
    display: flex; align-items: center; justify-content: center; font-size: 18px;
  }
  nav a.link {
    color: #cbd5e1; text-decoration: none; font-size: 14px; font-weight: 500;
    padding: 8px 16px; border-radius: 8px; transition: all 0.25s;
  }
  nav a.link:hover { background: rgba(255,255,255,0.1); color: #fff; }
  nav a.link.active { background: var(--gradient); color: #fff; }

  /* ---------- HERO ---------- */
  .hero {
    background: var(--gradient);
    color: #fff; text-align: center;
    padding: 80px 20px 130px;
    position: relative; overflow: hidden;
  }
  .hero::before, .hero::after {
    content: ""; position: absolute; border-radius: 50%;
    background: rgba(255,255,255,0.08);
  }
  .hero::before { width: 400px; height: 400px; top: -150px; left: -100px; }
  .hero::after { width: 300px; height: 300px; bottom: -120px; right: -60px; }
  .hero > * { position: relative; z-index: 1; }
  .badge {
    display: inline-block; background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 6px 18px; border-radius: 50px; font-size: 13px; font-weight: 500;
    margin-bottom: 22px;
  }
  .hero h1 { font-size: clamp(30px, 5vw, 52px); font-weight: 700; line-height: 1.2; margin-bottom: 16px; }
  .hero p { font-size: clamp(14px, 2vw, 18px); opacity: 0.92; max-width: 620px; margin: 0 auto 32px; }
  .hero-buttons { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
  .btn {
    text-decoration: none; padding: 14px 30px; border-radius: 50px;
    font-size: 15px; font-weight: 600; transition: all 0.3s; display: inline-block;
  }
  .btn-white { background: #fff; color: var(--primary); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
  .btn-white:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,0.28); }
  .btn-outline { border: 2px solid rgba(255,255,255,0.8); color: #fff; }
  .btn-outline:hover { background: #fff; color: var(--primary); transform: translateY(-3px); }

  /* ---------- STATS ---------- */
  .stats {
    max-width: 1100px; margin: -70px auto 0; padding: 0 20px;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 20px;
    position: relative; z-index: 2;
  }
  .stat {
    background: var(--card); border-radius: 18px; padding: 26px 22px;
    display: flex; align-items: center; gap: 18px;
    box-shadow: 0 10px 30px rgba(15,23,42,0.1);
    transition: transform 0.3s, box-shadow 0.3s;
  }
  .stat:hover { transform: translateY(-6px); box-shadow: 0 18px 40px rgba(79,70,229,0.2); }
  .icon {
    width: 56px; height: 56px; border-radius: 14px; font-size: 26px;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .i1 { background: #e0e7ff; } .i2 { background: #dcfce7; }
  .i3 { background: #fee2e2; } .i4 { background: #cffafe; }
  .stat .num { font-size: 30px; font-weight: 700; color: var(--dark); line-height: 1.1; }
  .stat .label { font-size: 13px; color: var(--muted); margin-top: 2px; }

  /* ---------- FEATURES ---------- */
  .section { max-width: 1100px; margin: 70px auto 40px; padding: 0 20px; text-align: center; }
  .section h2 { font-size: 30px; color: var(--dark); margin-bottom: 8px; }
  .section .sub { color: var(--muted); margin-bottom: 36px; }
  .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
  .feature {
    background: var(--card); border-radius: 18px; padding: 34px 26px;
    box-shadow: 0 6px 20px rgba(15,23,42,0.06);
    border-top: 4px solid transparent;
    transition: all 0.3s;
  }
  .feature:hover { transform: translateY(-8px); border-top-color: var(--primary); box-shadow: 0 18px 40px rgba(79,70,229,0.15); }
  .feature .f-icon { font-size: 40px; margin-bottom: 14px; }
  .feature h3 { color: var(--dark); font-size: 18px; margin-bottom: 8px; }
  .feature p { color: var(--muted); font-size: 14px; line-height: 1.7; }

  /* ---------- FOOTER ---------- */
  footer {
    margin-top: 60px; background: var(--dark); color: #94a3b8;
    text-align: center; padding: 26px 20px; font-size: 14px;
  }
  footer span { color: #fff; font-weight: 600; }

  @media (max-width: 600px) {
    nav { padding: 12px 4%; }
    nav .brand { width: 100%; margin-bottom: 6px; }
    .hero { padding: 60px 16px 110px; }
  }
</style>
</head>
<body>

  <nav>
    <span class="brand"><span class="logo">🎙️</span> Voice Agent</span>
    <a class="link active" href="/">Home</a>
    <a class="link" href="/voice">Voice Agent</a>
    <a class="link" href="/dashboard">Dashboard</a>
    <a class="link" href="/docs">API Docs</a>
  </nav>

  <section class="hero">
    <span class="badge">✨ AI Powered Voice Assistant</span>
    <h1>Voice Appointment Agent</h1>
   
   <p>Book and cancel appointments just by speaking. Works in English, Hindi and Marathi.</p>
    <div class="hero-buttons">
      <a class="btn btn-white" href="/voice">🎤 Talk to Agent</a>
      <a class="btn btn-outline" href="/dashboard">📊 View Dashboard</a>
    </div>
  </section>

  <section class="stats">
    <div class="stat"><div class="icon i1">📞</div><div><div class="num" id="total">...</div><div class="label">Total Calls</div></div></div>
    <div class="stat"><div class="icon i2">✅</div><div><div class="num" id="book">...</div><div class="label">Bookings</div></div></div>
    <div class="stat"><div class="icon i3">❌</div><div><div class="num" id="cancel">...</div><div class="label">Cancellations</div></div></div>
    <div class="stat"><div class="icon i4">📅</div><div><div class="num" id="active">...</div><div class="label">Active Appointments</div></div></div>
  </section>

  <section class="section">
    <h2>Features</h2>
    <p class="sub">What this agent can do for you</p>
    <div class="features">
  <div class="feature"><div class="f-icon">🌐</div><h3>3 Languages</h3><p>Speak in English, Hindi or Marathi and the agent replies in the same language.</p></div>
     <div class="feature"><div class="f-icon">🗓️</div><h3>Book &amp; Cancel</h3><p>Asks for your name and books or cancels appointments, just like a real receptionist.</p></div>
     <div class="feature"><div class="f-icon">📈</div><h3>Live Dashboard</h3><p>See live counts of every call and the full appointment list in one place.</p></div>
    </div>
  </section>

  <footer>Built with ❤️ using <span>FastAPI</span> by <span>Komal Shriram</span></footer>

<script>
function animate(id, target) {
  const el = document.getElementById(id);
  if (isNaN(target)) { el.textContent = target; return; }
  let n = 0;
  const step = Math.max(1, Math.ceil(target / 30));
  const t = setInterval(() => {
    n += step;
    if (n >= target) { n = target; clearInterval(t); }
    el.textContent = n;
  }, 30);
}

fetch("/stats")
  .then(r => r.json())
  .then(d => {
    const calls = d.calls_by_intent || {};
    const b = calls.book_appointment || 0;
    const c = calls.cancel_appointment || 0;
    animate("total", d.total_calls !== undefined ? d.total_calls : (b + c));
    animate("book", b);
    animate("cancel", c);
    animate("active", d.total_appointments !== undefined ? d.total_appointments : 0);
  })
  .catch(() => {
    ["total", "book", "cancel", "active"].forEach(id => {
      document.getElementById(id).textContent = "-";
    });
  });
</script>
</body>
</html>
"""
