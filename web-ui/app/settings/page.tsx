'use client'

import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Key, Eye, EyeOff, Check, Save, ExternalLink } from 'lucide-react'
import { type Provider, type SeoSettings, SETTINGS_KEY, DEFAULT_SETTINGS, loadSettings } from '@/lib/settings'

const PROVIDERS: { id: Provider; name: string; model: string; pricing: string; signupUrl: string }[] = [
  {
    id: 'claude',
    name: 'Anthropic Claude',
    model: 'claude-haiku-4-5-20251001',
    pricing: '$1 / $5 per 1M tok',
    signupUrl: 'https://console.anthropic.com/settings/keys',
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    model: 'deepseek-chat',
    pricing: '$0.27 / $1.10 per 1M tok',
    signupUrl: 'https://platform.deepseek.com/api_keys',
  },
]

export default function SettingsPage() {
  const [settings, setSettings] = useState<SeoSettings>(DEFAULT_SETTINGS)
  const [showKeys, setShowKeys] = useState({ claude: false, deepseek: false })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setSettings(loadSettings())
  }, [])

  const update = <K extends keyof SeoSettings>(key: K, value: SeoSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const save = () => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const activeKey = settings.provider === 'claude' ? settings.claude_api_key : settings.deepseek_api_key
  const activeProvider = PROVIDERS.find(p => p.id === settings.provider)!

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-brand-600" />
          Settings
        </h1>
        <p className="text-gray-500 mt-1 text-sm">
          Pilih LLM provider dan masukkan API key. Disimpan lokal di browser.
        </p>
      </div>

      {/* Provider selection */}
      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-gray-800 text-sm mb-4">LLM Provider Aktif</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PROVIDERS.map(p => {
            const active = settings.provider === p.id
            const hasKey = (p.id === 'claude' ? settings.claude_api_key : settings.deepseek_api_key).length > 0
            return (
              <button
                key={p.id}
                onClick={() => update('provider', p.id)}
                className={`text-left p-4 rounded-lg border-2 transition-all ${
                  active
                    ? 'border-brand-500 bg-brand-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="font-semibold text-sm text-gray-800">{p.name}</div>
                  {active && (
                    <span className="px-2 py-0.5 rounded-full bg-brand-600 text-white text-[10px] font-medium">
                      Aktif
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 font-mono">{p.model}</div>
                <div className="text-xs text-gray-400 mt-1">{p.pricing}</div>
                <div className="mt-2 flex items-center gap-1.5 text-xs">
                  <span className={`w-1.5 h-1.5 rounded-full ${hasKey ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className={hasKey ? 'text-green-600 font-medium' : 'text-gray-400'}>
                    {hasKey ? 'API key tersimpan' : 'API key belum diisi'}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* API Keys */}
      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-gray-800 text-sm mb-4 flex items-center gap-2">
          <Key className="w-4 h-4" />
          API Keys
        </h2>

        {PROVIDERS.map(p => {
          const fieldKey = (p.id === 'claude' ? 'claude_api_key' : 'deepseek_api_key') as keyof SeoSettings
          const value = settings[fieldKey] as string
          const visible = showKeys[p.id]
          return (
            <div key={p.id} className="mb-5 last:mb-0">
              <div className="flex items-center justify-between mb-1.5">
                <label className="label !mb-0">{p.name} API Key</label>
                <a
                  href={p.signupUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-brand-600 hover:underline flex items-center gap-1"
                >
                  Dapatkan key <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="relative">
                <input
                  type={visible ? 'text' : 'password'}
                  className="input pr-20 font-mono text-xs"
                  placeholder={p.id === 'claude' ? 'sk-ant-api03-...' : 'sk-...'}
                  value={value}
                  onChange={e => update(fieldKey, e.target.value)}
                  spellCheck={false}
                  autoComplete="off"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys(s => ({ ...s, [p.id]: !s[p.id] }))}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                  title={visible ? 'Sembunyikan' : 'Tampilkan'}
                >
                  {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Save */}
      <div className="flex items-center gap-3">
        <button
          onClick={save}
          disabled={!activeKey}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          {saved ? (
            <>
              <Check className="w-4 h-4" /> Tersimpan
            </>
          ) : (
            <>
              <Save className="w-4 h-4" /> Simpan Settings
            </>
          )}
        </button>
        {!activeKey && (
          <p className="text-xs text-amber-600">
            Isi API key untuk provider <span className="font-semibold">{activeProvider.name}</span> sebelum save.
          </p>
        )}
      </div>

      {/* Note */}
      <div className="mt-8 card p-4 bg-blue-50 border-blue-200">
        <p className="text-xs text-blue-700 font-medium mb-1">Catatan Keamanan</p>
        <p className="text-xs text-blue-600 leading-relaxed">
          API keys disimpan di localStorage browser ini saja. Tidak dikirim ke server selain ke n8n
          webhook lokal kamu. Untuk production, sebaiknya pindah ke backend env vars.
        </p>
      </div>
    </div>
  )
}
