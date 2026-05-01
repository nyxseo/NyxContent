"""Improve article quality: classifier with EN+ID patterns, HTML publisher box table,
better article prompt (extracts real data, deeper outline, forces internal links)."""
import json

WF_PATH = 'G:/NyxContent/workflow_clean.json'
OUT_PATH = 'G:/NyxContent/workflow_put.json'

with open(WF_PATH) as f:
    wf = json.load(f)

# Sanitize sticky notes — corruption protection
for n in wf['nodes']:
    if n.get('type') == 'n8n-nodes-base.stickyNote':
        n['parameters']['content'] = f"## {n['name']}"

# === FIX 1: Code Classify Pages — handle EN+ID URL patterns + better fallback ===
NEW_CLASSIFY = r"""const crawlResult = $json;
const prevData = $('Code Store Crawl ID').item.json;
const keyword = (prevData.keyword || '').toLowerCase();
const keywordSlug = keyword.replace(/\s+/g, '-');

const pages = crawlResult.data || [];

// TOFU = blog/educational | BOFU = money/conversion
// Cover both English and Indonesian URL conventions
const tofuPatterns = ['/blog', '/blogs', '/artikel', '/articles', '/panduan', '/tips', '/cara', '/apa-itu', '/pengertian', '/tutorial', '/news', '/berita', '/insight', '/resource', '/guide', '/learn'];
const bofuPatterns = ['/produk', '/products', '/product', '/layanan', '/services', '/jasa', '/harga', '/pricing', '/paket', '/package', '/beli', '/order', '/hubungi', '/contact', '/checkout', '/buy', '/booking'];

function pageInfo(p) {
  const url = (p.url || p.metadata?.sourceURL || p.metadata?.url || '').toLowerCase();
  const title = p.metadata?.title || p.metadata?.ogTitle || '';
  const description = p.metadata?.description || p.metadata?.ogDescription || '';
  return { url, title, description, content: (p.markdown || '').slice(0, 5000) };
}

function classifyByUrl(url) {
  for (const p of bofuPatterns) if (url.includes(p)) return 'BOFU';
  for (const p of tofuPatterns) if (url.includes(p)) return 'TOFU';
  return null;
}

function classifyByContent(info) {
  // Money keywords in title/description suggest BOFU
  const text = (info.title + ' ' + info.description).toLowerCase();
  const moneyTerms = ['harga', 'price', 'paket', 'package', 'beli', 'buy', 'order', 'pesan', 'jasa', 'services', 'service', 'product', 'produk', 'kontak', 'contact', 'hubungi'];
  const eduTerms = ['cara', 'tips', 'panduan', 'guide', 'tutorial', 'apa itu', 'what is', 'kenapa', 'mengapa', 'why', 'how to', 'bagaimana'];
  if (moneyTerms.some(t => text.includes(t))) return 'BOFU';
  if (eduTerms.some(t => text.includes(t))) return 'TOFU';
  return null;
}

function relevanceScore(info) {
  let score = 0;
  if (info.title.toLowerCase().includes(keyword)) score += 5;
  if (info.url.includes(keywordSlug)) score += 3;
  if (info.description.toLowerCase().includes(keyword)) score += 2;
  // Match individual keyword terms
  const terms = keyword.split(/\s+/).filter(t => t.length > 2);
  for (const t of terms) {
    if (info.title.toLowerCase().includes(t)) score += 1;
    if (info.content.toLowerCase().includes(t)) score += 0.5;
  }
  return score;
}

function deriveAnchor(info, fallback) {
  const t = (info.title || '').replace(/\s*\|\s*.*$/, '').replace(/\s*-\s*.*$/, '').trim();
  return t || fallback || keyword;
}

const tofu = [], bofu = [];
const homePageUrl = (prevData.website_url || '').replace(/\/$/, '');

for (const p of pages) {
  const info = pageInfo(p);
  if (!info.url) continue;
  // Skip homepage and irrelevant pages
  if (info.url === homePageUrl + '/' || info.url === homePageUrl) continue;
  if (info.url.includes('/privacy') || info.url.includes('/terms') || info.url.includes('/cookie')) continue;

  let cls = classifyByUrl(info.url) || classifyByContent(info);
  const score = relevanceScore(info);

  const entry = {
    url: info.url,
    title: deriveAnchor(info, ''),
    description: info.description.slice(0, 160),
    score,
  };

  if (cls === 'TOFU') tofu.push(entry);
  else if (cls === 'BOFU') bofu.push(entry);
  else if (score >= 1) {
    // Unclassified but relevant — default to TOFU (educational)
    tofu.push({ ...entry, title: entry.title || 'Pelajari lebih lanjut' });
  }
}

// Sort by relevance and pick top 3 each
tofu.sort((a, b) => b.score - a.score);
bofu.sort((a, b) => b.score - a.score);
const tofuTop = tofu.slice(0, 3);
const bofuTop = bofu.slice(0, 3);

const blogLinksText = tofuTop.length
  ? tofuTop.map((l, i) => `${i + 1}. URL: ${l.url}\n   Anchor: ${l.title}`).join('\n')
  : '(tidak ada halaman edukasi yang ditemukan — abaikan TOFU links)';
const moneyLinksText = bofuTop.length
  ? bofuTop.map((l, i) => `${i + 1}. URL: ${l.url}\n   Anchor: ${l.title}`).join('\n')
  : '(tidak ada halaman produk/layanan yang ditemukan — abaikan BOFU links)';

return [{
  json: {
    ...prevData,
    tofu_links: tofuTop,
    bofu_links: bofuTop,
    blog_links_text: blogLinksText,
    money_links_text: moneyLinksText,
    internal_links_count: tofuTop.length + bofuTop.length,
  }
}];"""


