import { request } from './http'

export async function getDoctorSchedules(token, days = 30) {
  return request(`/api/doctor/schedules?days=${days}`, { method: 'GET', token })
}

export async function updateDoctorSchedule(token, date, period, action) {
  return request(`/api/doctor/schedules/${date}/${period}`, {
    method: 'PATCH',
    token,
    data: { action }
  })
}
