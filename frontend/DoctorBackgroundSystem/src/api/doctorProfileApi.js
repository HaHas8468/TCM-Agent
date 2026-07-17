import { request } from './http'

export const doctorDepartmentOptions = ['中医内科', '呼吸内科', '神经内科', '心血管内科', '消化内科', '骨伤科', '妇科', '儿科', '皮肤科', '肾病科', '泌尿外科', '内分泌科']

export const doctorShiftOptions = ['周一至周五 8:00-17:00', '周一至周六 8:00-17:00', '周二至周日 9:00-18:00', '周一至周五 8:00-17:00']

const DEFAULT_DUTY_STATUS = '值班'
const DEFAULT_DEPARTMENT = doctorDepartmentOptions[0]
const DEFAULT_SHIFT = doctorShiftOptions[0]

function getDefaultDoctorDepartment(options = doctorDepartmentOptions) {
  return Array.isArray(options) ? options.find(Boolean) || DEFAULT_DEPARTMENT : DEFAULT_DEPARTMENT
}

export const doctorProfileApi = {
  getProfile: {
    method: 'GET',
    path: '/api/doctor/profile'
  },
  updateProfile: {
    method: 'PUT',
    path: '/api/doctor/profile'
  },
  updateContact: {
    method: 'PUT',
    path: '/api/doctor/profile'
  },
  updatePassword: {
    method: 'PUT',
    path: '/api/doctor/security/password'
  }
}

export function normalizeDoctorProfileState(source = {}, fallback = {}) {
  return {
    ...fallback,
    doctorId: source.doctorId || source.doctor_id || fallback.doctorId || '',
    name: source.name || fallback.name || '',
    title: source.title || fallback.title || '',
    role: source.role || fallback.role || '',
    account: source.account || source.username || fallback.account || '',
    phone: source.phone || fallback.phone || '',
    email: source.email || fallback.email || '',
    department: resolveDoctorDepartment(source.department || fallback.department),
    organization: source.organization || fallback.organization || '',
    shift: resolveDoctorShift(source.shift || source.duty_time || fallback.shift),
    focus: source.focus || source.specialty || fallback.focus || '',
    bio: source.bio || fallback.bio || '',
    signature: source.signature || fallback.signature || '',
    clinicRoom: source.clinicRoom || fallback.clinicRoom || ''
  }
}

export async function updateDoctorContact(token, payload = {}) {
  return request(doctorProfileApi.updateContact.path, {
    method: doctorProfileApi.updateContact.method,
    token,
    data: buildDoctorContactUpdatePayload(payload)
  })
}

export async function updateDoctorPassword(token, payload = {}) {
  return request(doctorProfileApi.updatePassword.path, {
    method: doctorProfileApi.updatePassword.method,
    token,
    data: buildDoctorPasswordUpdatePayload(payload)
  })
}

export function resolveDoctorDepartment(value, options = doctorDepartmentOptions) {
  const normalizedValue = String(value || '').trim()

  if (normalizedValue) {
    return normalizedValue
  }

  return getDefaultDoctorDepartment(options)
}

export function resolveDoctorShift(value) {
  const normalizedValue = String(value || '').trim()
  if (normalizedValue) {
    return normalizedValue
  }
  return DEFAULT_SHIFT
}

export function createDoctorProfileView(source = {}, dutyStatus = DEFAULT_DUTY_STATUS) {
  const profile = normalizeDoctorProfileState(source)

  return {
    name: profile.name,
    title: profile.title,
    role: profile.role,
    account: profile.account,
    department: profile.department,
    organization: profile.organization,
    shift: profile.shift,
    focus: profile.focus,
    bio: profile.bio,
    phone: profile.phone,
    email: profile.email,
    dutyStatus: dutyStatus || DEFAULT_DUTY_STATUS
  }
}

export function applyDoctorProfile(target, source = {}) {
  Object.assign(target, createDoctorProfileView(source, target?.dutyStatus || DEFAULT_DUTY_STATUS))
  return target
}

export function buildDoctorProfileUpdatePayload(form = {}) {
  return {
    name: form.name || '',
    account: form.account || '',
    department: resolveDoctorDepartment(form.department),
    shift: resolveDoctorShift(form.shift),
    focus: form.focus || '',
    bio: form.bio || '',
    phone: form.phone || '',
    password: form.password || ''
  }
}

export function buildDoctorProfileApiPayload(form = {}) {
  const payload = {
    name: form.name || '',
    username: form.account || '',
    department: resolveDoctorDepartment(form.department),
    duty_time: resolveDoctorShift(form.shift),
    specialty: form.focus || '',
    bio: form.bio || ''
  }

  if (form.phone) {
    payload.phone = form.phone
  }

  if (form.password) {
    payload.password = form.password
  }

  return payload
}

export function buildDoctorContactUpdatePayload(form = {}) {
  return {
    email: form.email || '',
    phone: form.phone || ''
  }
}

export function buildDoctorPasswordUpdatePayload(form = {}) {
  return {
    oldPassword: form.oldPassword || '',
    newPassword: form.newPassword || ''
  }
}

export async function getDoctorProfile(token) {
  return request(doctorProfileApi.getProfile.path, {
    method: doctorProfileApi.getProfile.method,
    token
  })
}

export async function updateDoctorProfile(token, payload = {}) {
  return request(doctorProfileApi.updateProfile.path, {
    method: doctorProfileApi.updateProfile.method,
    token,
    data: buildDoctorProfileApiPayload(payload)
  })
}
