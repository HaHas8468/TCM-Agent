import { request } from './http'

const CASE_LIST_PATH = import.meta.env.VITE_KNOWLEDGE_CASE_LIST_PATH || '/api/knowledge/case/doctor'
const CASE_CREATE_PATH = import.meta.env.VITE_KNOWLEDGE_CASE_CREATE_PATH || '/api/knowledge/case'
const CASE_UPDATE_PATH = import.meta.env.VITE_KNOWLEDGE_CASE_UPDATE_PATH || ''
const CASE_DELETE_PATH = import.meta.env.VITE_KNOWLEDGE_CASE_DELETE_PATH || ''

export const doctorCasesApi = {
  list: {
    method: 'GET',
    path: CASE_LIST_PATH
  },
  create: {
    method: 'POST',
    path: CASE_CREATE_PATH
  },
  update: {
    method: 'PUT',
    path: CASE_UPDATE_PATH
  },
  remove: {
    method: 'DELETE',
    path: CASE_DELETE_PATH
  }
}

function normalizeText(value) {
  return String(value || '').trim()
}

function normalizeTextList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeText(item)).filter(Boolean)
  }

  return normalizeText(value)
    .split(/[、，,\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function assignIfPresent(target, key, value) {
  if (Array.isArray(value) ? value.length : normalizeText(value)) {
    target[key] = value
  }
}

function hasPath(path) {
  return Boolean(normalizeText(path))
}

function buildKnowledgeCaseListPath(doctorId = '', limit) {
  const basePath = normalizeText(doctorCasesApi.list.path)

  if (!basePath) {
    return ''
  }

  const params = new URLSearchParams()
  const normalizedDoctorId = normalizeText(doctorId)
  const normalizedLimit = Number(limit)

  if (normalizedDoctorId) {
    params.set('doctor_id', normalizedDoctorId)
  }

  if (Number.isFinite(normalizedLimit) && normalizedLimit > 0) {
    params.set('limit', String(Math.floor(normalizedLimit)))
  }

  if (!params.size) {
    return basePath
  }

  return `${basePath}${basePath.includes('?') ? '&' : '?'}${params.toString()}`
}

function buildFallbackIdentifiers(entry = {}) {
  return {
    id: normalizeText(entry.id || entry.caseId || entry.case_id),
    caseId: normalizeText(entry.caseId || entry.case_id || entry.id),
    sourceId: normalizeText(entry.sourceId || entry.source_id)
  }
}

function resolveCaseItemPath(pathTemplate, entry = {}) {
  const normalizedTemplate = normalizeText(pathTemplate)

  if (!normalizedTemplate) {
    throw new Error('当前未配置医案更新或删除接口路径。')
  }

  const identifiers = buildFallbackIdentifiers(entry)
  const id = identifiers.sourceId || identifiers.caseId || identifiers.id

  if (!id) {
    throw new Error('当前医案缺少 caseId/sourceId，无法调用明细接口。')
  }

  let resolvedPath = normalizedTemplate
  const replacements = {
    ':id': identifiers.id || id,
    ':caseId': identifiers.caseId || id,
    ':sourceId': identifiers.sourceId || id,
    '{id}': identifiers.id || id,
    '{caseId}': identifiers.caseId || id,
    '{sourceId}': identifiers.sourceId || id
  }

  Object.entries(replacements).forEach(([placeholder, value]) => {
    if (value) {
      resolvedPath = resolvedPath.split(placeholder).join(encodeURIComponent(value))
    }
  })

  if (resolvedPath === normalizedTemplate) {
    return `${normalizedTemplate.replace(/\/+$/, '')}/${encodeURIComponent(id)}`
  }

  return resolvedPath
}

function normalizeDoctorObject(value) {
  if (!value || typeof value !== 'object') {
    return null
  }

  const name = normalizeText(value.name)
  const id = normalizeText(value.id || value.doctorId || value.doctor_id)

  if (!name) {
    return null
  }

  return id ? { name, id } : { name }
}

function normalizeDoctorActorList(value) {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => {
      if (typeof item === 'string') {
        const name = normalizeText(item)
        return name || null
      }

      return normalizeDoctorObject(item)
    })
    .filter(Boolean)
}

function buildUploaderDoctor(doctorProfile = {}) {
  const name = normalizeText(doctorProfile.name || doctorProfile.doctorName || doctorProfile.author)
  const id = normalizeText(doctorProfile.id || doctorProfile.doctorId || doctorProfile.doctor_id)

  if (!name) {
    return null
  }

  return id ? { name, id } : { name }
}

export function hasKnowledgeCaseListApi() {
  return hasPath(doctorCasesApi.list.path)
}

export function hasKnowledgeCaseUpdateApi() {
  return hasPath(doctorCasesApi.update.path)
}

export function hasKnowledgeCaseDeleteApi() {
  return hasPath(doctorCasesApi.remove.path)
}

export function normalizeKnowledgeCaseEntry(source = {}, fallback = {}, options = {}) {
  const linked = source?.linked && typeof source.linked === 'object' ? source.linked : fallback?.linked || null
  const uploaderDoctor = buildUploaderDoctor(options.doctorProfile)
  const doctorActors = normalizeDoctorActorList(source.doctors ?? fallback.doctors)
  const firstDoctorActor = doctorActors.find(Boolean)
  const fallbackDoctorName =
    typeof firstDoctorActor === 'string'
      ? normalizeText(firstDoctorActor)
      : normalizeText(firstDoctorActor?.name)
  const uploaderDoctorName = normalizeText(uploaderDoctor?.name)
  const resolvedAuthor = normalizeText(source.author || fallback.author || fallbackDoctorName || uploaderDoctorName)
  const resolvedUploaderDoctor = uploaderDoctorName ? uploaderDoctor : buildUploaderDoctor({ name: resolvedAuthor })

  return {
    id: normalizeText(source.id || source.caseId || source.case_id || fallback.id || fallback.caseId),
    caseId: normalizeText(source.caseId || source.case_id || source.id || fallback.caseId || fallback.id),
    sourceId: normalizeText(source.sourceId || source.source_id || fallback.sourceId),
    title: normalizeText(source.title || fallback.title),
    author: resolvedAuthor,
    publishedAt: normalizeText(
      source.publishedAt || source.publishDate || source.publish_date || fallback.publishedAt || fallback.publishDate
    ),
    category: normalizeText(source.category || fallback.category),
    sourceUrl: normalizeText(source.sourceUrl || source.source_url || fallback.sourceUrl),
    summary: normalizeText(source.summary || fallback.summary),
    content: normalizeText(source.content || source.rawText || source.raw_text || fallback.content || fallback.rawText),
    diseases: normalizeTextList(source.diseases ?? fallback.diseases),
    syndromes: normalizeTextList(source.syndromes ?? fallback.syndromes),
    symptoms: normalizeTextList(source.symptoms ?? fallback.symptoms),
    formulas: normalizeTextList(source.formulas ?? fallback.formulas),
    treatment: Array.isArray(source.treatmentMethods ?? source.treatment_methods ?? fallback.treatmentMethods)
      ? normalizeTextList(source.treatmentMethods ?? source.treatment_methods ?? fallback.treatmentMethods).join('、')
      : normalizeText(
          source.treatment || source.treatmentMethods || source.treatment_methods || fallback.treatment
        ),
    doctors: doctorActors,
    uploaderDoctor: resolvedUploaderDoctor,
    linked
  }
}

export function buildKnowledgeCasePayload(entry = {}, options = {}) {
  const uploaderDoctor = buildUploaderDoctor(options.doctorProfile)
  const normalizedEntry = normalizeKnowledgeCaseEntry(
    entry,
    {
      author: options.fallbackAuthor
    },
    {
      doctorProfile: options.doctorProfile
    }
  )
  const payloadDoctor = uploaderDoctor || buildUploaderDoctor({ name: normalizedEntry.author })
  const doctors = payloadDoctor
    ? [
        {
          name: payloadDoctor.name,
          id: payloadDoctor.id || ''
        }
      ]
    : []

  const payload = {
    title: normalizedEntry.title,
    publishDate: normalizedEntry.publishedAt,
    doctors
  }

  // 后端的可选文本字段若传空字符串仍会触发非空校验；未填写时应直接省略。
  assignIfPresent(payload, 'summary', normalizedEntry.summary)
  assignIfPresent(payload, 'rawText', normalizedEntry.content)
  assignIfPresent(payload, 'sourceUrl', normalizedEntry.sourceUrl)
  assignIfPresent(payload, 'diseases', normalizedEntry.diseases)
  assignIfPresent(payload, 'syndromes', normalizedEntry.syndromes)
  assignIfPresent(payload, 'symptoms', normalizedEntry.symptoms)
  assignIfPresent(payload, 'formulas', normalizedEntry.formulas)
  assignIfPresent(payload, 'treatmentMethods', normalizedEntry.treatment)

  return payload
}

function normalizeKnowledgeCaseListResponse(payload) {
  if (Array.isArray(payload)) {
    return payload
  }

  if (Array.isArray(payload?.list)) {
    return payload.list
  }

  if (Array.isArray(payload?.cases)) {
    return payload.cases
  }

  if (Array.isArray(payload?.rows)) {
    return payload.rows
  }

  if (Array.isArray(payload?.items)) {
    return payload.items
  }

  return []
}

export async function getKnowledgeCaseList(token, options = {}) {
  if (!hasKnowledgeCaseListApi()) {
    return null
  }

  const path = buildKnowledgeCaseListPath(options.doctorId, options.limit)

  if (!path) {
    return null
  }

  const payload = await request(path, {
    method: doctorCasesApi.list.method,
    token
  })

  return normalizeKnowledgeCaseListResponse(payload).map((item) =>
    normalizeKnowledgeCaseEntry(
      item,
      {
        author: options.fallbackAuthor
      },
      {
        doctorProfile: options.doctorProfile
      }
    )
  )
}

export async function createKnowledgeCaseEntry(entry = {}, options = {}) {
  const payload = buildKnowledgeCasePayload(entry, options)

  if (!payload.title) {
    throw new Error('请先填写医案标题。')
  }

  const response = await request(doctorCasesApi.create.path, {
    method: doctorCasesApi.create.method,
    token: options.token,
    data: payload
  })

  return normalizeKnowledgeCaseEntry(
    {
      ...entry,
      caseId: response?.caseId || entry.caseId || entry.id,
      id: response?.caseId || entry.id,
      sourceId: response?.sourceId || entry.sourceId,
      linked: response?.linked || entry.linked
    },
    {
      author: options.fallbackAuthor
    },
    {
      doctorProfile: options.doctorProfile
    }
  )
}

export async function updateKnowledgeCaseEntry(entry = {}, options = {}) {
  const payload = buildKnowledgeCasePayload(entry, options)
  const path = resolveCaseItemPath(doctorCasesApi.update.path, entry)

  if (!payload.title) {
    throw new Error('请先填写医案标题。')
  }

  const response = await request(path, {
    method: doctorCasesApi.update.method,
    token: options.token,
    data: payload
  })

  return normalizeKnowledgeCaseEntry(
    {
      ...entry,
      ...(response && typeof response === 'object' ? response : {})
    },
    {
      author: options.fallbackAuthor
    },
    {
      doctorProfile: options.doctorProfile
    }
  )
}

export async function deleteKnowledgeCaseEntry(entry = {}, options = {}) {
  const path = resolveCaseItemPath(doctorCasesApi.remove.path, entry)

  return request(path, {
    method: doctorCasesApi.remove.method,
    token: options.token
  })
}
