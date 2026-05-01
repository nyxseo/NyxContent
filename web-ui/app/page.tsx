'use client'

import { useState, useEffect } from 'react'
import { Zap, ExternalLink, Copy, CheckCircle, AlertCircle, Loader2, ChevronDown, Users, Cpu, Settings as SettingsIcon } from 'lucide-react'
import Link from 'next/link'
import type { Client } from '@/lib/clients'
import { loadSettings, type SeoSettings, type Provider } from '@/lib/settings'

const TONES = ['profesional', 'casual', 'akademis', 'persuasif', 'informatif']

const PROVIDER_LABELS: Record<Provider, string> = {
  claude: 'Claude (Anthropic)',
  deepseek: 'DeepSeek',
}

type JobResult = {
  status: string
  google_docs_url: string
  metadata: { slug: string; meta_title: string; meta_description: string }
  preview: string
  internal_links_count: number
  references: { title: string; url: string }[]
  word_count_actual: number
  keyword: string
  doc_title: string
  timestamp: string
}

export default function GeneratePage() {
  const [clients, setClients] = useState<Client[]>([])
  const [settings, setSettings] = useState<SeoSettings | null>(null)
  const [form, setForm] = useState({
    client_name: '',
    keyword: '',
    word_count: '1500',
    tone: 'profesional',
    provider: 'claude' as Provider,
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<JobResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('seo_clients')
    if (stored) setClients(JSON.parse(stored))
    const s = loadSettings()
    setSettings(s)
    setForm(f => ({ ...f, provider: s.provider }))
  }, [])

  const apiKeyForProvider = (p: Provider): string => {
    if (!settings) return ''
    return p === 'claude' ? settings.claude_api_key : settings.deepseek_api_key
  }
  const currentApiKey = apiKeyForProvider(form.provider)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentApiKey) {
      setError(`API key untuk ${PROVIDER_LABELS[form.provider]} belum diisi. Buka Settings dulu.`)
      return
    }
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          word_count: parseInt(form.word_count),
          api_key: currentApiKey,
        }),
      })
      const data = await res.json()

      if (!res.ok || data.status === 'error') {
        throw new Error(data.message || 'Terjadi kesalahan pada server')
      }

      const job: JobResult = { ...data, timestamp: new Date().toISOString() }
      setResult(job)

      // Simpan ke localStorage
      const history: JobResult[] = JSON.parse(localStorage.getItem('seo_history') || '[]')
      history.unshift(job)
      localStorage.setItem('seo_history', JSON.stringify(history.slice(0, 50)))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const copyUrl = () => {
    if (result?.google_docs_url) {
      navigator.clipboard.writeText(result.google_docs_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Zap className="w-6 h-6 text-brand-600" />
          Generate Artikel SEO
        </h1>
        <p className="text-gray-500 mt-1 text-sm">
          Isi form di bawah, klik Generate, dan tunggu artikel selesai (~3-5 menit)
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="card p-6 space-y-5">
            <div>
              <label className="label">Nama Client</label>
              {clients.length === 0 ? (
                <div className="input flex items-center gap-2 text-gray-400 text-sm cursor-default select-none">
                  <Users className="w-4 h-4 shrink-0" />
                  <span>Belum ada klien —</span>
                  <Link href="/clients" className="text-brand-600 hover:underline font-medium">Tambah dulu</Link>
                </div>
              ) : (
                <div className="relative">
                  <select
                    className="input appearance-none pr-8"
                    value={form.client_name}
                    onChange={e => setForm({ ...form, client_name: e.target.value })}
                    required
                  >
                    <option value="">— Pilih klien —</option>
                    {clients.map(c => (
                      <option key={c.id} value={c.client_name}>{c.client_name}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                </div>
              )}
            </div>

            <div>
              <label className="label">Keyword Target</label>
              <input
                className="input"
                placeholder="Contoh: jasa seo jakarta"
                value={form.keyword}
                onChange={e => setForm({ ...form, keyword: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="label">Jumlah Kata</label>
              <input
                className="input"
                type="number"
                min="500"
                max="5000"
                step="100"
                value={form.word_count}
                onChange={e => setForm({ ...form, word_count: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="label">Tone Penulisan</label>
              <div className="relative">
                <select
                  className="input appearance-none pr-8"
                  value={form.tone}
                  onChange={e => setForm({ ...form, tone: e.target.value })}
                >
                  {TONES.map(t => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            <div>
              <label className="label flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" />
                LLM Provider
              </label>
              <div className="relative">
                <select
                  className="input appearance-none pr-8"
                  value={form.provider}
                  onChange={e => setForm({ ...form, provider: e.target.value as Provider })}
                >
                  {(Object.keys(PROVIDER_LABELS) as Provider[]).map(p => (
                    <option key={p} value={p}>
                      {PROVIDER_LABELS[p]} {apiKeyForProvider(p) ? '✓' : '— belum ada API key'}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
              {!currentApiKey && (
                <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                  API key kosong —{' '}
                  <Link href="/settings" className="text-brand-600 hover:underline font-medium inline-flex items-center gap-0.5">
                    <SettingsIcon className="w-3 h-3" /> isi di Settings
                  </Link>
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !currentApiKey || clients.length === 0}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating... (~3-5 menit)
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Generate Artikel
                </>
              )}
            </button>
          </form>

          {/* Info box */}
          <div className="mt-4 card p-4 bg-blue-50 border-blue-200">
            <p className="text-xs text-blue-700 font-medium mb-1">Estimasi Biaya per Artikel</p>
            <p className="text-xs text-blue-600 leading-relaxed">
              {form.provider === 'claude' ? 'Claude Haiku 4.5' : 'DeepSeek Chat'}: ~$0.005–0.03<br />
              SerpAPI: ~$0.01<br />
              Firecrawl: sesuai plan
            </p>
          </div>
        </div>

        {/* Result */}
        <div className="lg:col-span-3">
          {error && (
            <div className="card p-5 border-red-200 bg-red-50 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-red-700 text-sm">Gagal Generate</p>
                <p className="text-red-600 text-sm mt-1">{error}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="card p-10 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-10 h-10 text-brand-500 animate-spin mb-4" />
              <p className="font-semibold text-gray-700">Sedang Memproses...</p>
              <p className="text-gray-400 text-sm mt-2">Riset web + generate artikel dengan Claude AI</p>
              <div className="mt-6 space-y-2 text-left w-full max-w-xs">
                {['Mencari referensi di web...', 'Crawling website klien...', 'Membuat metadata SEO...', 'Menulis artikel lengkap...'].map((step, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-gray-400">
                    <Loader2 className="w-3 h-3 animate-spin shrink-0" />
                    {step}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-4">
              {/* Success header */}
              <div className="card p-5 border-brand-200 bg-brand-50">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-brand-600" />
                  <p className="font-semibold text-brand-700">Artikel Berhasil Dibuat!</p>
                </div>
                <div className="flex gap-2">
                  <a
                    href={result.google_docs_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary flex items-center gap-2 text-sm"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Buka Google Docs
                  </a>
                  <button onClick={copyUrl} className="btn-secondary flex items-center gap-2 text-sm">
                    {copied ? <CheckCircle className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied!' : 'Copy URL'}
                  </button>
                </div>
              </div>

              {/* Metadata */}
              <div className="card p-5">
                <h3 className="font-semibold text-gray-800 text-sm mb-3">Metadata SEO</h3>
                <div className="space-y-2.5">
                  <MetaRow label="Slug" value={`/${result.metadata.slug}`} />
                  <MetaRow label="Meta Title" value={result.metadata.meta_title} />
                  <MetaRow label="Meta Description" value={result.metadata.meta_description} />
                  <MetaRow label="Jumlah Kata" value={`${result.word_count_actual?.toLocaleString()} kata`} />
                  <MetaRow label="Internal Links" value={`${result.internal_links_count} halaman`} />
                </div>
              </div>

              {/* Preview */}
              <div className="card p-5">
                <h3 className="font-semibold text-gray-800 text-sm mb-2">Preview Artikel</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{result.preview}...</p>
              </div>

              {/* References */}
              {result.references?.length > 0 && (
                <div className="card p-5">
                  <h3 className="font-semibold text-gray-800 text-sm mb-3">Referensi ({result.references.length})</h3>
                  <div className="space-y-2">
                    {result.references.map((ref, i) => (
                      <a
                        key={i}
                        href={ref.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-start gap-2 text-sm text-brand-600 hover:text-brand-700 hover:underline"
                      >
                        <span className="text-gray-400 shrink-0">{i + 1}.</span>
                        <span className="truncate">{ref.title || ref.url}</span>
                        <ExternalLink className="w-3 h-3 shrink-0 mt-0.5" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!result && !loading && !error && (
            <div className="card p-10 flex flex-col items-center justify-center text-center h-64">
              <Zap className="w-12 h-12 text-gray-200 mb-3" />
              <p className="text-gray-400 font-medium">Hasil artikel akan muncul di sini</p>
              <p className="text-gray-300 text-sm mt-1">Isi form dan klik Generate</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <span className="text-xs text-gray-400 w-32 shrink-0 pt-0.5">{label}</span>
      <span className="text-xs text-gray-700 font-mono break-all">{value}</span>
    </div>
  )
}
