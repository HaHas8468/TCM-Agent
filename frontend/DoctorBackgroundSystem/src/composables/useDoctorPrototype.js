import { computed, onMounted, reactive } from 'vue'
import {
  clearDoctorAuthSession,
  clearRememberedDoctorAccount,
  getDoctorAuthSession,
  getRememberedDoctorAccount,
  loginDoctor,
  rememberDoctorAccount,
  saveDoctorAuthSession
} from '../api/doctorAuthApi'
import { sendDoctorAgentMessage } from '../api/doctorAgentApi'
import { getDoctorQueue, mapQueueStatusToView } from '../api/doctorQueueApi'
import {
  finishDoctorOrder,
  saveDoctorOrder,
  startDoctorOrder
} from '../api/doctorWorkspaceApi'
import {
  getDoctorPatientBasic,
  getDoctorPatientHistory,
  getDoctorRecordDetail,
  normalizePatientBasic,
  normalizePatientHistory,
  normalizeRecordDetail,
  normalizeRecordListItem,
  searchDoctorRecords
} from '../api/doctorRecordsApi'
import { getDoctorDepartments } from '../api/doctorDepartmentsApi'
import {
  applyDoctorProfile,
  createDoctorProfileView,
  doctorDepartmentOptions,
  getDoctorProfile,
  normalizeDoctorProfileState,
  updateDoctorContact,
  updateDoctorPassword,
  updateDoctorProfile
} from '../api/doctorProfileApi'
import {
  createKnowledgeCaseEntry,
  deleteKnowledgeCaseEntry,
  getKnowledgeCaseList,
  hasKnowledgeCaseDeleteApi,
  hasKnowledgeCaseUpdateApi,
  normalizeKnowledgeCaseEntry,
  updateKnowledgeCaseEntry
} from '../api/doctorCasesApi'
import { doctorPrototypeSeed } from '../data/doctorPrototypeData'

function cloneSeed() {
  return JSON.parse(JSON.stringify(doctorPrototypeSeed))
}

function getQueuePatientSortRank(status) {
  const statusRank = new Map([
    [mapQueueStatusToView('ongoing'), 0],
    [mapQueueStatusToView('pending'), 1],
    [mapQueueStatusToView('finished'), 2],
    [mapQueueStatusToView('cancelled'), 3]
  ])

  return statusRank.get(status) ?? 4
}

function isQueuePatientClosed(status) {
  return [mapQueueStatusToView('finished'), mapQueueStatusToView('cancelled')].includes(status)
}

function normalizeModuleKey(moduleKey, navigationItems = [], fallback = 'queue') {
  const availableModuleKeys = Array.isArray(navigationItems)
    ? navigationItems.map((item) => item?.key).filter(Boolean)
    : []

  if (availableModuleKeys.includes(moduleKey)) {
    return moduleKey
  }

  if (availableModuleKeys.includes(fallback)) {
    return fallback
  }

  return availableModuleKeys[0] || fallback
}

function buildDepartmentOptions(...sources) {
  const options = []

  sources.forEach((source) => {
    if (Array.isArray(source)) {
      source.forEach((item) => {
        const value = String(item || '').trim()

        if (value) {
          options.push(value)
        }
      })

      return
    }

    const value = String(source || '').trim()

    if (value) {
      options.push(value)
    }
  })

  return Array.from(new Set(options))
}