# === FIX 2: Code Build Doc Content — Publisher box as HTML table + cleaner article HTML ===
NEW_BUILD_DOC = r"""const data = $json;
const today = new Date().toISOString().split('T')[0];
const keyword = data.keyword || '';
const articleText = data.article_text || '';
const metadata = data.metadata || {};

const extractSection = (text, startTag, endTag) => {
  const start = text.indexOf(startTag);
  if (start === -1) return '';
  const contentStart = start + startTag.length;
  const end = endTag ? text.indexOf(endTag, contentStart) : text.length;
  return text.slice(contentStart, end === -1 ? text.length : end).trim();
};

const publisherBoxRaw = extractSection(articleText, '[PUBLISHER BOX]', '[JUDUL ARTIKEL]');
const judul = extractSection(articleText, '[JUDUL ARTIKEL]', '[ISI ARTIKEL]').trim();
const isi = extractSection(articleText, '[ISI ARTIKEL]', '[SITASI/REFERENSI]');
const sitasi = extractSection(articleText, '[SITASI/REFERENSI]', null);

const escHtml = (s) => String(s || '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// === Parse publisher box ASCII into table rows ===
// Lines look like "| KEY: VALUE" or continuation "|   1. ..."
function parsePublisherBox(raw) {
  const rows = [];
  const lines = raw.split('\n').filter(l => l.trim().startsWith('|'));
  let currentKey = null;
  let currentVals = [];
  const flush = () => {
    if (currentKey !== null) rows.push({ key: currentKey, value: currentVals.join('<br>').trim() });
    currentKey = null; currentVals = [];
  };
  for (const line of lines) {
    const stripped = line.replace(/^\|\s?/, '').replace(/\s*\|?\s*$/, '');
    const colonIdx = stripped.indexOf(':');
    // Heuristic: "KEY:" pattern with uppercase key (no leading whitespace) starts a new row
    const looksLikeNewKey = colonIdx > 0 && colonIdx <= 30
      && /^[A-Z][A-Z0-9 _\/]*$/.test(stripped.slice(0, colonIdx).trim())
      && !line.startsWith('|   ') && !line.startsWith('|\t');
    if (looksLikeNewKey) {
      flush();
      currentKey = stripped.slice(0, colonIdx).trim();
      const v = stripped.slice(colonIdx + 1).trim();
      currentVals = v ? [v] : [];
    } else if (currentKey !== null) {
      currentVals.push(stripped.trim());
    }
  }
  flush();
  return rows;
}

const boxRows = parsePublisherBox(publisherBoxRaw);
const publisherBoxHtml = boxRows.length ? `
<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;border:1px solid #d1d5db;font-family:Arial,sans-serif;font-size:13px;margin:12px 0;">
  <thead>
    <tr style="background-color:#f3f4f6;">
      <th colspan="2" style="padding:10px;text-align:left;font-weight:600;color:#111827;border-bottom:2px solid #d1d5db;">📋 Publisher Box</th>
    </tr>
  </thead>
  <tbody>
${boxRows.map(r => `    <tr>
      <td style="padding:8px 12px;background-color:#f9fafb;font-weight:600;color:#374151;width:30%;vertical-align:top;border-bottom:1px solid #e5e7eb;">${escHtml(r.key)}</td>
      <td style="padding:8px 12px;color:#1f2937;border-bottom:1px solid #e5e7eb;">${r.value}</td>
    </tr>`).join('\n')}
  </tbody>
</table>` : '';

// === Convert article body markdown -> HTML with proper paragraphs and lists ===
function mdToHtml(md) {
  if (!md) return '';
  const lines = md.split('\n');
  const out = [];
  let inList = false, listType = null;

  const closeList = () => { if (inList) { out.push(`</${listType}>`); inList = false; listType = null; } };

  const inlineMd = (text) => text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+?)\]\(([^)]+?)\)/g, '<a href="$2">$1</a>')
    .replace(/`([^`]+?)`/g, '<code>$1</code>');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) { closeList(); continue; }

    // Headings
    let m = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (m) { closeList(); const lvl = m[1].length; out.push(`<h${lvl}>${inlineMd(m[2])}</h${lvl}>`); continue; }

    // Unordered list
    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList || listType !== 'ul') { closeList(); out.push('<ul>'); inList = true; listType = 'ul'; }
      out.push(`<li>${inlineMd(trimmed.replace(/^[-*]\s+/, ''))}</li>`);
      continue;
    }
    // Ordered list
    if (/^\d+\.\s+/.test(trimmed)) {
      if (!inList || listType !== 'ol') { closeList(); out.push('<ol>'); inList = true; listType = 'ol'; }
      out.push(`<li>${inlineMd(trimmed.replace(/^\d+\.\s+/, ''))}</li>`);
      continue;
    }
    // Paragraph
    closeList();
    out.push(`<p>${inlineMd(trimmed)}</p>`);
  }
  closeList();
  return out.join('\n');
}

const isiHtml = mdToHtml(isi);
const sitasiHtml = sitasi
  .split('\n')
  .filter(l => l.trim())
  .map(l => `<p style="margin:4px 0;">${escHtml(l.trim())}</p>`)
  .join('');

const fullHtml = `${publisherBoxHtml}
<h1>${escHtml(judul)}</h1>
<div>${isiHtml}</div>
<hr>
<h2>Sitasi &amp; Referensi</h2>
${sitasiHtml}`;

const docTitle = `${today}_${keyword.replace(/\s+/g, '-').toLowerCase()}`;

const folderId = data.articles_folder_id || data.drive_folder_id;
const boundary = '----nyx_seo_boundary_' + Math.random().toString(36).slice(2);
const meta = JSON.stringify({
  name: docTitle,
  mimeType: 'application/vnd.google-apps.document',
  parents: folderId ? [folderId] : []
});
const multipartBody =
  `--${boundary}\r\n` +
  `Content-Type: application/json; charset=UTF-8\r\n\r\n` +
  `${meta}\r\n` +
  `--${boundary}\r\n` +
  `Content-Type: text/html; charset=UTF-8\r\n\r\n` +
  `${fullHtml}\r\n` +
  `--${boundary}--`;

return [{
  json: {
    ...data,
    doc_title: docTitle,
    doc_html: fullHtml,
    judul_artikel: judul,
    preview_text: isi.replace(/^#+\s.*$/gm, '').replace(/\s+/g, ' ').trim().slice(0, 250),
    sitasi_text: sitasi,
    multipart_body: multipartBody,
    multipart_boundary: boundary
  }
}];"""


