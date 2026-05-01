'use client'

import { useState, useEffect } from 'react'
import { Users, Plus, Pencil, Trash2, Check, X, Globe, FileText } from 'lucide-react'
import { type Client, CLIENTS_KEY as STORAGE_KEY } from '@/lib/clients'

function newClient(): Client {
  return { id: crypto.randomUUID(), client_name: '', website_url: '', sitemap_url: '' }
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [editing, setEditing] = useState<Client | null>(null)
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState<Client>(newClient())

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) setClients(JSON.parse(stored))
  }, [])

  const save = (list: Client[]) => {
    setClients(list)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  }

  const startAdd = () => {
    setDraft(newClient())
    setAdding(true)
    setEditing(null)
  }

  const startEdit = (c: Client) => {
    setDraft({ ...c })
    setEditing(c)
    setAdding(false)
  }

  const cancelForm = () => {
    setAdding(false)
    setEditing(null)
  }

  const submitAdd = (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft.client_name.trim() || !draft.website_url.trim()) return
    save([...clients, draft])
    setAdding(false)
  }

  const submitEdit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft.client_name.trim() || !draft.website_url.trim()) return
    save(clients.map(c => c.id === draft.id ? draft : c))
    setEditing(null)
  }

  const remove = (id: string) => {
    if (!confirm('Hapus klien ini?')) return
    save(clients.filter(c => c.id !== id))
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-brand-600" />
            Manajemen Klien
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            {clients.length} klien tersimpan
          </p>
        </div>
        {!adding && (
          <button onClick={startAdd} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" />
            Tambah Klien
          </button>
        )}
      </div>

      {/* Add form */}
      {adding && (
        <div className="card p-6 mb-6 border-brand-200 bg-brand-50">
          <h3 className="font-semibold text-brand-800 mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Klien Baru
          </h3>
          <form onSubmit={submitAdd} className="space-y-4">
            <ClientFormFields draft={draft} onChange={setDraft} />
            <div className="flex gap-2 pt-1">
              <button type="submit" className="btn-primary flex items-center gap-1.5 text-sm">
                <Check className="w-4 h-4" /> Simpan
              </button>
              <button type="button" onClick={cancelForm} className="btn-secondary flex items-center gap-1.5 text-sm">
                <X className="w-4 h-4" /> Batal
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Client list */}
      {clients.length === 0 && !adding ? (
        <div className="card p-12 flex flex-col items-center justify-center text-center">
          <Users className="w-12 h-12 text-gray-200 mb-3" />
          <p className="text-gray-400 font-medium">Belum ada klien</p>
          <p className="text-gray-300 text-sm mt-1 mb-4">Klik "Tambah Klien" untuk mulai</p>
          <button onClick={startAdd} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> Tambah Klien Pertama
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {clients.map(c => (
            <div key={c.id}>
              {editing?.id === c.id ? (
                <div className="card p-5 border-yellow-200 bg-yellow-50">
                  <form onSubmit={submitEdit} className="space-y-4">
                    <ClientFormFields draft={draft} onChange={setDraft} />
                    <div className="flex gap-2 pt-1">
                      <button type="submit" className="btn-primary flex items-center gap-1.5 text-sm">
                        <Check className="w-4 h-4" /> Simpan
                      </button>
                      <button type="button" onClick={cancelForm} className="btn-secondary flex items-center gap-1.5 text-sm">
                        <X className="w-4 h-4" /> Batal
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="card p-5 flex items-start gap-4">
                  <div className="w-9 h-9 rounded-lg bg-brand-100 flex items-center justify-center shrink-0">
                    <Users className="w-4 h-4 text-brand-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-800 text-sm">{c.client_name}</p>
                    <div className="mt-1 space-y-0.5">
                      <p className="text-xs text-gray-400 flex items-center gap-1.5 truncate">
                        <Globe className="w-3 h-3 shrink-0" />
                        <span className="truncate">{c.website_url}</span>
                      </p>
                      {c.sitemap_url && (
                        <p className="text-xs text-gray-400 flex items-center gap-1.5 truncate">
                          <FileText className="w-3 h-3 shrink-0" />
                          <span className="truncate">{c.sitemap_url}</span>
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <button
                      onClick={() => startEdit(c)}
                      className="p-1.5 rounded-md text-gray-400 hover:text-brand-600 hover:bg-brand-50 transition-colors"
                      title="Edit"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => remove(c.id)}
                      className="p-1.5 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                      title="Hapus"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ClientFormFields({ draft, onChange }: { draft: Client; onChange: (c: Client) => void }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div className="sm:col-span-2">
        <label className="label">Nama Klien <span className="text-red-400">*</span></label>
        <input
          className="input"
          placeholder="Contoh: Toko ABC"
          value={draft.client_name}
          onChange={e => onChange({ ...draft, client_name: e.target.value })}
          required
          autoFocus
        />
      </div>
      <div>
        <label className="label">Website URL <span className="text-red-400">*</span></label>
        <input
          className="input"
          type="url"
          placeholder="https://contoh.com"
          value={draft.website_url}
          onChange={e => onChange({ ...draft, website_url: e.target.value })}
          required
        />
      </div>
      <div>
        <label className="label">Sitemap URL <span className="text-gray-400 font-normal">(opsional)</span></label>
        <input
          className="input"
          type="url"
          placeholder="https://contoh.com/sitemap.xml"
          value={draft.sitemap_url}
          onChange={e => onChange({ ...draft, sitemap_url: e.target.value })}
        />
      </div>
    </div>
  )
}
