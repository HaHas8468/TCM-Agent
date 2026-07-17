const diagnosisHistoryRecords = Object.freeze([
	{
		id: 'diagnosis-20260710',
		status: 'pending',
		statusLabel: '未开始',
		appointmentDate: '2026年7月10日 14:00',
		doctorName: '周明溪',
		department: '针灸科',
		clinic: '本草问方东院区 · 针灸门诊',
		diagnosisType: '初诊预约',
		resultTitle: '颈肩酸胀待面诊',
		resultSummary: '诊断尚未开始，已为你保留针灸科面诊时段，可提前整理疼痛部位、持续时间和近期作息变化。',
		chiefComplaint: '近两周久坐后颈肩酸胀，下午明显，偶有头部发紧，工作结束后疲劳感更重。',
		diagnosisBasis: '当前为预约前记录，正式诊断内容需以医生到院面诊结果为准，页面主要用于查看预约安排与就诊准备信息。',
		signals: ['颈肩酸胀', '久坐加重', '待面诊'],
		advice: [
			'预约前尽量保持规律作息，避免熬夜和高强度运动。',
			'如果有既往检查结果或用药记录，就诊时可一并携带。',
			'提前记录疼痛出现的时间、部位和诱因，便于医生快速了解情况。'
		],
		notices: [
			'请至少提前 10 分钟到达门诊完成报到。',
			'如需改期，请在预约开始前完成调整。',
			'本条内容为预约信息展示，不替代正式医疗诊断。'
		]
	},
	{
		id: 'diagnosis-20260702',
		status: 'finished',
		statusLabel: '已结束',
		appointmentDate: '2026年7月2日 09:30',
		doctorName: '林知远',
		department: '脾胃科',
		clinic: '本草问方国医馆 · 一诊室',
		diagnosisType: '复诊诊断',
		resultTitle: '脾胃湿困调理复查',
		resultSummary: '饭后腹胀与乏力较前缓解，但睡眠仍偏浅，医生建议继续脾胃调理并同步观察一周作息变化。',
		chiefComplaint: '近期饭后腹胀偶发，晨起乏力，睡眠浅，下午精神波动较明显。',
		diagnosisBasis: '结合复诊反馈、近期饮食情况与体感变化，当前以脾胃运化偏弱、湿困中焦为主，整体处于缓慢恢复阶段。',
		signals: ['饭后腹胀', '晨起乏力', '睡眠偏浅'],
		advice: [
			'继续保持清淡饮食，晚间减少生冷和过甜食物摄入。',
			'本周维持相对稳定的入睡时间，减少夜间加班或久坐。',
			'若腹胀明显加重或伴持续疼痛，建议尽快复诊评估。'
		],
		notices: [
			'本次记录为复诊结果摘要，正式结论以线下面诊病历为准。',
			'调理期间建议连续观察一周，再评估症状变化。',
			'如出现急性不适，请及时前往线下医院就诊。'
		]
	},
	{
		id: 'diagnosis-20260628',
		status: 'finished',
		statusLabel: '已结束',
		appointmentDate: '2026年6月28日 18:40',
		doctorName: '沈清和',
		department: '睡眠调理门诊',
		clinic: '本草问方夜诊中心',
		diagnosisType: '夜诊复盘',
		resultTitle: '睡眠浅与心神不宁调理跟进',
		resultSummary: '睡前焦虑较前减轻，但入睡时间仍偏长，建议继续温和调理并配合放松训练。',
		chiefComplaint: '入睡慢、夜间易醒，晨起口干，近期工作压力较大时更明显。',
		diagnosisBasis: '结合近一周睡眠反馈与当前体感，考虑以心神不宁兼情绪紧绷为主，建议继续调节作息与放松节律。',
		signals: ['入睡偏慢', '夜间易醒', '晨起口干'],
		advice: [
			'睡前 1 小时尽量减少电子屏幕使用，给身体留出放松过渡时间。',
			'可继续保持晚间热水泡脚或舒缓拉伸，帮助睡前放松。',
			'如果持续两周以上没有改善，建议再次复诊并调整方案。'
		],
		notices: [
			'当前内容为调理跟进记录，仅作前端演示。',
			'若出现持续胸闷、明显心悸等情况，请及时线下就医。',
			'建议结合日常睡眠记录，便于下次面诊对照变化。'
		]
	}
])

function cloneRecord(record) {
	return {
		...record,
		signals: [...record.signals],
		advice: [...record.advice],
		notices: [...record.notices]
	}
}

export function getDiagnosisHistoryList() {
	return diagnosisHistoryRecords.map((item) => cloneRecord(item))
}

export function getDiagnosisHistoryDetail(id) {
	const matchedRecord = diagnosisHistoryRecords.find((item) => item.id === id)
	return cloneRecord(matchedRecord || diagnosisHistoryRecords[0])
}
