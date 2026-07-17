// 时间格式化工具：后端统一返回 ISO8601（YYYY-MM-DDTHH:mm:ss）

function pad(value) {
  return String(value).padStart(2, '0')
}

// '2026-07-10T09:30:00' -> '2026年7月10日 09:30'
export function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (isNaN(date.getTime())) {
    return value
  }
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${pad(date.getHours())}:${pad(
    date.getMinutes()
  )}`
}

// 当前时间字符串（用于"最近同步"等展示）
export function formatNow() {
  return formatDateTime(new Date())
}
