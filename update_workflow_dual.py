"""Patch n8n workflow to support both Claude and DeepSeek providers."""
import json
import sys

WF_PATH = 'G:/NyxContent/workflow_live.json'
OUT_PATH = 'G:/NyxContent/workflow_put.json'

with open(WF_PATH) as f:
    wf = json.load(f)

# === Header parameters with conditional values ===
HEADERS = {
    'parameters': [
        {'name': 'x-api-key', 'value': "={{ $json.provider === 'deepseek' ? 'unused' : $json.api_key }}"},
        {'name': 'Authorization', 'value': "={{ $json.provider === 'deepseek' ? 'Bearer ' + $json.api_key : 'Bearer unused' }}"},
        {'name': 'anthropic-version', 'value': '2023-06-01'},
        {'name': 'Content-Type', 'value': 'application/json'},
    ]
}

URL_EXPR = "={{ $json.provider === 'deepseek' ? 'https://api.deepseek.com/chat/completions' : 'https://api.anthropic.com/v1/messages' }}"

# Body expressions: each picks Claude or DeepSeek shape based on provider
META_GEN_BODY = (
    "={{ ((p, sys, usr) => JSON.stringify(\n"
    "  p === 'deepseek'\n"
    "    ? { model: 'deepseek-chat', max_tokens: 1500, temperature: 0.3, messages: [{role:'system',content:sys},{role:'user',content:usr}] }\n"
    "    : { model: 'claude-haiku-4-5-20251001', max_tokens: 1500, temperature: 0.3, system: sys, messages: [{role:'user',content:usr}] }\n"
    "))(\n"
    "  $json.provider,\n"
    "  \"Kamu adalah SEO expert Indonesia berpengalaman. Tugasmu adalah membuat metadata SEO yang optimal. Jawab HANYA dalam format JSON valid tanpa teks tambahan apapun, tanpa markdown code fences.\",\n"
    "  `Buat metadata SEO lengkap untuk artikel dengan keyword target: '${$json.keyword}'\\n\\nWebsite klien: ${$json.website_url}\\n\\nBuat output dalam format JSON berikut (isi semua field, TANPA markdown code fences):\\n{\\n  \"slug\": \"url-artikel-tanpa-spasi-gunakan-strip\",\\n  \"meta_title\": \"Judul SEO 50-60 karakter mengandung keyword\",\\n  \"meta_description\": \"Deskripsi 150-160 karakter menarik mengandung keyword dan CTA\",\\n  \"alt_texts\": [\"Alt 1\",\"Alt 2\",\"Alt 3\",\"Alt 4\",\"Alt 5\"],\\n  \"excerpt\": \"Ringkasan artikel 2-3 kalimat menarik untuk preview\"\\n}`\n"
    ") }}"
)

META_RETRY_BODY = (
    "={{ ((p, sys, usr) => JSON.stringify(\n"
    "  p === 'deepseek'\n"
    "    ? { model: 'deepseek-chat', max_tokens: 1500, temperature: 0.1, messages: [{role:'system',content:sys},{role:'user',content:usr}] }\n"
    "    : { model: 'claude-haiku-4-5-20251001', max_tokens: 1500, temperature: 0.1, system: sys, messages: [{role:'user',content:usr}] }\n"
    "))(\n"
    "  $json.provider,\n"
    "  \"Kamu adalah SEO expert. Output HARUS JSON valid yang lengkap, tanpa code fences, tanpa teks tambahan.\",\n"
    "  `Retry: buat metadata SEO untuk keyword '${$json.keyword}'. Output JSON dengan field: slug, meta_title, meta_description, alt_texts (array 5 string), excerpt. JSON murni saja.`\n"
    ") }}"
)

# Article body uses pre-built prompts from Code node (kept short here)
ART_GEN_BODY = (
    "={{ ((p, sys, usr) => JSON.stringify(\n"
    "  p === 'deepseek'\n"
    "    ? { model: 'deepseek-chat', max_tokens: 8000, temperature: 0.7, messages: [{role:'system',content:sys},{role:'user',content:usr}] }\n"
    "    : { model: 'claude-haiku-4-5-20251001', max_tokens: 8000, temperature: 0.7, system: sys, messages: [{role:'user',content:usr}] }\n"
    "))($json.provider, $json.article_system_prompt, $json.article_user_prompt) }}"
)

