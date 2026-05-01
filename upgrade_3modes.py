"""Implement 3-mode quality system:
Mode 1: Expert content generation (updated prompt)
Mode 2: Rule-based scoring engine (in code, not AI)
Mode 3: Refinement pass (post-generation LLM polish)
"""
import json
import uuid

WF_PATH = 'G:/NyxContent/workflow_live.json'
OUT_PATH = 'G:/NyxContent/workflow_put.json'

with open(WF_PATH, encoding='utf-8') as f:
    wf = json.load(f)

# Sanitize sticky notes
for n in wf['nodes']:
    if n.get('type') == 'n8n-nodes-base.stickyNote':
        n['parameters']['content'] = f"## {n['name']}"

# ================================================================
# MODE 1: Expert generation prompt (updated)
# ================================================================

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
const linksBlock = linkInstructions.length ? linkInstructions.join('\n\n') : '(Klien belum punya halaman yang relevan untuk topik ini.)';

const sysPrompt = `Anda adalah expert content strategist, SEO specialist, dan praktisi yang menulis berdasarkan pengalaman nyata.

TUJUAN:
Artikel harus menjawab search intent secara dalam, memberikan insight bukan sekadar definisi, terasa ditulis oleh praktisi, struktur nyaman dibaca, dan unggul dibanding mayoritas konten di Google.

MODE KERJA:

1. SEARCH INTENT
Identifikasi: informasional / komersial / transaksional. Sesuaikan gaya penulisan.

2. HOOK KUAT DI AWAL
Paragraf pertama wajib berbasis problem nyata, memicu rasa penasaran, tidak boleh generik.

3. INSIGHT LAYER
Setiap section harus mengandung minimal satu: insight praktis, kesalahan umum, atau perspektif unik. Kalau hanya teori, rewrite.

4. DATA & REALISME
Gunakan angka realistis jika relevan. Hindari klaim ekstrem. Gunakan estimasi logis. Jangan mengarang angka.

5. USE CASE NYATA
Minimal 1 sampai 2 use case yang spesifik, kontekstual, dan ada dampak.

6. STRUKTUR PARAGRAF (WAJIB)
Maksimal 3 baris per paragraf. Setelah 2 sampai 3 baris, buat paragraf baru. Dilarang membuat blok teks panjang.

7. GAYA BAHASA
Natural, mudah dipahami, tidak terlalu formal.

8. SEMANTIC SEO
Gunakan keyword utama natural. Tambahkan variasi relevan. Hindari keyword stuffing.

9. ANTI GENERIC FILTER
Rewrite section yang terasa template, terlalu umum, atau seperti textbook.

10. FORMAT
Heading jelas, paragraf pendek, bullet jika perlu, alur logis.

STRICT RULES:
- Dilarang em dash (gunakan tanda hubung biasa)
- Dilarang paragraf panjang
- Dilarang klaim tanpa dasar
- Dilarang pengulangan ide
- Dilarang buzzword berlebihan

Output WAJIB mengikuti format yang diminta PERSIS, tanpa markdown code fences.`;

const userPrompt = `Tulis artikel SEO expert level untuk klien.

DATA:
Keyword: ${data.keyword}
Word count target: ${data.word_count} kata
Tone: ${data.tone}
Website: ${data.website_url}

METADATA:
Slug: ${data.metadata.slug}
Meta title: ${data.metadata.meta_title}
Meta description: ${data.metadata.meta_description}
Excerpt: ${data.metadata.excerpt}

REFERENSI KOMPETITOR (analisa outline, ekstrak data konkret jika ada):

REFERENSI 1: ${data.ref_1_title}
URL: ${data.ref_1_url}
${data.ref_1_markdown}

REFERENSI 2: ${data.ref_2_title}
URL: ${data.ref_2_url}
${data.ref_2_markdown}

REFERENSI 3: ${data.ref_3_title}
URL: ${data.ref_3_url}
${data.ref_3_markdown}

INTERNAL LINKS:
${linksBlock}

LANGKAH KERJA:
1. Identifikasi search intent.
2. Analisa outline 3 kompetitor, catat topik utama.
3. Susun outline yang lebih unggul (cover semua topik kompetitor + 2 section unik).
4. Tulis artikel dengan paragraf maksimal 3 baris, hook kuat, insight per section, use case nyata.
5. Sisipkan internal links yang diberikan.
6. Akhiri dengan FAQ, kesimpulan, CTA.
7. Tambah skor subjektif dan rekomendasi di akhir.

FORMAT OUTPUT WAJIB (tanda hubung biasa, BUKAN em dash):

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
(Artikel lengkap ${data.word_count} kata. Paragraf maksimal 3 baris. H2/H3 markdown. Internal links wajib disisipkan. FAQ, kesimpulan, CTA di akhir. Tanpa em dash.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}

[SKOR KONTEN]
Readability: X/100
SEO: X/100
E-E-A-T: X/100

[PENJELASAN SINGKAT]
(Satu paragraf pendek alasan skor.)

[REKOMENDASI LANJUTAN]
- Saran 1
- Saran 2
- Saran 3`;

