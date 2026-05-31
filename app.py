<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SW Version Manager</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet"/>
  <style>
    :root {
      --bg:#060b14; --panel:#0b1525; --panel2:#0e1c30;
      --border:#1a3a5c; --border2:#2a5a8c;
      --cyan:#00e5ff; --green:#00ff88; --purple:#b44fff;
      --orange:#ff8c00; --red:#ff3355; --yellow:#ffe600;
      --text:#d0e8ff; --text-dim:#4a7a9a;
      --mono:'Share Tech Mono',monospace;
      --ui:'Exo 2',sans-serif;
      --title:'Orbitron',sans-serif;
    }
    *{box-sizing:border-box;margin:0;padding:0;}
    body{background:var(--bg);color:var(--text);font-family:var(--ui);min-height:100vh;}

    /* HERO BG */
    .hero-bg {
      position:fixed;inset:0;z-index:0;
      background: url('/static/system_update.jpg') center/cover no-repeat;
      filter:brightness(0.12) saturate(1.5);
    }
    .hero-overlay {
      position:fixed;inset:0;z-index:1;
      background:
        radial-gradient(ellipse at 10% 0%, rgba(0,100,255,0.25) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 100%, rgba(180,80,255,0.15) 0%, transparent 50%),
        linear-gradient(180deg, rgba(6,11,20,0.6) 0%, rgba(6,11,20,0.85) 100%);
    }

    /* HEADER */
    header {
      position:sticky;top:0;z-index:200;
      border-bottom:1px solid var(--border);
      padding:0 2.5rem;
      display:flex;align-items:center;justify-content:space-between;
      height:70px;
      background:rgba(6,11,20,0.92);
      backdrop-filter:blur(16px);
      box-shadow:0 1px 30px rgba(0,229,255,0.08);
    }
    .logo {
      font-family:var(--title);font-size:1rem;font-weight:900;letter-spacing:3px;
      background:linear-gradient(90deg,var(--cyan),var(--purple));
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
      display:flex;align-items:center;gap:12px;
    }
    .logo-dot {
      width:10px;height:10px;background:var(--green);border-radius:50%;
      box-shadow:0 0 10px var(--green),0 0 20px var(--green);
      animation:pulse 2s infinite;flex-shrink:0;-webkit-text-fill-color:initial;
    }
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(0.8)}}

    nav{display:flex;gap:0.4rem;}
    nav a {
      font-family:var(--ui);font-weight:600;font-size:0.8rem;letter-spacing:2px;
      text-transform:uppercase;color:var(--text-dim);text-decoration:none;
      padding:0.45rem 1.1rem;border:1px solid transparent;border-radius:4px;transition:all 0.25s;
    }
    nav a:hover{color:var(--cyan);border-color:rgba(0,229,255,0.3);background:rgba(0,229,255,0.05);}
    nav a.active{color:var(--cyan);border-color:var(--cyan);background:rgba(0,229,255,0.08);box-shadow:0 0 12px rgba(0,229,255,0.15);}

    /* DEVICE SELECTOR in header */
    .device-select-wrap {
      display:flex;align-items:center;gap:0.8rem;
    }
    .device-label {
      font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;color:var(--text-dim);font-weight:600;
    }
    select.device-select {
      background:rgba(0,229,255,0.06);border:1px solid var(--cyan);color:var(--cyan);
      font-family:var(--mono);font-size:0.85rem;padding:0.35rem 0.8rem;border-radius:4px;
      outline:none;cursor:pointer;
    }
    select.device-select option{background:#0b1525;color:var(--text);}

    main{max-width:1200px;margin:0 auto;padding:2.5rem 2rem;position:relative;z-index:10;}

    h1 {
      font-family:var(--title);font-size:1.1rem;font-weight:700;letter-spacing:4px;
      color:var(--cyan);margin-bottom:2rem;display:flex;align-items:center;gap:14px;
      text-shadow:0 0 20px rgba(0,229,255,0.4);
    }
    h1::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--border2),transparent);}

    /* PANELS */
    .panel {
      background:rgba(11,21,37,0.85);backdrop-filter:blur(10px);
      border:1px solid var(--border);border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;
      position:relative;overflow:hidden;
    }
    .panel::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--border2),transparent);}

    /* TABLE */
    table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:0.9rem;}
    th{text-align:left;padding:0.7rem 1rem;color:var(--text-dim);font-family:var(--ui);font-size:0.7rem;letter-spacing:2.5px;text-transform:uppercase;border-bottom:1px solid var(--border);}
    td{padding:0.85rem 1rem;border-bottom:1px solid rgba(26,58,92,0.4);color:var(--text);}
    tr:last-child td{border-bottom:none;}
    tr:hover td{background:rgba(0,229,255,0.025);}

    .comp-os      {color:#00e5ff;font-weight:700;}
    .comp-backend {color:#b44fff;font-weight:700;}
    .comp-db      {color:#ff8c00;font-weight:700;}
    .comp-frontend{color:#00ff88;font-weight:700;}

    /* BADGES */
    .badge{display:inline-block;padding:3px 10px;border-radius:3px;font-size:0.7rem;font-family:var(--ui);font-weight:700;letter-spacing:1.5px;text-transform:uppercase;}
    .badge-initial  {background:rgba(74,122,154,0.15);color:var(--text-dim);border:1px solid var(--border);}
    .badge-updated  {background:rgba(0,255,136,0.1);color:var(--green);border:1px solid rgba(0,255,136,0.35);}
    .badge-upgrade  {background:rgba(0,255,136,0.1);color:var(--green);border:1px solid rgba(0,255,136,0.35);}
    .badge-downgrade{background:rgba(255,51,85,0.12);color:var(--red);border:1px solid rgba(255,51,85,0.4);}
    .badge-nochange {background:rgba(74,122,154,0.12);color:var(--text-dim);border:1px solid var(--border);}

    /* FORMS */
    .form-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1.2rem;margin-bottom:1.5rem;}
    .form-group label{display:block;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;color:var(--text-dim);margin-bottom:0.45rem;font-family:var(--ui);font-weight:600;}
    .form-group input,.form-group select{
      width:100%;background:rgba(0,0,0,0.4);border:1px solid var(--border);color:var(--text);
      font-family:var(--mono);font-size:0.95rem;padding:0.55rem 0.8rem;border-radius:5px;outline:none;transition:all 0.2s;
    }
    .form-group input:focus,.form-group select:focus{border-color:var(--cyan);box-shadow:0 0 10px rgba(0,229,255,0.15);}
    .form-group select option{background:#0b1525;}
    .form-group .hint{font-size:0.72rem;color:var(--text-dim);margin-top:0.3rem;font-family:var(--mono);}

    /* BUTTONS */
    .btn{font-family:var(--ui);font-weight:700;font-size:0.8rem;letter-spacing:2px;text-transform:uppercase;padding:0.65rem 1.6rem;border:1px solid;border-radius:5px;cursor:pointer;text-decoration:none;display:inline-block;transition:all 0.2s;}
    .btn-primary{background:rgba(0,229,255,0.08);color:var(--cyan);border-color:var(--cyan);}
    .btn-primary:hover{background:rgba(0,229,255,0.18);box-shadow:0 0 16px rgba(0,229,255,0.25);}
    .btn-success{background:rgba(0,255,136,0.08);color:var(--green);border-color:var(--green);}
    .btn-success:hover{background:rgba(0,255,136,0.18);box-shadow:0 0 16px rgba(0,255,136,0.25);}
    .btn-danger{background:rgba(255,51,85,0.08);color:var(--red);border-color:var(--red);}
    .btn-danger:hover{background:rgba(255,51,85,0.18);box-shadow:0 0 16px rgba(255,51,85,0.25);}
    .btn-ghost{background:transparent;color:var(--text-dim);border-color:var(--border);}
    .btn-ghost:hover{color:var(--text);border-color:var(--text-dim);}
    .btn-row{display:flex;gap:1rem;align-items:center;flex-wrap:wrap;}

    /* FLASH */
    .flash{padding:0.8rem 1.2rem;border-radius:5px;margin-bottom:1.5rem;font-family:var(--ui);font-weight:600;font-size:0.9rem;letter-spacing:1px;}
    .flash-success{background:rgba(0,255,136,0.08);border:1px solid rgba(0,255,136,0.3);color:var(--green);}

    /* STATS */
    .stats-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:1rem;margin-bottom:2rem;}
    .stat-card{background:rgba(11,21,37,0.8);backdrop-filter:blur(10px);border:1px solid var(--border);border-radius:8px;padding:1.3rem 1.5rem;position:relative;overflow:hidden;transition:border-color 0.3s;}
    .stat-card:hover{border-color:var(--border2);}
    .stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--cyan);}
    .stat-card.green::before{background:var(--green);}
    .stat-card.purple::before{background:var(--purple);}
    .stat-card.orange::before{background:var(--orange);}
    .stat-label{font-size:0.68rem;letter-spacing:2.5px;text-transform:uppercase;color:var(--text-dim);font-family:var(--ui);font-weight:600;margin-bottom:0.6rem;}
    .stat-value{font-family:var(--title);font-size:1.6rem;color:var(--cyan);line-height:1;}
    .stat-value.green{color:var(--green);}
    .stat-value.purple{color:var(--purple);}
    .stat-value.orange{color:var(--orange);}
    .stat-sub{font-family:var(--mono);font-size:0.75rem;color:var(--text-dim);margin-top:0.4rem;}

    /* PROGRESS BAR */
    .progress-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);z-index:500;align-items:center;justify-content:center;flex-direction:column;gap:2rem;}
    .progress-overlay.active{display:flex;}
    .progress-box{background:var(--panel2);border:1px solid var(--cyan);border-radius:10px;padding:3rem;width:500px;max-width:90%;text-align:center;box-shadow:0 0 40px rgba(0,229,255,0.2);}
    .progress-title{font-family:var(--title);font-size:1rem;letter-spacing:3px;color:var(--cyan);margin-bottom:0.5rem;}
    .progress-sub{font-family:var(--mono);font-size:0.8rem;color:var(--text-dim);margin-bottom:2rem;}
    .progress-bar-wrap{background:rgba(0,229,255,0.08);border:1px solid var(--border);border-radius:20px;height:20px;overflow:hidden;position:relative;}
    .progress-bar-fill{height:100%;width:0%;background:linear-gradient(90deg,var(--cyan),var(--purple));border-radius:20px;transition:width 0.3s ease;box-shadow:0 0 10px rgba(0,229,255,0.5);}
    .progress-pct{font-family:var(--mono);font-size:1.2rem;color:var(--cyan);margin-top:1rem;}
    .progress-steps{font-family:var(--mono);font-size:0.75rem;color:var(--text-dim);margin-top:0.5rem;min-height:1.2em;}

    /* DOWNGRADE MODAL */
    .modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.75);backdrop-filter:blur(4px);z-index:999;align-items:center;justify-content:center;}
    .modal-overlay.active{display:flex;}
    .modal{background:var(--panel2);border:1px solid var(--red);border-radius:10px;padding:2.5rem;max-width:480px;width:90%;box-shadow:0 0 40px rgba(255,51,85,0.25);animation:modalIn 0.3s ease;}
    @keyframes modalIn{from{transform:scale(0.9);opacity:0}to{transform:scale(1);opacity:1}}
    .modal-icon{font-size:2.5rem;text-align:center;margin-bottom:1rem;animation:shake 0.5s ease 0.3s;}
    @keyframes shake{0%,100%{transform:rotate(0)}25%{transform:rotate(-8deg)}75%{transform:rotate(8deg)}}
    .modal h2{font-family:var(--title);font-size:1rem;letter-spacing:3px;color:var(--red);text-align:center;margin-bottom:1rem;text-shadow:0 0 15px rgba(255,51,85,0.5);}
    .modal p{color:var(--text-dim);font-size:0.9rem;line-height:1.6;text-align:center;margin-bottom:0.6rem;}
    .modal-items{background:rgba(255,51,85,0.06);border:1px solid rgba(255,51,85,0.2);border-radius:5px;padding:0.8rem 1rem;margin:1rem 0;font-family:var(--mono);font-size:0.85rem;color:var(--red);}
    .modal-item{padding:0.2rem 0;}
    .modal-btns{display:flex;gap:0.8rem;margin-top:1.5rem;}
    .modal-btns .btn{flex:1;text-align:center;}
  </style>