ART_RETRY_BODY = (
    "={{ ((p, sys, usr) => JSON.stringify(\n"
    "  p === 'deepseek'\n"
    "    ? { model: 'deepseek-chat', max_tokens: 8000, temperature: 0.5, messages: [{role:'system',content:sys},{role:'user',content:usr}] }\n"
    "    : { model: 'claude-haiku-4-5-20251001', max_tokens: 8000, temperature: 0.5, system: sys, messages: [{role:'user',content:usr}] }\n"
    "))($json.provider, $json.article_retry_system_prompt, $json.article_retry_user_prompt) }}"
)

# === Code Find Client: pull provider + api_key from webhook body ===
NEW_FIND_CLIENT = """const body = $('Webhook').item.json.body;
const clientName = body.client_name;
const rows = items;

const match = rows.find(item => item.json.client_name === clientName);
if (!match) {
  throw new Error(`Client '${clientName}' not found in Google Sheets`);
}

const provider = (body.provider || 'claude').toLowerCase();
if (!['claude','deepseek'].includes(provider)) {
  throw new Error(`Unsupported provider: ${provider}`);
}
const apiKey = body.api_key || '';
if (!apiKey) {
  throw new Error(`API key untuk provider '${provider}' belum diisi di Settings`);
}

return [{
  json: {
    client_name: match.json.client_name,
    website_url: match.json.website_url,
    sitemap_url: match.json.sitemap_url || '',
    drive_folder_id: match.json.drive_folder_id || '',
    articles_folder_id: match.json.articles_folder_id || '',
    keyword: body.keyword,
    word_count: parseInt(body.word_count) || 1500,
    tone: body.tone || 'profesional',
    provider: provider,
    api_key: apiKey
  }
}];"""

# === Parsers handle both Claude (content[0].text) and DeepSeek (choices[0].message.content) ===
NEW_PARSE_METADATA = r"""const response = $json;
const prevData = $('Code Classify Pages').item.json;

let rawText = '';
try {
  rawText = response.content?.[0]?.text || response.choices?.[0]?.message?.content || '';
} catch(e) {
  throw new Error('LLM metadata response malformed: ' + JSON.stringify(response).slice(0, 500));
}

if (!rawText) {
  throw new Error('Empty LLM response: ' + JSON.stringify(response).slice(0, 500));
}

rawText = rawText.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/\s*```$/i, '').trim();

let metadata;
try {
  metadata = JSON.parse(rawText);
} catch(e) {
  return [{ json: { ...prevData, metadata_valid: false, metadata_raw: rawText, metadata: null } }];
}

const isValid = metadata.slug && metadata.meta_title && metadata.meta_description &&
  Array.isArray(metadata.alt_texts) && metadata.alt_texts.length >= 1 && metadata.excerpt;

return [{
  json: {
    ...prevData,
    metadata_valid: !!isValid,
    metadata_raw: rawText,
    metadata: metadata
  }
}];"""

NEW_VALIDATE_ARTICLE = r"""const response = $json;
const prevData = $('Merge Metadata').item.json;

let articleText = '';
try {
  articleText = response.content?.[0]?.text || response.choices?.[0]?.message?.content || '';
} catch(e) {
  throw new Error('LLM article response malformed');
}

if (!articleText) {
  throw new Error('Empty article text: ' + JSON.stringify(response).slice(0, 300));
}

const hasPublisherBox = articleText.includes('[PUBLISHER BOX]');
const hasTitle = articleText.includes('[JUDUL ARTIKEL]');
const hasContent = articleText.includes('[ISI ARTIKEL]');
const hasCitations = articleText.includes('[SITASI/REFERENSI]');

const wordCount = articleText.split(/\s+/).filter(w => w.length > 0).length;
const targetWords = prevData.word_count;
const wordCountOk = wordCount >= targetWords * 0.75;

const isValid = hasPublisherBox && hasTitle && hasContent && hasCitations && wordCountOk;

return [{
  json: {
    ...prevData,
    article_text: articleText,
    article_valid: isValid,
    article_word_count: wordCount,
    validation_details: { hasPublisherBox, hasTitle, hasContent, hasCitations, wordCount, targetWords, wordCountOk }
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

return [{
  json: {
    ...prevData,
    article_text: articleText || prevData.article_text || '',
    article_valid: true
  }
}];"""