const retrySys = `Anda adalah expert content strategist Indonesia. Output Anda HARUS lengkap dengan section: [PUBLISHER BOX], [JUDUL ARTIKEL], [ISI ARTIKEL], [SITASI/REFERENSI], [SKOR KONTEN], [PENJELASAN SINGKAT], [REKOMENDASI LANJUTAN]. Aturan ketat: dilarang em dash, paragraf maksimal 3 baris, sisipkan internal links yang diberikan, jangan mengarang data.`;

const retryUser = `Retry: tulis ulang artikel ${data.word_count} kata untuk keyword '${data.keyword}'.

Tone: ${data.tone}. Website: ${data.website_url}. Slug: ${data.metadata.slug}.

Referensi (ringkas):
1. ${data.ref_1_title} - ${data.ref_1_url}
${(data.ref_1_markdown || '').slice(0, 1500)}

2. ${data.ref_2_title} - ${data.ref_2_url}
${(data.ref_2_markdown || '').slice(0, 1500)}

3. ${data.ref_3_title} - ${data.ref_3_url}
${(data.ref_3_markdown || '').slice(0, 1500)}

Internal links wajib:
${linksBlock}

FORMAT (ikut persis, tanpa em dash):

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
(Artikel lengkap, paragraf max 3 baris, H2/H3, FAQ, kesimpulan, CTA, internal links.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}

[SKOR KONTEN]
Readability: X/100
SEO: X/100
E-E-A-T: X/100

[PENJELASAN SINGKAT]
(Satu paragraf.)

[REKOMENDASI LANJUTAN]
- Saran 1
- Saran 2`;

return [{
  json: {
    ...data,
    article_system_prompt: sysPrompt,
    article_user_prompt: userPrompt,
    article_retry_system_prompt: retrySys,
    article_retry_user_prompt: retryUser
  }
}];"""


# ================================================================
# MODE 3: Refinement nodes
# ================================================================

CODE_BUILD_REFINEMENT = r"""const data = $json;

const refinementSys = `Anda adalah editor senior konten SEO Indonesia. Tugas Anda merevisi artikel agar paragraf maksimal 3 baris, hook lebih kuat dengan problem nyata, tambah insight per section yang masih template, rewrite bagian generik agar lebih spesifik, perbaiki transisi antar section, dan validasi fakta dengan menghapus klaim lemah atau memberikan estimasi realistis.

ATURAN KETAT:
- Dilarang em dash (gunakan tanda hubung biasa)
- Dilarang paragraf panjang
- Dilarang filler
- Pertahankan struktur output asli (PUBLISHER BOX, JUDUL ARTIKEL, ISI ARTIKEL, SITASI, SKOR KONTEN, PENJELASAN SINGKAT, REKOMENDASI LANJUTAN)
- Pertahankan internal links yang sudah ada di artikel
- Jangan ubah metadata SEO (slug, meta title, meta description)`;

