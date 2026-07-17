// 后续如果后端不是同源部署，统一在这里填写 baseURL，例如：http://127.0.0.1:8000
const CUSTOM_API_BASE_URL = 'http://111.119.237.88:16009'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || CUSTOM_API_BASE_URL

function normalizeBaseUrl(value) {
  return String(value || '').trim().replace(/\/+$/, '')
}

export function buildApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const normalizedBaseUrl = normalizeBaseUrl(API_BASE_URL)

  return normalizedBaseUrl ? `${normalizedBaseUrl}${normalizedPath}` : normalizedPath
}

async function parseResponseBody(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    return response.json()
  }

  const text = await response.text()
  return text ? { msg: text } : null
}

function formatHttpErrorMessage(response, payload) {
  if (payload?.msg) {
    return payload.msg
  }

  if (payload?.detail) {
    if (typeof payload.detail === 'string') {
      return payload.detail
    }

    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => item?.msg || item?.message || JSON.stringify(item))
        .filter(Boolean)
        .join('；')
    }
  }

  return `请求失败（HTTP ${response.status}）`
}

export async function request(path, options = {}) {
  const { method = 'GET', data, headers = {}, token, unwrapData = true } = options
  const url = buildApiUrl(path)
  const requestHeaders = {
    Accept: 'application/json',
    ...headers
  }

  if (data !== undefined) {
    requestHeaders['Content-Type'] = 'application/json'
  }

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`
  }

  let response

  try {
    response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: data !== undefined ? JSON.stringify(data) : undefined
    })
  } catch (error) {
    console.error('[http] network error', {
      url,
      method,
      headers: requestHeaders,
      data,
      error
    })

    throw new Error('无法连接到医生端接口，请检查 baseURL 或服务状态。')
  }

  const payload = await parseResponseBody(response)

  if (!response.ok) {
    console.error('[http] request failed', {
      url,
      method,
      status: response.status,
      statusText: response.statusText,
      requestData: data,
      responseBody: payload
    })

    throw new Error(formatHttpErrorMessage(response, payload))
  }

  if (payload && typeof payload.code !== 'undefined' && payload.code !== 0) {
    console.error('[http] business error', {
      url,
      method,
      requestData: data,
      responseBody: payload
    })

    throw new Error(payload.msg || '接口返回失败，请稍后重试。')
  }

  return unwrapData ? payload?.data ?? payload : payload
}
