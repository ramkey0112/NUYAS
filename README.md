# NUYAS (Flask + Supabase + Vercel)
Qurani, adhkar, nyakati za swala, kozi na jamii kwa Kiswahili. Inasakinishwa kwenye simu kama app (PWA).

Matoleo: Flask 3.1.3, Werkzeug 3.1.8, supabase 2.33.0, requests 2.33.1, Python 3.12.

## Vipengele

### Bure
- **Qurani Tukufu** — soma + sikiliza aya kwa aya (sauti ya Alafasy)
- Adhkar za asubuhi na jioni
- Nyakati za swala (mji wako)
- Tasbih
- Jamii (chati)

### Uanachama (TSh / mwezi)
- Kozi zote kamili
- Masomo ya kina + sauti
- Maudhui mapya mapema

## 1. Supabase
Tengeneza project. SQL Editor: endesha `schema.sql`, kisha `migration_v2.sql`.
Kisha endesha grants:
```sql
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
```
Project Settings > API: nakili **Project URL** na **secret / service_role key**.

## 2. GitHub
Push code kwenye repo yako.

## 3. Vercel
Import repo. Weka Environment Variables (angalia `.env.example`):
`SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ADMIN_EMAILS`, `PRICE_TZS`, `PAY_NUMBER`, `PAY_NAME`, `SITE_URL`, `CRON_SECRET`.
Hiari: `CLICKPESA_*`, `RESEND_API_KEY`, `MAIL_FROM`, `WA_TOKEN`, `WA_PHONE_ID`, `WA_TEMPLATE`.

## 4. PWA
Chrome (Android): menyu > Install app.  
Safari (iPhone): Share > Add to Home Screen.
