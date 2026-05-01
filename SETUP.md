# Setup Guide: SEO Content Engine

## Struktur Project
```
NyxContent/
├── SEO-Content-Engine-n8n-workflow.json  ← Import ke n8n
├── Dockerfile.n8n                         ← Deploy n8n ke Railway
├── railway.toml                           ← Konfigurasi Railway
└── web-ui/                                ← Deploy ke Vercel
    ├── app/
    ├── components/
    └── ...
```

---

## STEP 1: Deploy n8n ke Railway

1. Buka https://railway.app → New Project → Deploy from GitHub
2. Upload/push folder `NyxContent/` ke GitHub repo
3. Railway akan otomatis detect `Dockerfile.n8n`

### Environment Variables di Railway (wajib):
```
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://YOUR_RAILWAY_URL
N8N_EDITOR_BASE_URL=https://YOUR_RAILWAY_URL
DB_TYPE=sqlite
EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
EXECUTIONS_DATA_SAVE_ON_ERROR=all
```

4. Setelah deploy, Railway akan memberikan URL seperti:
   `https://seo-engine-xxx.up.railway.app`

---

## STEP 2: Setup n8n Credentials

Buka n8n di Railway URL, lalu tambahkan credentials:

### A. Google OAuth2 (untuk Sheets + Drive)
- Settings → Credentials → New → Google Sheets OAuth2 API
- Client ID: `<CLIENT_ID kamu dari Google Cloud Console>`
- Client Secret: `<CLIENT_SECRET kamu>`
- Klik Connect → Login Google → Allow

### B. SerpAPI (HTTP Query Auth)
- New → Query Auth
- Parameter name: `api_key`
- Value: `<SERPAPI_KEY kamu>`

### C. Firecrawl (HTTP Header Auth)
- New → Header Auth
- Header name: `Authorization`
- Header value: `Bearer <FIRECRAWL_KEY kamu>`

### D. Anthropic Claude
- TIDAK perlu disimpan sebagai credential di n8n
- API key dikirim per-request dari UI (lihat Settings page)
- Sama untuk DeepSeek

---

## STEP 3: Import Workflow ke n8n

1. n8n → Workflows → Import from file
2. Upload `SEO-Content-Engine-n8n-workflow.json`
3. Buka workflow → node `GSheets Get All Clients`
4. Ganti `YOUR_SPREADSHEET_ID_HERE` dengan ID spreadsheet Google Sheets kamu
5. Assign credentials ke setiap node yang belum terhubung
6. Klik Activate (toggle ON)

### Webhook URL n8n kamu:
```
https://YOUR_RAILWAY_URL/webhook/seo-content-engine
```

---

## STEP 4: Setup Google Sheets

Buat spreadsheet baru, sheet bernama `Clients` dengan header:
```
client_name | website_url | sitemap_url | drive_folder_id | articles_folder_id
```

Isi minimal 1 baris data klien untuk test.

---

## STEP 5: Deploy Web UI ke Vercel

```bash
cd web-ui
cp .env.example .env.local
# Edit .env.local:
# N8N_WEBHOOK_URL=https://YOUR_RAILWAY_URL/webhook/seo-content-engine
# WEBHOOK_SECRET=random-secret-string

npm install
npm run build  # test dulu
```

Deploy ke Vercel:
1. Push folder `web-ui/` ke GitHub
2. Vercel → New Project → Import repo
3. Framework: Next.js (auto-detect)
4. Environment Variables:
   - `N8N_WEBHOOK_URL` = `https://YOUR_RAILWAY_URL/webhook/seo-content-engine`
   - `WEBHOOK_SECRET` = string rahasia (bebas)
5. Deploy!

---

## STEP 6: Test

Buka Vercel URL → isi form:
- Client Name: nama dari Sheets
- Keyword: `jasa seo jakarta`
- Word Count: `1500`
- Tone: `profesional`

Klik Generate → tunggu ~3-5 menit → Google Docs URL akan muncul.

---

## ⚠️ PENTING: Regenerate API Keys

API keys yang digunakan saat setup ini telah terekspos. Segera regenerate:
- Firecrawl: https://firecrawl.dev/account
- SerpAPI: https://serpapi.com/manage-api-key
- Claude: https://console.anthropic.com/settings/keys
- Google OAuth: https://console.cloud.google.com/apis/credentials

Update credentials di n8n setelah regenerate.