# === Build article prompts in a Code node so Article HTTP nodes can reference them ===
# This Code node sits between "Merge Metadata" and "Claude Generate Article"
BUILD_ARTICLE_PROMPTS = r"""const data = items[0].json;

const sysPrompt = "Kamu adalah penulis konten SEO profesional Indonesia. Tugas kamu adalah membuat artikel blog berkualitas tinggi yang ramah SEO, informatif, dan engaging. Ikuti PERSIS format output yang diminta.";

const userPrompt = `Buat artikel SEO lengkap dengan spesifikasi berikut:

=== DATA ARTIKEL ===
Keyword Target: ${data.keyword}
Jumlah Kata Target: ${data.word_count} kata
Tone: ${data.tone}
Website Klien: ${data.website_url}

=== METADATA SEO ===
Slug: ${data.metadata.slug}
Meta Title: ${data.metadata.meta_title}
Meta Description: ${data.metadata.meta_description}
Excerpt: ${data.metadata.excerpt}
Alt Text Utama: ${data.metadata.alt_texts[0]}

=== REFERENSI 1 ===
Judul: ${data.ref_1_title}
URL: ${data.ref_1_url}
Konten:
${data.ref_1_markdown}

=== REFERENSI 2 ===
Judul: ${data.ref_2_title}
URL: ${data.ref_2_url}
Konten:
${data.ref_2_markdown}

=== REFERENSI 3 ===
Judul: ${data.ref_3_title}
URL: ${data.ref_3_url}
Konten:
${data.ref_3_markdown}

=== INTERNAL LINKS - TOFU ===
${data.blog_links_text}

=== INTERNAL LINKS - BOFU ===
${data.money_links_text}

=== FORMAT OUTPUT WAJIB ===
[PUBLISHER BOX]
+--------------------------------------------------+
| KEYWORD TARGET: ${data.keyword}
| URL SLUG: ${data.metadata.slug}
| META TITLE: ${data.metadata.meta_title}
| META DESCRIPTION: ${data.metadata.meta_description}
| ALT TEXT: ${data.metadata.alt_texts[0]}
| EXCERPT: ${data.metadata.excerpt}
| REFERENSI:
|   1. ${data.ref_1_title} - ${data.ref_1_url}
|   2. ${data.ref_2_title} - ${data.ref_2_url}
|   3. ${data.ref_3_title} - ${data.ref_3_url}
| WEBSITE: ${data.website_url}
+--------------------------------------------------+

[JUDUL ARTIKEL]
${data.metadata.meta_title}

[ISI ARTIKEL]
(Tulis artikel lengkap ${data.word_count} kata. Gunakan H2 dan H3 untuk struktur. Sisipkan TOFU internal links di bagian edukasi dengan anchor text yang natural. Sisipkan BOFU internal links di bagian akhir/CTA. Gunakan keyword secara natural di seluruh artikel.)

[SITASI/REFERENSI]
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}`;

const retrySys = "Kamu adalah penulis konten SEO profesional Indonesia. Ikuti PERSIS format output yang diminta. Ini adalah retry - pastikan semua section [PUBLISHER BOX], [JUDUL ARTIKEL], [ISI ARTIKEL], [SITASI/REFERENSI] ada.";

const retryUser = `Buat artikel SEO ${data.word_count} kata untuk keyword '${data.keyword}'.

Website: ${data.website_url}
Metadata: slug=${data.metadata.slug}, title=${data.metadata.meta_title}

Referensi:
1. ${data.ref_1_title} - ${data.ref_1_url}
2. ${data.ref_2_title} - ${data.ref_2_url}
3. ${data.ref_3_title} - ${data.ref_3_url}

GUNAKAN FORMAT INI PERSIS:
[PUBLISHER BOX]
+--------------------------------------------------+
| KEYWORD TARGET: ${data.keyword}
| URL SLUG: ${data.metadata.slug}
| META TITLE: ${data.metadata.meta_title}
| META DESCRIPTION: ${data.metadata.meta_description}
| EXCERPT: ${data.metadata.excerpt}
+--------------------------------------------------+

[JUDUL ARTIKEL]
${data.metadata.meta_title}

[ISI ARTIKEL]
(Tulis artikel lengkap ${data.word_count} kata)

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

# Apply node updates
fixes = []
for n in wf['nodes']:
    name = n['name']
    params = n['parameters']

    if name == 'Code Find Client':
        params['jsCode'] = NEW_FIND_CLIENT
        fixes.append('Code Find Client')
    elif name == 'Code Parse Metadata':
        params['jsCode'] = NEW_PARSE_METADATA
        fixes.append('Code Parse Metadata')
    elif name == 'Code Validate Article':
        params['jsCode'] = NEW_VALIDATE_ARTICLE
        fixes.append('Code Validate Article')
    elif name == 'Code Validate Retry':
        params['jsCode'] = NEW_VALIDATE_RETRY
        fixes.append('Code Validate Retry')
    elif name == 'Claude Generate Metadata':
        params['url'] = URL_EXPR
        params['headerParameters'] = HEADERS
        params['jsonBody'] = META_GEN_BODY
        fixes.append('Claude Generate Metadata')
    elif name == 'Claude Metadata Retry':
        params['url'] = URL_EXPR
        params['headerParameters'] = HEADERS
        params['jsonBody'] = META_RETRY_BODY
        fixes.append('Claude Metadata Retry')
    elif name == 'Claude Generate Article':
        params['url'] = URL_EXPR
        params['headerParameters'] = HEADERS
        params['jsonBody'] = ART_GEN_BODY
        fixes.append('Claude Generate Article')
    elif name == 'Claude Article Retry':
        params['url'] = URL_EXPR
        params['headerParameters'] = HEADERS
        params['jsonBody'] = ART_RETRY_BODY
        fixes.append('Claude Article Retry')

# === Insert "Code Build Article Prompts" node between Merge Metadata and Claude Generate Article ===
existing_names = {n['name'] for n in wf['nodes']}
if 'Code Build Article Prompts' not in existing_names:
    # Find Merge Metadata node position to place new node nearby
    merge_pos = next((n['position'] for n in wf['nodes'] if n['name'] == 'Merge Metadata'), [5500, 512])
    new_node = {
        'parameters': {'jsCode': BUILD_ARTICLE_PROMPTS},
        'id': 'sce-build-art-prompts-0001',
        'name': 'Code Build Article Prompts',
        'type': 'n8n-nodes-base.code',
        'typeVersion': 2,
        'position': [merge_pos[0] + 200, merge_pos[1]],
    }
    wf['nodes'].append(new_node)
    fixes.append('+ Code Build Article Prompts (new node)')

# Re-wire connections:
# OLD:  Merge Metadata -> Claude Generate Article
# NEW:  Merge Metadata -> Code Build Article Prompts -> Claude Generate Article
mm = wf['connections'].get('Merge Metadata', {}).get('main', [[]])
if mm and mm[0]:
    # If Merge Metadata still points to Claude Generate Article, redirect via new node
    if any(c['node'] == 'Claude Generate Article' for c in mm[0]):
        mm[0] = [c for c in mm[0] if c['node'] != 'Claude Generate Article']
        mm[0].append({'node': 'Code Build Article Prompts', 'type': 'main', 'index': 0})
        wf['connections']['Code Build Article Prompts'] = {
            'main': [[{'node': 'Claude Generate Article', 'type': 'main', 'index': 0}]]
        }
        fixes.append('Rewired: Merge Metadata -> Code Build Article Prompts -> Claude Generate Article')

# Same for Article Retry: needs prompts too. The retry path is: IF Article Valid (false) -> Claude Article Retry
# But retry also references $json.article_retry_user_prompt. The data flows from Code Validate Article (which has prevData from Merge Metadata).
# The retry doesn't go through Code Build Article Prompts, so we need to make sure the prompts persist.
# Simpler: also expose retry prompts via the Code Build Article Prompts node, and ensure Code Validate Article preserves them.

# Update Code Validate Article to preserve article_retry_*_prompt fields from prevData
# (prevData is $('Merge Metadata').item.json — but those fields are added by Code Build Article Prompts which runs AFTER Merge Metadata)
# Better: change validate to pull from Code Build Article Prompts
NEW_VALIDATE_ARTICLE_V2 = NEW_VALIDATE_ARTICLE.replace(
    "$('Merge Metadata').item.json",
    "$('Code Build Article Prompts').item.json"
)
for n in wf['nodes']:
    if n['name'] == 'Code Validate Article':
        n['parameters']['jsCode'] = NEW_VALIDATE_ARTICLE_V2

print('All fixes:')
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
