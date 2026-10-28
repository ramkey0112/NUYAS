# Nuru ya Siku v2 (Flask + Supabase + Vercel)

## 1. Supabase
SQL Editor: endesha `schema.sql`, kisha `migration_v2.sql`. Nakili Project URL na service_role key.

## 2. Mazingira (.env.example -> Vercel Environment Variables)
Zote zinahitajika kwenye Vercel. `SITE_URL` iwe kiungo chako cha Vercel.

## 3. ClickPesa
- Tengeneza Application kwenye ClickPesa dashboard, chukua Client ID na API Key.
- Weka `CLICKPESA_CLIENT_ID` na `CLICKPESA_API_KEY`.
- (Hiari) Webhook URL: `https://SITE/webhooks/clickpesa`. App hujihakiki yenyewe na ClickPesa, hivyo webhook si lazima.
- Malipo: mtumiaji anaweka namba ya simu, anapokea USSD push, ukurasa unachunguza hali hadi ikamilike.

## 4. Ukumbusho (Vercel Cron)
`vercel.json` ina kazi mbili: 06:00 (asubuhi) na 18:00 (jioni) saa za EAT. Weka `CRON_SECRET` (Vercel huituma kama Bearer token).
- Email: fungua akaunti Resend, weka `RESEND_API_KEY` na `MAIL_FROM` (domain yako).
- WhatsApp: Meta WhatsApp Cloud API. Tengeneza template (lugha sw) yenye kigezo kimoja {{1}}, kiitwe `adhkar_reminder`, ipitishwe na Meta, kisha weka `WA_TOKEN` na `WA_PHONE_ID`.
- Vercel Hobby inaruhusu cron za mara moja kwa siku tu (inatosha).

## 5. Deploy
`git init && git add . && git commit -m v2`, push GitHub, import Vercel. Weka `ADMIN_EMAILS`, jisajili kwa barua pepe hiyo.

## Kabla ya kuzindua
Sheria na masharti, faragha, na maudhui ya adhkar/kozi vihakikiwe na mwanasheria na mwalimu.
