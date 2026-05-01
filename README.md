# Nyx SEO Content Engine

Generator artikel SEO Indonesia berbasis n8n + Next.js. Workflow lengkap dari riset SERP, scrape kompetitor, generate metadata + artikel, refinement editorial pass, scoring rule-based, sampai upload ke Google Docs.

## Fitur

- **Multi-LLM**: switch Claude (Anthropic) atau DeepSeek dari UI
- **Riset otomatis**: SerpAPI top 3 → Firecrawl scrape konten kompetitor
- **Internal links**: Firecrawl crawl website klien, classify TOFU/BOFU, auto-insert dengan anchor natural
- **Refinement pass**: editor LLM polish artikel + auto-split paragraf > 3 baris
- **Rule-based scoring**: Readability / SEO / E-E-A-T dihitung di backend (bukan AI), dengan flags otomatis
- **Output Google Docs**: Publisher Box jadi tabel HTML, isi artikel dengan H2/H3 rapi, sitasi, skor, rekomendasi
- **Basic Auth**: UI dilindungi password (dikonfigurasi via env vars)

## Tech Stack

- **n8n** (workflow engine) — di-deploy ke Railway via Docker
- **Next.js 14** App Router + TailwindCSS — di-deploy ke Vercel
- **Anthropic Claude API** dan **DeepSeek API** sebagai LLM provider
- **SerpAPI** untuk SERP data
- **Firecrawl** untuk web scraping & crawling
- **Google Sheets** untuk database klien
- **Google Drive + Docs** untuk output artikel

## Struktur Project

```
NyxContent/
├── SEO-Content-Engine-n8n-workflow.json   # Workflow n8n (import ke n8n)
├── Dockerfile.n8n                          # Image untuk Railway
├── railway.toml                            # Config deploy Railway
├── DEPLOY.md                               # Panduan deploy lengkap
├── SETUP.md                                # Panduan setup awal
└── web-ui/                                 # Next.js UI (deploy ke Vercel)
    ├── app/
    ├── components/
    ├── lib/
    ├── middleware.ts                       # Basic Auth
    └── ...
```

## Quick Start (Local)

```bash
# 1. Jalankan n8n via Docker
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n

# 2. Import workflow ke n8n di http://localhost:5678
# 3. Setup credentials (Google OAuth, SerpAPI, Firecrawl)
# 4. Aktifkan workflow

# 5. Jalankan Web UI
cd web-ui
cp .env.example .env.local
# Edit .env.local dengan N8N_WEBHOOK_URL=http://localhost:5678/webhook/seo-content-engine
npm install
npm run dev
# Buka http://localhost:3000
```

## Deploy

Lihat [DEPLOY.md](./DEPLOY.md) untuk panduan lengkap deploy ke Railway (n8n) + Vercel (Next.js) dengan Basic Auth.

## License

MIT
