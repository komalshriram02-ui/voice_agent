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
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Appointment Agent</title>
<style>
  body { margin: 0; font-family: Arial, sans-serif; background: #f4f6fb; color: #222; }
  nav { background: #1f4fd8; padding: 14px 24px; display: flex; gap: 24px; align-items: center; flex-wrap: wrap; }
  nav .brand { color: #fff; font-weight: bold; font-size: 18px; margin-right: auto; }
  nav a { color: #fff; text-decoration: none; font-size: 15px; }
  nav a:hover { text-decoration: underline; }
  .hero { text-align: center; padding: 40px 20px 10px; }
  .hero h1 { margin: 0 0 8px; }
  .hero p { color: #555; margin: 0; }
  .cards { display: flex; gap: 16px; justify-content: center; padding: 24px; flex-wrap: wrap; }
  .card { background: #fff; border-radius: 10px; padding: 20px 30px; min-width: 150px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .card .num { font-size: 32px; font-weight: bold; color: #1f4fd8; }
  .card .label { color: #666; margin-top: 4px; }
  .buttons { display: flex; gap: 16px; justify-content: center; padding: 10px 20px 40px; flex-wrap: wrap; }
  .btn { background: #1f4fd8; color: #fff; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 16px; }
  .btn:hover { background: #1740b0; }
</style>
</head>
<body>
  <nav>
    <span class="brand">Voice Appointment Agent</span>
    <a href="/">Home</a>
    <a href="/voice">Voice Agent</a>
    <a href="/dashboard">Dashboard</a>
    <a href="/docs">API Docs</a>
  </nav>

  <div class="hero">
    <h1>Voice Appointment Agent</h1>
    <p>English, Hindi aur Marathi mein appointment book aur cancel karo</p>
  </div>

  <div class="cards">
    <div class="card"><div class="num" id="total">...</div><div class="label">Total Calls</div></div>
    <div class="card"><div class="num" id="book">...</div><div class="label">Bookings</div></div>
    <div class="card"><div class="num" id="cancel">...</div><div class="label">Cancellations</div></div>
    <div class="card"><div class="num" id="active">...</div><div class="label">Active Appointments</div></div>
  </div>

  <div class="buttons">
    <a class="btn" href="/voice">Talk to Agent</a>
    <a class="btn" href="/dashboard">View Dashboard</a>
    <a class="btn" href="/docs">API Docs</a>
  </div>

<script>
fetch("/stats")
  .then(r => r.json())
  .then(d => {
    const calls = d.calls_by_intent || {};
    const b = calls.book_appointment || 0;
    const c = calls.cancel_appointment || 0;
    document.getElementById("total").textContent = d.total_calls !== undefined ? d.total_calls : (b + c);
    document.getElementById("book").textContent = b;
    document.getElementById("cancel").textContent = c;
    document.getElementById("active").textContent = d.total_appointments !== undefined ? d.total_appointments : 0;

  })
  .catch(() => {
    document.getElementById("total").textContent = "-";
    document.getElementById("book").textContent = "-";
    document.getElementById("cancel").textContent = "-";
    document.getElementById("active").textContent = "-";
    
  });
</script>
</body>
</html>
"""