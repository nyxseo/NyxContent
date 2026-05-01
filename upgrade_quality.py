"""Upgrade article quality: integrate user's strict prompt, add scoring + recommendations sections,
update HTML rendering, enforce no-em-dash rule."""
import json

WF_PATH = 'G:/NyxContent/workflow_live.json'
OUT_PATH = 'G:/NyxContent/workflow_put.json'

with open(WF_PATH, encoding='utf-8') as f:
    wf = json.load(f)

# Sanitize sticky notes (corruption protection)
for n in wf['nodes']:
    if n.get('type') == 'n8n-nodes-base.stickyNote':
        n['parameters']['content'] = f"## {n['name']}"

# === Build Article Prompts: enforced quality standard ===
# Note: hyphen "-" is used everywhere instead of em dash, per strict rules.
NEW_BUILD_PROMPTS = r"""const data = items[0].json;

const tofuLinksAvail = (data.tofu_links || []).length > 0;
const bofuLinksAvail = (data.bofu_links || []).length > 0;

const linkInstructions = [];
if (tofuLinksAvail) {
  linkInstructions.push(`TOFU Internal Links (sisipkan di bagian edukasi/penjelasan, format markdown [anchor](URL), gunakan exact URL):
${data.blog_links_text}`);
}
if (bofuLinksAvail) {
  linkInstructions.push(`BOFU Internal Links (sisipkan di bagian rekomendasi/CTA, format markdown [anchor](URL), gunakan exact URL):
${data.money_links_text}`);
}
const linksBlock = linkInstructions.length ? linkInstructions.join('\n\n') : '(Klien belum punya halaman blog/produk yang relevan untuk topik ini. Fokus pada konten artikel saja.)';

const sysPrompt = `Anda adalah expert content strategist, editor senior, dan penulis berpengalaman lintas topik di Indonesia. Tugas Anda menulis artikel yang dianalisis, di-fact-check, dan disusun agar menjadi konten berkualitas tinggi, terpercaya, mudah dibaca, dan siap bersaing di Google.

PRINSIP UTAMA:
1. Sesuai search intent. Identifikasi apakah keyword bersifat informasional, komersial, transaksional, atau navigasional. Konten harus langsung menjawab kebutuhan user, tidak bertele-tele, tidak ada filler.
2. Terasa ditulis manusia ahli. Hindari pola template AI. Tambahkan insight, contoh konkret, skenario realistis, atau aplikasi nyata.
3. Akurat dan bisa diverifikasi. Hanya gunakan pengetahuan umum valid atau estimasi realistis. Jangan mengarang angka, statistik, atau klaim. Hindari sumber spesifik yang tidak ada di REFERENSI.
4. Future-proof. Hindari menyebut tahun spesifik kecuali benar-benar perlu. Hindari informasi yang cepat usang.
5. E-E-A-T kuat. Tunjukkan pengalaman, expertise, authoritativeness, trustworthiness lewat penjelasan yang spesifik dan kontekstual.

ATURAN KETAT:
- DILARANG menggunakan em dash (karakter panjang). Gunakan tanda hubung biasa (-), titik, atau koma sebagai pengganti.
- Jangan gunakan buzzword berlebihan ("revolusioner", "game changer", "luar biasa", "tak tertandingi").
- Hindari klaim absolut. Sebut keterbatasan jika ada.
- Jangan mengulang ide yang sama dengan kata berbeda.
- Jangan membuat data palsu. Jika tidak ada angka di referensi, jangan paksa memasukkan angka.

READABILITY:
- Bahasa natural. Profesional tapi santai.
- Paragraf pendek 2 sampai 4 baris maksimal.
- Beri spacing rapi antar paragraf (satu baris kosong).
- Hindari kalimat panjang. Pecah menjadi beberapa kalimat.
- Jelaskan istilah teknis dengan sederhana saat pertama kali muncul.
- Gunakan bullet point jika cocok.

STRUKTUR:
- Pembukaan kuat dan menarik. Hook + preview value.
- Alur logis antar bagian. Tidak ada pengulangan ide.
- H1 untuk judul, H2 untuk section utama, H3 untuk sub-section.
- Akhiri dengan kesimpulan dan CTA yang relevan.

SEO:
- Keyword utama muncul natural di H1, paragraf pertama, dan minimal 2 H2.
- Gunakan variasi keyword (LSI) tanpa keyword stuffing.
- Internal links wajib disisipkan dengan anchor text natural dan kontekstual.

KOMPETITOR DAN DATA:
- Analisa outline 3 referensi yang diberikan. Catat topik utama yang mereka bahas.
- Outline Anda harus lebih unggul. Cover semua topik kompetitor plus minimal 2 section unik (FAQ, common pitfalls, perbandingan, atau case study singkat).
- Jika ada angka, harga, persentase, atau nama tools yang muncul di referensi, kutip secara inline dengan sumber. Jangan mengarang.

OUTPUT WAJIB MENGIKUTI FORMAT YANG DIMINTA PERSIS, tanpa markdown code fences di sekitar output.`;

const userPrompt = `Tulis artikel SEO untuk klien.

DATA ARTIKEL
Keyword target: ${data.keyword}
Word count target: ${data.word_count} kata (toleransi 15 persen)
Tone: ${data.tone}
Website klien: ${data.website_url}

METADATA SEO (gunakan persis):
Slug: ${data.metadata.slug}
Meta title: ${data.metadata.meta_title}
Meta description: ${data.metadata.meta_description}
Excerpt: ${data.metadata.excerpt}

REFERENSI KOMPETITOR (analisa outline, ekstrak data konkret jika ada, jangan mengarang):

REFERENSI 1: ${data.ref_1_title}
URL: ${data.ref_1_url}
Konten:
${data.ref_1_markdown}

REFERENSI 2: ${data.ref_2_title}
URL: ${data.ref_2_url}
Konten:
${data.ref_2_markdown}

REFERENSI 3: ${data.ref_3_title}
URL: ${data.ref_3_url}
Konten:
${data.ref_3_markdown}

INTERNAL LINKS YANG WAJIB DISISIPKAN:
${linksBlock}

LANGKAH KERJA:
1. Identifikasi search intent dari keyword.
2. Analisa outline 3 kompetitor di atas. Catat topik yang mereka bahas.
3. Susun outline Anda yang lebih unggul (cover semua topik kompetitor plus 2 section unik).
4. Tulis artikel mengikuti aturan readability dan strict rules di system prompt.
5. Sisipkan internal links yang diberikan dengan anchor natural.
6. Akhiri dengan FAQ (3 sampai 5 pertanyaan), kesimpulan, dan CTA.
7. Tambahkan analisa skor dan rekomendasi lanjutan di akhir output.

FORMAT OUTPUT WAJIB IKUTI PERSIS (gunakan tanda hubung "-" bukan em dash):

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
|   1. ${data.ref_1_title} - ${data.ref_1_url}
|   2. ${data.ref_2_title} - ${data.ref_2_url}
|   3. ${data.ref_3_title} - ${data.ref_3_url}

[JUDUL ARTIKEL]
${data.metadata.meta_title}

[ISI ARTIKEL]
(Tulis artikel lengkap ${data.word_count} kata. Paragraf pendek 2 sampai 4 baris. Gunakan H2 dan H3 markdown. Sisipkan internal links yang diberikan. Akhiri dengan FAQ, kesimpulan, CTA. Jangan pakai em dash.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}

[SKOR KONTEN]
Readability: X/100
(Satu sampai dua kalimat alasan singkat.)

SEO: X/100
(Satu sampai dua kalimat alasan singkat.)

E-E-A-T: X/100
(Satu sampai dua kalimat alasan singkat.)

[REKOMENDASI LANJUTAN]
- Saran konkret 1 (apa yang masih bisa ditingkatkan)
- Saran konkret 2 (bagian mana yang paling lemah)
- Saran konkret 3 (prioritas perbaikan berikutnya)`;

const retrySys = `Anda adalah expert content strategist Indonesia. Output Anda harus mengikuti format yang diminta PERSIS. Section wajib lengkap: [PUBLISHER BOX], [JUDUL ARTIKEL], [ISI ARTIKEL], [SITASI/REFERENSI], [SKOR KONTEN], [REKOMENDASI LANJUTAN]. Aturan ketat: dilarang em dash, paragraf pendek 2 sampai 4 baris, bahasa natural, sisipkan internal links yang diberikan, jangan mengarang data.`;

const retryUser = `Retry karena artikel sebelumnya tidak lengkap. Tulis ulang artikel SEO ${data.word_count} kata untuk keyword '${data.keyword}'.

Tone: ${data.tone}. Website: ${data.website_url}. Slug: ${data.metadata.slug}. Meta title: ${data.metadata.meta_title}.

Ringkasan referensi (ekstrak data jika ada, jangan mengarang):
1. ${data.ref_1_title} - ${data.ref_1_url}
${(data.ref_1_markdown || '').slice(0, 1500)}

2. ${data.ref_2_title} - ${data.ref_2_url}
${(data.ref_2_markdown || '').slice(0, 1500)}

3. ${data.ref_3_title} - ${data.ref_3_url}
${(data.ref_3_markdown || '').slice(0, 1500)}

Internal links wajib:
${linksBlock}

FORMAT OUTPUT (ikut persis, jangan pakai em dash):

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
(Artikel lengkap ${data.word_count} kata, paragraf pendek 2 sampai 4 baris, H2/H3, FAQ, kesimpulan, CTA. Sisipkan internal links. Jangan em dash.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}

[SKOR KONTEN]
Readability: X/100
SEO: X/100
E-E-A-T: X/100

[REKOMENDASI LANJUTAN]
- Saran 1
- Saran 2
- Saran 3`;

return [{
  json: {
    ...data,
    article_system_prompt: sysPrompt,
    article_user_prompt: userPrompt,
    article_retry_system_prompt: retrySys,
    article_retry_user_prompt: retryUser
  }
}];"""


