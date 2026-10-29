import os, uuid, re, datetime as dt, requests
from functools import wraps
from flask import Flask, send_from_directory, render_template, request, redirect, url_for, session, flash, abort, jsonify
from markupsafe import Markup, escape
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client
try:
    from pywebpush import webpush, WebPushException
except Exception:
    webpush = None
    WebPushException = Exception
import json

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
# Permanent session — lasts 90 days even if browser is closed
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
    PERMANENT_SESSION_LIFETIME=dt.timedelta(days=90),
    SESSION_REFRESH_EACH_REQUEST=True,
)
db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
E = os.environ.get
PRICE = int(E("PRICE_TZS", 3000))
SITE = E("SITE_URL", "")
PAY_NUMBER = E("PAY_NUMBER", "")
PAY_NAME = E("PAY_NAME", "")
ADMINS = [x.strip().lower() for x in E("ADMIN_EMAILS", "").split(",") if x.strip()]
VAPID_PUBLIC = E("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE = E("VAPID_PRIVATE_KEY", "")
VAPID_EMAIL = E("VAPID_CLAIM_EMAIL", "mailto:admin@nuyas.app")
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
 "help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
 "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
 "edit": '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
 "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
}
@app.template_global()
def icon(n, s=20):
    return Markup(f'<svg class="ic" width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_I.get(n, "")}</svg>')

def safe_html(html):
    """Allow basic formatting tags from the rich editor."""
    if not html:
        return Markup("")
    # Minimal allowlist; Quill outputs p, strong, em, u, ol, ul, li, br, a, h1-h3
    return Markup(html)

# ---------- auth ----------
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    r = db.table("users").select("*").eq("id", uid).limit(1).execute().data
    if not r:
        session.clear()
        return None
    u = r[0]
    until = parse(u.get("premium_until"))
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
        if not u["is_admin"]:
            abort(403)
        return f(u, *a, **k)
    return login_required(w)

@app.context_processor
def inject():
    return {"user": current_user(), "PRICE": PRICE, "PAY_NUMBER": PAY_NUMBER, "PAY_NAME": PAY_NAME, "VAPID_PUBLIC": VAPID_PUBLIC}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        email = f["email"].strip().lower()
        name = f["name"].strip()
        if not name or "@" not in email or len(f["password"]) < 6:
            flash("Jaza taarifa zote. Nenosiri liwe na herufi 6 au zaidi.")
        elif not f.get("terms"):
            flash("Kubali Masharti na Sera ya Faragha ili uendelee.")
        elif db.table("users").select("id").eq("email", email).execute().data:
            flash("Barua pepe hii tayari imesajiliwa. Ingia badala yake.")
        else:
            r = db.table("users").insert({
                "name": name,
                "email": email,
                "city": f.get("city", "Mwanza").strip() or "Mwanza",
                "password_hash": generate_password_hash(f["password"]),
            }).execute().data[0]
            session.permanent = True
            session["uid"] = r["id"]
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        r = db.table("users").select("*").eq("email", request.form["email"].strip().lower()).limit(1).execute().data
        if r and check_password_hash(r[0]["password_hash"], request.form["password"]):
            session.permanent = True
            session["uid"] = r[0]["id"]
            return redirect(url_for("dashboard"))
        flash("Barua pepe au nenosiri si sahihi.")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/privacy")
def privacy():
    return render_template("legal.html", page="privacy")

@app.route("/terms")
def terms():
    return render_template("legal.html", page="terms")