# === FIX 3: Code Build Article Prompts — much better article prompt ===
NEW_BUILD_PROMPTS = r"""const data = items[0].json;

// Build TOFU/BOFU instructions — empty if no links available
const tofuLinksAvail = (data.tofu_links || []).length > 0;
const bofuLinksAvail = (data.bofu_links || []).length > 0;

const linkInstructions = [];
if (tofuLinksAvail) {
  linkInstructions.push(`WAJIB sisipkan SEMUA TOFU internal links berikut di bagian edukasi/penjelasan menggunakan format markdown [anchor](URL). Gunakan exact URL yang diberikan:
${data.blog_links_text}`);
}
if (bofuLinksAvail) {
  linkInstructions.push(`WAJIB sisipkan SEMUA BOFU internal links berikut di bagian rekomendasi/CTA menggunakan format markdown [anchor](URL). Gunakan exact URL yang diberikan:
${data.money_links_text}`);
}
const linksBlock = linkInstructions.length ? linkInstructions.join('\n\n') : '(Klien belum punya halaman blog/produk yang relevan — fokus pada konten artikel saja.)';

const sysPrompt = `Kamu adalah penulis konten SEO senior Indonesia dengan 10+ tahun pengalaman. Standar kualitas kamu:

1. READABILITY TINGGI:
   - Paragraf pendek (2-3 kalimat maksimal)
   - Kalimat sederhana, hindari jargon tanpa penjelasan
   - Gunakan kata transisi (selain itu, namun, oleh karena itu)
   - Active voice, tone conversational tapi tetap profesional
   - Sisipkan analogi/contoh konkret untuk konsep abstrak

2. DATA-DRIVEN:
   - Ekstrak angka, statistik, persentase, harga, tahun, nama brand dari REFERENSI yang diberikan
   - Cite fakta secara inline: "Menurut [sumber], [fakta spesifik]..."
   - JANGAN mengarang angka — hanya gunakan yang ada di referensi

3. OUTLINE LEBIH UNGGUL:
   - Cover SEMUA topik yang dibahas kompetitor
   - TAMBAHKAN minimal 2 section unik yang tidak dibahas kompetitor (FAQ, common pitfalls, case study, comparison table, dll)
   - Lebih komprehensif, lebih dalam, lebih actionable

4. STRUKTUR WAJIB:
   - Pembuka (1-2 paragraf, hook + preview value)
   - Minimal 4 H2 utama dengan 2-3 H3 di bawahnya
   - Setiap H2 minimal 150 kata
   - FAQ section di akhir (3-5 pertanyaan)
   - Kesimpulan + CTA

5. SEO ON-PAGE:
   - Keyword target di H1, paragraf pertama, dan minimal 3 H2
   - LSI keywords (variasi natural keyword)
   - Internal links dengan anchor text yang natural & contextual

Output HARUS mengikuti format yang diminta PERSIS, tanpa markdown code fences di sekitar output.`;

const userPrompt = `Buat artikel SEO berkualitas tinggi.

## DATA ARTIKEL
- Keyword Target: **${data.keyword}**
- Word Count Target: **${data.word_count} kata** (toleransi ±15%)
- Tone: ${data.tone}
- Website Klien: ${data.website_url}

## METADATA SEO (sudah disetujui, gunakan persis)
- Slug: ${data.metadata.slug}
- Meta Title: ${data.metadata.meta_title}
- Meta Description: ${data.metadata.meta_description}
- Excerpt: ${data.metadata.excerpt}

## REFERENSI KOMPETITOR — EKSTRAK DATA, ANGKA, FAKTA DARI SINI

### REFERENSI 1: ${data.ref_1_title}
URL: ${data.ref_1_url}
Konten:
${data.ref_1_markdown}

### REFERENSI 2: ${data.ref_2_title}
URL: ${data.ref_2_url}
Konten:
${data.ref_2_markdown}

### REFERENSI 3: ${data.ref_3_title}
URL: ${data.ref_3_url}
Konten:
${data.ref_3_markdown}

## INTERNAL LINKS YANG WAJIB DISISIPKAN
${linksBlock}

## INSTRUKSI KHUSUS
1. **Analisa outline kompetitor** dari 3 referensi di atas — catat topik utama yang mereka bahas.
2. **Buat outline kamu LEBIH UNGGUL**: cover semua topik mereka + tambahkan 2 section yang tidak ada di kompetitor (misal: FAQ, perbandingan, case study, common mistakes).
3. **Ekstrak data konkret**: angka statistik, persentase, harga, nama tools, tahun — dari referensi. Cite secara inline.
4. **Sisipkan internal links** sesuai instruksi di atas, gunakan format markdown [anchor](URL) — JANGAN ubah URL.
5. **Readability**: paragraf pendek (2-3 kalimat), bahasa sederhana, transisi antar paragraf.

## FORMAT OUTPUT — IKUTI PERSIS

[PUBLISHER BOX]
| KEYWORD TARGET: ${data.keyword}
| URL SLUG: ${data.metadata.slug}
| META TITLE: ${data.metadata.meta_title}
| META DESCRIPTION: ${data.metadata.meta_description}
| ALT TEXT: ${data.metadata.alt_texts[0]}
| EXCERPT: ${data.metadata.excerpt}
| WORD COUNT TARGET: ${data.word_count}
| WEBSITE: ${data.website_url}
| REFERENSI:
|   1. ${data.ref_1_title} — ${data.ref_1_url}
|   2. ${data.ref_2_title} — ${data.ref_2_url}
|   3. ${data.ref_3_title} — ${data.ref_3_url}

[JUDUL ARTIKEL]
${data.metadata.meta_title}

[ISI ARTIKEL]
(Tulis artikel lengkap ${data.word_count} kata mengikuti SEMUA instruksi di atas. Gunakan H2 dan H3 markdown. Sisipkan internal links. Cite data dari referensi. Akhiri dengan FAQ + Kesimpulan + CTA.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url} (Diakses ${new Date().toISOString().split('T')[0]})
2. ${data.ref_2_title} - ${data.ref_2_url} (Diakses ${new Date().toISOString().split('T')[0]})
3. ${data.ref_3_title} - ${data.ref_3_url} (Diakses ${new Date().toISOString().split('T')[0]})`;

const retrySys = `Kamu adalah penulis konten SEO senior Indonesia. Output kamu HARUS mengikuti format PERSIS yang diminta. Pastikan SEMUA section ada: [PUBLISHER BOX], [JUDUL ARTIKEL], [ISI ARTIKEL], [SITASI/REFERENSI]. Wajib sisipkan internal links yang diberikan dan cite data dari referensi. Readability: paragraf pendek 2-3 kalimat, bahasa sederhana.`;

const retryUser = `Retry: artikel sebelumnya tidak lengkap. Buat ulang artikel SEO ${data.word_count} kata untuk keyword '${data.keyword}'.

Tone: ${data.tone}
Website: ${data.website_url}
Slug: ${data.metadata.slug}
Meta Title: ${data.metadata.meta_title}

Referensi (ekstrak data konkret dari sini):
1. ${data.ref_1_title} — ${data.ref_1_url}
${(data.ref_1_markdown || '').slice(0, 1500)}

2. ${data.ref_2_title} — ${data.ref_2_url}
${(data.ref_2_markdown || '').slice(0, 1500)}

3. ${data.ref_3_title} — ${data.ref_3_url}
${(data.ref_3_markdown || '').slice(0, 1500)}

Internal links wajib:
${linksBlock}

FORMAT OUTPUT (IKUTI PERSIS):

[PUBLISHER BOX]
| KEYWORD TARGET: ${data.keyword}
| URL SLUG: ${data.metadata.slug}
| META TITLE: ${data.metadata.meta_title}
| META DESCRIPTION: ${data.metadata.meta_description}
| ALT TEXT: ${data.metadata.alt_texts[0]}
| EXCERPT: ${data.metadata.excerpt}
| WORD COUNT TARGET: ${data.word_count}

[JUDUL ARTIKEL]
${data.metadata.meta_title}

[ISI ARTIKEL]
(Artikel lengkap ${data.word_count} kata, paragraf pendek 2-3 kalimat, dengan H2/H3, FAQ section, kesimpulan, CTA. WAJIB sisipkan internal links dan data dari referensi.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}`;

return [{
  json: {
    ...data,
    article_system_prompt: sysPrompt,
    article_user_prompt: userPrompt,
    article_retry_system_prompt: retrySys,
    article_retry_user_prompt: retryUser
  }
}];"""


