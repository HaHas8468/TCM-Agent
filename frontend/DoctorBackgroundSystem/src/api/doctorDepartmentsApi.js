import { request } from './http'

export const doctorDepartmentsApi = {
  getDepartments: {
    method: 'GET',
    path: '/api/departments'
  }
}

export function normalizeDepartmentOptions(payload) {
  if (!Array.isArray(payload)) {
    return []
  }

  return Array.from(
    new Set(
      payload
        .map((item) => String(item?.department || '').trim())
        .filter(Boolean)
    )
  )
}

export async function getDoctorDepartments(token) {
  const payload = await request(doctorDepartmentsApi.getDepartments.path, {
    method: doctorDepartmentsApi.getDepartments.method,
    token
  })

  return normalizeDepartmentOptions(payload)
}
