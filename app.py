import os, uuid, re, datetime as dt, requests
from functools import wraps
from flask import Flask, send_from_directory, render_template, request, redirect, url_for, session, flash, abort, jsonify
from markupsafe import Markup, escape
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")))
db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
E = os.environ.get
PRICE = int(E("PRICE_TZS", 3000))
SITE = E("SITE_URL", "")
ADMINS = [x.strip().lower() for x in E("ADMIN_EMAILS", "").split(",") if x.strip()]
NOW = lambda: dt.datetime.now(dt.timezone.utc)
parse = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None

# ---------- SVG icons ----------
_I = {
 "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
 "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
 "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
 "user": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
 "card": '<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
 "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
 "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
 "send": '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
 "reply": '<polyline points="9 14 4 9 9 4"/><path d="M20 20v-7a4 4 0 0 0-4-4H4"/>',
 "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/>',
 "bell": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
 "moon": '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
 "check": '<polyline points="20 6 9 17 4 12"/>',
 "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
 "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
 "sliders": '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>',
 "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
 "refresh": '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
 "play": '<polygon points="5 3 19 12 5 21 5 3"/>',
}
@app.template_global()
def icon(n, s=20):
    return Markup(f'<svg class="ic" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_I[n]}</svg>')

# ---------- auth ----------
def current_user():
    uid = session.get("uid")
    if not uid: return None
    r = db.table("users").select("*").eq("id", uid).limit(1).execute().data
    if not r:
        session.clear(); return None
    u = r[0]; until = parse(u.get("premium_until"))
    u.update(premium=bool(until and until > NOW()), until=until, is_admin=u["email"].lower() in ADMINS)
    return u

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current_user()
        return f(u, *a, **k) if u else redirect(url_for("login"))
    return w

def admin_required(f):
    @wraps(f)
    def w(u, *a, **k):
        if not u["is_admin"]: abort(403)
        return f(u, *a, **k)
    return login_required(w)

@app.context_processor
def inject(): return {"user": current_user(), "PRICE": PRICE}

@app.route("/")
def index(): return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form; email = f["email"].strip().lower(); name = f["name"].strip()
        if not name or "@" not in email or len(f["password"]) < 6: flash("Jaza taarifa zote. Nenosiri liwe na herufi 6 au zaidi.")
        elif not f.get("terms"): flash("Kubali Masharti na Sera ya Faragha ili uendelee.")
        elif db.table("users").select("id").eq("email", email).execute().data: flash("Barua pepe hii tayari imesajiliwa. Ingia badala yake.")
        else:
            r = db.table("users").insert({"name": name, "email": email, "city": f.get("city", "Mwanza").strip() or "Mwanza",
                "password_hash": generate_password_hash(f["password"])}).execute().data[0]
            session["uid"] = r["id"]; return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        r = db.table("users").select("*").eq("email", request.form["email"].strip().lower()).limit(1).execute().data
        if r and check_password_hash(r[0]["password_hash"], request.form["password"]):
            session["uid"] = r[0]["id"]; return redirect(url_for("dashboard"))
        flash("Barua pepe au nenosiri si sahihi.")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/privacy")
def privacy(): return render_template("legal.html", page="privacy")
@app.route("/terms")
def terms(): return render_template("legal.html", page="terms")

