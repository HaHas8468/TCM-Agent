import { request } from './http'

export const doctorWorkspaceApi = {
  startOrder: {
    method: 'PUT',
    path: '/api/orders'
  },
  finishOrder: {
    method: 'PUT',
    path: '/api/orders'
  },
  saveOrder: {
    method: 'PUT',
    path: '/api/orders'
  }
}

function splitTextList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean)
  }

  return String(value || '')
    .split(/[、/，,；;\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizeOrderPayloadValue(value) {
  return String(value || '').trim()
}

function hasOwn(target, key) {
  return Boolean(target) && Object.prototype.hasOwnProperty.call(target, key)
}

function pickNormalizedOrderPayloadValue(sources = []) {
  for (const source of sources) {
    if (!source) {
      continue
    }

    if (source.present) {
      return normalizeOrderPayloadValue(source.value)
    }

    const normalizedValue = normalizeOrderPayloadValue(source.value)

    if (normalizedValue) {
      return normalizedValue
    }
  }

  return ''
}

function pickOrderPayloadListValue(sources = []) {
  for (const source of sources) {
    if (!source) {
      continue
    }

    if (source.present) {
      return splitTextList(source.value)
    }

    const normalizedList = splitTextList(source.value)

    if (normalizedList.length) {
      return normalizedList
    }
  }

  return []
}

function buildOrderActionPath(orderId, action) {
  const normalizedOrderId = String(orderId || '').trim()

  if (!normalizedOrderId) {
    throw new Error('当前接诊单缺少 order_id，无法调用工作台接口。')
  }

  return `${doctorWorkspaceApi.startOrder.path}/${normalizedOrderId}/${action}`
}

export function buildDoctorOrderDecisionPayload(payload = {}, patient = {}) {
  const doctorConfirmation = payload.doctorConfirmation || {}
  const treatmentPlan = payload.treatmentPlan || {}
  const currentConfirmation = patient.doctorConfirmation || {}
  const currentTreatmentPlan = patient.treatmentPlan || {}
  const currentPlan = patient.aiPlan || {}

  return {
    syndrome: pickNormalizedOrderPayloadValue([
      { present: hasOwn(doctorConfirmation, 'syndrome'), value: doctorConfirmation.syndrome },
      { present: hasOwn(payload, 'aiAdjustment'), value: payload.aiAdjustment },
      { present: hasOwn(currentConfirmation, 'syndrome'), value: currentConfirmation.syndrome },
      { value: currentPlan.syndrome }
    ]),
    prescription: pickNormalizedOrderPayloadValue([
      { present: hasOwn(doctorConfirmation, 'prescription'), value: doctorConfirmation.prescription },
      { present: hasOwn(treatmentPlan, 'formula'), value: treatmentPlan.formula },
      { present: hasOwn(currentConfirmation, 'prescription'), value: currentConfirmation.prescription },
      { present: hasOwn(currentTreatmentPlan, 'formula'), value: currentTreatmentPlan.formula },
      { value: currentPlan.formula }
    ]),
    ingredients: pickOrderPayloadListValue([
      { present: hasOwn(doctorConfirmation, 'herbs'), value: doctorConfirmation.herbs },
      { present: hasOwn(currentConfirmation, 'herbs'), value: currentConfirmation.herbs },
      { value: patient.agentResult?.diagnosisResult?.herbs || [] }
    ]),
    advice: pickNormalizedOrderPayloadValue([
      { present: hasOwn(doctorConfirmation, 'advice'), value: doctorConfirmation.advice },
      { present: hasOwn(treatmentPlan, 'followUp'), value: treatmentPlan.followUp },
      { present: hasOwn(treatmentPlan, 'advice'), value: treatmentPlan.advice },
      { present: hasOwn(currentConfirmation, 'advice'), value: currentConfirmation.advice },
      { present: hasOwn(currentTreatmentPlan, 'followUp'), value: currentTreatmentPlan.followUp },
      { value: currentTreatmentPlan.advice }
    ]),
    therapy: pickNormalizedOrderPayloadValue([
      { present: hasOwn(doctorConfirmation, 'treatment'), value: doctorConfirmation.treatment },
      { present: hasOwn(payload, 'therapy'), value: payload.therapy },
      { present: hasOwn(currentConfirmation, 'treatment'), value: currentConfirmation.treatment },
      { value: currentPlan.therapy }
    ]),
    precautions: pickNormalizedOrderPayloadValue([
      { present: hasOwn(doctorConfirmation, 'precautions'), value: doctorConfirmation.precautions },
      { present: hasOwn(treatmentPlan, 'precautions'), value: treatmentPlan.precautions },
      { present: hasOwn(currentConfirmation, 'precautions'), value: currentConfirmation.precautions },
      { value: currentTreatmentPlan.precautions }
    ])
  }
}

export async function startDoctorOrder(token, orderId) {
  return request(buildOrderActionPath(orderId, 'start'), {
    method: doctorWorkspaceApi.startOrder.method,
    token
  })
}

export async function saveDoctorOrder(token, orderId, payload = {}, patient = {}) {
  return request(buildOrderActionPath(orderId, 'save'), {
    method: doctorWorkspaceApi.saveOrder.method,
    token,
    data: buildDoctorOrderDecisionPayload(payload, patient)
  })
}

export async function finishDoctorOrder(token, orderId, payload = {}, patient = {}) {
  return request(buildOrderActionPath(orderId, 'finish'), {
    method: doctorWorkspaceApi.finishOrder.method,
    token,
    data: buildDoctorOrderDecisionPayload(payload, patient)
  })
}
