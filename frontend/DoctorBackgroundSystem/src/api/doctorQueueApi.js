import { request } from './http'

const PERIOD_MAP = {
  今日全部: 'all',
  上午: 'morning',
  下午: 'afternoon'
}

export const doctorQueueApi = {
  getQueue: {
    method: 'GET',
    path: '/api/doctor/queue'
  }
}

export function formatQueueDate(date = new Date()) {
  const current = date instanceof Date ? date : new Date(date)
  const year = current.getFullYear()
  const month = String(current.getMonth() + 1).padStart(2, '0')
  const day = String(current.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

export function mapQueuePeriodToApi(period) {
  return PERIOD_MAP[period] || PERIOD_MAP['今日全部']
}

export function mapQueueStatusToView(status) {
  if (status === 'pending') {
    return '待接诊'
  }

  if (status === 'ongoing') {
    return '问诊中'
  }

  if (status === 'finished') {
    return '已结束'
  }

  if (status === 'cancelled') {
    return '已取消'
  }

  return status || '未知状态'
}

export function buildDoctorQueuePath(filters = {}, date = formatQueueDate()) {
  const params = new URLSearchParams()

  params.set('date', date)
  params.set('period', mapQueuePeriodToApi(filters.period))

  if (filters.department && filters.department !== '全部') {
    params.set('department', filters.department)
  }

  return `${doctorQueueApi.getQueue.path}?${params.toString()}`
}

export async function getDoctorQueue(token, filters = {}, date = formatQueueDate()) {
  const payload = await request(buildDoctorQueuePath(filters, date), {
    method: doctorQueueApi.getQueue.method,
    token,
    unwrapData: false
  })

  return {
    list: Array.isArray(payload?.data) ? payload.data : [],
    kpi: payload?.kpi || null
  }
}
