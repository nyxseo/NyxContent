'use client'

import { useEffect, useState } from 'react'
import { Clock, ExternalLink, Trash2, FileText } from 'lucide-react'

type Job = {
  keyword: string
  doc_title: string
  google_docs_url: string
  metadata: { slug: string; meta_title: string; meta_description: string }
  word_count_actual: number
  internal_links_count: number
  timestamp: string
  client_name?: string
}

export default function HistoryPage() {
  const [jobs, setJobs] = useState<Job[]>([])

  useEffect(() => {
    const saved = localStorage.getItem('seo_history')
    if (saved) setJobs(JSON.parse(saved))
  }, [])

  const clearAll = () => {
    if (confirm('Hapus semua riwayat?')) {
      localStorage.removeItem('seo_history')
      setJobs([])
    }
  }

  const remove = (i: number) => {
    const updated = jobs.filter((_, idx) => idx !== i)
    setJobs(updated)
    localStorage.setItem('seo_history', JSON.stringify(updated))
  }

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('id-ID', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    } catch { return iso }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Clock className="w-6 h-6 text-brand-600" />
            Riwayat Generate
          </h1>
          <p className="text-gray-500 mt-1 text-sm">{jobs.length} artikel tersimpan di browser ini</p>
        </div>
        {jobs.length > 0 && (
          <button onClick={clearAll} className="btn-secondary flex items-center gap-2 text-red-500 border-red-200 hover:bg-red-50">
            <Trash2 className="w-4 h-4" />
            Hapus Semua
          </button>
        )}
      </div>

      {jobs.length === 0 ? (
        <div className="card p-16 flex flex-col items-center justify-center text-center">
          <Clock className="w-12 h-12 text-gray-200 mb-3" />
          <p className="text-gray-400 font-medium">Belum ada riwayat</p>
          <p className="text-gray-300 text-sm mt-1">Generate artikel pertamamu di halaman Generate</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job, i) => (
            <div key={i} className="card p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-lg bg-brand-50 border border-brand-100 flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4 text-brand-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-gray-800 text-sm truncate">{job.metadata?.meta_title || job.keyword}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {job.client_name && <span className="mr-2 text-gray-500">{job.client_name}</span>}
                      <span className="font-mono text-brand-600">/{job.metadata?.slug}</span>
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span>{job.word_count_actual?.toLocaleString()} kata</span>
                      <span>·</span>
                      <span>{job.internal_links_count} internal links</span>
                      <span>·</span>
                      <span>{formatDate(job.timestamp)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {job.google_docs_url && (
                    <a
                      href={job.google_docs_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Buka Docs
                    </a>
                  )}
                  <button
                    onClick={() => remove(i)}
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