# Apply patches
fixes = []
for n in wf['nodes']:
    name = n['name']
    if name == 'Code Classify Pages':
        n['parameters']['jsCode'] = NEW_CLASSIFY
        fixes.append('Code Classify Pages (EN+ID patterns + relevance scoring)')
    elif name == 'Code Build Doc Content':
        n['parameters']['jsCode'] = NEW_BUILD_DOC
        fixes.append('Code Build Doc Content (Publisher Box as HTML table)')
    elif name == 'Code Build Article Prompts':
        n['parameters']['jsCode'] = NEW_BUILD_PROMPTS
        fixes.append('Code Build Article Prompts (data extraction + better outline + force links)')

print('Applied:')
for f in fixes:
    print(f'  - {f}')

allowed_settings = {'executionOrder', 'saveManualExecutions', 'callerPolicy', 'errorWorkflow', 'timezone'}
wf_put = {
    'name': wf['name'],
    'nodes': wf['nodes'],
    'connections': wf['connections'],
    'settings': {k: v for k, v in wf.get('settings', {}).items() if k in allowed_settings},
    'staticData': wf.get('staticData'),
    'pinData': wf.get('pinData', {}),
}
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(wf_put, f, ensure_ascii=False)
print(f'\nWrote {OUT_PATH}')
