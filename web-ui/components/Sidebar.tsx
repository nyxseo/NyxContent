'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { FileText, Clock, Users, Zap, Settings, LogOut } from 'lucide-react'

const nav = [
  { href: '/',         label: 'Generate',  icon: Zap },
  { href: '/history',  label: 'History',   icon: Clock },
  { href: '/clients',  label: 'Clients',   icon: Users },
  { href: '/settings', label: 'Settings',  icon: Settings },
]

// Browser-side logout: send a request with bogus credentials so the browser
// drops the cached Basic Auth, then redirect to root which will re-prompt.
function handleLogout() {
  // Use a unique invalid credential to invalidate the cached one
  fetch(window.location.origin, {
    headers: { Authorization: 'Basic ' + btoa('logout:' + Date.now()) },
  }).finally(() => {
    window.location.href = '/'
  })
}

export default function Sidebar() {
  const path = usePathname()

  return (
    <aside className="w-60 shrink-0 bg-gray-900 flex flex-col h-screen">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-gray-700">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-white font-semibold text-sm leading-none">SEO Engine</p>
            <p className="text-gray-400 text-xs mt-0.5">Multi-LLM</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = path === href
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-brand-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-gray-700 space-y-2">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          title="Clear cached Basic Auth"
        >
          <LogOut className="w-3.5 h-3.5 shrink-0" />
          Logout
        </button>
        <div className="px-3">
          <p className="text-gray-500 text-xs">Claude · DeepSeek</p>
          <p className="text-gray-600 text-xs mt-0.5">Switchable di Settings</p>
        </div>
      </div>
    </aside>
  )
}