# === Code Validate Article: also normalize em dashes (replace with hyphen) and parse new sections ===
NEW_VALIDATE_ARTICLE = r"""const response = $json;
const prevData = $('Code Build Article Prompts').item.json;

let articleText = '';
try {
  articleText = response.content?.[0]?.text || response.choices?.[0]?.message?.content || '';
} catch(e) {
  throw new Error('LLM article response malformed');
}

if (!articleText) {
  throw new Error('Empty article text');
}

// Strict rule: replace any em dash that slipped through with hyphen
articleText = articleText.replace(/—/g, '-').replace(/–/g, '-');

const hasPublisherBox = articleText.includes('[PUBLISHER BOX]');
const hasTitle = articleText.includes('[JUDUL ARTIKEL]');
const hasContent = articleText.includes('[ISI ARTIKEL]');
const hasCitations = articleText.includes('[SITASI/REFERENSI]');

// Optional sections (warn but don't fail if missing)
const hasScoring = articleText.includes('[SKOR KONTEN]');
const hasRecommendations = articleText.includes('[REKOMENDASI LANJUTAN]');

const wordCount = articleText.split(/\s+/).filter(w => w.length > 0).length;
const targetWords = prevData.word_count;
const wordCountOk = wordCount >= targetWords * 0.7;

const isValid = hasPublisherBox && hasTitle && hasContent && hasCitations && wordCountOk;

return [{
  json: {
    ...prevData,
    article_text: articleText,
    article_valid: isValid,
    article_word_count: wordCount,
    validation_details: {
      hasPublisherBox, hasTitle, hasContent, hasCitations, hasScoring, hasRecommendations,
      wordCount, targetWords, wordCountOk
    }
  }
}];"""