# ---------- content ----------
def prayer_times(city):
    try:
        t = requests.get(
            "https://api.aladhan.com/v1/timingsByCity",
            params={"city": city, "country": "Tanzania", "method": 2},
            timeout=5,
        ).json()["data"]["timings"]
        return {k: t[k] for k in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")}
    except Exception:
        return None

@app.route("/dashboard")
@login_required
def dashboard(u):
    kind = "asubuhi" if (NOW() + dt.timedelta(hours=3)).hour < 14 else "jioni"
    items = db.table("adhkar").select("*").eq("type", kind).order("id").execute().data
    try:
        banners = db.table("banners").select("*").eq("active", True).order("position").limit(5).execute().data
    except Exception:
        banners = []
    return render_template("dashboard.html", u=u, kind=kind, items=items, times=prayer_times(u["city"]), banners=banners)

@app.route("/courses")
@login_required
def courses(u):
    q = (request.args.get("q") or "").strip()
    # Newest courses first
    rows = db.table("courses").select("*").order("id", desc=True).execute().data
    if q:
        ql = q.lower()
        rows = [c for c in rows if ql in (c.get("title") or "").lower() or ql in (c.get("description") or "").lower()]
    return render_template("courses.html", cs=rows, q=q)

@app.route("/course/<int:cid>")
@login_required
def course(u, cid):
    c = db.table("courses").select("*").eq("id", cid).limit(1).execute().data
    if not c:
        abort(404)
    ls = db.table("lessons").select("id,title,is_free,position").eq("course_id", cid).order("position").execute().data
    return render_template("course.html", c=c[0], ls=ls)

@app.route("/lesson/<int:lid>")
@login_required
def lesson(u, lid):
    r = db.table("lessons").select("*").eq("id", lid).limit(1).execute().data
    if not r:
        abort(404)
    if not (r[0]["is_free"] or u["premium"] or u["is_admin"]):
        flash("Somo hili ni la wanachama. Lipia ili kuendelea.")
        return redirect(url_for("pay"))
    return render_template("lesson.html", l=r[0])

# ---------- ClickPesa + Manual payments ----------
CP = "https://api.clickpesa.com/third-parties"

def cp_headers():
    """Generate ClickPesa JWT token (valid ~1 hour)."""
    r = requests.post(
        f"{CP}/generate-token",
        headers={"client-id": E("CLICKPESA_CLIENT_ID", ""), "api-key": E("CLICKPESA_API_KEY", "")},
        timeout=15,
    )
    r.raise_for_status()
    t = r.json().get("token") or ""
    # Token from API already includes "Bearer " prefix in some responses
    if t and not t.lower().startswith("bearer "):
        t = "Bearer " + t
    return {"Authorization": t, "Content-Type": "application/json"}

def activate(uid, days=30):
    usr = db.table("users").select("premium_until").eq("id", uid).execute().data[0]
    start = max(NOW(), parse(usr["premium_until"]) or NOW())
    db.table("users").update({"premium_until": (start + dt.timedelta(days=days)).isoformat()}).eq("id", uid).execute()

def approve_payment(p, payment_ref=None):
    """Mark payment approved and activate membership (idempotent)."""
    if p["status"] == "approved":
        return "approved"
    upd = {"status": "approved"}
    if payment_ref:
        upd["reference"] = payment_ref
    db.table("payments").update(upd).eq("id", p["id"]).execute()
    activate(p["user_id"])
    return "approved"

def reject_payment(p, message=None):
    if p["status"] != "pending":
        return p["status"]
    upd = {"status": "rejected"}
    if message:
        upd["reference"] = (message or "")[:80]
    db.table("payments").update(upd).eq("id", p["id"]).execute()
    return "rejected"

def check_payment(order):
    """Query ClickPesa API for status (polling fallback). Auto-activates on success."""
    p = db.table("payments").select("*").eq("order_reference", order).limit(1).execute().data
    if not p:
        return None
    p = p[0]
    if p["status"] != "pending":
        return p["status"]
    # Manual payments are approved by admin only
    if (p.get("method") or "").lower() == "manual":
        return "pending"
    try:
        d = requests.get(f"{CP}/payments/{order}", headers=cp_headers(), timeout=15).json()
        d = d[0] if isinstance(d, list) and d else d
        st = (d or {}).get("status", "")
        if st in ("SUCCESS", "SETTLED"):
            return approve_payment(p, (d or {}).get("paymentReference"))
        if st == "FAILED":
            return reject_payment(p, (d or {}).get("message"))
    except Exception:
        pass
    return "pending"

@app.route("/pay", methods=["GET", "POST"])
@login_required
def pay(u):
    if request.method == "POST":
        method = request.form.get("method", "clickpesa")
        if method == "manual":
            ref = (request.form.get("reference") or "").strip()[:80]
            phone = re.sub(r"\D", "", request.form.get("phone", ""))
            if phone.startswith("0"):
                phone = "255" + phone[1:]
            if not ref:
                flash("Weka namba ya kumbukumbu (reference) ya malipo.")
            else:
                order = "MN" + uuid.uuid4().hex[:16]
                db.table("payments").insert({
                    "user_id": u["id"],
                    "amount": PRICE,
                    "method": "Manual",
                    "order_reference": order,
                    "reference": ref,
                    "phone": phone or None,
                    "status": "pending",
                }).execute()
                flash("Ombi lako limetumwa. Admin atathibitisha hivi karibuni.")
                return redirect(url_for("pay"))
        else:
            n = re.sub(r"\D", "", request.form.get("phone", ""))
            if n.startswith("0"):
                n = "255" + n[1:]
            if not re.fullmatch(r"255\d{9}", n):
                flash("Weka namba sahihi ya simu, mfano 0712345678.")
            else:
                # orderReference max 20 chars (ClickPesa limit)
                order = ("NY" + uuid.uuid4().hex)[:20]
                ok = False
                err_msg = None
                try:
                    r = requests.post(
                        f"{CP}/payments/initiate-ussd-push-request",
                        headers=cp_headers(),
                        timeout=20,
                        json={
                            "amount": str(PRICE),
                            "currency": "TZS",
                            "orderReference": order,
                            "phoneNumber": n,
                        },
                    )
                    ok = r.status_code in (200, 201)
                    if not ok:
                        try:
                            err_msg = r.json().get("message") or r.text[:120]
                        except Exception:
                            err_msg = r.text[:120]
                except Exception as e:
                    err_msg = str(e)[:120]
                if ok:
                    db.table("payments").insert({
                        "user_id": u["id"],
                        "amount": PRICE,
                        "method": "ClickPesa",
                        "order_reference": order,
                        "phone": n,
                        "status": "pending",
                    }).execute()
                    return redirect(url_for("pay", ref=order))
                flash("Imeshindwa kutuma ombi la malipo. " + (err_msg or "Jaribu tena au tumia malipo ya mkono."))
    mine = db.table("payments").select("*").eq("user_id", u["id"]).order("id", desc=True).limit(8).execute().data
    return render_template("pay.html", mine=mine, ref=request.args.get("ref"))

@app.route("/pay/status/<order>")
@login_required
def pay_status(u, order):
    p = db.table("payments").select("user_id,status").eq("order_reference", order).limit(1).execute().data
    if not p or p[0]["user_id"] != u["id"]:
        abort(404)
    if p[0]["status"] != "pending":
        return jsonify(status=p[0]["status"])
    try:
        return jsonify(status=check_payment(order))
    except Exception:
        return jsonify(status="pending")

@app.route("/webhooks/clickpesa", methods=["POST"])
def cp_webhook():
    """
    ClickPesa Application Webhook.
    Configure in Dashboard → Settings → Developers → Application → Webhooks:
      PAYMENT RECEIVED  →  https://YOUR_DOMAIN/webhooks/clickpesa
      PAYMENT FAILED    →  https://YOUR_DOMAIN/webhooks/clickpesa
    """
    j = request.get_json(silent=True) or {}
    event = (j.get("event") or "").upper().strip()
    data = j.get("data") if isinstance(j.get("data"), dict) else j
    order = (data or {}).get("orderReference") or j.get("orderReference")
    status = ((data or {}).get("status") or "").upper()
    payment_ref = (data or {}).get("paymentReference")
    message = (data or {}).get("message")

    if not order:
        return jsonify(ok=True, note="no orderReference"), 200

    p = db.table("payments").select("*").eq("order_reference", str(order)).limit(1).execute().data
    if not p:
        # Unknown order — acknowledge so ClickPesa does not retry forever
        return jsonify(ok=True, note="unknown order"), 200
    p = p[0]

    # Already finalized
    if p["status"] in ("approved", "rejected"):
        return jsonify(ok=True, status=p["status"]), 200

    # Prefer event name; fall back to status field
    success = event in ("PAYMENT RECEIVED", "PAYMENT.RECEIVED") or status in ("SUCCESS", "SETTLED")
    failed = event in ("PAYMENT FAILED", "PAYMENT.FAILED") or status == "FAILED"

    if success:
        approve_payment(p, payment_ref)
        return jsonify(ok=True, status="approved"), 200
    if failed:
        reject_payment(p, message)
        return jsonify(ok=True, status="rejected"), 200

    # Unknown intermediate status — keep pending, optionally re-query
    try:
        check_payment(str(order))
    except Exception:
        pass
    return jsonify(ok=True, status="pending"), 200

# ---------- community ----------
def fmt(m):
    return {
        "id": m["id"],
        "uid": m["user_id"],
        "name": (m.get("users") or {}).get("name", "Mtumiaji"),
        "body": "Ujumbe huu umefutwa." if m["deleted"] else m["body"],
        "deleted": m["deleted"],
        "reply_name": m.get("reply_name"),
        "reply_body": m.get("reply_body"),
        "at": m["created_at"],
    }

@app.route("/community")
@login_required
def community(u):
    return render_template("community.html")

@app.route("/community/api")
@login_required
def community_api(u):
    after = request.args.get("after", type=int, default=0)
    q = db.table("messages").select("*, users(name)")
    rows = (
        q.gt("id", after).order("id").limit(100).execute().data
        if after
        else list(reversed(q.order("id", desc=True).limit(60).execute().data))
    )
    return jsonify([fmt(m) for m in rows])

@app.route("/community/send", methods=["POST"])
@login_required
def community_send(u):
    j = request.get_json(silent=True) or {}
    body = (j.get("body") or "").strip()[:500]
    if not body:
        abort(400)
    row = {"user_id": u["id"], "body": body}
    if j.get("reply_to"):
        p = db.table("messages").select("body,deleted,users(name)").eq("id", int(j["reply_to"])).limit(1).execute().data
        if p:
            row.update(
                reply_to=int(j["reply_to"]),
                reply_name=p[0]["users"]["name"],
                reply_body=("" if p[0]["deleted"] else p[0]["body"][:120]),
            )
    db.table("messages").insert(row).execute()
    return jsonify(ok=True)

@app.route("/community/delete/<int:mid>", methods=["POST"])
@login_required
def community_delete(u, mid):
    m = db.table("messages").select("user_id").eq("id", mid).limit(1).execute().data
    if not m or not (m[0]["user_id"] == u["id"] or u["is_admin"]):
        abort(403)
    db.table("messages").update({"deleted": True}).eq("id", mid).execute()
    return jsonify(ok=True)

# ---------- profile ----------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile(u):
    if request.method == "POST":
        f = request.form
        ph = re.sub(r"\D", "", f.get("phone", ""))
        if ph.startswith("0"):
            ph = "255" + ph[1:]
        db.table("users").update({
            "name": f["name"].strip() or u["name"],
            "city": f["city"].strip() or "Mwanza",
            "bio": f.get("bio", "")[:200],
            "phone": ph or None,
            "notify_email": bool(f.get("notify_email")),
            "notify_whatsapp": bool(f.get("notify_whatsapp") and ph),
        }).eq("id", u["id"]).execute()
        flash("Wasifu umehifadhiwa.")
        return redirect(url_for("profile"))
    return render_template("profile.html", u=u)

@app.route("/profile/password", methods=["POST"])
@login_required
def change_password(u):
    f = request.form
    if not check_password_hash(u["password_hash"], f["old"]):
        flash("Nenosiri la sasa si sahihi.")
    elif len(f["new"]) < 6:
        flash("Nenosiri jipya liwe na herufi 6 au zaidi.")
    else:
        db.table("users").update({"password_hash": generate_password_hash(f["new"])}).eq("id", u["id"]).execute()
        flash("Nenosiri limebadilishwa.")
    return redirect(url_for("profile"))

@app.route("/profile/delete", methods=["POST"])
@login_required
def delete_account(u):
    if not check_password_hash(u["password_hash"], request.form["password"]) or request.form.get("confirm", "").strip().upper() != "FUTA":
        flash("Haikufutwa. Andika FUTA na nenosiri sahihi.")
        return redirect(url_for("profile"))
    db.table("users").delete().eq("id", u["id"]).execute()
    session.clear()
    flash("Akaunti yako na taarifa zako zimefutwa.")
    return redirect(url_for("index"))

# ---------- reminders (Vercel Cron) ----------
def send_email(to, subject, html):
    if not E("RESEND_API_KEY"):
        return
    requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": "Bearer " + E("RESEND_API_KEY")},
        timeout=15,
        json={"from": E("MAIL_FROM", "NUYAS <onboarding@resend.dev>"), "to": [to], "subject": subject, "html": html},
    )

