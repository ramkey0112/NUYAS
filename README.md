# NUYAS (Flask + Supabase + Vercel)
Adhkar, nyakati za swala, kozi na jamii kwa Kiswahili. Inasakinishwa kwenye simu kama app (PWA).
Matoleo: Flask 3.1.3, Werkzeug 3.1.8, supabase 2.33.0, requests 2.33.1, Python 3.12.

## 1. Supabase
Tengeneza project. SQL Editor: endesha `schema.sql`, kisha `migration_v2.sql`.
Project Settings > API: nakili **Project URL** na **service_role / secret key** (siri, isiende GitHub).

## 2. GitHub
`git init && git add . && git commit -m "NUYAS" && git branch -M main`
`git remote add origin https://github.com/JINA/nuyas.git && git push -u origin main`

## 3. Vercel
Add New > Project > chagua repo. Kabla ya Deploy, weka Environment Variables (angalia `.env.example`):
`SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ADMIN_EMAILS`, `PRICE_TZS`, `PAY_NUMBER`, `PAY_NAME`, `SITE_URL`, `CRON_SECRET`.
Hiari: `CLICKPESA_*`, `RESEND_API_KEY`, `MAIL_FROM`, `WA_TOKEN`, `WA_PHONE_ID`, `WA_TEMPLATE`.
Baada ya deploy ya kwanza, weka `SITE_URL` halisi kisha Redeploy. Jisajili kwa barua pepe ya `ADMIN_EMAILS` ili uwe admin.

## 4. ClickPesa
Weka `CLICKPESA_CLIENT_ID` na `CLICKPESA_API_KEY`. Webhook (hiari): `https://SITE/webhooks/clickpesa`.

## 5. Ukumbusho (Vercel Cron)
`vercel.json`: 06:00 na 18:00 EAT. Weka `CRON_SECRET`. Email kupitia Resend; WhatsApp kupitia Meta Cloud API (template `adhkar_reminder`, lugha sw, kigezo {{1}}).

## 6. Kusakinisha kwenye simu (PWA)
Fungua tovuti kwa Chrome (Android): menyu > "Install app". Safari (iPhone): Share > "Add to Home Screen". Ikoni iko `static/`.

## Kabla ya kuzindua
Sheria na masharti, faragha, na maudhui ya adhkar/kozi vihakikiwe na mwanasheria na mwalimu.
