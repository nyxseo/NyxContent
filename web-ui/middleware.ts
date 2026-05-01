import { NextRequest, NextResponse } from 'next/server'

/**
 * Basic Auth middleware. Protects all routes (UI + API) behind a single
 * username/password set via env vars: UI_USERNAME and UI_PASSWORD.
 *
 * If either env var is missing, auth is DISABLED (useful for local dev).
 */
export function middleware(req: NextRequest) {
  const username = process.env.UI_USERNAME
  const password = process.env.UI_PASSWORD

  // No credentials configured → skip auth (local dev convenience)
  if (!username || !password) return NextResponse.next()

  const auth = req.headers.get('authorization')

  if (auth) {
    const [scheme, encoded] = auth.split(' ')
    if (scheme === 'Basic' && encoded) {
      try {
        const decoded = atob(encoded)
        const sepIdx = decoded.indexOf(':')
        const user = decoded.slice(0, sepIdx)
        const pass = decoded.slice(sepIdx + 1)
        if (user === username && pass === password) {
          return NextResponse.next()
        }
      } catch {
        // fall through to 401
      }
    }
  }

  return new NextResponse('Authentication required', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Nyx SEO Engine"',
      'Content-Type': 'text/plain',
    },
  })
}

export const config = {
  // Protect everything except Next.js internals and static files
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|gif|svg|ico|webp)$).*)'],
}
