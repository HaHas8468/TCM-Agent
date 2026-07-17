import { request } from './http'

const DEFAULT_PAGE = 1
const DEFAULT_PAGE_SIZE = 20

export const doctorRecordsApi = {
  searchRecords: {
    method: 'GET',
    path: '/api/records'
  },
  getRecordDetail: {
    method: 'GET',
    path: '/api/records'
  },
  getPatientHistory: {
    method: 'GET',
    path: '/api/patient'
  },
  getPatientBasic: {
    method: 'GET',
    path: '/api/patients/bypatientid'
  }
}

export function formatRecordDateTime(value) {
  const text = String(value || '').trim()

  if (!text) {
    return ''
  }

  return text.replace('T', ' ').slice(0, 16)
}

function buildDateFilter(value) {
  const text = String(value || '').trim()
  return text || ''
}

export function buildRecordsSearchPath(filters = {}, pagination = {}) {
  const params = new URLSearchParams()
  const page = pagination.page || DEFAULT_PAGE
  const pageSize = pagination.pageSize || DEFAULT_PAGE_SIZE
  const patientName = String(filters.patientName || filters.name || '').trim()
  const patientId = String(filters.patientId || '').trim()
  const syndrome = String(filters.syndrome || '').trim()
  const date = buildDateFilter(filters.date)

  params.set('page', String(page))
  params.set('page_size', String(pageSize))

  if (patientName) {
    params.set('name', patientName)
  }

  if (patientId) {
    params.set('patient_id', patientId)
  }

  if (syndrome) {
    params.set('syndrome', syndrome)
  }

  if (date) {
    params.set('date_from', date)
    params.set('date_to', date)
  }

  return `${doctorRecordsApi.searchRecords.path}?${params.toString()}`
}

export function normalizeRecordListItem(source = {}, fallback = {}) {
  return {
    ...fallback,
    recordId: source.recordId || source.record_id || fallback.recordId || '',
    patientId: source.patientId || source.patient?.patient_id || fallback.patientId || '',
    patientName: source.patientName || source.patient?.name || fallback.patientName || '',
    syndrome: source.syndrome || fallback.syndrome || '',
    formula: source.formula || source.prescription || fallback.formula || '',
    visitTime: formatRecordDateTime(source.visitTime || source.date || fallback.visitTime),
    department: source.department || fallback.department || '',
    doctorName: source.doctorName || source.doctor?.name || fallback.doctorName || '',
    patientGender: source.patientGender || source.patient?.gender || fallback.patientGender || '',
    patientAge: source.patientAge || source.patient?.age || fallback.patientAge || '',
    fourDiagnosis: fallback.fourDiagnosis || null,
    therapy: source.therapy || source.treatment_principle || fallback.therapy || '',
    ingredients: Array.isArray(source.ingredients)
      ? source.ingredients.filter(Boolean)
      : Array.isArray(fallback.ingredients)
        ? fallback.ingredients
        : [],
    advice: source.advice || fallback.advice || '',
    precautions: source.precautions || fallback.precautions || '',
    chatSummary: fallback.chatSummary || ''
  }
}

export function normalizeRecordDetail(source = {}, fallback = {}) {
  return {
    ...normalizeRecordListItem(source, fallback),
    fourDiagnosis: {
      chiefComplaint: source.chiefComplaint || source.chief_complaint || fallback.fourDiagnosis?.chiefComplaint || '',
      presentIllness: source.presentIllness || source.present_illness || fallback.fourDiagnosis?.presentIllness || '',
      tongue: source.tongue || fallback.fourDiagnosis?.tongue || '',
      pulse: source.pulse || fallback.fourDiagnosis?.pulse || ''
    },
    therapy: source.therapy || source.treatment_principle || fallback.therapy || '',
    ingredients: Array.isArray(source.ingredients)
      ? source.ingredients.filter(Boolean)
      : Array.isArray(fallback.ingredients)
        ? fallback.ingredients
        : [],
    advice: source.advice || fallback.advice || '',
    precautions: source.precautions || fallback.precautions || '',
    chatSummary: source.chatSummary || fallback.chatSummary || ''
  }
}

export function normalizePatientHistory(source = {}) {
  const historyItems = Array.isArray(source.historySyndromes || source.history_syndromes)
    ? source.historySyndromes || source.history_syndromes
    : []
  const allergyHistory = Array.isArray(source.allergyHistory || source.allergy_history)
    ? source.allergyHistory || source.allergy_history
    : []

  return {
    patientId: source.patientId || source.patient_id || '',
    name: String(source.name || '').trim(),
    gender: String(source.gender || '').trim(),
    age: source.age != null && source.age !== '' ? Number(source.age) : null,
    phone: String(source.phone || '').trim(),
    historyItems: historyItems.map((item) => ({
      date: String(item.date || '').trim(),
      syndrome: String(item.syndrome || '').trim(),
      prescription: String(item.prescription || '').trim()
    })),
    historySyndromes: historyItems.map((item) => String(item.syndrome || '').trim()).filter(Boolean),
    historyPrescriptions: historyItems.map((item) => String(item.prescription || '').trim()).filter(Boolean),
    allergyHistory: allergyHistory.filter(Boolean)
  }
}

export async function searchDoctorRecords(token, filters = {}, pagination = {}) {
  const payload = await request(buildRecordsSearchPath(filters, pagination), {
    method: doctorRecordsApi.searchRecords.method,
    token
  })

  return {
    list: Array.isArray(payload?.list) ? payload.list : [],
    total: payload?.total || 0,
    page: payload?.page || DEFAULT_PAGE,
    pageSize: payload?.page_size || DEFAULT_PAGE_SIZE
  }
}

export async function getDoctorRecordDetail(token, recordId) {
  return request(`${doctorRecordsApi.getRecordDetail.path}/${recordId}`, {
    method: doctorRecordsApi.getRecordDetail.method,
    token
  })
}

export async function getDoctorPatientHistory(token, patientId) {
  return request(`${doctorRecordsApi.getPatientHistory.path}/${patientId}/history`, {
    method: doctorRecordsApi.getPatientHistory.method,
    token
  })
}

export function normalizePatientBasic(source = {}) {
  const allergyHistory = Array.isArray(source.allergyHistory || source.allergy_history)
    ? source.allergyHistory || source.allergy_history
    : []

  return {
    patientId: source.patientId || source.patient_id || '',
    gender: String(source.gender || '').trim(),
    age: source.age != null && source.age !== '' ? Number(source.age) : null,
    allergyHistory: allergyHistory.filter(Boolean)
  }
}

export async function getDoctorPatientBasic(token, patientId) {
  return request(`${doctorRecordsApi.getPatientBasic.path}/${patientId}/basic`, {
    method: doctorRecordsApi.getPatientBasic.method,
    token
  })
}