NEW_VALIDATE_RETRY = r"""const response = $json;
const prevData = $('Code Validate Article').item.json;

let articleText = '';
try {
  articleText = response.content?.[0]?.text || response.choices?.[0]?.message?.content || '';
} catch(e) {
  articleText = prevData.article_text || '';
}

articleText = (articleText || '').replace(/—/g, '-').replace(/–/g, '-');

return [{
  json: {
    ...prevData,
    article_text: articleText || prevData.article_text || '',
    article_valid: true
  }
}];"""


# === Code Build Doc Content: render new SKOR KONTEN + REKOMENDASI sections in Google Docs ===
NEW_BUILD_DOC = r"""const data = $json;
const today = new Date().toISOString().split('T')[0];
const keyword = data.keyword || '';
let articleText = data.article_text || '';
const metadata = data.metadata || {};

// Replace em dashes (defensive)
articleText = articleText.replace(/—/g, '-').replace(/–/g, '-');

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
const sitasi = extractSection(articleText, '[SITASI/REFERENSI]', '[SKOR KONTEN]')
              || extractSection(articleText, '[SITASI/REFERENSI]', null);
const skor = extractSection(articleText, '[SKOR KONTEN]', '[REKOMENDASI LANJUTAN]')
            || extractSection(articleText, '[SKOR KONTEN]', null);
const rekomendasi = extractSection(articleText, '[REKOMENDASI LANJUTAN]', null);

const escHtml = (s) => String(s || '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// Parse publisher box ASCII into table rows
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
      <th colspan="2" style="padding:10px;text-align:left;font-weight:600;color:#111827;border-bottom:2px solid #d1d5db;">Publisher Box</th>
    </tr>
  </thead>
  <tbody>
${boxRows.map(r => `    <tr>
      <td style="padding:8px 12px;background-color:#f9fafb;font-weight:600;color:#374151;width:30%;vertical-align:top;border-bottom:1px solid #e5e7eb;">${escHtml(r.key)}</td>
      <td style="padding:8px 12px;color:#1f2937;border-bottom:1px solid #e5e7eb;">${r.value}</td>
    </tr>`).join('\n')}
  </tbody>
</table>` : '';

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
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) { closeList(); continue; }
    let m = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (m) { closeList(); const lvl = m[1].length; out.push(`<h${lvl}>${inlineMd(m[2])}</h${lvl}>`); continue; }
    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList || listType !== 'ul') { closeList(); out.push('<ul>'); inList = true; listType = 'ul'; }
      out.push(`<li>${inlineMd(trimmed.replace(/^[-*]\s+/, ''))}</li>`);
      continue;
    }
    if (/^\d+\.\s+/.test(trimmed)) {
      if (!inList || listType !== 'ol') { closeList(); out.push('<ol>'); inList = true; listType = 'ol'; }
      out.push(`<li>${inlineMd(trimmed.replace(/^\d+\.\s+/, ''))}</li>`);
      continue;
    }
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

// Parse [SKOR KONTEN] into structured table
function parseSkor(raw) {
  if (!raw) return [];
  const items = [];
  const lines = raw.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(/^(Readability|SEO|E-?E-?A-?T)\s*:\s*(\d+)\s*\/\s*100/i);
    if (m) {
      const explanation = (lines[i + 1] || '').trim().replace(/^\(|\)$/g, '');
      items.push({ label: m[1].toUpperCase().replace(/-/g, '-'), score: parseInt(m[2]), note: explanation });
    }
  }
  return items;
}

const skorItems = parseSkor(skor);
const skorHtml = skorItems.length ? `
<h2>Skor Konten</h2>
<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;border:1px solid #d1d5db;font-family:Arial,sans-serif;font-size:13px;margin:12px 0;">
  <thead>
    <tr style="background-color:#f3f4f6;">
      <th style="padding:8px;text-align:left;width:25%;">Kategori</th>
      <th style="padding:8px;text-align:left;width:15%;">Skor</th>
      <th style="padding:8px;text-align:left;">Catatan</th>
    </tr>
  </thead>
  <tbody>
${skorItems.map(s => `    <tr>
      <td style="padding:8px 12px;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">${escHtml(s.label)}</td>
      <td style="padding:8px 12px;color:#111827;font-weight:600;border-bottom:1px solid #e5e7eb;">${s.score}/100</td>
      <td style="padding:8px 12px;color:#374151;border-bottom:1px solid #e5e7eb;">${escHtml(s.note)}</td>
    </tr>`).join('\n')}
  </tbody>
</table>` : '';

function parseRekomendasi(raw) {
  if (!raw) return [];
  return raw.split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0 && /^[-*0-9]/.test(l))
    .map(l => l.replace(/^[-*]\s*/, '').replace(/^\d+[.)]\s*/, ''));
}

const rekomendasiItems = parseRekomendasi(rekomendasi);
const rekomendasiHtml = rekomendasiItems.length ? `
<h2>Rekomendasi Lanjutan</h2>
<ul>
${rekomendasiItems.map(r => `  <li>${escHtml(r)}</li>`).join('\n')}
</ul>` : '';

const fullHtml = `${publisherBoxHtml}
<h1>${escHtml(judul)}</h1>
<div>${isiHtml}</div>
<hr>
<h2>Sitasi dan Referensi</h2>
${sitasiHtml}
${skorHtml}
${rekomendasiHtml}`;

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
    skor_items: skorItems,
    rekomendasi_items: rekomendasiItems,
    multipart_body: multipartBody,
    multipart_boundary: boundary
  }
}];"""