const refinementUser = `Berikut artikel yang perlu direvisi:

${data.article_text}

Lakukan refinement berikut:
1. Pastikan SEMUA paragraf maksimal 3 baris. Pecah paragraf panjang.
2. Perkuat hook di pembuka jika masih generic. Tambah problem nyata.
3. Tambah insight per section (insight praktis, kesalahan umum, perspektif unik) jika section terasa template.
4. Rewrite bagian generik atau seperti textbook.
5. Perbaiki transisi antar section.
6. Hapus klaim tanpa dasar atau ganti dengan estimasi realistis.
7. Pertahankan internal links markdown [anchor](URL) yang sudah ada.

OUTPUT FORMAT (ikut persis):

[ARTIKEL REVISI]
(Artikel hasil revisi LENGKAP dengan SEMUA section asli: [PUBLISHER BOX], [JUDUL ARTIKEL], [ISI ARTIKEL], [SITASI/REFERENSI], [SKOR KONTEN], [PENJELASAN SINGKAT], [REKOMENDASI LANJUTAN])

[DAFTAR PERUBAHAN]
- Perubahan konkret 1
- Perubahan konkret 2
- Perubahan konkret 3
(Daftar perubahan ringkas, masing-masing satu baris)`;

return [{
  json: {
    ...data,
    refinement_system_prompt: refinementSys,
    refinement_user_prompt: refinementUser
  }
}];"""


CODE_APPLY_REFINEMENT = r"""const response = $json;
const prevData = $('Code Build Refinement Request').item.json;

let refinedRaw = '';
try {
  refinedRaw = response.content?.[0]?.text || response.choices?.[0]?.message?.content || '';
} catch(e) {
  refinedRaw = '';
}

// Defensive em-dash strip
refinedRaw = (refinedRaw || '').replace(/—/g, '-').replace(/–/g, '-');

const extract = (text, start, end) => {
  const s = text.indexOf(start);
  if (s === -1) return '';
  const cs = s + start.length;
  const e = end ? text.indexOf(end, cs) : text.length;
  return text.slice(cs, e === -1 ? text.length : e).trim();
};

let revisedArticle = extract(refinedRaw, '[ARTIKEL REVISI]', '[DAFTAR PERUBAHAN]');
const changesText = extract(refinedRaw, '[DAFTAR PERUBAHAN]', null);

// Validation: revised article must contain key sections, otherwise fallback to original
const looksValid = revisedArticle.includes('[PUBLISHER BOX]')
  && revisedArticle.includes('[JUDUL ARTIKEL]')
  && revisedArticle.includes('[ISI ARTIKEL]')
  && revisedArticle.length >= prevData.article_text.length * 0.5;

const finalArticle = looksValid ? revisedArticle : prevData.article_text;

const changes = changesText
  .split('\n')
  .map(l => l.trim())
  .filter(l => l.length > 0 && /^[-*0-9]/.test(l))
  .map(l => l.replace(/^[-*]\s*/, '').replace(/^\d+[.)]\s*/, ''));

return [{
  json: {
    ...prevData,
    article_text: finalArticle,
    refinement_applied: looksValid,
    refinement_changes: changes
  }
}];"""


# ================================================================
# MODE 2: Rule-based scoring (Code Compute Scores)
# ================================================================

CODE_COMPUTE_SCORES = r"""const data = $json;
const articleText = data.article_text || '';
const keyword = (data.keyword || '').toLowerCase();
const targetWords = data.word_count || 1500;

const extract = (text, start, end) => {
  const s = text.indexOf(start);
  if (s === -1) return '';
  const cs = s + start.length;
  const e = end ? text.indexOf(end, cs) : text.length;
  return text.slice(cs, e === -1 ? text.length : e).trim();
};

const isi = extract(articleText, '[ISI ARTIKEL]', '[SITASI/REFERENSI]') || articleText;

// Strip headings/links for sentence counting
const cleanText = isi
  .replace(/^#+\s.*$/gm, '')
  .replace(/\[([^\]]+?)\]\([^)]+?\)/g, '$1');

// === READABILITY ===
// Formula: 100 - (avg_sentence_length * 1.2) - (long_paragraph_penalty * 5) - (complex_word_ratio * 30)
const sentences = cleanText.split(/[.!?]+/).map(s => s.trim()).filter(s => s.split(/\s+/).filter(w => w).length > 2);
const avgSentLen = sentences.length
  ? sentences.reduce((a, s) => a + s.split(/\s+/).filter(w => w).length, 0) / sentences.length
  : 0;

