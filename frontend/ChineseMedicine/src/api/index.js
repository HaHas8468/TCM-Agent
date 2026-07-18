// 患者端 API 服务层：统一封装所有后端接口调用
import { request, getPatientId, getToken, BASE_URL } from '../config/http'
import {
  mapProfileToForm,
  mapFormToProfile,
  flattenDepartments,
  mapDiagnosisHistory,
  mapOrderDetail,
  mapDiagnosisToResult
} from './mappers'
import { createSseParser } from './sse-parser'

// ============ 一、鉴权 ============

// 1.1 患者注册
export function register(payload) {
  return request({
    url: '/api/auth/register',
    method: 'POST',
    data: {
      username: payload.username,
      password: payload.password,
      confirm_password: payload.confirmPassword
    },
    auth: false,
    loading: true
  })
}

// 1.2 患者登录
export function login(payload) {
  return request({
    url: '/api/auth/login',
    method: 'POST',
    data: { username: payload.username, password: payload.password },
    auth: false,
    loading: true,
    showError: false
  })
}

// ============ 二、患者档案 ============

// 2.1 获取个人档案（返回已映射的表单结构）
export function getProfile() {
  return request({
    url: '/api/patient/profile',
    method: 'GET',
    loading: true
  }).then((data) => mapProfileToForm(data))
}

// 2.2 更新个人档案
export function updateProfile(form) {
  return request({
    url: '/api/patient/profile',
    method: 'PUT',
    data: mapFormToProfile(form),
    loading: true
  })
}

// ============ 三、AI 智能问诊 ============

// 3.1b Agent 正式流式入口。服务端以 SSE 返回文本片段、结构化结果和 [DONE]。
// @returns {{ abort: Function, promise: Promise<void> }} 可取消的单次流式请求。
function createStreamRequest(payload, handlers) {
  const patientId = getPatientId()
  const token = getToken()
  const body = {
    session_id: payload.sessionId,
    user_input: payload.userInput,
    mode: payload.mode || 'normal',
    scene: payload.scene || 'guide'
  }
  if (patientId) body.patient_id = patientId
  return {
    url: BASE_URL + '/api/agent/chat/stream',
    body: JSON.stringify(body),
    headers: Object.assign(
      { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      token ? { Authorization: `Bearer ${token}` } : {}
    ),
    parser: createSseParser(handlers)
  }
}

function startH5Stream(request) {
  let reader = null
  let aborted = false
  const decoder = new TextDecoder('utf-8')
  const promise = fetch(request.url, {
    method: 'POST',
    headers: request.headers,
    body: request.body
  })
    .then((response) => {
      if (!response.ok || !response.body) {
        throw new Error(`流式请求失败（${response.status}）`)
      }
      reader = response.body.getReader()
      const pump = () => reader.read().then(({ done, value }) => {
        if (done) {
          request.parser.push(decoder.decode())
          request.parser.close()
          return
        }
        request.parser.push(decoder.decode(value, { stream: true }))
        return request.parser.isFinished() ? reader.cancel() : pump()
      })
      return pump()
    })
    .catch((error) => {
      if (!aborted && !request.parser.isFinished()) {
        request.parser.error(error)
      }
    })

  return {
    abort() {
      aborted = true
      if (reader) reader.cancel()
    },
    promise
  }
}

function startWeChatStream(request) {
  let task = null
  let aborted = false
  const decoder = new TextDecoder('utf-8')
  const promise = new Promise((resolve) => {
    task = uni.request({
      url: request.url,
      method: 'POST',
      data: request.body,
      header: request.headers,
      enableChunked: true,
      timeout: 60000,
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          request.parser.error(new Error(`流式请求失败（${res.statusCode}）`))
        }
      },
      fail: (error) => {
        if (!aborted) request.parser.error(new Error(error.errMsg || '网络异常，请稍后重试'))
      },
      complete: () => {
        request.parser.push(decoder.decode())
        if (!aborted && !request.parser.isFinished()) request.parser.close()
        resolve()
      }
    })
    task.onChunkReceived((chunk) => {
      request.parser.push(decoder.decode(chunk.data, { stream: true }))
    })
  })
  return {
    abort() {
      aborted = true
      if (task) task.abort()
    },
    promise
  }
}

export function sendAgentMessageStream(payload, handlers = {}) {
  const request = createStreamRequest(payload, handlers)
  // #ifdef MP-WEIXIN
  return startWeChatStream(request)
  // #endif
  // #ifdef H5
  return startH5Stream(request)
  // #endif
  const error = new Error('当前平台暂不支持流式智能挂号')
  handlers.onError && handlers.onError(error)
  return { abort() {}, promise: Promise.resolve() }
}

// ============ 四、挂号 ============

// 4.1 科室列表（含医生）
export function getDepartments() {
  return request({
    url: '/api/departments',
    method: 'GET',
    loading: true
  }).then((data) => flattenDepartments(data))
}

// 4.2 医生可预约时段
export function getDoctorSlots(doctorId, date) {
  return request({
    url: `/api/doctors/${doctorId}/slots`,
    method: 'GET',
    data: { date },
    loading: false
  })
}

// 4.3 创建挂号订单
export function createOrder(payload) {
  const body = {
    doctor_id: payload.doctorId,
    department: payload.department,
    date: payload.date,
    time: payload.time,
    source: payload.source || 'direct' // smart=智能推荐 / direct=直接挂号
  }
  const patientId = getPatientId()
  if (patientId) {
    body.patient_id = patientId
  }
  return request({
    url: '/api/orders',
    method: 'POST',
    data: body,
    loading: true
  })
}

// ============ 九、历史诊断（患者端） ============

// 9.1 患者历史诊断列表
export function getDiagnosisHistory(status = 'all') {
  return request({
    url: '/api/patient/diagnosis-history',
    method: 'GET',
    data: { status },
    loading: true
  }).then((list) => mapDiagnosisHistory(list))
}

// 9.2 历史诊断详情（挂号/病历详情，同 7.2）
export function getOrderDetail(orderId) {
  return request({
    url: `/api/orders/${orderId}`,
    method: 'GET',
    loading: true
  })
}

// 供页面直接使用的详情映射（结合列表带入的 status / department）
export function buildOrderDetail(data, ctx) {
  return mapOrderDetail(data, ctx)
}

// 供页面直接使用的诊断结果映射
export function buildDiagnosisResult(diagnosis, response) {
  return mapDiagnosisToResult(diagnosis, response)
}
