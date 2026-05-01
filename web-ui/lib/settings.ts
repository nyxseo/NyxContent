export type Provider = 'claude' | 'deepseek'

export type SeoSettings = {
  provider: Provider
  claude_api_key: string
  deepseek_api_key: string
}

export const SETTINGS_KEY = 'seo_settings'

export const DEFAULT_SETTINGS: SeoSettings = {
  provider: 'claude',
  claude_api_key: '',
  deepseek_api_key: '',
}

export function loadSettings(): SeoSettings {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (!raw) return DEFAULT_SETTINGS
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return DEFAULT_SETTINGS
  }
}
