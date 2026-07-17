import { buildApiUrl } from './http'

export const doctorAgentApi = {
  chatStream: {
    method: 'POST',
    path: '/api/agent/chat/stream'
  }
}

function normalizeSessionSuffix(value) {
  return String(value || '')
    .trim()
    .replace(/^S+/i, '')
    .replace(/[^A-Za-z0-9_-]/g, '')
}

function normalizeDoctorAgentMode(mode, patient = {}) {
  const normalizedMode = String(mode || '')
    .trim()
    .toLowerCase()

  if (normalizedMode === 'normal' || normalizedMode === 'follow-up') {
    return normalizedMode
  }

  return patient.agentSessionId ? 'follow-up' : 'normal'
}

export function buildDoctorAgentSessionId(patient = {}) {
  if (patient.agentSessionId) {
    return patient.agentSessionId
  }

  const suffix = normalizeSessionSuffix(patient.orderId || patient.recordId || patient.id || Date.now())
  return suffix ? `S${suffix}` : `S${Date.now()}`
}

export function buildDoctorAgentPayload(patient = {}, userInput = '', mode) {
  const normalizedInput = String(userInput || '').trim()
  const patientId = String(patient.id || patient.patientId || '').trim()

  return {
    session_id: buildDoctorAgentSessionId(patient),
    user_input: normalizedInput,
    mode: normalizeDoctorAgentMode(mode, patient),
    scene: 'doctor',
    ...(patientId ? { patient_id: patientId } : {})
  }
}

export function normalizeAgentDiagnosis(source = {}, responseText = '') {
  const diagnosis = source && typeof source === 'object' ? source : {}

  return {
    syndrome: String(diagnosis.syndrome || '').trim(),
    formula: String(diagnosis.prescription || diagnosis.formula || '').trim(),
    herbs: Array.isArray(diagnosis.ingredients)
      ? diagnosis.ingredients.filter(Boolean)
      : Array.isArray(diagnosis.herbs)
        ? diagnosis.herbs.filter(Boolean)
        : [],
    treatment: String(diagnosis.therapy || diagnosis.treatment || diagnosis.treatment_principle || '').trim(),
    description: String(diagnosis.description || diagnosis.syndrome_description || responseText || '').trim(),
    allergyWarnings: Array.isArray(diagnosis.allergy_warnings)
      ? diagnosis.allergy_warnings.filter(Boolean)
      : Array.isArray(diagnosis.allergyWarnings)
        ? diagnosis.allergyWarnings.filter(Boolean)
        : [],
    department: String(diagnosis.department || '').trim(),
    advice: String(diagnosis.advice || '').trim(),
    precautions: String(diagnosis.precautions || '').trim()
  }
}

function normalizeAgentResponsePayload(source = {}) {
  const payload = source && typeof source === 'object' ? source : {}
  const data = payload.data && typeof payload.data === 'object' ? payload.data : payload

  return {
    status: String(data.status || '').trim(),
    response: String(data.response ?? ''),
    session_id: String(data.session_id || '').trim(),
    finish: Boolean(data.finish),
    diagnosis: normalizeAgentDiagnosis(data.diagnosis_result || data.diagnosis, data.response || ''),
    ask_round: Number(data.ask_round) || 0
  }
}

// SSE 行缓冲解析器：按行解析 `data: ` 前缀，正确处理流式分块
function createSseLineParser(onEvent) {
  let buffer = ''
  let finished = false

  const finish = () => {
    finished = true
  }

  const consumeLine = (rawLine) => {
    const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
    if (!line) return
    if (!line.startsWith('data:')) return
    const data = line.slice(5).replace(/^ /, '')
    if (!data) return
    if (data === '[DONE]') {
      finish()
      onEvent && onEvent({ type: 'done' })
      return
    }
    if (data === '[METADATA]') {
      return
    }
    if (data.startsWith('{')) {
      try {
        const parsed = JSON.parse(data)
        const payloadData = normalizeAgentResponsePayload(parsed)
        onEvent && onEvent({ type: 'payload', data: payloadData })
      } catch (error) {
        onEvent && onEvent({ type: 'error', error: new Error('流式响应中的结构化结果格式错误') })
      }
      return
    }
    onEvent && onEvent({ type: 'text', data })
  }

  return {
    push(text) {
      if (finished || !text) return
      buffer += text
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      lines.forEach(consumeLine)
    },
    close() {
      if (finished) return
      if (buffer) consumeLine(buffer)
      if (!finished) finish()
    },
    isFinished() {
      return finished
    }
  }
}

export async function sendDoctorAgentMessage(token, patient = {}, userInput = '', mode, onChunk) {
  const payload = buildDoctorAgentPayload(patient, userInput, mode)

  if (!payload.user_input) {
    throw new Error('请先输入要发送给智能助手的内容。')
  }

  const response = await fetch(buildApiUrl(doctorAgentApi.chatStream.path), {
    method: doctorAgentApi.chatStream.method,
    headers: {
      Accept: 'text/event-stream, application/json, text/plain, */*',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(payload)
  })

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => '')
    throw new Error(text || `请求失败（HTTP ${response.status}）`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let responseText = ''
  let sessionId = payload.session_id
  let lastPayload = null

  const parser = createSseLineParser((event) => {
    if (event.type === 'payload') {
      const payloadData = event.data
      if (payloadData.session_id) {
        sessionId = payloadData.session_id
      }
      lastPayload = payloadData
      const chunk = payloadData.response || ''
      if (chunk) {
        responseText += chunk
        if (typeof onChunk === 'function') {
          onChunk(chunk, {
            responseText,
            session_id: sessionId,
            finish: Boolean(payloadData.finish),
            status: payloadData.status,
            metadata: payloadData
          })
        }
      } else if (typeof onChunk === 'function') {
        // 即使这一帧 response 为空，也通知一次（如 status/finish 变化、ask_round 计数）
        onChunk('', {
          responseText,
          session_id: sessionId,
          finish: Boolean(payloadData.finish),
          status: payloadData.status,
          metadata: payloadData
        })
      }
    } else if (event.type === 'text' && typeof onChunk === 'function') {
      responseText += event.data
      onChunk(event.data, {
        responseText,
        session_id: sessionId,
        finish: false,
        status: '',
        metadata: null
      })
    } else if (event.type === 'error' && typeof onChunk === 'function') {
      onChunk('', {
        responseText,
        session_id: sessionId,
        finish: false,
        status: 'error',
        metadata: { error: event.error.message }
      })
    }
  })

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      parser.push(chunk)
    }
  } finally {
    parser.close()
    reader.releaseLock()
  }

  return {
    ...(lastPayload || normalizeAgentResponsePayload({ data: {} })),
    response: responseText,
    session_id: sessionId,
    diagnosis: normalizeAgentDiagnosis(lastPayload?.diagnosis, responseText)
  }
}