def send_whatsapp(phone, text):
    if not (E("WA_TOKEN") and E("WA_PHONE_ID")):
        return
    requests.post(
        f"https://graph.facebook.com/v20.0/{E('WA_PHONE_ID')}/messages",
        headers={"Authorization": "Bearer " + E("WA_TOKEN")},
        timeout=15,
        json={
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": E("WA_TEMPLATE", "adhkar_reminder"),
                "language": {"code": "sw"},
                "components": [{"type": "body", "parameters": [{"type": "text", "text": text[:900]}]}],
            },
        },
    )

@app.route("/cron/<kind>")
def cron(kind):
    if kind not in ("asubuhi", "jioni") or request.headers.get("Authorization") != "Bearer " + E("CRON_SECRET", "x"):
        abort(401)
    items = db.table("adhkar").select("*").eq("type", kind).order("id").execute().data
    if not items:
        return "no content"
    a = items[NOW().timetuple().tm_yday % len(items)]
    us = db.table("users").select("email,name,phone,notify_email,notify_whatsapp").or_("notify_email.eq.true,notify_whatsapp.eq.true").execute().data
    sent = 0
    for x in us:
        try:
            if x["notify_email"]:
                send_email(
                    x["email"],
                    f"Adhkar za {kind}",
                    f'<div style="font-family:sans-serif;max-width:520px"><p>Salaam {escape(x["name"])},</p><p style="font-size:26px;direction:rtl;text-align:right">{escape(a["arabic"])}</p><p>{escape(a["swahili"])}</p><p><a href="{SITE}/dashboard">Fungua NUYAS</a></p><p style="color:#777;font-size:12px">Zima ukumbusho kwenye Wasifu.</p></div>',
                )
            if x["notify_whatsapp"] and x["phone"]:
                send_whatsapp(x["phone"], f'{a["arabic"]} - {a["swahili"]}')
            sent += 1
        except Exception:
            pass
    return f"sent {sent}"

