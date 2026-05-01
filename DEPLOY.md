# Deploy Guide: Nyx SEO Content Engine

Panduan deploy:
1. **n8n** ke Railway
2. **Web UI Next.js** ke Vercel dengan Basic Auth password protection

---

## Persiapan: Push ke GitHub

```bash
cd G:/NyxContent

git init
git add .
git commit -m "Initial commit"

# Buat repo baru di github.com (kosong, tanpa README)
git remote add origin https://github.com/USERNAME/nyx-seo-engine.git
git branch -M main
git push -u origin main
```

`.gitignore` sudah disiapkan — `.env.local`, `node_modules`, dan file kerja sementara tidak akan ke-push.

---

## Bagian 1: Deploy n8n ke Railway

### Step 1.1 — Buat project Railway

1. Buka https://railway.app → **New Project** → **Deploy from GitHub repo**
2. Pilih repo `nyx-seo-engine`
3. Railway auto-detect `Dockerfile.n8n` dan `railway.toml`

### Step 1.2 — Tambah persistent volume (WAJIB)

Tanpa volume, semua credentials & workflow akan hilang setiap redeploy.

1. Di Railway dashboard, buka service **n8n**
2. Klik tab **Variables** → scroll ke **Volumes**
3. Klik **+ New Volume**:
   - Mount path: `/home/node/.n8n`
   - Size: 1 GB cukup
4. Save

### Step 1.3 — Set environment variables

Di tab **Variables** pada service n8n, tambahkan:

```
WEBHOOK_URL=https://YOUR_RAILWAY_URL
N8N_EDITOR_BASE_URL=https://YOUR_RAILWAY_URL
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=PASSWORD_KUAT_DI_SINI
N8N_ENCRYPTION_KEY=GANTI_DENGAN_RANDOM_32_CHAR
```

**Penting:**
- `YOUR_RAILWAY_URL` = domain Railway tanpa trailing slash (contoh: `https://nyx-seo-engine.up.railway.app`). Bisa pakai `https://${{RAILWAY_PUBLIC_DOMAIN}}` agar otomatis.
- `N8N_ENCRYPTION_KEY` JANGAN diganti setelah set, karena dipakai untuk enkripsi credentials.
- Generate random string: di terminal lokal jalankan `node -e "console.log(require('crypto').randomBytes(16).toString('hex'))"`

### Step 1.4 — Generate domain & redeploy

1. Tab **Settings** → **Networking** → **Generate Domain** (contoh: `nyx-seo-engine.up.railway.app`)
2. Update `WEBHOOK_URL` dan `N8N_EDITOR_BASE_URL` dengan domain tersebut
3. Klik **Deploy** untuk redeploy

### Step 1.5 — Setup credentials di n8n

Buka `https://YOUR_RAILWAY_URL` → login pakai `N8N_BASIC_AUTH_USER` + `N8N_BASIC_AUTH_PASSWORD`. Setup credentials:

**A. Google Sheets OAuth2 API**
- Settings → Credentials → New → cari "Google Sheets OAuth2 API"
- Client ID & Client Secret dari Google Cloud Console
- **OAuth Redirect URL** yang ditampilkan n8n harus ditambahkan ke Google Cloud Console → APIs & Services → Credentials → Authorized redirect URIs
- Klik **Sign in with Google** → authorize

**B. Google Drive OAuth2 API** — sama caranya

**C. SerpAPI** (Header Auth)
- New → Header Auth
- Name: `api_key` (param), Value: SerpAPI key Anda
- Atau pakai HTTP Query Auth: Name `api_key`, Value: key

**D. Firecrawl** (Header Auth)
- Name: `Authorization`
- Value: `Bearer fc-XXX`

> Anthropic & DeepSeek API key tidak perlu disimpan di n8n — dikirim per-request dari UI.

### Step 1.6 — Import workflow

1. Workflows → **Import from File** → upload `SEO-Content-Engine-n8n-workflow.json`
2. Buka workflow → assign credentials yang baru dibuat ke node yang masih ada warning (Google Sheets, Google Drive, SerpAPI, Firecrawl)
3. Update Spreadsheet ID di node **GSheets Get All Clients** dan **GSheets Update Folder ID** dengan ID Google Sheets Anda
4. Toggle **Active** di pojok kanan atas

### Step 1.7 — Test webhook

