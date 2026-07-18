// 前后端字段映射：把后端 API 数据结构转换成前端页面使用的结构（以及反向）
import { formatDateTime, formatNow } from '../utils/format'

function splitAllergy(value) {
  if (!value || !value.trim() || value.trim() === '无') return []
  return value
    .split(/[、,，;；]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function joinAllergy(list) {
  if (!Array.isArray(list) || list.length === 0) return '无'
  return list.join('、')
}

// 后端档案 -> 前端表单（profile.vue）
export function mapProfileToForm(profile = {}) {
  if (!profile || typeof profile !== 'object') return {}
  return {
    name: profile.name || '',
    gender: profile.gender || '女',
    birth: profile.birth_date || '',
    age: profile.age != null ? String(profile.age) : '',
    phone: profile.phone || '',
    allergyHistory: joinAllergy(profile.allergy_history)
  }
}

// 前端表单 -> 后端档案（PUT /api/patient/profile）
// 注意：avatar 按附录 D 由前端本地管理，不在此提交
export function mapFormToProfile(form = {}) {
  const ageNum = form.age !== '' && form.age != null ? Number(form.age) : null
  const payload = {
    name: form.name,
    gender: form.gender,
    birth_date: form.birth,
    age: isNaN(ageNum) ? null : ageNum,
    phone: form.phone,
    allergy_history: splitAllergy(form.allergyHistory)
  }

  if (form.password) {
    payload.password = form.password
  }

  return payload
}

// 后端科室列表 -> 前端下拉/医生卡片结构（direct.vue）
export function flattenDepartments(data = []) {
  const departments = []
  const doctors = []
  ;(data || []).forEach((group) => {
    const department = group.department
    if (department && !departments.includes(department)) {
      departments.push(department)
    }
    ;(group.doctors || []).forEach((doc) => {
      doctors.push({
        id: doc.doctor_id,
        name: doc.name,
        title: '',
        department: department || '',
        state: '可预约',
        desc: doc.specialty || ''
      })
    })
  })
  return { departments, doctors }
}

// 后端历史诊断列表 -> 前端 history 卡片结构（history.vue）
export function mapDiagnosisHistory(list = []) {
  return (list || []).map((item) => {
    const status = item.status || 'pending'
    const statusLabel =
      status === 'finished'
        ? '已结束'
        : status === 'pending'
        ? '未开始'
        : status === 'ongoing'
        ? '进行中'
        : status
    return {
      id: item.order_id,
      createdAt: item.created_at || item.date || '',
      status,
      statusLabel,
      appointmentDate: [item.appointment_date, item.appointment_time].filter(Boolean).join(' ') || formatDateTime(item.date),
      doctorName: (item.doctor && item.doctor.name) || '接诊医生',
      department: item.department || '',
      clinic: '本草问方 · ' + (item.department || '门诊'),
      diagnosisType: status === 'finished' ? '已完成诊断' : '预约登记',
      resultTitle: status === 'finished' ? item.diagnosis_summary || '诊断已完成' : '待面诊',
      resultSummary: status === 'finished' ? item.diagnosis_summary || '' : item.symptoms_summary || '等待医生面诊',
      chiefComplaint: item.symptoms_summary || '',
      diagnosisBasis: item.diagnosis_summary || '',
      advice: item.advice_list || [],
      notices: ['本记录来自线上挂号系统，正式结论以线下面诊为准。']
    }
  })
}

// 后端挂号/病历详情 -> 前端 history-detail 结构（history-detail.vue）
// status / department 由列表页带入（详情接口未返回这两个字段）
export function mapOrderDetail(data = {}, ctx = {}) {
  const status = ctx.status || (data.syndrome ? 'finished' : 'pending')
  const statusLabel =
    status === 'finished'
      ? '已结束'
      : status === 'pending'
      ? '未开始'
      : status === 'ongoing'
      ? '进行中'
      : status
  const advice = Array.isArray(data.advice)
    ? data.advice
    : Array.isArray(data.advice_list)
    ? data.advice_list
    : data.advice
    ? [data.advice]
    : []
  const notices = Array.isArray(data.notices)
    ? data.notices.filter(Boolean)
    : typeof data.notices === 'string' && data.notices
    ? [data.notices]
    : data.notice
    ? [data.notice]
    : ['本记录来自线上挂号系统，正式结论以线下面诊为准。']
  return {
    id: data.record_id || data.order_id || ctx.id || '',
    status,
    statusLabel,
    department: ctx.department || data.department || '',
    doctorName: (data.doctor && data.doctor.name) || '接诊医生',
    appointmentDate: [data.appointment_date, data.appointment_time].filter(Boolean).join(' ') || ctx.apptLabel || formatDateTime(data.date),
    chiefComplaint: data.chief_complaint || '',
    resultSummary: data.present_illness || data.symptoms_summary || '',
    diagnosisBasis: data.syndrome
      ? `辨证：${data.syndrome}${data.treatment_principle ? '；治法：' + data.treatment_principle : ''}`
      : data.present_illness || '',
    advice,
    doctorAdvice: advice.join('；'),
    syndrome: data.syndrome || '',
    treatmentPrinciple: data.treatment_principle || '',
    prescription: data.prescription || '',
    ingredients: Array.isArray(data.ingredients) ? data.ingredients.filter(Boolean) : [],
    tongue: data.tongue || '',
    pulse: data.pulse || '',
    notices
  }
}

// 智能问诊 diagnosed -> 前端 recommendation / result 结构（smart.vue）
export function mapDiagnosisToResult(diagnosis = {}, response = '') {
  const diag = diagnosis || {}
  const signals = [diag.syndrome, diag.prescription].filter(Boolean)
  if (diag.allergy_warnings && diag.allergy_warnings.length) {
    signals.push('过敏提醒：' + diag.allergy_warnings.join('、'))
  }

  //疗法字段只放真正的煎服法/疗法内容（diag.therapy），系统分析回复已在 reason 中展示
  const therapy = diag.therapy || undefined

  return {
    title: diag.syndrome ? `初步辨证：${diag.syndrome}` : '初步辨证完成',
    summary: diag.prescription ? `推荐方剂：${diag.prescription}` : response || '',
    department: diag.department || '待定',
    priority: '建议尽快预约',
    reason: response || diag.department || '已完成初步辨证，可查看详情或继续挂号。',
    signals,
    therapy: therapy || undefined,
    advice: ['可点击下方按钮查看结果详情，或按推荐科室继续挂号。'],
    notices: ['当前结果由智能体生成，仅供就诊参考，不替代正式医疗诊断。'],
    updatedAt: formatNow()
  }
}