# ---------- admin ----------
@app.route("/admin")
@admin_required
def admin(u):
    pays = db.table("payments").select("*, users(name,email)").order("id", desc=True).limit(30).execute().data
    try:
        banners = db.table("banners").select("*").order("position").limit(30).execute().data
    except Exception:
        banners = []
    try:
        qs = db.table("questions").select("id,body,created_at,active,users(name)").order("id", desc=True).limit(20).execute().data
    except Exception:
        qs = []
    courses = db.table("courses").select("id,title,description").order("id", desc=True).execute().data
    lessons = db.table("lessons").select("id,course_id,title,position,is_free").order("id", desc=True).execute().data
    adhkar = db.table("adhkar").select("*").order("id", desc=True).limit(50).execute().data
    try:
        notifs = db.table("notifications").select("*").order("id", desc=True).limit(40).execute().data or []
    except Exception:
        notifs = []
    return render_template(
        "admin.html",
        pays=pays,
        cs=courses,
        lessons=lessons,
        banners=banners,
        qs=qs,
        adhkar=adhkar,
        notifs=notifs,
    )

@app.route("/admin/grant", methods=["POST"])
@admin_required
def admin_grant(u):
    r = db.table("users").select("id").eq("email", request.form["email"].strip().lower()).execute().data
    if r:
        activate(r[0]["id"], int(request.form.get("days") or 30))
        flash("Uanachama umetolewa.")
    else:
        flash("Mtumiaji hajapatikana.")
    return redirect(url_for("admin") + "#malipo")