function formatTimestamp() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')

  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(
    now.getMinutes()
  )}`
}

function formatClock() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')

  return `${pad(now.getHours())}:${pad(now.getMinutes())}`
}

function formatErrorMessage(error, fallbackMessage) {
  return error instanceof Error ? error.message : fallbackMessage
}

function hasOwn(target, key) {
  return Boolean(target) && Object.prototype.hasOwnProperty.call(target, key)
}

function matchesPatientEntry(entry, patientId = '', orderId = '') {
  if (!entry) {
    return false
  }

  if (orderId) {
    return entry.orderId === orderId
  }

  if (patientId) {
    return entry.id === patientId
  }

  return false
}

function findPatientEntry(collection = [], patientId = '', orderId = '') {
  return collection.find((entry) => matchesPatientEntry(entry, patientId, orderId)) || null
}

function normalizeCaseLibraryTextList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean)
  }

  return String(value || '')
    .split(/[、，,；;\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizeCaseLibraryEntry(entry = {}, fallbackAuthor = '') {
  return {
    id: String(entry.id || '').trim(),
    title: String(entry.title || '').trim(),
    author: String(entry.author || fallbackAuthor || '').trim(),
    publishedAt: String(entry.publishedAt || formatTimestamp().slice(0, 10)).trim(),
    category: String(entry.category || '').trim(),
    sourceUrl: String(entry.sourceUrl || '').trim(),
    summary: String(entry.summary || '').trim(),
    content: String(entry.content || '').trim(),
    diseases: normalizeCaseLibraryTextList(entry.diseases),
    syndromes: normalizeCaseLibraryTextList(entry.syndromes),
    symptoms: normalizeCaseLibraryTextList(entry.symptoms),
    formulas: normalizeCaseLibraryTextList(entry.formulas),
    treatment: String(entry.treatment || '').trim()
  }
}

function sortCaseLibraryEntries(entries = []) {
  return [...entries].sort((left, right) => {
    const rightTime = new Date(right?.publishedAt || 0).getTime()
    const leftTime = new Date(left?.publishedAt || 0).getTime()

    if (rightTime !== leftTime) {
      return rightTime - leftTime
    }

    return String(right?.id || '').localeCompare(String(left?.id || ''))
  })
}

function createQueuePatientPlaceholder(patient = {}) {
  const patientId = patient.id || patient.patientId || ''

  return {
    id: patientId,
    orderId: patient.orderId || '',
    recordId: patient.recordId || '',
    name: patient.name || '',
    gender: patient.gender || '',
    age: patient.age != null && patient.age !== '' ? patient.age : '',
    department: patient.department || '',
    visitType: patient.visitType || '',
    schedule: patient.schedule || '',
    status: patient.status || '待接诊',
    symptomBrief: patient.symptomBrief || '',
    registrationNote: patient.registrationNote || '',
    basicInfo: {
      phone: '',
      patientId,
      bloodPressure: '',
      allergies: [],
      historySyndromes: [],
      historyPrescriptions: []
    },
    fourDiagnosis: {
      chiefComplaint: '',
      presentIllness: '',
      tongue: '待录入',
      pulse: '待录入'
    },
    treatmentPlan: {
      formula: '',
      usage: '',
      followUp: '',
      precautions: ''
    },
    aiPlan: {
      gaps: [],
      syndrome: '',
      therapy: '',
      formula: '',
      evidence: [],
      recommendations: {
        herbs: [],
        cases: []
      }
    },
    chatMessages: [],
    knowledgeQueries: [],
    agentMessages: [],
    agentConversationStatus: '',
    agentAskRound: 0,
    agentLastResponse: ''
  }
}

function mergeQueuePatientWithLocal(queueItem, localPatient = {}) {
  const placeholder = createQueuePatientPlaceholder({
    id: queueItem.patient_id || localPatient.id || '',
    orderId: queueItem.order_id || localPatient.orderId || '',
    recordId: localPatient.recordId || '',
    name: queueItem.patient_name || localPatient.name || '',
    department: queueItem.department || localPatient.department || '',
    schedule: queueItem.time || localPatient.schedule || '',
    status: mapQueueStatusToView(queueItem.status)
  })
  const localAiPlan = localPatient.aiPlan || {}
  const localRecommendations = localAiPlan.recommendations || {}

  return {
    ...placeholder,
    ...localPatient,
    id: placeholder.id,
    orderId: placeholder.orderId,
    name: placeholder.name,
    gender: placeholder.gender || localPatient.gender,
    age: placeholder.age || localPatient.age,
    department: placeholder.department,
    schedule: placeholder.schedule,
    status: placeholder.status,
    basicInfo: {
      ...placeholder.basicInfo,
      ...(localPatient.basicInfo || {}),
      patientId: placeholder.id
    },
    fourDiagnosis: {
      ...placeholder.fourDiagnosis,
      ...(localPatient.fourDiagnosis || {})
    },
    treatmentPlan: {
      ...placeholder.treatmentPlan,
      ...(localPatient.treatmentPlan || {})
    },
    aiPlan: {
      ...placeholder.aiPlan,
      ...localAiPlan,
      gaps: Array.isArray(localAiPlan.gaps) ? localAiPlan.gaps : [],
      evidence: Array.isArray(localAiPlan.evidence) ? localAiPlan.evidence : [],
      recommendations: {
        herbs: Array.isArray(localRecommendations.herbs) ? localRecommendations.herbs : [],
        cases: Array.isArray(localRecommendations.cases) ? localRecommendations.cases : []
      }
    },
    chatMessages: Array.isArray(localPatient.chatMessages) ? localPatient.chatMessages : [],
    knowledgeQueries: Array.isArray(localPatient.knowledgeQueries) ? localPatient.knowledgeQueries : [],
    agentMessages: Array.isArray(localPatient.agentMessages) ? localPatient.agentMessages : []
  }
}

function createDiagnosisHerbItems(ingredients = []) {
  return Array.isArray(ingredients)
    ? ingredients.filter(Boolean).map((name) => ({ name, summary: '', detail: '' }))
    : []
}

function isRecordDetailLoaded(record) {
  return Boolean(record?.fourDiagnosis && typeof record.fourDiagnosis === 'object' && record.doctorName)
}

function appendAgentMessage(patient, message) {
  if (!patient) {
    return
  }

  if (!Array.isArray(patient.agentMessages)) {
    patient.agentMessages = []
  }

  patient.agentMessages.push(message)
}

function upsertAgentMessage(patient, messageId, text, time = formatClock()) {
  if (!patient) {
    return
  }

  if (!Array.isArray(patient.agentMessages)) {
    patient.agentMessages = []
  }

  const targetMessage = patient.agentMessages.find((item) => item.id === messageId)

  if (targetMessage) {
    targetMessage.text = text
    return
  }

  patient.agentMessages.push({
    id: messageId,
    sender: 'agent',
    roleLabel: '\u667a\u80fd\u52a9\u624b',
    time,
    text
  })
}

function updateAgentMessageText(patient, messageId, text) {
  if (!patient) {
    return
  }

  if (!Array.isArray(patient.agentMessages)) {
    patient.agentMessages = []
  }

  const targetMessage = patient.agentMessages.find((item) => item.id === messageId)

  if (targetMessage) {
    targetMessage.text = text
    return
  }

  upsertAgentMessage(patient, messageId, text)
}

function syncAgentDiagnosisToPatient(patient, diagnosis = {}, responseText = '') {
  if (!patient) {
    return
  }

  const herbs = Array.isArray(diagnosis.herbs) ? diagnosis.herbs : []
  const existingPlan = patient.aiPlan || {}
  const existingRecommendations = existingPlan.recommendations || {}
  const treatmentText = String(diagnosis.treatment || diagnosis.therapy || '').trim()

  patient.agentResult = {
    ...(patient.agentResult || {}),
    diagnosisResult: {
      syndrome: diagnosis.syndrome || '',
      formula: diagnosis.formula || '',
      herbs,
      treatment: treatmentText,
      description: diagnosis.description || responseText || '',
      allergyWarnings: Array.isArray(diagnosis.allergyWarnings) ? diagnosis.allergyWarnings : [],
      department: diagnosis.department || '',
      advice: diagnosis.advice || '',
      precautions: diagnosis.precautions || ''
    }
  }

  patient.aiPlan = {
    ...existingPlan,
    syndrome: diagnosis.syndrome || existingPlan.syndrome || '',
    therapy: treatmentText || existingPlan.therapy || '',
    formula: diagnosis.formula || existingPlan.formula || '',
    evidence: responseText ? [responseText] : Array.isArray(existingPlan.evidence) ? existingPlan.evidence : [],
    recommendations: {
      herbs: herbs.length ? createDiagnosisHerbItems(herbs) : existingRecommendations.herbs || [],
      cases: existingRecommendations.cases || []
    }
  }

  if (diagnosis.formula) {
    patient.treatmentPlan = {
      ...(patient.treatmentPlan || {}),
      formula: diagnosis.formula
    }
  }
}

export function useDoctorPrototype() {
  const seed = cloneSeed()
  const storedAuthToken = getDoctorAuthSession()
  const initialRememberedAccount = getRememberedDoctorAccount() || seed.settings?.profile?.account || ''
  const profileSeed = seed.settings?.profile || seed.doctorProfile || {}
  const doctorProfile = createDoctorProfileView(profileSeed, seed.doctorProfile?.dutyStatus)
  const initialQueuePatients = []
  const initialRecords = []

  const state = reactive({
    // 刷新页面时先复用本地令牌，再由 mounted 钩子向后端校验其有效性。
    loggedIn: Boolean(storedAuthToken),
    loginPending: false,
    loginError: '',
    authToken: storedAuthToken,
    doctorId: '',
    rememberedAccount: initialRememberedAccount,
    agentSending: false,
    agentError: '',
    queueLoading: false,
    queueError: '',
    queueKpi: null,
    queuePatients: initialQueuePatients,
    recordsLoading: false,
    recordsError: '',
    recordDetailLoading: false,
    workspaceLoading: false,
    workspaceError: '',
    workspaceActionPending: false,
    workspaceActionType: '',
    workspaceActionError: '',
    workspaceActionSuccess: '',
    recordSearchResults: initialRecords,
    activeModule: 'queue',
    activePatientId: '',
    activePatientOrderId: '',
    activeRecordId: '',
    queueFilters: {
      department: '全部',
      period: '今日全部'
    },
    navigationItems: seed.navigationItems,
    doctorProfile,
    departmentOptions: buildDepartmentOptions(doctorDepartmentOptions, [profileSeed.department]),
    patients: initialQueuePatients,
    records: initialRecords,
    caseLibrary: [],
    settings: seed.settings,
    settingsSaveMeta: {
      section: '初始化',
      message: '当前为原型默认配置，可在设置中心修改后立即保存。',
      lastSavedAt: '2026-07-06 11:12'
    }
  })

  const queueDepartments = computed(() => {
    const departments = buildDepartmentOptions(
      state.departmentOptions,
      state.patients.map((item) => item.department || ''),
      state.queuePatients.map((item) => item.department || '')
    )

    return ['全部'].concat(departments)
  })

  const queuePeriods = ['今日全部', '上午', '下午']

  const activeNavigation = computed(() => {
    return state.navigationItems.find((item) => item.key === state.activeModule) || state.navigationItems[0]
  })

  function isPatientInPeriod(schedule, period) {
    if (!schedule || period === '今日全部') {
      return true
    }

    const timeMatch = String(schedule).match(/(\d{1,2}):?(\d{0,2})/)
    if (!timeMatch) {
      return true
    }

    const hour = parseInt(timeMatch[1], 10)

    if (period === '上午') {
      return hour >= 6 && hour < 12
    }

    if (period === '下午') {
      return hour >= 12 && hour < 18
    }

    return true
  }

  const filteredPatients = computed(() => {
    let patients = [...state.queuePatients]

    if (state.queueFilters.department && state.queueFilters.department !== '全部') {
      patients = patients.filter((patient) => patient.department === state.queueFilters.department)
    }

    if (state.queueFilters.period) {
      patients = patients.filter((patient) => isPatientInPeriod(patient.schedule, state.queueFilters.period))
    }

    return patients.sort((left, right) => {
      return getQueuePatientSortRank(left?.status) - getQueuePatientSortRank(right?.status)
    })
  })

  const activePatient = computed(() => {
    if (state.activePatientOrderId) {
      return findPatientEntry(state.patients, '', state.activePatientOrderId)
    }

    if (!state.activePatientId) {
      return null
    }

    return findPatientEntry(state.patients, state.activePatientId) || null
  })

  const activeRecord = computed(() => {
    if (state.activeRecordId) {
      return (
        state.records.find((record) => record.recordId === state.activeRecordId) ||
        state.recordSearchResults.find((record) => record.recordId === state.activeRecordId) ||
        null
      )
    }

    return state.recordSearchResults[0] || state.records[0] || null
  })

  const queueStats = computed(() => {
    if (state.queueKpi) {
      return [
        { label: '今日挂号', value: String(state.queueKpi.today_total ?? 0), meta: '医生端主入口' },
        { label: '待接诊', value: String(state.queueKpi.pending ?? 0), meta: '可按科室继续筛选' },
        { label: '问诊中', value: String(state.queueKpi.ongoing ?? 0), meta: '含 AI 补采任务' },
        { label: '已归档', value: String(state.queueKpi.finished ?? 0), meta: '处方已回写病历' }
      ]
    }

    const total = state.queuePatients.length
    const waiting = state.queuePatients.filter((patient) => patient.status === '待接诊').length
    const consulting = state.queuePatients.filter((patient) => patient.status === '问诊中').length
    const completed = state.queuePatients.filter((patient) => patient.status === '已结束').length

    return [
      { label: '今日挂号', value: String(total), meta: '医生端主入口' },
      { label: '待接诊', value: String(waiting), meta: '可按科室继续筛选' },
      { label: '问诊中', value: String(consulting), meta: '含 AI 补采任务' },
      { label: '已归档', value: String(completed), meta: '处方已回写病历' }
    ]
  })

  function syncDoctorProfileState(nextProfile = {}) {
    state.settings.profile = normalizeDoctorProfileState(nextProfile, state.settings.profile)
    applyDoctorProfile(state.doctorProfile, state.settings.profile)
    state.departmentOptions = buildDepartmentOptions(
      state.departmentOptions,
      [state.settings.profile.department, state.doctorProfile.department]
    )
  }

  function clearWorkspaceActionState() {
    state.workspaceActionPending = false
    state.workspaceActionType = ''
    state.workspaceActionError = ''
    state.workspaceActionSuccess = ''
  }

  function startWorkspaceAction(type = '') {
    state.workspaceActionPending = true
    state.workspaceActionType = type
    state.workspaceActionError = ''
    state.workspaceActionSuccess = ''
  }

  function setWorkspaceActionError(message, type = state.workspaceActionType) {
    state.workspaceActionPending = false
    state.workspaceActionType = type
    state.workspaceActionError = message
    state.workspaceActionSuccess = ''
  }

  function setWorkspaceActionSuccess(message, type = state.workspaceActionType) {
    state.workspaceActionPending = false
    state.workspaceActionType = type
    state.workspaceActionError = ''
    state.workspaceActionSuccess = message
  }

  function syncOrderStatusState(orderId, patientId, status) {
    const nextStatus = mapQueueStatusToView(status)

    if (!nextStatus) {
      return
    }

    state.queuePatients.forEach((item) => {
      if ((orderId && item.orderId === orderId) || (!orderId && patientId && item.id === patientId)) {
        item.status = nextStatus
      }
    })

    state.patients.forEach((item) => {
      if ((orderId && item.orderId === orderId) || (!orderId && patientId && item.id === patientId)) {
        item.status = nextStatus
      }
    })
  }

  function syncLinkedRecordFromPatient(patient) {
    if (!patient) {
      return
    }

    const linkedRecord =
      state.records.find((record) => record.patientId === patient.id) ||
      state.recordSearchResults.find((record) => record.patientId === patient.id)

    if (!linkedRecord) {
      return
    }

    linkedRecord.patientName = patient.name
    linkedRecord.department = patient.department
    const doctorConfirmation = patient.doctorConfirmation || {}
    const treatmentPlan = patient.treatmentPlan || {}
    const aiPlan = patient.aiPlan || {}

    linkedRecord.syndrome = hasOwn(doctorConfirmation, 'syndrome')
      ? doctorConfirmation.syndrome || ''
      : aiPlan.syndrome || linkedRecord.syndrome
    linkedRecord.formula = hasOwn(doctorConfirmation, 'prescription')
      ? doctorConfirmation.prescription || ''
      : hasOwn(treatmentPlan, 'formula')
        ? treatmentPlan.formula || ''
        : linkedRecord.formula
    linkedRecord.therapy = hasOwn(doctorConfirmation, 'treatment')
      ? doctorConfirmation.treatment || ''
      : aiPlan.therapy || linkedRecord.therapy
    linkedRecord.ingredients = hasOwn(doctorConfirmation, 'herbs')
      ? Array.isArray(doctorConfirmation.herbs)
        ? doctorConfirmation.herbs.filter(Boolean)
        : []
      : Array.isArray(linkedRecord.ingredients)
        ? linkedRecord.ingredients
        : []
    linkedRecord.advice = hasOwn(doctorConfirmation, 'advice')
      ? doctorConfirmation.advice || ''
      : hasOwn(treatmentPlan, 'followUp')
        ? treatmentPlan.followUp || ''
        : linkedRecord.advice
    linkedRecord.precautions = hasOwn(doctorConfirmation, 'precautions')
      ? doctorConfirmation.precautions || ''
      : hasOwn(treatmentPlan, 'precautions')
        ? treatmentPlan.precautions || ''
        : linkedRecord.precautions
    linkedRecord.doctorConfirmation = patient.doctorConfirmation
    linkedRecord.agentResult = patient.agentResult
    linkedRecord.fourDiagnosis = {
      ...(patient.fourDiagnosis || {})
    }
    linkedRecord.chatSummary = Array.isArray(patient.agentMessages)
      ? patient.agentMessages
          .slice(-2)
          .map((message) => `${message.roleLabel}: ${message.text}`)
          .join('；')
      : linkedRecord.chatSummary
  }

  function applyWorkspacePayloadToPatient(patient, payload = {}) {
    if (!patient || !payload) {
      return
    }

    const nextTreatmentPlan = payload.treatmentPlan || {}
    const nextDoctorConfirmation = payload.doctorConfirmation || {}

    patient.fourDiagnosis = {
      ...patient.fourDiagnosis,
      ...payload.fourDiagnosis
    }

    patient.treatmentPlan = {
      ...patient.treatmentPlan,
      ...nextTreatmentPlan
    }

    if (payload.agentResult) {
      patient.agentResult = {
        ...payload.agentResult
      }
    }

    if (payload.doctorConfirmation) {
      patient.doctorConfirmation = {
        ...(patient.doctorConfirmation || {}),
        ...nextDoctorConfirmation
      }
    }

    if (hasOwn(nextDoctorConfirmation, 'advice')) {
      patient.treatmentPlan.followUp = nextDoctorConfirmation.advice || ''
    }

    if (hasOwn(nextDoctorConfirmation, 'precautions')) {
      patient.treatmentPlan.precautions = nextDoctorConfirmation.precautions || ''
    }

    if (hasOwn(payload, 'aiAdjustment')) {
      patient.aiPlan.syndrome = payload.aiAdjustment
    }

    if (hasOwn(payload, 'therapy')) {
      patient.aiPlan.therapy = payload.therapy
    }

    if (hasOwn(nextTreatmentPlan, 'formula')) {
      patient.aiPlan.formula = nextTreatmentPlan.formula
    }

    if (payload.gapNote) {
      patient.aiPlan.gaps.unshift(payload.gapNote)
    }

    if (payload.completeVisit) {
      patient.status = '已结束'
    } else if (patient.status === '待接诊') {
      patient.status = '问诊中'
    }

    syncLinkedRecordFromPatient(patient)
  }

  function syncQueuePatientsState(queueItems = []) {
    state.queuePatients = queueItems

    queueItems.forEach((patient) => {
      const current = findPatientEntry(state.patients, patient.id, patient.orderId)

      if (current) {
        Object.assign(current, patient)
        return
      }

      state.patients.unshift(patient)
    })
  }

  function upsertRecordState(record) {
    if (!record || !record.recordId) {
      return record
    }

    const current = state.records.find((item) => item.recordId === record.recordId)

    if (current) {
      Object.assign(current, record)
      return current
    }

    state.records.unshift(record)
    return record
  }

  function syncRecordSearchResults(records = []) {
    const sorted = [...records].sort((a, b) => {
      // 病历按就诊时间降序：时间越晚的排在越上面
      const va = a.visitTime || ''
      const vb = b.visitTime || ''
      if (va === vb) return 0
      return vb > va ? 1 : -1
    })
    state.recordSearchResults = sorted
    sorted.forEach((record) => {
      upsertRecordState(record)
    })

    const hasActiveRecord = sorted.some((record) => record.recordId === state.activeRecordId)

    if (!hasActiveRecord) {
      state.activeRecordId = sorted[0]?.recordId || ''
    }
  }

  function applyPatientHistoryToPatient(patient, history = {}) {
    if (!patient) {
      return
    }

    if (history.gender) {
      patient.gender = history.gender
    }
    if (history.age != null && history.age !== '') {
      patient.age = history.age
    }
    if (history.name) {
      patient.name = history.name
    }

    patient.basicInfo = {
      ...(patient.basicInfo || {}),
      patientId: history.patientId || patient.id,
      phone: history.phone || patient.basicInfo?.phone || '',
      allergies: history.allergyHistory && history.allergyHistory.length
        ? history.allergyHistory
        : patient.basicInfo?.allergies || [],
      historySyndromes: history.historySyndromes.length
        ? history.historySyndromes
        : patient.basicInfo?.historySyndromes || [],
      historyPrescriptions: history.historyPrescriptions.length
        ? history.historyPrescriptions
        : patient.basicInfo?.historyPrescriptions || []
    }
  }

  function applyRecordDetailToPatient(patient, record) {
    if (!patient || !record) {
      return
    }

    const existingPlan = patient.aiPlan || {}
    const existingRecommendations = existingPlan.recommendations || {}
    const existingTreatmentPlan = patient.treatmentPlan || {}
    const ingredients = Array.isArray(record.ingredients) ? record.ingredients : []
    const evidence = [record.fourDiagnosis?.presentIllness, record.fourDiagnosis?.chiefComplaint].filter(Boolean)

    patient.recordId = record.recordId || patient.recordId
    patient.name = record.patientName || patient.name
    patient.gender = record.patientGender || patient.gender
    patient.age = Number(record.patientAge) || patient.age
    patient.symptomBrief = record.fourDiagnosis?.chiefComplaint || patient.symptomBrief
    patient.registrationNote = record.fourDiagnosis?.presentIllness || patient.registrationNote
    patient.fourDiagnosis = {
      ...(patient.fourDiagnosis || {}),
      ...(record.fourDiagnosis || {})
    }
    patient.treatmentPlan = {
      ...existingTreatmentPlan,
      formula: record.formula || existingTreatmentPlan.formula || '',
      followUp: record.advice || existingTreatmentPlan.followUp || '',
      precautions: record.precautions || existingTreatmentPlan.precautions || ''
    }
    patient.aiPlan = {
      ...existingPlan,
      syndrome: record.syndrome || existingPlan.syndrome || '',
      therapy: record.therapy || existingPlan.therapy || '',
      formula: record.formula || existingPlan.formula || '',
      evidence: evidence.length ? evidence : Array.isArray(existingPlan.evidence) ? existingPlan.evidence : [],
      recommendations: {
        herbs: ingredients.length ? createDiagnosisHerbItems(ingredients) : existingRecommendations.herbs || [],
        cases: existingRecommendations.cases || []
      }
    }
    patient.agentResult = {
      ...(patient.agentResult || {}),
      diagnosisResult: {
        syndrome: record.syndrome || '',
        formula: record.formula || '',
        herbs: ingredients,
        treatment: record.therapy || '',
        description: record.fourDiagnosis?.presentIllness || record.fourDiagnosis?.chiefComplaint || '',
        allergyWarnings: patient.basicInfo?.allergies || [],
        advice: record.advice || '',
        precautions: record.precautions || ''
      }
    }
    patient.doctorConfirmation = {
      ...(patient.doctorConfirmation || {}),
      syndrome: record.syndrome || '',
      treatment: record.therapy || '',
      prescription: record.formula || '',
      herbs: ingredients,
      advice: record.advice || '',
      precautions: record.precautions || ''
    }
  }

  async function runRecordsSearch(filters = {}, pagination = {}, options = {}) {
    if (!state.authToken) {
      return {
        list: [],
        total: 0,
        page: 1,
        pageSize: 20
      }
    }

    const { silent = false, syncList = true, throwOnError = false } = options

    if (!silent) {
      state.recordsLoading = true
      state.recordsError = ''
    }

    try {
      const response = await searchDoctorRecords(state.authToken, filters, pagination)
      const normalizedList = response.list.map((item) => {
        const fallback =
          state.records.find((record) => record.recordId === item.record_id) ||
          state.recordSearchResults.find((record) => record.recordId === item.record_id) ||
          {}

        return normalizeRecordListItem(item, fallback)
      })

      if (syncList) {
        syncRecordSearchResults(normalizedList)
      }

      return {
        ...response,
        list: normalizedList
      }
    } catch (error) {
      const message = formatErrorMessage(error, '病历检索失败，请稍后重试。')

      if (!silent) {
        state.recordsError = message
      }

      if (throwOnError) {
        throw error
      }

      return {
        list: [],
        total: 0,
        page: 1,
        pageSize: 20
      }
    } finally {
      if (!silent) {
        state.recordsLoading = false
      }
    }
  }

  async function fetchRecordDetail(recordId, options = {}) {
    if (!state.authToken || !recordId) {
      return null
    }

    const { silent = false, throwOnError = false } = options

    if (!silent) {
      state.recordDetailLoading = true
      state.recordsError = ''
    }

    try {
      const response = await getDoctorRecordDetail(state.authToken, recordId)
      const fallback =
        state.records.find((record) => record.recordId === recordId) ||
        state.recordSearchResults.find((record) => record.recordId === recordId) ||
        {}
      const detailRecord = normalizeRecordDetail(response, fallback)

      return upsertRecordState(detailRecord)
    } catch (error) {
      const message = formatErrorMessage(error, '病历详情加载失败，请稍后重试。')

      if (!silent) {
        state.recordsError = message
      }

      if (throwOnError) {
        throw error
      }

      return null
    } finally {
      if (!silent) {
        state.recordDetailLoading = false
      }
    }
  }

  async function hydrateWorkspacePatient(patient, seedRecord = null) {
    if (!patient || !state.authToken) {
      return
    }

    state.workspaceLoading = true
    state.workspaceError = ''

    let basicMessage = ''
    let historyMessage = ''
    let detailMessage = ''

    try {
      const basicResponse = await getDoctorPatientBasic(state.authToken, patient.id)
      const basic = normalizePatientBasic(basicResponse)
      if (basic.gender) {
        patient.gender = basic.gender
      }
      if (basic.age != null && basic.age !== '') {
        patient.age = basic.age
      }
      patient.basicInfo = {
        ...patient.basicInfo,
        allergies: basic.allergyHistory.length ? basic.allergyHistory : patient.basicInfo?.allergies || []
      }
    } catch (error) {
      basicMessage = formatErrorMessage(error, '患者基本信息同步失败。')
    }

    try {
      const historyResponse = await getDoctorPatientHistory(state.authToken, patient.id)
      applyPatientHistoryToPatient(patient, normalizePatientHistory(historyResponse))
    } catch (error) {
      historyMessage = formatErrorMessage(error, '患者历史病历同步失败。')
    }

    try {
      let latestRecord =
        seedRecord && seedRecord.recordId
          ? upsertRecordState(normalizeRecordListItem(seedRecord, seedRecord))
          : null

      if (!latestRecord && patient.recordId) {
        latestRecord =
          state.records.find((record) => record.recordId === patient.recordId) ||
          state.recordSearchResults.find((record) => record.recordId === patient.recordId) ||
          null
      }

      if (latestRecord?.recordId) {
        const detailRecord = await fetchRecordDetail(latestRecord.recordId, {
          silent: true,
          throwOnError: true
        })

        if (detailRecord) {
          patient.recordId = detailRecord.recordId
          state.activeRecordId = detailRecord.recordId
          applyRecordDetailToPatient(patient, detailRecord)
        }
      } else if (!seedRecord?.recordId) {
        patient.recordId = ''
      }
    } catch (error) {
      detailMessage = formatErrorMessage(error, '患者病历详情同步失败。')
    }

    if (basicMessage || detailMessage || historyMessage) {
      state.workspaceError = [basicMessage, detailMessage, historyMessage].filter(Boolean).join(' ')
    }

    state.workspaceLoading = false
  }

  async function fetchQueue() {
    if (!state.authToken) {
      return
    }

    state.queueLoading = true
    state.queueError = ''

    try {
      const queueResponse = await getDoctorQueue(state.authToken, state.queueFilters)
      const queueItems = queueResponse.list.map((item) => {
        const localPatient =
          findPatientEntry(state.patients, item.patient_id, item.order_id) ||
          findPatientEntry(state.queuePatients, item.patient_id, item.order_id) ||
          {}

        return mergeQueuePatientWithLocal(item, localPatient)
      })

      syncQueuePatientsState(queueItems)
      state.queueKpi = queueResponse.kpi
    } catch (error) {
      state.queueError = formatErrorMessage(error, '接诊队列加载失败，请稍后重试。')
    } finally {
      state.queueLoading = false
    }
  }

  async function fetchDepartmentOptions() {
    if (!state.authToken) {
      return
    }

    try {
      const departmentOptions = await getDoctorDepartments(state.authToken)

      state.departmentOptions = buildDepartmentOptions(
        doctorDepartmentOptions,
        departmentOptions,
        [state.settings.profile.department, state.doctorProfile.department]
      )
    } catch (error) {
      console.warn('医生科室列表获取失败，已回退到本地配置。', error)
    }
  }

  async function fetchCaseLibrary() {
    if (!state.authToken) {
      return
    }

    try {
      const cases = await getKnowledgeCaseList(state.authToken, {
        doctorId: state.doctorId,
        limit: 5,
        fallbackAuthor: state.doctorProfile.name,
        doctorProfile: {
          name: state.doctorProfile.name,
          id: state.doctorId
        }
      })

      if (Array.isArray(cases)) {
        state.caseLibrary = sortCaseLibraryEntries(cases)
      }
    } catch (error) {
      console.warn('医案库列表获取失败。', error)
    }
  }

  async function login(credentials) {
    if (state.loginPending) {
      return
    }

    state.loginPending = true
    state.loginError = ''

    try {
      const result = await loginDoctor(credentials)
      const account = credentials?.account?.trim() || state.rememberedAccount || state.settings.profile.account

      if (credentials?.remember) {
        rememberDoctorAccount(account)
        state.rememberedAccount = account
      } else {
        clearRememberedDoctorAccount()
        state.rememberedAccount = ''
      }

      saveDoctorAuthSession({
        token: result?.token
      })

      state.authToken = result?.token || ''
      state.doctorId = result?.doctor_id || ''
      state.activeModule = normalizeModuleKey(
        result?.default_landing || state.settings.workspace.defaultLandingModule,
        state.navigationItems
      )
      state.settings.workspace.defaultLandingModule = state.activeModule
      state.departmentOptions = buildDepartmentOptions(
        doctorDepartmentOptions,
        [state.settings.profile.department, result?.department]
      )
      syncDoctorProfileState({
        name: result?.name || state.settings.profile.name,
        account,
        department: result?.department || state.settings.profile.department
      })

      try {
        const profile = await getDoctorProfile(state.authToken)

        syncDoctorProfileState(profile)
        state.doctorId = profile?.doctor_id || state.doctorId
      } catch (profileError) {
        console.warn('医生资料获取失败，已回退到登录返回信息。', profileError)
      }

      state.loggedIn = true
      await Promise.allSettled([fetchDepartmentOptions(), fetchQueue(), fetchCaseLibrary()])
    } catch (error) {
      state.loggedIn = false
      state.authToken = ''
      state.doctorId = ''
      clearDoctorAuthSession()
      state.loginError = formatErrorMessage(error, '登录失败，请稍后重试。')
    } finally {
      state.loginPending = false
    }
  }

  async function restoreDoctorSession() {
    if (!state.authToken) {
      return
    }

    try {
      const profile = await getDoctorProfile(state.authToken)
      state.doctorId = profile?.doctor_id || state.doctorId
      syncDoctorProfileState(profile || {})
      state.loggedIn = true
      await Promise.allSettled([fetchDepartmentOptions(), fetchQueue(), fetchCaseLibrary()])
    } catch (error) {
      // 令牌过期或已被撤销时才回到登录页，避免每次刷新都丢失登录态。
      console.warn('医生登录态已失效，请重新登录。', error)
      state.loggedIn = false
      state.authToken = ''
      state.doctorId = ''
      clearDoctorAuthSession()
    }
  }

  function logout() {
    state.loggedIn = false
    state.loginError = ''
    state.authToken = ''
    state.doctorId = ''
    state.departmentOptions = buildDepartmentOptions(doctorDepartmentOptions, [state.settings.profile.department])
    state.agentSending = false
    state.agentError = ''
    state.queueLoading = false
    state.queueError = ''
    state.queueKpi = null
    state.queuePatients = []
    state.recordsLoading = false
    state.recordsError = ''
    state.recordDetailLoading = false
    state.workspaceLoading = false
    state.workspaceError = ''
    clearWorkspaceActionState()
    state.recordSearchResults = []
    state.patients = []
    state.records = []
    state.activePatientId = ''
    state.activePatientOrderId = ''
    state.activeRecordId = ''
    state.activeModule = 'queue'
    clearDoctorAuthSession()
  }

  function setActiveModule(moduleKey) {
    const nextModule = normalizeModuleKey(moduleKey, state.navigationItems, state.activeModule)

    state.activeModule = nextModule

    if (nextModule !== 'workspace') {
      clearWorkspaceActionState()
    }

    if (nextModule === 'queue' && state.authToken) {
      fetchQueue()
    }

    if (nextModule === 'settings' && state.authToken) {
      fetchDepartmentOptions()
    }

    if (nextModule === 'cases' && state.authToken) {
      fetchCaseLibrary()
    }
  }

  function returnToQueue() {
    state.activeModule = 'queue'
    state.activePatientId = ''
    state.activePatientOrderId = ''
    state.agentSending = false
    state.agentError = ''
    clearWorkspaceActionState()

    if (state.authToken) {
      fetchQueue()
    }
  }

  function updateQueueFilter(key, value) {
    state.queueFilters[key] = value

    if (state.authToken) {
      fetchQueue()
    }
  }

  function updateDutyStatus(status) {
    if (!['值班', '休息'].includes(status)) {
      return
    }

    state.doctorProfile.dutyStatus = status
  }

  function searchRecords(filters) {
    return runRecordsSearch(filters).then(async (response) => {
      if (state.activeRecordId) {
        const activeRecord = state.records.find((record) => record.recordId === state.activeRecordId)

        if (activeRecord && !isRecordDetailLoaded(activeRecord)) {
          await fetchRecordDetail(state.activeRecordId, {
            silent: true
          })
        }
      }

      return response
    })
  }

  async function deprecatedLocalOpenConsultation(target) {
    const patientId = typeof target === 'object' ? target?.patientId : target
    const seedRecord = typeof target === 'object' ? target : null

    if (!patientId) {
      return
    }

    let patient = findPatientEntry(state.patients, patientId)

    if (!patient) {
      patient = createQueuePatientPlaceholder({
        id: patientId,
        recordId: seedRecord?.recordId || '',
        name: seedRecord?.patientName || '',
        gender: seedRecord?.patientGender || '',
        age: seedRecord?.patientAge != null ? Number(seedRecord.patientAge) : '',
        department: seedRecord?.department || '',
        schedule: '',
        status: '问诊中'
      })
      state.patients.unshift(patient)
    }

    state.activePatientId = patientId
    state.activePatientOrderId = patient.orderId || ''
    state.activeModule = 'workspace'
    state.agentSending = false
    state.agentError = ''
    state.workspaceError = ''

    if (patient.status === '待接诊') {
      patient.status = '问诊中'
    }

    if (seedRecord?.recordId) {
      patient.recordId = seedRecord.recordId
      state.activeRecordId = seedRecord.recordId
    } else if (patient.recordId) {
      state.activeRecordId = patient.recordId
    } else {
      state.activeRecordId = ''
    }

    await hydrateWorkspacePatient(patient, seedRecord)
  }

  async function openRecord(recordId) {
    if (!recordId) {
      return
    }

    state.activeRecordId = recordId
    state.activePatientOrderId = ''
    state.activeModule = 'records'
    state.agentSending = false
    state.agentError = ''
    state.recordsError = ''
    clearWorkspaceActionState()

    const record = await fetchRecordDetail(recordId)

    if (record?.patientId) {
      state.activePatientId = record.patientId
      state.activePatientOrderId = ''
    }
  }

  async function openWorkspaceConsultation(target) {
    const patientId = typeof target === 'object' ? target?.patientId || target?.id : target
    const orderId = typeof target === 'object' ? target?.orderId || target?.order_id || '' : ''
    const seedRecord = typeof target === 'object' && target?.recordId ? target : null

    if (!patientId) {
      return
    }

    let patient =
      findPatientEntry(state.patients, patientId, orderId) ||
      findPatientEntry(state.queuePatients, patientId, orderId) ||
      null

    if (!patient) {
      patient = createQueuePatientPlaceholder({
        id: patientId,
        orderId,
        recordId: seedRecord?.recordId || '',
        name: target?.patientName || seedRecord?.patientName || '',
        gender: seedRecord?.patientGender || '',
        age: seedRecord?.patientAge != null ? Number(seedRecord.patientAge) : '',
        department: target?.department || seedRecord?.department || '',
        schedule: target?.schedule || target?.time || '',
        status: orderId ? '待接诊' : '问诊中'
      })
      state.patients.unshift(patient)
    }

    clearWorkspaceActionState()
    state.queueError = ''
    state.workspaceError = ''

    if (target && typeof target === 'object') {
      patient.orderId = patient.orderId || orderId
      patient.name = target.patientName || target.name || patient.name
      patient.department = target.department || patient.department
      patient.schedule = target.schedule || target.time || patient.schedule
    }

    if (isQueuePatientClosed(patient.status)) {
      state.queueError = '\u5df2\u7ed3\u675f\u6216\u5df2\u53d6\u6d88\u7684\u63a5\u8bca\u5355\u4e0d\u80fd\u518d\u6b21\u8fdb\u5165\u5de5\u4f5c\u53f0\u3002'
      return
    }

    if (state.authToken && patient.orderId && patient.status === '待接诊') {
      try {
        const response = await startDoctorOrder(state.authToken, patient.orderId)
        syncOrderStatusState(patient.orderId, patient.id, response?.status || 'ongoing')
      } catch (error) {
        state.queueError = formatErrorMessage(error, '接诊启动失败，请稍后重试。')
        return
      }
    }

    state.activePatientId = patientId
    state.activePatientOrderId = patient.orderId || orderId || ''
    state.activeModule = 'workspace'
    state.agentSending = false
    state.agentError = ''
    state.workspaceError = ''

    if (patient.status === '待接诊') {
      patient.status = '问诊中'
    }

    if (seedRecord?.recordId) {
      patient.recordId = seedRecord.recordId
      state.activeRecordId = seedRecord.recordId
    }

    const linkedRecord =
      state.records.find((record) => record.patientId === patientId) ||
      state.recordSearchResults.find((record) => record.patientId === patientId)

    if (linkedRecord) {
      state.activeRecordId = linkedRecord.recordId
    }

    await hydrateWorkspacePatient(patient, seedRecord)
  }

  function sendDoctorMessage(text) {
    if (!activePatient.value || !text || !text.trim()) {
      return
    }

    activePatient.value.chatMessages.push({
      id: `msg-${Date.now()}`,
      sender: 'doctor',
      roleLabel: '医生',
      time: '实时',
      text: text.trim()
    })

    if (activePatient.value.status === '待接诊') {
      activePatient.value.status = '问诊中'
    }
  }

  async function sendAgentMessage(text) {
    if (!activePatient.value || !text || !text.trim() || !state.authToken || state.agentSending) {
      return
    }

    const patient = activePatient.value
    const question = text.trim()
    const userMessageId = `agent-user-${Date.now()}`
    const replyMessageId = `agent-reply-${Date.now() + 1}`
    const conversationMode = patient.agentSessionId ? 'follow-up' : 'normal'

    state.agentSending = true
    state.agentError = ''
    patient.agentConversationStatus = 'streaming'
    patient.agentAskRound = 0
    patient.agentLastResponse = ''

    appendAgentMessage(patient, {
      id: userMessageId,
      sender: 'doctor',
      roleLabel: '\u533b\u751f',
      time: formatClock(),
      text: question
    })

    try {
      let latestResponse = ''
      let latestStatus = ''
      let latestFinish = false
      let latestSessionId = patient.agentSessionId || ''
      let latestDiagnosis = null

      const response = await sendDoctorAgentMessage(
        state.authToken,
        patient,
        question,
        conversationMode,
        (chunkText, meta = {}) => {
          if (chunkText) {
            if (!Array.isArray(patient.agentMessages) || !patient.agentMessages.find((item) => item.id === replyMessageId)) {
              upsertAgentMessage(patient, replyMessageId, chunkText, formatClock())
            }

            latestResponse += chunkText
            updateAgentMessageText(patient, replyMessageId, latestResponse)
            patient.agentLastResponse = latestResponse
          }

          if (meta.session_id) {
            latestSessionId = meta.session_id
          }

          if (meta.status) {
            latestStatus = meta.status
          }

          if (meta.metadata?.diagnosis) {
            latestDiagnosis = meta.metadata.diagnosis
          }

          if (typeof meta.finish !== 'undefined' && meta.finish !== latestFinish) {
            latestFinish = Boolean(meta.finish)
            console.log('finish', latestFinish)
          }

          if (meta.metadata && Object.prototype.hasOwnProperty.call(meta.metadata, 'ask_round')) {
            patient.agentAskRound = Number(meta.metadata.ask_round) || patient.agentAskRound
          }
        }
      )

      const replyText = response?.response || latestResponse

      patient.agentSessionId = response?.session_id || latestSessionId || patient.agentSessionId
      patient.agentConversationStatus = response?.status || latestStatus || (replyText ? 'done' : '')
      patient.agentAskRound = response?.status === 'asking' ? response?.ask_round || 1 : patient.agentAskRound || 0
      patient.agentLastResponse = replyText

      if (replyText) {
        updateAgentMessageText(patient, replyMessageId, replyText)
      }

      if ((response?.status === 'diagnosed' || latestStatus === 'diagnosed') && (response?.diagnosis || latestDiagnosis)) {
        syncAgentDiagnosisToPatient(patient, response.diagnosis || latestDiagnosis, replyText)
      }

      if (response?.status === 'error' || latestStatus === 'error') {
        state.agentError = replyText
      }
    } catch (error) {
      const message = formatErrorMessage(error, '\u667a\u80fd\u52a9\u624b\u6682\u65f6\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002')

      state.agentError = message
      patient.agentConversationStatus = 'error'
      patient.agentAskRound = 0
      patient.agentLastResponse = message
      if (!Array.isArray(patient.agentMessages) || !patient.agentMessages.find((item) => item.id === replyMessageId)) {
        upsertAgentMessage(patient, replyMessageId, message, formatClock())
      } else {
        updateAgentMessageText(patient, replyMessageId, message)
      }
    } finally {
      state.agentSending = false
    }
  }

  function updatePatientInfo(payload) {
    if (!activePatient.value || !payload) {
      return
    }

    const patient = activePatient.value

    patient.name = payload.name
    patient.gender = payload.gender
    patient.age = Number(payload.age) || patient.age

    if (Object.prototype.hasOwnProperty.call(payload, 'symptomBrief')) {
      patient.symptomBrief = payload.symptomBrief
    }

    if (Object.prototype.hasOwnProperty.call(payload, 'registrationNote')) {
      patient.registrationNote = payload.registrationNote
    }

    patient.basicInfo = {
      ...patient.basicInfo,
      allergies: payload.allergies,
      historySyndromes: payload.historySyndromes,
      historyPrescriptions: payload.historyPrescriptions
    }

    const linkedRecord = state.records.find((record) => record.patientId === patient.id)

    if (linkedRecord) {
      linkedRecord.patientName = patient.name
    }
  }

  function deprecatedLocalSaveDiagnosis(payload) {
    if (!activePatient.value || !payload) {
      return
    }

    activePatient.value.fourDiagnosis = {
      ...activePatient.value.fourDiagnosis,
      ...payload.fourDiagnosis
    }

    activePatient.value.treatmentPlan = {
      ...activePatient.value.treatmentPlan,
      ...payload.treatmentPlan
    }

    if (payload.agentResult) {
      activePatient.value.agentResult = {
        ...payload.agentResult
      }
    }

    if (payload.doctorConfirmation) {
      activePatient.value.doctorConfirmation = {
        ...(activePatient.value.doctorConfirmation || {}),
        ...payload.doctorConfirmation
      }
    }

    if (hasOwn(payload.doctorConfirmation, 'advice')) {
      activePatient.value.treatmentPlan.followUp = payload.doctorConfirmation.advice || ''
    }

    if (hasOwn(payload.doctorConfirmation, 'precautions')) {
      activePatient.value.treatmentPlan.precautions = payload.doctorConfirmation.precautions || ''
    }

    if (hasOwn(payload, 'aiAdjustment')) {
      activePatient.value.aiPlan.syndrome = payload.aiAdjustment
    }

    if (hasOwn(payload, 'therapy')) {
      activePatient.value.aiPlan.therapy = payload.therapy
    }

    if (hasOwn(payload.treatmentPlan, 'formula')) {
      activePatient.value.aiPlan.formula = payload.treatmentPlan.formula
    }

    if (payload.gapNote) {
      activePatient.value.aiPlan.gaps.unshift(payload.gapNote)
    }

    if (payload.completeVisit) {
      activePatient.value.status = '已结束'
    } else if (activePatient.value.status === '待接诊') {
      activePatient.value.status = '问诊中'
    }

    const linkedRecord = state.records.find((record) => record.patientId === activePatient.value.id)

    if (!linkedRecord) {
      return
    }

    linkedRecord.syndrome = hasOwn(activePatient.value.doctorConfirmation, 'syndrome')
      ? activePatient.value.doctorConfirmation.syndrome || ''
      : activePatient.value.aiPlan.syndrome
    linkedRecord.formula = hasOwn(activePatient.value.doctorConfirmation, 'prescription')
      ? activePatient.value.doctorConfirmation.prescription || ''
      : activePatient.value.treatmentPlan.formula
    linkedRecord.therapy = hasOwn(activePatient.value.doctorConfirmation, 'treatment')
      ? activePatient.value.doctorConfirmation.treatment || ''
      : activePatient.value.aiPlan.therapy
    linkedRecord.ingredients = hasOwn(activePatient.value.doctorConfirmation, 'herbs')
      ? Array.isArray(activePatient.value.doctorConfirmation.herbs)
        ? activePatient.value.doctorConfirmation.herbs.filter(Boolean)
        : []
      : Array.isArray(linkedRecord.ingredients)
        ? linkedRecord.ingredients
        : []
    linkedRecord.advice = hasOwn(activePatient.value.doctorConfirmation, 'advice')
      ? activePatient.value.doctorConfirmation.advice || ''
      : activePatient.value.treatmentPlan.followUp || ''
    linkedRecord.precautions = hasOwn(activePatient.value.doctorConfirmation, 'precautions')
      ? activePatient.value.doctorConfirmation.precautions || ''
      : activePatient.value.treatmentPlan.precautions || ''
    linkedRecord.doctorConfirmation = activePatient.value.doctorConfirmation
    linkedRecord.agentResult = activePatient.value.agentResult
    linkedRecord.fourDiagnosis = {
      ...activePatient.value.fourDiagnosis
    }
    linkedRecord.chatSummary = activePatient.value.chatMessages
      .slice(-2)
      .map((message) => `${message.roleLabel}：${message.text}`)
      .join('；')
  }

  function deprecatedLocalSaveDiagnosisAndReturnToQueue(payload) {
    deprecatedLocalSaveDiagnosis({
      ...payload,
      completeVisit: false
    })
    state.activePatientId = ''
    state.activePatientOrderId = ''
    state.activeRecordId = ''
    returnToQueue()
  }

  async function saveWorkspaceDiagnosisAndReturnToQueue(payload) {
    if (!activePatient.value || !payload) {
      return
    }

    const patient = activePatient.value

    if (!patient.orderId) {
      applyWorkspacePayloadToPatient(patient, {
        ...payload,
        completeVisit: false
      })
      clearWorkspaceActionState()
      state.activePatientId = ''
      state.activePatientOrderId = ''
      state.activeRecordId = ''
      returnToQueue()
      return
    }

    if (!state.authToken) {
      setWorkspaceActionError('当前登录状态已失效，请重新登录后再暂存接诊结果。', 'save')
      return
    }

    startWorkspaceAction('save')

    try {
      const response = await saveDoctorOrder(state.authToken, patient.orderId, payload, patient)
      applyWorkspacePayloadToPatient(patient, {
        ...payload,
        completeVisit: false
      })
      syncOrderStatusState(patient.orderId, patient.id, response?.status || 'ongoing')
      clearWorkspaceActionState()
      state.activePatientId = ''
      state.activePatientOrderId = ''
      state.activeRecordId = ''
      state.activeModule = 'queue'
      await fetchQueue()
    } catch (error) {
      setWorkspaceActionError(formatErrorMessage(error, '接诊暂存失败，请稍后重试。'), 'save')
    }
  }

  function updateSettingsSaveMeta(section, message) {
    state.settingsSaveMeta.section = section
    state.settingsSaveMeta.message = message
    state.settingsSaveMeta.lastSavedAt = formatTimestamp()
  }

  function pushSettingsActivity(action) {
    state.settings.activity.unshift({
      time: formatTimestamp(),
      action,
      operator: state.doctorProfile.name
    })

    if (state.settings.activity.length > 6) {
      state.settings.activity.pop()
    }
  }

  async function saveProfileSettings(payload, onSuccess, onError) {
    if (!state.authToken) {
      const message = '当前登录状态已失效，请重新登录后再保存个人资料。'

      if (typeof onError === 'function') {
        onError(message)
      }

      return
    }

    try {
      await updateDoctorProfile(state.authToken, payload)
      syncDoctorProfileState(payload)

      pushSettingsActivity('更新个人资料与侧边栏展示信息')
      updateSettingsSaveMeta('个人资料', '个人资料已保存，侧边栏和登录信息已同步更新。')

      if (typeof onSuccess === 'function') {
        onSuccess()
      }
    } catch (error) {
      if (typeof onError === 'function') {
        onError(formatErrorMessage(error, '个人资料保存失败，请稍后重试。'))
      }
    }
  }

  async function saveContactSettings(payload, onSuccess, onError) {
    if (!state.authToken) {
      const message = '当前登录状态已失效，请重新登录后再保存联系信息。'

      if (typeof onError === 'function') {
        onError(message)
      }

      return
    }

    try {
      await updateDoctorContact(state.authToken, payload)
      syncDoctorProfileState(payload)

      pushSettingsActivity('更新联系信息')
      updateSettingsSaveMeta('联系信息', '联系信息已保存。')

      if (typeof onSuccess === 'function') {
        onSuccess()
      }
    } catch (error) {
      if (typeof onError === 'function') {
        onError(formatErrorMessage(error, '联系信息保存失败，请稍后重试。'))
      }
    }
  }

  function saveNotificationSettings(payload) {
    state.settings.notifications = {
      ...state.settings.notifications,
      ...payload
    }

    pushSettingsActivity('更新消息提醒与通知策略')
    updateSettingsSaveMeta('消息提醒', '通知策略已保存，后续可直接对接站内信、短信或邮件接口。')
  }

  function saveWorkspaceSettings(payload) {
    state.settings.workspace = {
      ...state.settings.workspace,
      ...payload
    }

    pushSettingsActivity('更新工作台偏好配置')
    updateSettingsSaveMeta('工作台偏好', '工作台偏好已保存，默认入口会在下次登录时生效。')
  }

  async function saveSecuritySettings(payload, onSuccess, onError) {
    if (!state.authToken) {
      const message = '当前登录状态已失效，请重新登录后再修改密码。'

      if (typeof onError === 'function') {
        onError(message)
      }

      return
    }

    try {
      if (payload.oldPassword && payload.newPassword) {
        await updateDoctorPassword(state.authToken, {
          oldPassword: payload.oldPassword,
          newPassword: payload.newPassword
        })
      }

      const nextSecurity = {
        ...state.settings.security,
        ...payload
      }

      if (payload.oldPassword && payload.newPassword) {
        nextSecurity.lastPasswordUpdate = formatTimestamp().slice(0, 10)
      }

      delete nextSecurity.passwordChanged
      delete nextSecurity.oldPassword
      delete nextSecurity.newPassword
      delete nextSecurity.confirmPassword

      state.settings.security = nextSecurity

      pushSettingsActivity('更新账号安全策略')
      updateSettingsSaveMeta('账号安全', '安全设置已保存，二次验证与会话策略已更新。')

      if (typeof onSuccess === 'function') {
        onSuccess()
      }
    } catch (error) {
      if (typeof onError === 'function') {
        onError(formatErrorMessage(error, '密码修改失败，请稍后重试。'))
      }
    }
  }

  async function saveCaseLibraryEntry(payload) {
    const normalizedEntry = normalizeCaseLibraryEntry(payload, state.doctorProfile.name)

    if (!normalizedEntry.title) {
      throw new Error('请先填写医案标题。')
    }

    if (normalizedEntry.id) {
      let nextEntry = normalizedEntry

      if (state.authToken && hasKnowledgeCaseUpdateApi()) {
        nextEntry = await updateKnowledgeCaseEntry(normalizedEntry, {
          token: state.authToken,
          fallbackAuthor: state.doctorProfile.name,
          doctorProfile: {
            name: state.doctorProfile.name,
            id: state.doctorId
          }
        })
      }

      state.caseLibrary = sortCaseLibraryEntries(
        state.caseLibrary.map((entry) => {
          if (entry.id !== normalizedEntry.id) {
            return entry
          }

          return normalizeKnowledgeCaseEntry(nextEntry, entry)
        })
      )

      return
    }

    if (state.authToken) {
      const createOptions = {
        token: state.authToken,
        fallbackAuthor: state.doctorProfile.name,
        doctorProfile: {
          name: state.doctorProfile.name,
          id: state.doctorId
        }
      }

      const createdEntry = await createKnowledgeCaseEntry(normalizedEntry, createOptions)

      state.caseLibrary = sortCaseLibraryEntries([createdEntry, ...state.caseLibrary])
      return
    }

    state.caseLibrary = sortCaseLibraryEntries([
      normalizeKnowledgeCaseEntry(
        {
          ...normalizedEntry,
          id: `CASE-${Date.now()}`
        },
        {
          author: state.doctorProfile.name
        }
      ),
      ...state.caseLibrary
    ])
  }

  async function deleteCaseLibraryEntry(entryId) {
    const normalizedId = String(entryId || '').trim()

    if (!normalizedId) {
      return
    }

    const targetEntry = state.caseLibrary.find((entry) => entry.id === normalizedId)

    if (state.authToken && targetEntry && hasKnowledgeCaseDeleteApi()) {
      await deleteKnowledgeCaseEntry(targetEntry, {
        token: state.authToken
      })
    }

    state.caseLibrary = state.caseLibrary.filter((entry) => entry.id !== normalizedId)
  }

  function deprecatedLocalFinishConsultation(payload) {
    deprecatedLocalSaveDiagnosis({
      ...payload,
      completeVisit: true
    })
    state.activePatientId = ''
    state.activePatientOrderId = ''
    state.activeRecordId = ''
    returnToQueue()
  }

  async function finishWorkspaceConsultation(payload) {
    if (!activePatient.value || !payload) {
      return
    }

    const patient = activePatient.value

    if (!patient.orderId) {
      applyWorkspacePayloadToPatient(patient, {
        ...payload,
        completeVisit: true
      })
      clearWorkspaceActionState()
      state.activePatientId = ''
      state.activePatientOrderId = ''
      state.activeRecordId = ''
      returnToQueue()
      return
    }

    if (!state.authToken) {
      setWorkspaceActionError('当前登录状态已失效，请重新登录后再完成接诊。', 'finish')
      return
    }

    startWorkspaceAction('finish')

    try {
      const response = await finishDoctorOrder(state.authToken, patient.orderId, payload, patient)
      applyWorkspacePayloadToPatient(patient, {
        ...payload,
        completeVisit: true
      })
      syncOrderStatusState(patient.orderId, patient.id, response?.status || 'finished')
      clearWorkspaceActionState()
      state.activePatientId = ''
      state.activePatientOrderId = ''
      state.activeRecordId = ''
      state.activeModule = 'queue'
      await fetchQueue()
    } catch (error) {
      setWorkspaceActionError(formatErrorMessage(error, '完成接诊失败，请稍后重试。'), 'finish')
    }
  }

  onMounted(() => {
    restoreDoctorSession()
  })

  return {
    state,
    activeNavigation,
    filteredPatients,
    activePatient,
    activeRecord,
    queueStats,
    queueDepartments,
    queuePeriods,
    login,
    logout,
    setActiveModule,
    returnToQueue,
    updateQueueFilter,
    updateDutyStatus,
    searchRecords,
    openConsultation: openWorkspaceConsultation,
    openRecord,
    sendDoctorMessage,
    sendAgentMessage,
    updatePatientInfo,
    saveDiagnosisAndReturnToQueue: saveWorkspaceDiagnosisAndReturnToQueue,
    saveProfileSettings,
    saveContactSettings,
    saveNotificationSettings,
    saveWorkspaceSettings,
    saveSecuritySettings,
    saveCaseLibraryEntry,
    deleteCaseLibraryEntry,
    finishConsultation: finishWorkspaceConsultation
  }
}