# ---------- content ----------
def prayer_times(city):
    try:
        t = requests.get("https://api.aladhan.com/v1/timingsByCity", params={"city": city, "country": "Tanzania", "method": 2}, timeout=5).json()["data"]["timings"]
        return {k: t[k] for k in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")}
    except Exception: return None

@app.route("/dashboard")
@login_required
def dashboard(u):
    kind = "asubuhi" if (NOW() + dt.timedelta(hours=3)).hour < 14 else "jioni"
    items = db.table("adhkar").select("*").eq("type", kind).order("id").execute().data
    return render_template("dashboard.html", u=u, kind=kind, items=items, times=prayer_times(u["city"]))

@app.route("/courses")
@login_required
def courses(u): return render_template("courses.html", cs=db.table("courses").select("*").order("id").execute().data)

@app.route("/course/<int:cid>")
@login_required
def course(u, cid):
    c = db.table("courses").select("*").eq("id", cid).limit(1).execute().data
    if not c: abort(404)
    ls = db.table("lessons").select("id,title,is_free,position").eq("course_id", cid).order("position").execute().data
    return render_template("course.html", c=c[0], ls=ls)

@app.route("/lesson/<int:lid>")
@login_required
def lesson(u, lid):
    r = db.table("lessons").select("*").eq("id", lid).limit(1).execute().data
    if not r: abort(404)
    if not (r[0]["is_free"] or u["premium"] or u["is_admin"]):
        flash("Somo hili ni la wanachama. Lipia ili kuendelea."); return redirect(url_for("pay"))
    return render_template("lesson.html", l=r[0])

# ---------- ClickPesa ----------
CP = "https://api.clickpesa.com/third-parties"
def cp_headers():
    t = requests.post(f"{CP}/generate-token", headers={"client-id": E("CLICKPESA_CLIENT_ID", ""), "api-key": E("CLICKPESA_API_KEY", "")}, timeout=15).json()["token"]
    return {"Authorization": t, "Content-Type": "application/json"}

def activate(uid, days=30):
    usr = db.table("users").select("premium_until").eq("id", uid).execute().data[0]
    start = max(NOW(), parse(usr["premium_until"]) or NOW())
    db.table("users").update({"premium_until": (start + dt.timedelta(days=days)).isoformat()}).eq("id", uid).execute()

def check_payment(order):
    p = db.table("payments").select("*").eq("order_reference", order).limit(1).execute().data
    if not p: return None
    p = p[0]
    if p["status"] != "pending": return p["status"]
    d = requests.get(f"{CP}/payments/{order}", headers=cp_headers(), timeout=15).json()
    d = d[0] if isinstance(d, list) and d else d
    st = (d or {}).get("status", "")
    if st in ("SUCCESS", "SETTLED"):
        db.table("payments").update({"status": "approved"}).eq("id", p["id"]).execute(); activate(p["user_id"]); return "approved"
    if st == "FAILED":
        db.table("payments").update({"status": "rejected"}).eq("id", p["id"]).execute(); return "rejected"
    return "pending"

@app.route("/pay", methods=["GET", "POST"])
@login_required
def pay(u):
    if request.method == "POST":
        n = re.sub(r"\D", "", request.form["phone"])
        if n.startswith("0"): n = "255" + n[1:]
        if not re.fullmatch(r"255\d{9}", n): flash("Weka namba sahihi ya simu, mfano 0712345678.")
        else:
            order = "NY" + uuid.uuid4().hex[:18]
            try:
                r = requests.post(f"{CP}/payments/initiate-ussd-push-request", headers=cp_headers(), timeout=20,
                    json={"amount": str(PRICE), "currency": "TZS", "orderReference": order, "phoneNumber": n})
                ok = r.status_code in (200, 201)
            except Exception: ok = False
            if ok:
                db.table("payments").insert({"user_id": u["id"], "amount": PRICE, "method": "ClickPesa", "order_reference": order, "phone": n}).execute()
                return redirect(url_for("pay", ref=order))
            flash("Imeshindwa kutuma ombi la malipo. Hakikisha namba ni sahihi, kisha jaribu tena.")
    mine = db.table("payments").select("*").eq("user_id", u["id"]).order("id", desc=True).limit(5).execute().data
    return render_template("pay.html", mine=mine, ref=request.args.get("ref"))

@app.route("/pay/status/<order>")
@login_required
def pay_status(u, order):
    p = db.table("payments").select("user_id").eq("order_reference", order).limit(1).execute().data
    if not p or p[0]["user_id"] != u["id"]: abort(404)
    try: return jsonify(status=check_payment(order))
    except Exception: return jsonify(status="pending")

@app.route("/webhooks/clickpesa", methods=["POST"])
def cp_webhook():
    j = request.get_json(silent=True) or {}
    order = (j.get("data") or {}).get("orderReference") or j.get("orderReference")
    if order:
        try: check_payment(str(order))  # hali inathibitishwa moja kwa moja na ClickPesa
        except Exception: pass
    return "", 200

# ---------- community ----------
def fmt(m):
    return {"id": m["id"], "uid": m["user_id"], "name": (m.get("users") or {}).get("name", "Mtumiaji"),
            "body": "Ujumbe huu umefutwa." if m["deleted"] else m["body"], "deleted": m["deleted"],
            "reply_name": m.get("reply_name"), "reply_body": m.get("reply_body"), "at": m["created_at"]}

@app.route("/community")
@login_required
def community(u): return render_template("community.html")

@app.route("/community/api")
@login_required
def community_api(u):
    after = request.args.get("after", type=int, default=0)
    q = db.table("messages").select("*, users(name)")
    rows = (q.gt("id", after).order("id").limit(100).execute().data if after
            else list(reversed(q.order("id", desc=True).limit(60).execute().data)))
    return jsonify([fmt(m) for m in rows])

@app.route("/community/send", methods=["POST"])
@login_required
def community_send(u):
    j = request.get_json(silent=True) or {}
    body = (j.get("body") or "").strip()[:500]
    if not body: abort(400)
    row = {"user_id": u["id"], "body": body}
    if j.get("reply_to"):
        p = db.table("messages").select("body,deleted,users(name)").eq("id", int(j["reply_to"])).limit(1).execute().data
        if p: row.update(reply_to=int(j["reply_to"]), reply_name=p[0]["users"]["name"], reply_body=("" if p[0]["deleted"] else p[0]["body"][:120]))
    db.table("messages").insert(row).execute()
    return jsonify(ok=True)

@app.route("/community/delete/<int:mid>", methods=["POST"])
@login_required
def community_delete(u, mid):
    m = db.table("messages").select("user_id").eq("id", mid).limit(1).execute().data
    if not m or not (m[0]["user_id"] == u["id"] or u["is_admin"]): abort(403)
    db.table("messages").update({"deleted": True}).eq("id", mid).execute()
    return jsonify(ok=True)

# ---------- profile ----------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile(u):
    if request.method == "POST":
        f = request.form; ph = re.sub(r"\D", "", f.get("phone", ""))
        if ph.startswith("0"): ph = "255" + ph[1:]
        db.table("users").update({"name": f["name"].strip() or u["name"], "city": f["city"].strip() or "Mwanza",
            "bio": f.get("bio", "")[:200], "phone": ph or None,
            "notify_email": bool(f.get("notify_email")), "notify_whatsapp": bool(f.get("notify_whatsapp") and ph)}).eq("id", u["id"]).execute()
        flash("Wasifu umehifadhiwa."); return redirect(url_for("profile"))
    return render_template("profile.html", u=u)

@app.route("/profile/password", methods=["POST"])
@login_required
def change_password(u):
    f = request.form
    if not check_password_hash(u["password_hash"], f["old"]): flash("Nenosiri la sasa si sahihi.")
    elif len(f["new"]) < 6: flash("Nenosiri jipya liwe na herufi 6 au zaidi.")
    else:
        db.table("users").update({"password_hash": generate_password_hash(f["new"])}).eq("id", u["id"]).execute(); flash("Nenosiri limebadilishwa.")
    return redirect(url_for("profile"))

@app.route("/profile/delete", methods=["POST"])
@login_required
def delete_account(u):
    if not check_password_hash(u["password_hash"], request.form["password"]) or request.form.get("confirm", "").strip().upper() != "FUTA":
        flash("Haikufutwa. Andika FUTA na nenosiri sahihi."); return redirect(url_for("profile"))
    db.table("users").delete().eq("id", u["id"]).execute()  # malipo na jumbe vinafutwa pia (cascade)
    session.clear(); flash("Akaunti yako na taarifa zako zimefutwa."); return redirect(url_for("index"))

# ---------- reminders (Vercel Cron) ----------
def send_email(to, subject, html):
    if not E("RESEND_API_KEY"): return
    requests.post("https://api.resend.com/emails", headers={"Authorization": "Bearer " + E("RESEND_API_KEY")}, timeout=15,
        json={"from": E("MAIL_FROM", "NUYAS <onboarding@resend.dev>"), "to": [to], "subject": subject, "html": html})

def send_whatsapp(phone, text):
    if not (E("WA_TOKEN") and E("WA_PHONE_ID")): return
    requests.post(f"https://graph.facebook.com/v20.0/{E('WA_PHONE_ID')}/messages", headers={"Authorization": "Bearer " + E("WA_TOKEN")}, timeout=15,
        json={"messaging_product": "whatsapp", "to": phone, "type": "template",
              "template": {"name": E("WA_TEMPLATE", "adhkar_reminder"), "language": {"code": "sw"},
                           "components": [{"type": "body", "parameters": [{"type": "text", "text": text[:900]}]}]}})

@app.route("/cron/<kind>")
def cron(kind):
    if kind not in ("asubuhi", "jioni") or request.headers.get("Authorization") != "Bearer " + E("CRON_SECRET", "x"): abort(401)
    items = db.table("adhkar").select("*").eq("type", kind).order("id").execute().data
    if not items: return "no content"
    a = items[NOW().timetuple().tm_yday % len(items)]
    us = db.table("users").select("email,name,phone,notify_email,notify_whatsapp").or_("notify_email.eq.true,notify_whatsapp.eq.true").execute().data
    sent = 0
    for x in us:
        try:
            if x["notify_email"]:
                send_email(x["email"], f"Adhkar za {kind}", f'<div style="font-family:sans-serif;max-width:520px"><p>Salaam {escape(x["name"])},</p><p style="font-size:26px;direction:rtl;text-align:right">{escape(a["arabic"])}</p><p>{escape(a["swahili"])}</p><p><a href="{SITE}/dashboard">Fungua NUYAS</a></p><p style="color:#777;font-size:12px">Zima ukumbusho kwenye Wasifu.</p></div>')
            if x["notify_whatsapp"] and x["phone"]:
                send_whatsapp(x["phone"], f'{a["arabic"]} - {a["swahili"]}')
            sent += 1
        except Exception: pass
    return f"sent {sent}"

# ---------- admin ----------
@app.route("/admin")
@admin_required
def admin(u):
    pays = db.table("payments").select("*, users(name,email)").order("id", desc=True).limit(15).execute().data
    return render_template("admin.html", pays=pays, cs=db.table("courses").select("id,title").execute().data)

@app.route("/admin/grant", methods=["POST"])
@admin_required
def admin_grant(u):
    r = db.table("users").select("id").eq("email", request.form["email"].strip().lower()).execute().data
    if r: activate(r[0]["id"], int(request.form.get("days") or 30)); flash("Uanachama umetolewa.")
    else: flash("Mtumiaji hajapatikana.")
    return redirect(url_for("admin"))

@app.route("/admin/add/<kind>", methods=["POST"])
@admin_required
def admin_add(u, kind):
    f = request.form
    if kind == "adhkar": db.table("adhkar").insert({"type": f["type"], "arabic": f["arabic"], "swahili": f["swahili"], "source": f.get("source")}).execute()
    elif kind == "course": db.table("courses").insert({"title": f["title"], "description": f.get("description")}).execute()
    elif kind == "lesson": db.table("lessons").insert({"course_id": int(f["course_id"]), "title": f["title"], "body": f.get("body"),
        "audio_url": f.get("audio_url") or None, "position": int(f.get("position") or 1), "is_free": f.get("is_free") == "on"}).execute()
    else: abort(400)
    flash("Imeongezwa."); return redirect(url_for("admin"))



# ---------- quran (free) ----------
@app.route("/quran")
@login_required
def quran(u):
    try:
        r = requests.get("https://api.alquran.cloud/v1/surah", timeout=10).json()
        surahs = r.get("data") or []
    except Exception:
        surahs = []
        flash("Imeshindikana kupakia orodha ya surah. Jaribu tena.")
    return render_template("quran.html", surahs=surahs)

@app.route("/quran/<int:n>")
@login_required
def surah(u, n):
    if n < 1 or n > 114:
        abort(404)
    try:
        ar = requests.get(f"https://api.alquran.cloud/v1/surah/{n}/quran-uthmani", timeout=12).json()["data"]
        # Swahili translation
        sw_map = {}
        for ed in ("sw.abubakar", "sw.barwani"):
            try:
                tr = requests.get(f"https://api.alquran.cloud/v1/surah/{n}/{ed}", timeout=10).json()["data"]
                sw_map = {a["numberInSurah"]: a["text"] for a in tr["ayahs"]}
                if sw_map:
                    break
            except Exception:
                continue
        # English fallback / secondary
        en_map = {}
        try:
            tr = requests.get(f"https://api.alquran.cloud/v1/surah/{n}/en.sahih", timeout=10).json()["data"]
            en_map = {a["numberInSurah"]: a["text"] for a in tr["ayahs"]}
        except Exception:
            pass
        ayahs = []
        for a in ar["ayahs"]:
            sw = sw_map.get(a["numberInSurah"], "")
            en = en_map.get(a["numberInSurah"], "")
            ayahs.append({
                "number": a["number"],
                "numberInSurah": a["numberInSurah"],
                "text": a["text"],
                "translation": sw or en,
                "translation_en": en if sw else "",
            })
        surah_meta = {
            "number": ar["number"],
            "name": ar["name"],
            "englishName": ar["englishName"],
            "englishNameTranslation": ar["englishNameTranslation"],
            "numberOfAyahs": ar["numberOfAyahs"],
            "revelationType": ar["revelationType"],
        }
    except Exception:
        flash("Imeshindikana kupakia surah. Jaribu tena.")
        return redirect(url_for("quran"))
    return render_template("surah.html", surah=surah_meta, ayahs=ayahs)


# ---------- PWA ----------
@app.route("/sw.js")
def sw():
    r = send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
    r.headers["Cache-Control"] = "no-cache"; r.headers["Service-Worker-Allowed"] = "/"; return r

@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")

@app.route("/offline")
def offline():
    return render_template("offline.html")