@app.route("/admin/payment/<int:pid>/<action>", methods=["POST"])
@admin_required
def admin_payment_action(u, pid, action):
    if action not in ("approve", "reject"):
        abort(400)
    p = db.table("payments").select("*").eq("id", pid).limit(1).execute().data
    if not p:
        abort(404)
    p = p[0]
    if p["status"] != "pending":
        flash("Malipo haya yameshahukumiwa.")
        return redirect(url_for("admin") + "#malipo")
    if action == "approve":
        db.table("payments").update({"status": "approved"}).eq("id", pid).execute()
        activate(p["user_id"])
        flash("Malipo yamethibitishwa na uanachama umewekwa.")
    else:
        db.table("payments").update({"status": "rejected"}).eq("id", pid).execute()
        flash("Malipo yamekataliwa.")
    return redirect(url_for("admin") + "#malipo")

@app.route("/admin/add/<kind>", methods=["POST"])
@admin_required
def admin_add(u, kind):
    f = request.form
    if kind == "adhkar":
        db.table("adhkar").insert({
            "type": f["type"],
            "arabic": f["arabic"],
            "swahili": f["swahili"],
            "source": f.get("source"),
        }).execute()
        try:
            broadcast_push(
                "Adhkar mpya",
                f'{f["arabic"][:80]} — {(f.get("swahili") or "")[:120]}',
                url="/dashboard",
                kind="adhkar",
                created_by=u["id"],
            )
        except Exception:
            pass
        flash("Adhkar imeongezwa. Arifa imetumwa.")
        return redirect(url_for("admin") + "#adhkar")
    elif kind == "course":
        db.table("courses").insert({"title": f["title"], "description": f.get("description")}).execute()
        flash("Kozi imeongezwa.")
        return redirect(url_for("admin") + "#masomo")
    elif kind == "lesson":
        body = f.get("body") or ""
        cid = int(f["course_id"])
        ins = db.table("lessons").insert({
            "course_id": cid,
            "title": f["title"],
            "body": body,
            "audio_url": f.get("audio_url") or None,
            "position": int(f.get("position") or 1),
            "is_free": f.get("is_free") == "on",
        }).execute().data
        lid = ins[0]["id"] if ins else None
        try:
            broadcast_push(
                "Somo jipya",
                f["title"],
                url=f"/lesson/{lid}" if lid else "/courses",
                kind="lesson",
                created_by=u["id"],
            )
        except Exception:
            pass
        flash("Somo limeongezwa. Arifa imetumwa.")
        return redirect(url_for("admin_course", cid=cid))
    else:
        abort(400)
    return redirect(url_for("admin") + "#masomo")

@app.route("/admin/course/<int:cid>")
@admin_required
def admin_course(u, cid):
    c = db.table("courses").select("*").eq("id", cid).limit(1).execute().data
    if not c:
        abort(404)
    # Newest lessons first in admin view; position still used for learner order
    ls = db.table("lessons").select("*").eq("course_id", cid).order("id", desc=True).execute().data
    return render_template("admin_course.html", c=c[0], ls=ls)

