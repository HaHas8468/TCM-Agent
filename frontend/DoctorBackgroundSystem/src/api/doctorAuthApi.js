import { request } from './http'

export const DOCTOR_AUTH_STORAGE_KEYS = {
  token: 'doctor_auth_token',
  rememberedAccount: 'doctor_auth_account'
}

export const doctorAuthApi = {
  login: {
    method: 'POST',
    path: '/api/doctor/auth/login'
  }
}

function safeStorage() {
  if (typeof window === 'undefined') {
    return null
  }

  return window.localStorage
}

export function buildDoctorLoginPayload(credentials = {}) {
  return {
    username: String(credentials.account || credentials.username || '').trim(),
    password: String(credentials.password || '')
  }
}

export async function loginDoctor(credentials = {}) {
  const payload = buildDoctorLoginPayload(credentials)

  if (!payload.username || !payload.password) {
    throw new Error('请输入用户名和密码。')
  }

  return request(doctorAuthApi.login.path, {
    method: doctorAuthApi.login.method,
    data: payload
  })
}

export function saveDoctorAuthSession(session = {}) {
  const storage = safeStorage()

  if (!storage) {
    return
  }

  if (session.token) {
    storage.setItem(DOCTOR_AUTH_STORAGE_KEYS.token, session.token)
  }
}

export function getDoctorAuthSession() {
  const storage = safeStorage()

  if (!storage) {
    return ''
  }

  return storage.getItem(DOCTOR_AUTH_STORAGE_KEYS.token) || ''
}

export function clearDoctorAuthSession() {
  const storage = safeStorage()

  if (!storage) {
    return
  }

  storage.removeItem(DOCTOR_AUTH_STORAGE_KEYS.token)
}

export function rememberDoctorAccount(account) {
  const storage = safeStorage()

  if (!storage) {
    return
  }

  storage.setItem(DOCTOR_AUTH_STORAGE_KEYS.rememberedAccount, String(account || '').trim())
}

export function clearRememberedDoctorAccount() {
  const storage = safeStorage()

  if (!storage) {
    return
  }

  storage.removeItem(DOCTOR_AUTH_STORAGE_KEYS.rememberedAccount)
}

export function getRememberedDoctorAccount() {
  const storage = safeStorage()

  if (!storage) {
    return ''
  }

  return storage.getItem(DOCTOR_AUTH_STORAGE_KEYS.rememberedAccount) || ''
}
