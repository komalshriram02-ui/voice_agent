from datetime import datetime
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .intent import detect_intent
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
    call = models.Call(
        caller_phone=data.caller_phone,
        transcript=data.transcript,
        intent=detect_intent(data.transcript),
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
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Agent Dashboard</title>
<style>
  body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 24px; color: #222; }
  h1 { margin-top: 0; }
  .cards { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .card { background: #fff; border-radius: 10px; padding: 20px 28px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); min-width: 180px; }
  .card .num { font-size: 40px; font-weight: bold; color: #2563eb; }
  .card .label { color: #666; margin-top: 4px; }
  table { background: #fff; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); min-width: 320px; }
  th, td { padding: 12px 20px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #2563eb; color: #fff; }
  #status { color: #888; font-size: 13px; margin-top: 12px; }
</style>
</head>
<body>
  <h1>Voice Agent Dashboard</h1>

  <div class="cards">
    <div class="card"><div class="num" id="appts">-</div><div class="label">Total Appointments</div></div>
    <div class="card"><div class="num" id="calls">-</div><div class="label">Total Calls</div></div>
  </div>

  <h2>Calls by Intent</h2>
  <table>
    <thead><tr><th>Intent</th><th>Count</th></tr></thead>
    <tbody id="intents"></tbody>
  </table>

  <div id="status">Loading...</div>

<script>
async function loadStats() {
  try {
    const res = await fetch("/stats");
    const data = await res.json();
    document.getElementById("appts").textContent = data.total_appointments;
    document.getElementById("calls").textContent = data.total_calls;

    const body = document.getElementById("intents");
    body.innerHTML = "";
    for (const [intent, count] of Object.entries(data.calls_by_intent)) {
      const tr = document.createElement("tr");
      const td1 = document.createElement("td");
      const td2 = document.createElement("td");
      td1.textContent = intent;
      td2.textContent = count;
      tr.appendChild(td1);
      tr.appendChild(td2);
      body.appendChild(tr);
    }
    document.getElementById("status").textContent =
      "Last updated: " + new Date().toLocaleTimeString() + " (auto-refresh every 5 sec)";
  } catch (e) {
    document.getElementById("status").textContent = "Could not load stats.";
  }
}
loadStats();
setInterval(loadStats, 5000);
</script>
<h2>Appointments</h2>
<table>
  <thead><tr><th>Name</th><th>Date and time</th><th>Status</th></tr></thead>
  <tbody id="apptRows"></tbody>
</table>
<script>
function loadAppts() {
  fetch("/appointments")
    .then(function(r) { return r.json(); })
    .then(function(list) {
      var html = "";
      list.reverse().forEach(function(a) {
        html += "<tr><td>" + (a.customer_name || "-") + "</td><td>" +
          a.appointment_time.replace("T", " ").slice(0, 16) + "</td><td>" +
          a.status + "</td></tr>";
      });
      document.getElementById("apptRows").innerHTML = html;
    });
}
loadAppts();
setInterval(loadAppts, 5000);
</script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Agent Dashboard</title>
<style>
  body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 24px; color: #222; }
  h1 { margin-top: 0; }
  .cards { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .card { background: #fff; border-radius: 10px; padding: 20px 28px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); min-width: 180px; }
  .card .num { font-size: 40px; font-weight: bold; color: #2563eb; }
  .card .label { color: #666; margin-top: 4px; }
  table { background: #fff; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); min-width: 320px; }
  th, td { padding: 12px 20px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #2563eb; color: #fff; }
  #status { color: #888; font-size: 13px; margin-top: 12px; }
</style>
</head>
<body>
  <h1>Voice Agent Dashboard</h1>

  <div class="cards">
    <div class="card"><div class="num" id="appts">-</div><div class="label">Total Appointments</div></div>
    <div class="card"><div class="num" id="calls">-</div><div class="label">Total Calls</div></div>
  </div>

  <h2>Calls by Intent</h2>
  <table>
    <thead><tr><th>Intent</th><th>Count</th></tr></thead>
    <tbody id="intents"></tbody>
  </table>

  <div id="status">Loading...</div>

<script>
async function loadStats() {
  try {
    const res = await fetch("/stats");
    const data = await res.json();
    document.getElementById("appts").textContent = data.total_appointments;
    document.getElementById("calls").textContent = data.total_calls;

    const body = document.getElementById("intents");
    body.innerHTML = "";
    for (const [intent, count] of Object.entries(data.calls_by_intent)) {
      const tr = document.createElement("tr");
      const td1 = document.createElement("td");
      const td2 = document.createElement("td");
      td1.textContent = intent;
      td2.textContent = count;
      tr.appendChild(td1);
      tr.appendChild(td2);
      body.appendChild(tr);
    }
    document.getElementById("status").textContent =
      "Last updated: " + new Date().toLocaleTimeString() + " (auto-refresh every 5 sec)";
  } catch (e) {
    document.getElementById("status").textContent = "Could not load stats.";
  }
}
loadStats();
setInterval(loadStats, 5000);
</script>
</body>
</html>
"""

@app.get("/voice", response_class=HTMLResponse)
def voice_page():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Voice Agent</title>
<style>
  body { font-family: Arial, sans-serif; background: #f4f6f8; text-align: center; padding: 40px; }
  button { background: #2563eb; color: #fff; border: none; border-radius: 50px; padding: 20px 40px; font-size: 20px; cursor: pointer; }
  select { font-size: 18px; padding: 8px 14px; border-radius: 8px; margin-bottom: 20px; }
  .box { background: #fff; border-radius: 10px; padding: 20px; margin: 20px auto; max-width: 500px; }
</style>
</head>
<body>
  <h1>Voice Agent</h1>
  <select id="lang" onchange="setLang()">
    <option value="en-IN">English</option>
    <option value="hi-IN">हिन्दी (Hindi)</option>
    <option value="mr-IN">मराठी (Marathi)</option>
  </select>
  <br>
  <button onclick="startListening()">Click the button and speak</button>
  <div class="box">You said: <b id="said">-</b></div>
  <div class="box">Agent: <b id="reply">-</b></div>
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