@app.route("/admin/lesson/<int:lid>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_lesson(u, lid):
    r = db.table("lessons").select("*").eq("id", lid).limit(1).execute().data
    if not r:
        abort(404)
    lesson = r[0]
    if request.method == "POST":
        f = request.form
        db.table("lessons").update({
            "title": f["title"].strip(),
            "body": f.get("body") or "",
            "audio_url": f.get("audio_url") or None,
            "position": int(f.get("position") or 1),
            "is_free": f.get("is_free") == "on",
            "course_id": int(f["course_id"]),
        }).eq("id", lid).execute()
        flash("Somo limesasishwa.")
        return redirect(url_for("admin_course", cid=int(f["course_id"])))
    cs = db.table("courses").select("id,title").order("id").execute().data
    return render_template("admin_edit_lesson.html", lesson=lesson, cs=cs)

@app.route("/admin/lesson/<int:lid>/delete", methods=["POST"])
@admin_required
def admin_delete_lesson(u, lid):
    r = db.table("lessons").select("course_id").eq("id", lid).limit(1).execute().data
    cid = r[0]["course_id"] if r else None
    db.table("lessons").delete().eq("id", lid).execute()
    flash("Somo limefutwa.")
    if cid:
        return redirect(url_for("admin_course", cid=cid))
    return redirect(url_for("admin") + "#masomo")

@app.route("/admin/course/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_delete_course(u, cid):
    db.table("courses").delete().eq("id", cid).execute()
    flash("Kozi imefutwa (pamoja na masomo yake).")
    return redirect(url_for("admin") + "#masomo")

@app.route("/admin/adhkar/<int:aid>/delete", methods=["POST"])
@admin_required
def admin_delete_adhkar(u, aid):
    db.table("adhkar").delete().eq("id", aid).execute()
    flash("Adhkar imefutwa.")
    return redirect(url_for("admin") + "#adhkar")

@app.route("/admin/question/<int:qid>/toggle", methods=["POST"])
@admin_required
def admin_question_toggle(u, qid):
    r = db.table("questions").select("active").eq("id", qid).limit(1).execute().data
    if r:
        db.table("questions").update({"active": not r[0]["active"]}).eq("id", qid).execute()
    return redirect(url_for("admin") + "#maswali")

@app.route("/admin/question/<int:qid>/delete", methods=["POST"])
@admin_required
def admin_question_delete(u, qid):
    db.table("questions").delete().eq("id", qid).execute()
    flash("Swali limefutwa.")
    return redirect(url_for("admin") + "#maswali")

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
        sw_map = {}
        try:
            tr = requests.get(f"https://api.alquran.cloud/v1/surah/{n}/sw.barwani", timeout=12).json()["data"]
            sw_map = {a["numberInSurah"]: a["text"] for a in tr["ayahs"]}
        except Exception:
            pass
        ayahs = []
        for a in ar["ayahs"]:
            ayahs.append({
                "number": a["number"],
                "numberInSurah": a["numberInSurah"],
                "text": a["text"],
                "translation": sw_map.get(a["numberInSurah"], ""),
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

# ---------- maswali (Q&A) — users can ask too ----------
@app.route("/maswali")
@login_required
def maswali(u):
    q = (request.args.get("q") or "").strip()
    qs = db.table("questions").select("*, users(name)").eq("active", True).order("id", desc=True).limit(80).execute().data
    if q:
        ql = q.lower()
        qs = [x for x in qs if ql in (x.get("body") or "").lower() or ql in ((x.get("users") or {}).get("name") or "").lower()]
    return render_template("maswali.html", qs=qs, q=q)

@app.route("/maswali/uliza", methods=["POST"])
@login_required
def uliza_swali(u):
    body = (request.form.get("body") or "").strip()[:1000]
    if not body:
        flash("Andika swali lako.")
        return redirect(url_for("maswali"))
    db.table("questions").insert({"user_id": u["id"], "body": body, "active": True}).execute()
    flash("Swali lako limewekwa. Asante!")
    return redirect(url_for("maswali"))

@app.route("/maswali/<int:qid>")
@login_required
def swali(u, qid):
    q = db.table("questions").select("*, users(name)").eq("id", qid).limit(1).execute().data
    if not q:
        abort(404)
    ans = db.table("answers").select("*, users(name)").eq("question_id", qid).eq("deleted", False).order("id").execute().data
    return render_template("swali.html", q=q[0], answers=ans)

@app.route("/maswali/<int:qid>/jibu", methods=["POST"])
@login_required
def jibu_swali(u, qid):
    body = (request.form.get("body") or "").strip()[:800]
    if not body:
        flash("Andika jibu.")
        return redirect(url_for("swali", qid=qid))
    q = db.table("questions").select("id").eq("id", qid).eq("active", True).limit(1).execute().data
    if not q:
        abort(404)
    db.table("answers").insert({"question_id": qid, "user_id": u["id"], "body": body}).execute()
    flash("Jibu limewasilishwa.")
    return redirect(url_for("swali", qid=qid))

@app.route("/admin/swali", methods=["POST"])
@admin_required
def admin_swali(u):
    body = (request.form.get("body") or "").strip()[:1000]
    if body:
        db.table("questions").insert({"user_id": u["id"], "body": body}).execute()
        flash("Swali limewekwa.")
    return redirect(url_for("admin") + "#maswali")

@app.route("/admin/banner", methods=["POST"])
@admin_required
def admin_banner(u):
    f = request.form
    title = (f.get("title") or "").strip()[:120] or None
    link = (f.get("link_url") or "").strip() or None
    pos = int(f.get("position") or 1)
    img = (f.get("image_url") or "").strip()
    file = request.files.get("image")
    if file and file.filename:
        ext = (file.filename.rsplit(".", 1)[-1] or "jpg").lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            flash("Aina ya picha hairuhusiwi. Tumia JPG, PNG au WebP.")
            return redirect(url_for("admin") + "#banner")
        path = f"{uuid.uuid4().hex}.{ext}"
        data = file.read()
        try:
            db.storage.from_("banners").upload(path, data, {"content-type": file.content_type or "image/jpeg", "upsert": "true"})
            img = db.storage.from_("banners").get_public_url(path)
        except Exception:
            try:
                db.storage.create_bucket("banners", options={"public": True})
                db.storage.from_("banners").upload(path, data, {"content-type": file.content_type or "image/jpeg", "upsert": "true"})
                img = db.storage.from_("banners").get_public_url(path)
            except Exception as e2:
                flash(f"Upload imeshindikana: {e2}.")
                return redirect(url_for("admin") + "#banner")
    if not img:
        flash("Weka picha (upload) au URL.")
        return redirect(url_for("admin") + "#banner")
    db.table("banners").insert({
        "title": title,
        "image_url": img,
        "link_url": link,
        "position": pos,
        "active": True,
    }).execute()
    flash("Banner imeongezwa.")
    return redirect(url_for("admin") + "#banner")

@app.route("/admin/banner/toggle/<int:bid>", methods=["POST"])
@admin_required
def admin_banner_toggle(u, bid):
    r = db.table("banners").select("active").eq("id", bid).limit(1).execute().data
    if r:
        db.table("banners").update({"active": not r[0]["active"]}).eq("id", bid).execute()
    return redirect(url_for("admin") + "#banner")

@app.route("/admin/banner/<int:bid>/delete", methods=["POST"])
@admin_required
def admin_banner_delete(u, bid):
    db.table("banners").delete().eq("id", bid).execute()
    flash("Banner imefutwa.")
    return redirect(url_for("admin") + "#banner")


# ---------- Web Push (hata browser ikiwa imefungwa) ----------
def send_web_push(subscription, payload):
    """Send one Web Push notification. Returns True on success."""
    if not webpush or not VAPID_PRIVATE or not VAPID_PUBLIC:
        return False
    try:
        webpush(
            subscription_info={
                "endpoint": subscription["endpoint"],
                "keys": {"p256dh": subscription["p256dh"], "auth": subscription["auth"]},
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=VAPID_PRIVATE,
            vapid_claims={"sub": VAPID_EMAIL},
        )
        return True
    except WebPushException as e:
        # Gone / unsubscribed — delete
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status in (404, 410):
            try:
                db.table("push_subscriptions").delete().eq("endpoint", subscription["endpoint"]).execute()
            except Exception:
                pass
        return False
    except Exception:
        return False

def broadcast_push(title, body, url="/", kind="broadcast", created_by=None):
    """Save notification log and push to all subscribers."""
    try:
        db.table("notifications").insert({
            "title": title[:120],
            "body": body[:500],
            "url": url,
            "kind": kind,
            "created_by": created_by,
        }).execute()
    except Exception:
        pass
    try:
        subs = db.table("push_subscriptions").select("*").execute().data or []
    except Exception:
        subs = []
    payload = {"title": title, "body": body, "url": url, "tag": kind}
    ok = 0
    for s in subs:
        if send_web_push(s, payload):
            ok += 1
    return ok

@app.route("/api/push/subscribe", methods=["POST"])
@login_required
def push_subscribe(u):
    j = request.get_json(silent=True) or {}
    endpoint = (j.get("endpoint") or "").strip()
    keys = j.get("keys") or {}
    p256dh = keys.get("p256dh") or ""
    auth = keys.get("auth") or ""
    if not endpoint or not p256dh or not auth:
        return jsonify(ok=False, error="missing keys"), 400
    try:
        # upsert by endpoint
        existing = db.table("push_subscriptions").select("id").eq("endpoint", endpoint).limit(1).execute().data
        row = {
            "user_id": u["id"],
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": (request.headers.get("User-Agent") or "")[:240],
        }
        if existing:
            db.table("push_subscriptions").update(row).eq("id", existing[0]["id"]).execute()
        else:
            db.table("push_subscriptions").insert(row).execute()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)[:120]), 500

@app.route("/api/push/unsubscribe", methods=["POST"])
@login_required
def push_unsubscribe(u):
    j = request.get_json(silent=True) or {}
    endpoint = (j.get("endpoint") or "").strip()
    if endpoint:
        try:
            db.table("push_subscriptions").delete().eq("endpoint", endpoint).execute()
        except Exception:
            pass
    return jsonify(ok=True)

@app.route("/admin/broadcast", methods=["POST"])
@admin_required
def admin_broadcast(u):
    title = (request.form.get("title") or "").strip()[:120] or "NUYAS"
    raw = request.form.get("body") or ""
    import re as _re
    text = _re.sub(r"<[^>]+>", " ", raw)
    text = _re.sub(r"\s+", " ", text).strip()[:400]
    url = (request.form.get("url") or "/dashboard").strip() or "/dashboard"
    if not text:
        flash("Andika ujumbe.")
        return redirect(url_for("admin") + "#broadcast")
    n = broadcast_push(title, text, url=url, kind="broadcast", created_by=u["id"])
    flash(f"Arifa imetumwa kwa vifaa {n}.")
    return redirect(url_for("admin") + "#broadcast")

@app.route("/notifications")
@login_required
def notifications_page(u):
    try:
        items = db.table("notifications").select("*").order("id", desc=True).limit(80).execute().data or []
    except Exception:
        items = []
    read_ids = set()
    try:
        rows = db.table("notification_reads").select("notification_id").eq("user_id", u["id"]).execute().data or []
        read_ids = {r["notification_id"] for r in rows}
    except Exception:
        pass
    for n in items:
        n["is_read"] = n["id"] in read_ids
    # mark all visible as read
    try:
        for n in items:
            if not n["is_read"]:
                db.table("notification_reads").upsert({
                    "user_id": u["id"],
                    "notification_id": n["id"],
                }).execute()
                n["is_read"] = True
    except Exception:
        pass
    return render_template("notifications.html", items=items)

@app.route("/api/notifications/unread")
@login_required
def notifications_unread(u):
    try:
        all_n = db.table("notifications").select("id").order("id", desc=True).limit(100).execute().data or []
        ids = [x["id"] for x in all_n]
        if not ids:
            return jsonify(count=0)
        reads = db.table("notification_reads").select("notification_id").eq("user_id", u["id"]).in_("notification_id", ids).execute().data or []
        read_ids = {r["notification_id"] for r in reads}
        count = sum(1 for i in ids if i not in read_ids)
        return jsonify(count=count)
    except Exception:
        return jsonify(count=0)

@app.route("/admin/notification/<int:nid>/edit", methods=["GET", "POST"])
@admin_required
def admin_notification_edit(u, nid):
    r = db.table("notifications").select("*").eq("id", nid).limit(1).execute().data
    if not r:
        abort(404)
    n = r[0]
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()[:120]
        body = (request.form.get("body") or "").strip()[:500]
        url = (request.form.get("url") or "/").strip() or "/"
        if not title or not body:
            flash("Jaza kichwa na ujumbe.")
            return redirect(url_for("admin_notification_edit", nid=nid))
        db.table("notifications").update({"title": title, "body": body, "url": url}).eq("id", nid).execute()
        flash("Arifa imesasishwa.")
        return redirect(url_for("admin") + "#broadcast")
    return render_template("admin_notification_edit.html", n=n)

@app.route("/admin/notification/<int:nid>/delete", methods=["POST"])
@admin_required
def admin_notification_delete(u, nid):
    try:
        db.table("notification_reads").delete().eq("notification_id", nid).execute()
    except Exception:
        pass
    db.table("notifications").delete().eq("id", nid).execute()
    flash("Arifa imefutwa.")
    return redirect(url_for("admin") + "#broadcast")

# ---------- PWA ----------
@app.route("/sw.js")
def sw():
    r = send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
    r.headers["Cache-Control"] = "no-cache"
    r.headers["Service-Worker-Allowed"] = "/"
    return r

@app.route("/manifest.webmanifest")
def manifest():
    return send_from_directory(app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")

@app.route("/offline")
def offline():
    return render_template("offline.html")