</head>
<body>

<div class="hero-bg"></div>
<div class="hero-overlay"></div>

<header>
  <div class="logo"><span class="logo-dot"></span>SW-VERSION-MGR</div>
  <div class="device-select-wrap">
    <span class="device-label">Device:</span>
    <select class="device-select" onchange="switchDevice(this.value)">
      {% for d in devices %}
        <option value="{{ d }}" {{ 'selected' if d == device else '' }}>{{ d.upper() }}</option>
      {% endfor %}
    </select>
  </div>
  <nav>
    <a href="{{ url_for('index', device=device) }}"   class="{{ 'active' if request.endpoint == 'index' else '' }}">Dashboard</a>
    <a href="{{ url_for('update', device=device) }}"  class="{{ 'active' if request.endpoint == 'update' else '' }}">Update</a>
    <a href="{{ url_for('history', device=device) }}" class="{{ 'active' if request.endpoint == 'history' else '' }}">History</a>
  </nav>
</header>

<main>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, message in messages %}
      <div class="flash flash-{{ category }}">✓ {{ message }}</div>
    {% endfor %}
  {% endwith %}

  {% block content %}{% endblock %}
</main>

<script>
function switchDevice(device) {
  const url = new URL(window.location.href);
  url.searchParams.set('device', device);
  window.location.href = url.toString();
}
</script>

</body>
</html>
