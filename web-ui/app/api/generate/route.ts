import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const n8nUrl = process.env.N8N_WEBHOOK_URL
  if (!n8nUrl) {
    return NextResponse.json(
      { status: 'error', message: 'N8N_WEBHOOK_URL belum dikonfigurasi di environment variables' },
      { status: 500 }
    )
  }

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ status: 'error', message: 'Request body tidak valid' }, { status: 400 })
  }

  try {
    const n8nRes = await fetch(n8nUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(process.env.WEBHOOK_SECRET ? { 'X-Webhook-Secret': process.env.WEBHOOK_SECRET } : {}),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10 * 60 * 1000),
    })

    const text = await n8nRes.text()

    if (!text || !text.trim()) {
      return NextResponse.json(
        {
          status: 'error',
          message: `n8n workflow gagal (HTTP ${n8nRes.status}) — response kosong. Kemungkinan: Google credentials belum di-authorize, atau ada node yang error. Cek http://localhost:5678/executions untuk detail.`,
        },
        { status: 502 }
      )
    }

    let data: unknown
    try {
      data = JSON.parse(text)
    } catch {
      return NextResponse.json(
        {
          status: 'error',
          message: `n8n mengembalikan response tidak valid (HTTP ${n8nRes.status}): ${text.slice(0, 300)}`,
        },
        { status: 502 }
      )
    }

    return NextResponse.json(data, { status: n8nRes.ok ? 200 : 502 })
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Unknown error'
    if (msg.includes('TimeoutError') || msg.includes('abort') || msg.includes('The operation was aborted')) {
      return NextResponse.json(
        { status: 'error', message: 'Timeout — n8n membutuhkan waktu terlalu lama (>10 menit). Coba lagi.' },
        { status: 504 }
      )
    }
    return NextResponse.json(
      { status: 'error', message: `Gagal menghubungi n8n: ${msg}` },
      { status: 502 }
    )
  }
}