const paragraphs = isi.split(/\n\n+/).map(p => p.trim()).filter(p => p && !p.match(/^#+\s/));
const longParaCount = paragraphs.filter(p => {
  const words = p.split(/\s+/).filter(w => w).length;
  return words > 60;  // ~3 baris @ ~20 kata/baris
}).length;

const allWords = cleanText.split(/\s+/).filter(w => w.length > 0);
const complexWordCount = allWords.filter(w => w.replace(/[^a-zA-Z]/g, '').length > 13).length;
const complexRatio = allWords.length ? complexWordCount / allWords.length : 0;

const readability = Math.max(0, Math.min(100, Math.round(
  100 - (avgSentLen * 1.2) - (longParaCount * 5) - (complexRatio * 30)
)));

// === SEO ===
// (keyword_presence + heading_optimization + semantic_variation + internal_link_score + content_depth) * 20
const h1Match = articleText.match(/^#\s+(.+)$/m);
const h1Text = (h1Match ? h1Match[1] : (data.metadata?.meta_title || '')).toLowerCase();
const h2Texts = [...articleText.matchAll(/^##\s+(.+)$/gm)].map(m => m[1]);
const h3Texts = [...articleText.matchAll(/^###\s+(.+)$/gm)].map(m => m[1]);

const introPara = (paragraphs[0] || isi.slice(0, 600)).toLowerCase();

let keyword_presence = 0;
if (h1Text.includes(keyword)) keyword_presence += 0.5;
if (introPara.includes(keyword)) keyword_presence += 0.5;

const h2WithKw = h2Texts.filter(h => h.toLowerCase().includes(keyword)).length;
const heading_optimization = h2Texts.length
  ? Math.min(1, h2WithKw / Math.max(2, Math.ceil(h2Texts.length / 2)))
  : 0;

const kwTerms = keyword.split(/\s+/).filter(t => t.length > 2);
const allHeadings = [...h2Texts, ...h3Texts].join(' ').toLowerCase();
const variantHits = kwTerms.filter(t => allHeadings.includes(t)).length;
const semantic_variation = kwTerms.length ? variantHits / kwTerms.length : 0;

const internalLinks = (isi.match(/\[[^\]]+\]\([^)]+\)/g) || []).length;
const internal_link_score = Math.min(1, internalLinks / 3);

const isiWordCount = isi.split(/\s+/).filter(w => w).length;
const depthByWords = Math.min(1, isiWordCount / targetWords);
const depthByH2 = Math.min(1, h2Texts.length / 4);
const content_depth = (depthByWords + depthByH2) / 2;

const seo = Math.round(
  keyword_presence * 20 +
  heading_optimization * 20 +
  semantic_variation * 20 +
  internal_link_score * 20 +
  content_depth * 20
);

// === E-E-A-T ===
// (experience + example_quality + data_realism + trust_clarity) * 25
const isiLower = isi.toLowerCase();

const expPhrases = [
  'berdasarkan pengalaman', 'dalam praktik', 'pengalaman saya', 'pengalaman kami',
  'klien kami', 'praktik nyata', 'kami pernah', 'pernah menangani',
  'studi kasus kami', 'di lapangan', 'menurut pengalaman', 'kami sering'
];
const expHits = expPhrases.filter(p => isiLower.includes(p)).length;
const experience_signal = Math.min(1, expHits / 2);

const examplePhrases = ['misalnya', 'contohnya', 'sebagai contoh', 'sebagai ilustrasi', 'studi kasus', 'use case'];
const exampleHits = examplePhrases.filter(p => isiLower.includes(p)).length;
const numbersRegex = /\b\d+([.,]\d+)?\s*(persen|%|juta|ribu|jt|rb|tahun|bulan|hari|jam|menit|detik|kata|orang|klien|website|halaman|pengunjung|kunjungan|trafik|backlink)/gi;
const numberHits = (isi.match(numbersRegex) || []).length;
const example_quality = Math.min(1, (exampleHits + numberHits * 0.3) / 3);

const data_realism = numberHits > 0 ? Math.min(1, 0.4 + (numberHits / 10)) : 0.3;

const hedgeWords = ['tergantung', 'umumnya', 'biasanya', 'sebagian besar', 'mungkin', 'dalam beberapa kasus', 'idealnya', 'rata-rata', 'kemungkinan'];
const hedgeHits = hedgeWords.filter(p => isiLower.includes(p)).length;
const absoluteWords = ['pasti', 'selalu ', 'tidak pernah', '100%', 'tanpa kecuali', 'dijamin', 'sempurna'];
const absoluteHits = absoluteWords.filter(p => isiLower.includes(p)).length;
const trust_clarity = Math.max(0, Math.min(1, 0.5 + (hedgeHits * 0.1) - (absoluteHits * 0.2)));

const eeat = Math.round(
  experience_signal * 25 +
  example_quality * 25 +
  data_realism * 25 +
  trust_clarity * 25
);

// === FLAGS ===
const flags = [];
if (longParaCount > 0) flags.push(`${longParaCount} paragraf masih lebih dari 3 baris`);
if (articleText.includes('—') || articleText.includes('–')) flags.push('Em dash atau en dash terdeteksi');
if (internalLinks < 2) flags.push(`Internal links hanya ${internalLinks}, idealnya 3+`);
if (!h1Text.includes(keyword)) flags.push('Keyword utama tidak ada di H1');
if (isiWordCount < targetWords * 0.7) flags.push(`Word count rendah: ${isiWordCount}/${targetWords}`);
if (h2Texts.length < 3) flags.push(`Hanya ${h2Texts.length} H2 sections, idealnya 4+`);
if (absoluteHits > 0) flags.push(`${absoluteHits} klaim absolut terdeteksi (pasti/selalu/dijamin)`);
if (avgSentLen > 22) flags.push(`Rata-rata kalimat ${Math.round(avgSentLen)} kata, terlalu panjang`);
if (experience_signal === 0) flags.push('Tidak ada signal pengalaman/praktisi (E-E-A-T lemah)');

return [{
  json: {
    ...data,
    computed_scores: {
      readability,
      seo,
      eeat,
      flags,
      breakdown: {
        avg_sentence_length: Math.round(avgSentLen * 10) / 10,
        long_paragraph_count: longParaCount,
        complex_word_ratio: Math.round(complexRatio * 1000) / 1000,
        keyword_presence,
        heading_optimization: Math.round(heading_optimization * 100) / 100,
        semantic_variation: Math.round(semantic_variation * 100) / 100,
        internal_link_score: Math.round(internal_link_score * 100) / 100,
        content_depth: Math.round(content_depth * 100) / 100,
        experience_signal: Math.round(experience_signal * 100) / 100,
        example_quality: Math.round(example_quality * 100) / 100,
        data_realism: Math.round(data_realism * 100) / 100,
        trust_clarity: Math.round(trust_clarity * 100) / 100,
        word_count: isiWordCount,
        h2_count: h2Texts.length,
        h3_count: h3Texts.length,
        internal_link_count: internalLinks
      }
    }
  }
}];"""


# ================================================================
# Updated Build Doc Content (renders computed scores + changes)
# ================================================================

NEW_BUILD_DOC = r"""const data = $json;
const today = new Date().toISOString().split('T')[0];
const keyword = data.keyword || '';
let articleText = data.article_text || '';
const computed = data.computed_scores || {};
const changes = data.refinement_changes || [];
const metadata = data.metadata || {};

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
const skor = extractSection(articleText, '[SKOR KONTEN]', '[PENJELASAN SINGKAT]')
            || extractSection(articleText, '[SKOR KONTEN]', '[REKOMENDASI LANJUTAN]')
            || extractSection(articleText, '[SKOR KONTEN]', null);
const penjelasan = extractSection(articleText, '[PENJELASAN SINGKAT]', '[REKOMENDASI LANJUTAN]')
                  || extractSection(articleText, '[PENJELASAN SINGKAT]', null);
const rekomendasi = extractSection(articleText, '[REKOMENDASI LANJUTAN]', null);

const escHtml = (s) => String(s || '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// Publisher Box ASCII -> HTML table
function parsePublisherBox(raw) {
  const rows = [];
  const lines = raw.split('\n').filter(l => l.trim().startsWith('|'));
  let currentKey = null, currentVals = [];
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
  .split('\n').filter(l => l.trim())
  .map(l => `<p style="margin:4px 0;">${escHtml(l.trim())}</p>`)
  .join('');

// === Computed scores table (rule-based, OBJECTIVE) ===
const scoreColor = (s) => s >= 80 ? '#16a34a' : s >= 60 ? '#ca8a04' : '#dc2626';
const objectiveScoreHtml = (computed.readability !== undefined) ? `
<h2>Skor Konten (Algoritmik)</h2>
<table border="1" cellpadding="8" cellspacing="0" style="width:100%;border-collapse:collapse;border:1px solid #d1d5db;font-family:Arial,sans-serif;font-size:13px;margin:12px 0;">
  <thead><tr style="background-color:#f3f4f6;">
    <th style="padding:8px;text-align:left;width:30%;">Kategori</th>
    <th style="padding:8px;text-align:left;width:20%;">Skor</th>
    <th style="padding:8px;text-align:left;">Catatan</th>
  </tr></thead>
  <tbody>
    <tr><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #e5e7eb;">Readability</td>
        <td style="padding:8px 12px;font-weight:700;color:${scoreColor(computed.readability)};border-bottom:1px solid #e5e7eb;">${computed.readability}/100</td>
        <td style="padding:8px 12px;color:#374151;border-bottom:1px solid #e5e7eb;">avg kalimat ${computed.breakdown?.avg_sentence_length || 0} kata, ${computed.breakdown?.long_paragraph_count || 0} paragraf panjang</td></tr>
    <tr><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #e5e7eb;">SEO</td>
        <td style="padding:8px 12px;font-weight:700;color:${scoreColor(computed.seo)};border-bottom:1px solid #e5e7eb;">${computed.seo}/100</td>
        <td style="padding:8px 12px;color:#374151;border-bottom:1px solid #e5e7eb;">${computed.breakdown?.h2_count || 0} H2, ${computed.breakdown?.internal_link_count || 0} internal links, ${computed.breakdown?.word_count || 0} kata</td></tr>
    <tr><td style="padding:8px 12px;font-weight:600;border-bottom:1px solid #e5e7eb;">E-E-A-T</td>
        <td style="padding:8px 12px;font-weight:700;color:${scoreColor(computed.eeat)};border-bottom:1px solid #e5e7eb;">${computed.eeat}/100</td>
        <td style="padding:8px 12px;color:#374151;border-bottom:1px solid #e5e7eb;">experience ${computed.breakdown?.experience_signal || 0}, examples ${computed.breakdown?.example_quality || 0}, trust ${computed.breakdown?.trust_clarity || 0}</td></tr>
  </tbody>
</table>` : '';

const flagsHtml = (computed.flags && computed.flags.length) ? `
<h3>Flags Otomatis</h3>
<ul style="color:#dc2626;">
${computed.flags.map(f => `  <li>${escHtml(f)}</li>`).join('\n')}
</ul>` : '';

// === Subjective scores (LLM opinion, optional) ===
function parseSkorBox(raw) {
  if (!raw) return [];
  const items = [];
  const lines = raw.split('\n');
  for (const line of lines) {
    const m = line.match(/(Readability|SEO|E-?E-?A-?T)\s*:\s*(\d+)\s*\/\s*100/i);
    if (m) items.push({ label: m[1].toUpperCase(), score: parseInt(m[2]) });
  }
  return items;
}
const subjItems = parseSkorBox(skor);
const subjectiveHtml = subjItems.length ? `
<h3>Skor Konten (Catatan AI)</h3>
<p style="font-size:12px;color:#6b7280;margin:4px 0;">Penilaian subjektif dari AI penulis. Skor objektif algoritmik ada di tabel di atas.</p>
<table border="1" cellpadding="6" cellspacing="0" style="width:auto;border-collapse:collapse;border:1px solid #e5e7eb;font-family:Arial,sans-serif;font-size:12px;margin:8px 0;">
  <tbody>
${subjItems.map(s => `    <tr><td style="padding:4px 12px;font-weight:600;color:#374151;">${escHtml(s.label)}</td><td style="padding:4px 12px;color:#1f2937;">${s.score}/100</td></tr>`).join('\n')}
  </tbody>
</table>
${penjelasan ? `<p style="font-size:12px;color:#374151;font-style:italic;">${escHtml(penjelasan)}</p>` : ''}` : '';

function parseRekomendasi(raw) {
  if (!raw) return [];
  return raw.split('\n').map(l => l.trim())
    .filter(l => l.length > 0 && /^[-*0-9]/.test(l))
    .map(l => l.replace(/^[-*]\s*/, '').replace(/^\d+[.)]\s*/, ''));
}
const rekomendasiItems = parseRekomendasi(rekomendasi);
const rekomendasiHtml = rekomendasiItems.length ? `
<h2>Rekomendasi Lanjutan</h2>
<ul>
${rekomendasiItems.map(r => `  <li>${escHtml(r)}</li>`).join('\n')}
</ul>` : '';

// === Refinement changes ===
const changesHtml = changes.length ? `
<h2>Daftar Perubahan dari Refinement</h2>
<p style="font-size:12px;color:#6b7280;">Catatan editor pass setelah generasi awal.</p>
<ul>
${changes.map(c => `  <li>${escHtml(c)}</li>`).join('\n')}
</ul>` : '';

const fullHtml = `${publisherBoxHtml}
<h1>${escHtml(judul)}</h1>
<div>${isiHtml}</div>
<hr>
<h2>Sitasi dan Referensi</h2>
${sitasiHtml}
${objectiveScoreHtml}
${flagsHtml}
${subjectiveHtml}
${rekomendasiHtml}
${changesHtml}`;

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
    skor_subjective: subjItems,
    rekomendasi_items: rekomendasiItems,
    multipart_body: multipartBody,
    multipart_boundary: boundary
  }
}];"""


# ================================================================
# Updated Build Response (returns computed scores + changes + recommendations)
# ================================================================

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
    scores: prevData.computed_scores || { readability: 0, seo: 0, eeat: 0, flags: [] },
    scores_subjective: prevData.skor_subjective || [],
    recommendations: prevData.rekomendasi_items || [],
    refinement_changes: prevData.refinement_changes || [],
    refinement_applied: prevData.refinement_applied || false
  }
}];"""


# ================================================================
# Apply patches and add new nodes
# ================================================================

# Update existing nodes
for n in wf['nodes']:
    name = n['name']
    if name == 'Code Build Article Prompts':
        n['parameters']['jsCode'] = NEW_BUILD_PROMPTS
    elif name == 'Code Build Doc Content':
        n['parameters']['jsCode'] = NEW_BUILD_DOC
    elif name == 'Code Build Response':
        n['parameters']['jsCode'] = NEW_BUILD_RESPONSE

# Find Merge Article position to place new nodes nearby
merge_pos = next((n['position'] for n in wf['nodes'] if n['name'] == 'Merge Article'), [7000, 512])
base_x, base_y = merge_pos[0] + 240, merge_pos[1]

PROVIDER_EXPR = "$('Code Find Client').item.json.provider"
KEY_EXPR = "$('Code Find Client').item.json.api_key"
URL_EXPR = "={{ " + PROVIDER_EXPR + " === 'deepseek' ? 'https://api.deepseek.com/chat/completions' : 'https://api.anthropic.com/v1/messages' }}"

REFINE_HEADERS = {
    'parameters': [
        {'name': 'x-api-key', 'value': "={{ " + PROVIDER_EXPR + " === 'deepseek' ? '' : " + KEY_EXPR + " }}"},
        {'name': 'Authorization', 'value': "={{ " + PROVIDER_EXPR + " === 'deepseek' ? 'Bearer ' + " + KEY_EXPR + " : '' }}"},
        {'name': 'anthropic-version', 'value': '2023-06-01'},
        {'name': 'Content-Type', 'value': 'application/json'},
    ]
}

REFINE_BODY = (
    "={{ ((p, sys, usr) => JSON.stringify(\n"
    "  p === 'deepseek'\n"
    "    ? { model: 'deepseek-chat', max_tokens: 8000, temperature: 0.5, messages: [{role:'system',content:sys},{role:'user',content:usr}] }\n"
    "    : { model: 'claude-haiku-4-5-20251001', max_tokens: 8000, temperature: 0.5, system: sys, messages: [{role:'user',content:usr}] }\n"
    "))(" + PROVIDER_EXPR + ", $json.refinement_system_prompt, $json.refinement_user_prompt) }}"
)

new_nodes_to_add = [
    {
        'parameters': {'jsCode': CODE_BUILD_REFINEMENT},
        'id': 'sce-refine-build-' + uuid.uuid4().hex[:8],
        'name': 'Code Build Refinement Request',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [base_x, base_y],
    },
    {
        'parameters': {
            'method': 'POST',
            'url': URL_EXPR,
            'sendHeaders': True,
            'headerParameters': REFINE_HEADERS,
            'sendBody': True,
            'specifyBody': 'json',
            'jsonBody': REFINE_BODY,
            'options': {}
        },
        'id': 'sce-refine-http-' + uuid.uuid4().hex[:8],
        'name': 'Refine Article',
        'type': 'n8n-nodes-base.httpRequest',
        'typeVersion': 4.2,
        'position': [base_x + 240, base_y],
        'retryOnFail': True,
        'maxTries': 3,
        'waitBetweenTries': 3000,
    },
    {
        'parameters': {'jsCode': CODE_APPLY_REFINEMENT},
        'id': 'sce-refine-apply-' + uuid.uuid4().hex[:8],
        'name': 'Code Apply Refinement',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [base_x + 480, base_y],
    },
    {
        'parameters': {'jsCode': CODE_COMPUTE_SCORES},
        'id': 'sce-compute-scores-' + uuid.uuid4().hex[:8],
        'name': 'Code Compute Scores',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [base_x + 720, base_y],
    },
]

# Avoid duplicates if script runs again
existing = {n['name'] for n in wf['nodes']}
for nn in new_nodes_to_add:
    if nn['name'] not in existing:
        wf['nodes'].append(nn)

# === Re-wire connections ===
# OLD: Merge Article -> Code Build Doc Content
# NEW: Merge Article -> Code Build Refinement Request -> Refine Article -> Code Apply Refinement -> Code Compute Scores -> Code Build Doc Content

# Disconnect old: remove Merge Article -> Code Build Doc Content
ma_main = wf['connections'].get('Merge Article', {}).get('main', [[]])
if ma_main and ma_main[0]:
    ma_main[0] = [c for c in ma_main[0] if c['node'] != 'Code Build Doc Content']
    if not any(c['node'] == 'Code Build Refinement Request' for c in ma_main[0]):
        ma_main[0].append({'node': 'Code Build Refinement Request', 'type': 'main', 'index': 0})
    wf['connections']['Merge Article'] = {'main': ma_main}

# Add new chain
wf['connections']['Code Build Refinement Request'] = {
    'main': [[{'node': 'Refine Article', 'type': 'main', 'index': 0}]]
}
wf['connections']['Refine Article'] = {
    'main': [[{'node': 'Code Apply Refinement', 'type': 'main', 'index': 0}]]
}
wf['connections']['Code Apply Refinement'] = {
    'main': [[{'node': 'Code Compute Scores', 'type': 'main', 'index': 0}]]
}
wf['connections']['Code Compute Scores'] = {
    'main': [[{'node': 'Code Build Doc Content', 'type': 'main', 'index': 0}]]
}

print('Patches:')
print('  - Mode 1: Updated Code Build Article Prompts (expert prompt)')
print('  - Mode 3: Added Code Build Refinement Request')
print('  - Mode 3: Added Refine Article (HTTP)')
print('  - Mode 3: Added Code Apply Refinement')
print('  - Mode 2: Added Code Compute Scores (rule-based)')
print('  - Updated Code Build Doc Content (renders objective + subjective scores + changes)')
print('  - Updated Code Build Response (returns computed_scores + changes)')
print('  - Re-wired connections through new pipeline')

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