```bash
curl -X POST https://YOUR_RAILWAY_URL/webhook/seo-content-engine \
  -H "Content-Type: application/json" \
  -d '{"client_name":"Test","keyword":"test","word_count":500,"tone":"profesional","provider":"claude","api_key":"YOUR_CLAUDE_KEY"}'
```

Tunggu 3-5 menit, harus return JSON dengan `google_docs_url`.

---

## Bagian 2: Deploy Web UI ke Vercel

### Step 2.1 — Import ke Vercel

1. Buka https://vercel.com/new
2. Import repo `nyx-seo-engine`
3. **Root Directory** → klik **Edit** → pilih folder `web-ui`
4. Framework Preset: **Next.js** (auto-detect)
5. Build & Output Settings: biarkan default
6. **JANGAN klik Deploy dulu** — set env vars dulu

### Step 2.2 — Set environment variables

Klik **Environment Variables** → tambahkan:

| Name | Value |
|---|---|
| `N8N_WEBHOOK_URL` | `https://YOUR_RAILWAY_URL/webhook/seo-content-engine` |
| `WEBHOOK_SECRET` | Sembarang string, contoh: `nyx-prod-secret-2026` |
| `UI_USERNAME` | Pilih username, contoh: `admin` |
| `UI_PASSWORD` | Pilih password kuat, minimal 16 karakter |

> `UI_USERNAME` dan `UI_PASSWORD` ini yang dipakai untuk masuk ke UI Next.js.

### Step 2.3 — Deploy

Klik **Deploy** → tunggu ~2 menit → dapat URL Vercel (contoh: `nyx-seo-engine.vercel.app`)

### Step 2.4 — Test akses

1. Buka URL Vercel di browser
2. Browser akan minta username + password (Basic Auth popup)
3. Masukkan `UI_USERNAME` dan `UI_PASSWORD`
4. UI muncul

### Step 2.5 — Setup di UI

1. Buka `/settings` → masukkan Claude/DeepSeek API key, Save
2. Buka `/clients` → tambah klien (sesuai yang ada di Google Sheets di n8n)
3. Buka `/` → pilih klien, isi keyword, klik Generate

---

## Bagian 3: Update setelah deploy

### Cara update kode

```bash
# Edit file yang perlu
git add .
git commit -m "deskripsi update"
git push
```

Railway dan Vercel auto-redeploy saat push ke `main`.

### Update workflow n8n (kalau ada perubahan)

Workflow di n8n hanya bisa di-edit via n8n UI atau via API. Tidak otomatis dari git push.

Untuk export workflow ke file:
```bash
curl -H "X-N8N-API-KEY: YOUR_API_KEY" \
  https://YOUR_RAILWAY_URL/api/v1/workflows/WORKFLOW_ID > workflow.json
```

Untuk import ke n8n lain: Workflows → Import from File.

---

## Troubleshooting

### "n8n workflow gagal — response kosong" di UI

- Cek `https://YOUR_RAILWAY_URL/executions` untuk lihat node yang error
- Pastikan workflow Active di n8n

### Browser tidak minta password Basic Auth

- Pastikan `UI_USERNAME` dan `UI_PASSWORD` sudah di-set di Vercel env vars
- Redeploy setelah set env vars (atau klik Settings → Environment Variables → Redeploy)

### Lupa password Basic Auth

- Vercel dashboard → project → Settings → Environment Variables → edit `UI_PASSWORD` → Redeploy
- Untuk clear cached basic auth di browser: tutup browser atau buka Incognito

### n8n credentials hilang setelah redeploy

- Volume belum dimount di `/home/node/.n8n`
- Atau `N8N_ENCRYPTION_KEY` berubah (jangan diganti setelah set!)

### "Authentication failed" saat workflow call Anthropic

- Claude API key di Settings UI tidak valid
- Cek di n8n executions → node Claude Generate Metadata → lihat error detail

---

## Estimasi biaya

| Service | Plan minimal | Biaya/bulan |
|---|---|---|
| Railway | Hobby | $5 (sudah include database & traffic basic) |
| Vercel | Hobby | Free (cukup untuk personal/internal use) |
| Domain custom | optional | ~$10/tahun |

API costs (per artikel):
- Claude Haiku 4.5: ~$0.005 - $0.03
- DeepSeek Chat: ~$0.005 - $0.02
- SerpAPI: ~$0.01
- Firecrawl: sesuai plan