# === Code Build Response: include skor + rekomendasi in JSON returned to UI ===
NEW_BUILD_RESPONSE = r"""const driveResponse = $json;
const prevData = $('Code Build Doc Content').item.json;

const docId = driveResponse.id || '';
const docUrl = docId ? `https://docs.google.com/document/d/${docId}/edit` : '';

const references = [
  { title: prevData.ref_1_title || '', url: prevData.ref_1_url || '' },
  { title: prevData.ref_2_title || '', url: prevData.ref_2_url || '' },
  { title: prevData.ref_3_title || '', url: prevData.ref_3_url || '' }
].filter(r => r.url);

return [{
  json: {
    status: 'success',
    google_docs_url: docUrl,
    doc_id: docId,
    doc_title: prevData.doc_title,
    metadata: {
      slug: prevData.metadata?.slug || '',
      meta_title: prevData.metadata?.meta_title || '',
      meta_description: prevData.metadata?.meta_description || ''
    },
    preview: prevData.preview_text || '',
    internal_links_count: prevData.internal_links_count || 0,
    references: references,
    word_count_actual: prevData.article_word_count || 0,
    keyword: prevData.keyword,
    scores: prevData.skor_items || [],
    recommendations: prevData.rekomendasi_items || []
  }
}];"""


fixes = []
for n in wf['nodes']:
    name = n['name']
    if name == 'Code Build Article Prompts':
        n['parameters']['jsCode'] = NEW_BUILD_PROMPTS
        fixes.append('Code Build Article Prompts (E-E-A-T + scoring + strict rules)')
    elif name == 'Code Validate Article':
        n['parameters']['jsCode'] = NEW_VALIDATE_ARTICLE
        fixes.append('Code Validate Article (em dash strip + scoring detection)')
    elif name == 'Code Validate Retry':
        n['parameters']['jsCode'] = NEW_VALIDATE_RETRY
        fixes.append('Code Validate Retry (em dash strip)')
    elif name == 'Code Build Doc Content':
        n['parameters']['jsCode'] = NEW_BUILD_DOC
        fixes.append('Code Build Doc Content (renders Skor + Rekomendasi)')
    elif name == 'Code Build Response':
        n['parameters']['jsCode'] = NEW_BUILD_RESPONSE
        fixes.append('Code Build Response (returns scores + recommendations)')

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
