// 本地 AI 会话记录存储：保存本次登录中的智能挂号会话
const SESSIONS_STORAGE_KEY = 'cm-ai-sessions'

function padNumber(value) {
	return String(value).padStart(2, '0')
}

function buildTimestamp(date = new Date()) {
	const year = date.getFullYear()
	const month = padNumber(date.getMonth() + 1)
	const day = padNumber(date.getDate())
	const hours = padNumber(date.getHours())
	const minutes = padNumber(date.getMinutes())
	const seconds = padNumber(date.getSeconds())

	return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

function buildDateLabel(date = new Date()) {
	const year = date.getFullYear()
	const month = date.getMonth() + 1
	const day = date.getDate()
	const hours = padNumber(date.getHours())
	const minutes = padNumber(date.getMinutes())

	return `${year}年${month}月${day}日 ${hours}:${minutes}`
}

function parseStoredList(value) {
	if (!value) return []
	if (typeof value === 'string') {
		try {
			const parsed = JSON.parse(value)
			return Array.isArray(parsed) ? parsed : []
		} catch (error) {
			return []
		}
	}
	if (Array.isArray(value)) return value
	return []
}

function readAll() {
	return parseStoredList(uni.getStorageSync(SESSIONS_STORAGE_KEY))
}

function writeAll(list) {
	uni.setStorageSync(SESSIONS_STORAGE_KEY, list)
}

// 生成会话摘要：取用户首条消息前 20 个字符
function buildSummary(messages = []) {
	const firstUserMsg = messages.find((item) => item.role === 'user')
	const text = firstUserMsg ? firstUserMsg.text : ''
	const trimmed = String(text || '').trim()
	if (!trimmed) return 'AI 智能挂号会话'
	return trimmed.length > 20 ? `${trimmed.slice(0, 20)}…` : trimmed
}

// 规范化单条消息
function normalizeMessage(msg = {}) {
	return {
		id: msg.id || `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
		role: msg.role === 'user' ? 'user' : 'assistant',
		text: String(msg.text || ''),
		thinking: false,
		timestamp: msg.timestamp || buildTimestamp()
	}
}

// 规范化一条会话记录
function normalizeSession(session = {}) {
	const messages = Array.isArray(session.messages) ? session.messages.map(normalizeMessage) : []
	return {
		id: session.id || `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
		summary: session.summary || buildSummary(messages),
		messages,
		department: session.department || '',
		diagnosis: session.diagnosis || null,
		createdAt: session.createdAt || buildTimestamp(),
		updatedAt: session.updatedAt || buildTimestamp()
	}
}

/**
 * 保存或更新一条 AI 会话记录
 * @param {Object} session 会话对象，包含 id、messages、department、diagnosis 等
 * @returns {Object} 规范化后的会话
 */
export function saveAiSession(session = {}) {
	const list = readAll()
	const normalized = normalizeSession(session)
	const existingIndex = list.findIndex((item) => item.id === normalized.id)

	if (existingIndex >= 0) {
		list[existingIndex] = { ...list[existingIndex], ...normalized, createdAt: list[existingIndex].createdAt, updatedAt: buildTimestamp() }
	} else {
		list.unshift(normalized)
	}

	// 只保留最近 50 条
	const trimmed = list.slice(0, 50)
	writeAll(trimmed)
	return normalized
}

/**
 * 获取所有 AI 会话记录（按更新时间倒序）
 * @returns {Array}
 */
export function getAiSessions() {
	return readAll()
		.map(normalizeSession)
		.sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''))
}

/**
 * 根据 ID 获取单条 AI 会话记录
 * @param {string} id
 * @returns {Object|null}
 */
export function getAiSessionById(id) {
	if (!id) return null
	const list = readAll()
	const found = list.find((item) => item.id === id)
	return found ? normalizeSession(found) : null
}

/**
 * 删除一条 AI 会话记录
 * @param {string} id
 */
export function deleteAiSession(id) {
	if (!id) return
	const list = readAll().filter((item) => item.id !== id)
	writeAll(list)
}

/**
 * 清空所有 AI 会话记录
 */
export function clearAiSessions() {
	writeAll([])
}

export { buildDateLabel, buildTimestamp }
