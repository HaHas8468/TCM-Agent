const DIAGNOSIS_RESULT_STORAGE_KEY = 'cm-latest-diagnosis-result'

export const defaultDiagnosisResult = Object.freeze({
	title: '暂无诊断结果',
	summary: '完成一次智能挂号沟通后，最新诊断结果会自动同步到这里，方便你随时查看。',
	department: '待生成',
	priority: '待更新',
	reason: '当前还没有新的诊断记录。你可以先进入智能挂号，与助手沟通症状后生成建议结果。',
	signals: ['等待问诊', '支持同步', '可继续挂号'],
	advice: [
		'先进入智能挂号，描述主要症状、持续时间和最担心的问题。',
		'生成结果后，可回到信息页继续查看建议科室与调理方向。',
		'若已经明确需求，也可以直接前往挂号中心自行选择。'
	],
	notices: [
		'当前页面展示最近一次智能挂号生成的结果。',
		'本页面内容仅作前端演示，不替代医生正式诊断。',
		'如出现明显加重或急性不适，请及时线下就医。'
	],
	updatedAt: '等待生成'
})

function padNumber(value) {
	return String(value).padStart(2, '0')
}

function buildDateLabel(date = new Date()) {
	const year = date.getFullYear()
	const month = date.getMonth() + 1
	const day = date.getDate()
	const hours = padNumber(date.getHours())
	const minutes = padNumber(date.getMinutes())

	return `${year}年${month}月${day}日 ${hours}:${minutes}`
}

function normalizeArray(value, fallback) {
	return Array.isArray(value) && value.length ? value : fallback
}

function normalizeDiagnosisResult(result = {}) {
	return {
		...defaultDiagnosisResult,
		...result,
		signals: normalizeArray(result.signals, defaultDiagnosisResult.signals),
		advice: normalizeArray(result.advice, defaultDiagnosisResult.advice),
		notices: normalizeArray(result.notices, defaultDiagnosisResult.notices),
		updatedAt: result.updatedAt || buildDateLabel()
	}
}

function parseStoredResult(value) {
	if (!value) {
		return null
	}

	if (typeof value === 'string') {
		try {
			return JSON.parse(value)
		} catch (error) {
			return null
		}
	}

	if (typeof value === 'object') {
		return value
	}

	return null
}

export function getLatestDiagnosisResult() {
	const storedResult = parseStoredResult(uni.getStorageSync(DIAGNOSIS_RESULT_STORAGE_KEY))

	if (!storedResult) {
		return {
			...defaultDiagnosisResult
		}
	}

	return normalizeDiagnosisResult(storedResult)
}

export function saveLatestDiagnosisResult(result) {
	const normalizedResult = normalizeDiagnosisResult(result)
	uni.setStorageSync(DIAGNOSIS_RESULT_STORAGE_KEY, normalizedResult)
	return normalizedResult
}
