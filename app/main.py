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


@app.get("/")
def home():
    return {"message": "Voice agent backend is running"}


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
  .box { background: #fff; border-radius: 10px; padding: 20px; margin: 20px auto; max-width: 500px; }
</style>
</head>
<body>
  <h1>Voice Agent</h1>
  <button onclick="startListening()">Click the button and speak</button>
  <div class="box">You said: <b id="said">-</b></div>
  <div class="box">Agent: <b id="reply">-</b></div>
<script>
var step = "start";
var custName = "";

function say(msg, listenAfter) {
  document.getElementById("reply").innerText = msg;
  var u = new SpeechSynthesisUtterance(msg);
  u.onend = function() { if (listenAfter) startListening(); };
  speechSynthesis.speak(u);
}

function pad(n) { return (n < 10 ? "0" : "") + n; }

function parseWhen(text) {
  var t = text.toLowerCase().replace(/[.]/g, "");
  var m = t.match(/([0-9]{1,2})(:([0-9]{2}))? *(am|pm)/);
  if (!m) return null;
  var hour = parseInt(m[1]);
  var min = m[3] ? parseInt(m[3]) : 0;
  if (m[4] == "pm" && hour < 12) hour += 12;
  if (m[4] == "am" && hour == 12) hour = 0;
  var d = new Date();
  if (t.indexOf("day after tomorrow") >= 0) d.setDate(d.getDate() + 2);
  else if (t.indexOf("tomorrow") >= 0) d.setDate(d.getDate() + 1);
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + "T" + pad(hour) + ":" + pad(min) + ":00";
}

function handle(text) {
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
        say("Sure. What is your name?", true);
      } else if (d.intent == "cancel_appointment") {
       step = "cancelname"; say("Sure. What name is the appointment under?", true);
      } else {
        say("Sorry, I did not understand.", false);
      }
    });
  } else if (step == "name") {
    custName = text.replace(/my name is|i am|this is/gi, "").trim();
if (!custName) { say("Sorry, I did not catch your name. Please say your name.", true); return; }
    step = "time";
    say("Thanks " + custName + ". Which day and time? For example, tomorrow at 5 PM.", true);
  } else if (step == "cancelname") {
    var cn = text.replace(/my name is|i am|this is/gi, "").trim();
    fetch("/appointments/cancel-by-name", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({customer_name: cn})
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      step = "start";
      if (d.found) say("Done. Your appointment is cancelled, " + cn + ".", false);
      else say("Sorry, I could not find a booked appointment under that name.", false);
    });
  } else if (step == "time") {
    var when = parseWhen(text);
    if (!when) {
      say("Sorry, please say it like tomorrow at 5 PM.", true);
      return;
    }
    fetch("/appointments", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({customer_name: custName, phone: "browser", appointment_time: when})
    })
    .then(function(r) {
      step = "start";
      if (r.ok) say("Done. Your appointment is booked, " + custName + ".", false);
      else say("Sorry, something went wrong.", false);
    });
  }
}

function startListening() {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { alert("Use Chrome"); return; }
  var rec = new SR();
  rec.lang = "en-IN";
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