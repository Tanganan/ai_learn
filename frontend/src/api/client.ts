/** 统一的 HTTP 出口：前端只认 /api，模型与数据库都由后端代管。 */
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }

  get isModelUnavailable(): boolean {
    return this.status === 503
  }
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  signal?: AbortSignal
}

/** SSE 事件的回调签名：事件名 + 已解析的数据 */
export type StreamEventHandler = (event: string, data: unknown) => void

/**
 * 以 POST 发起 SSE 请求（EventSource 不支持 POST，也不便于传 JSON）。
 * 服务端按 `event: xxx\ndata: {...}\n\n` 输出，这里按空行切片逐帧派发。
 */
export async function postStream(
  path: string,
  body: unknown,
  signal: AbortSignal | undefined,
  onEvent: StreamEventHandler,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      throw error
    }
    throw new ApiError('无法连接后端服务，请确认 FastAPI 已启动', 0)
  }

  if (!response.ok) {
    let message = `请求失败（HTTP ${response.status}）`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (typeof payload.detail === 'string') {
        message = payload.detail
      }
    } catch {
      // 非 JSON 响应沿用默认文案
    }
    throw new ApiError(message, response.status)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new ApiError('当前浏览器不支持流式响应', 0)
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }
      buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, '\n')

      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const frame = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        dispatchFrame(frame, onEvent)
        boundary = buffer.indexOf('\n\n')
      }
    }
    if (buffer.trim()) {
      dispatchFrame(buffer, onEvent)
    }
  } finally {
    reader.releaseLock()
  }
}

function dispatchFrame(frame: string, onEvent: StreamEventHandler) {
  let event = 'message'
  const dataLines: string[] = []

  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }

  if (dataLines.length === 0) {
    return
  }
  const raw = dataLines.join('\n')
  let data: unknown = raw
  try {
    data = JSON.parse(raw)
  } catch {
    // 保留原始字符串，交给调用方处理
  }
  onEvent(event, data)
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      throw error
    }
    throw new ApiError('无法连接后端服务，请确认 FastAPI 已启动', 0)
  }

  if (!response.ok) {
    let message = `请求失败（HTTP ${response.status}）`
    try {
      const payload = (await response.json()) as {
        detail?: string | Array<{ msg?: string }>
      }
      if (typeof payload.detail === 'string') {
        message = payload.detail
      } else if (Array.isArray(payload.detail) && payload.detail[0]?.msg) {
        message = payload.detail[0].msg
      }
    } catch {
      // 响应体不是 JSON 时沿用默认文案
    }
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}
