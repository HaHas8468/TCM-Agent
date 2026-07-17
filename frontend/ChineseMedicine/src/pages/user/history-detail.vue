<template>
	<view class="detail-page">
		<view class="detail-page__orb detail-page__orb--top"></view>
		<view class="detail-page__orb detail-page__orb--bottom"></view>

		<button class="back-btn" @tap="goBack">
			<image class="back-btn__icon" src="/static/design-assets/icons/lucide/arrow-left.svg" mode="aspectFit"></image>
		</button>

		<view v-if="loading" class="detail-loading">
			<text class="detail-loading__text">加载中...</text>
		</view>

		<view v-else-if="viewType === 'ai'" class="detail-shell">
			<view class="hero-card">
				<view class="hero-card__head">
					<text class="hero-card__eyebrow">AI 智能挂号</text>
					<view class="hero-card__badge hero-card__badge--ai">对话记录</view>
				</view>
				<text class="hero-card__label">会话主题</text>
				<text class="hero-card__desc">{{ aiSession.summary }}</text>
			</view>

			<view v-if="aiSession.department" class="section-card">
				<text class="section-card__title">AI 推荐科室</text>
				<view class="info-grid">
					<view class="info-item">
						<text class="info-item__label">建议科室</text>
						<text class="info-item__value">{{ aiSession.department }}</text>
					</view>
					<view class="info-item">
						<text class="info-item__label">会话时间</text>
						<text class="info-item__value">{{ aiSession.updatedAt }}</text>
					</view>
				</view>
			</view>

			<view class="section-card">
				<text class="section-card__title">对话内容</text>
				<view class="chat-thread">
					<view
						v-for="(msg, idx) in aiSession.messages"
						:key="idx"
						class="chat-bubble"
						:class="msg.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--assistant'"
					>
						<view class="chat-bubble__label">
							{{ msg.role === 'user' ? '我' : '问方助手' }}
						</view>
						<text class="chat-bubble__text">{{ msg.text }}</text>
					</view>
					<view v-if="!aiSession.messages.length" class="chat-empty">
						<text class="chat-empty__text">本次会话暂无内容</text>
					</view>
				</view>
			</view>
		</view>

		<view v-else class="detail-shell">
			<view class="hero-card">
				<view class="hero-card__head">
					<text class="hero-card__eyebrow">面诊</text>
					<view
						class="hero-card__badge"
						:class="record.status === 'finished' ? 'hero-card__badge--finished' : 'hero-card__badge--pending'"
					>
						{{ record.statusLabel }}
					</view>
				</view>
				<text class="hero-card__label">症状概要</text>
				<text class="hero-card__desc">{{ heroSummary }}</text>
			</view>

			<view class="section-card">
				<text class="section-card__title">预约信息</text>
				<view class="info-grid">
					<view class="info-item">
						<text class="info-item__label">主诊医生</text>
						<text class="info-item__value">{{ record.doctorName }}</text>
					</view>
					<view class="info-item">
						<text class="info-item__label">就诊科室</text>
						<text class="info-item__value">{{ record.department }}</text>
					</view>
					<view class="info-item">
						<text class="info-item__label">预约时间</text>
						<text class="info-item__value">{{ record.appointmentDate }}</text>
					</view>
				</view>
			</view>

			<view v-if="record.status === 'finished'" class="section-card">
				<text class="section-card__title">诊断说明</text>
				<view class="copy-block">
					<text class="copy-block__label">情况概述</text>
					<text class="copy-block__text">{{ record.chiefComplaint }}</text>
				</view>
				<view class="copy-block">
					<text class="copy-block__label">当前记录</text>
					<text class="copy-block__text">{{ diagnosisDescription }}</text>
				</view>
			</view>

			<view v-if="record.status === 'finished'" class="section-card">
				<text class="section-card__title">辨证与治疗</text>
				<view class="detail-grid">
					<view class="detail-grid__item">
						<text class="detail-grid__label">辨证</text>
						<text class="detail-grid__value">{{ record.syndrome || '待补充' }}</text>
					</view>
					<view class="detail-grid__item">
						<text class="detail-grid__label">疗法</text>
						<text class="detail-grid__value">{{ record.treatmentPrinciple || '待补充' }}</text>
					</view>
					<view class="detail-grid__item">
						<text class="detail-grid__label">方剂</text>
						<text class="detail-grid__value">{{ record.prescription || '待补充' }}</text>
					</view>
					<view class="detail-grid__item detail-grid__item--full">
						<text class="detail-grid__label">药材</text>
						<text class="detail-grid__value">{{ ingredientsLabel }}</text>
					</view>
				</view>
			</view>

			<view v-if="record.status === 'finished'" class="section-card">
				<text class="section-card__title">门诊补充信息</text>
				<view class="detail-grid">
					<view class="detail-grid__item">
						<text class="detail-grid__label">就诊医生</text>
						<text class="detail-grid__value">{{ record.doctorName || '待分配' }}</text>
					</view>
					<view class="detail-grid__item detail-grid__item--full">
						<text class="detail-grid__label">医嘱</text>
						<text class="detail-grid__value">{{ doctorAdviceLabel }}</text>
					</view>
					<view class="detail-grid__item detail-grid__item--full">
						<text class="detail-grid__label">注意事项</text>
						<text class="detail-grid__value">{{ noticeSummary }}</text>
					</view>
				</view>
			</view>

			<view class="section-card">
				<text class="section-card__title">调理建议</text>
				<view class="advice-list">
					<view v-for="(item, index) in visibleAdvice" :key="`${index}-${item}`" class="advice-item">
						<view class="advice-item__index">{{ index + 1 }}</view>
						<text class="advice-item__text">{{ item }}</text>
					</view>
				</view>
			</view>

			<view class="section-card section-card--notice">
				<text class="section-card__title">注意事项</text>
				<view class="notice-list">
					<view v-for="(item, index) in visibleNotices" :key="`${index}-${item}`" class="notice-item">
						<view class="notice-item__dot"></view>
						<text class="notice-item__text">{{ item }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { getOrderDetail, buildOrderDetail } from '../../api'

	export default {
		data() {
			return {
				record: {
					advice: [],
					notices: [],
					ingredients: []
				},
				aiSession: {
					messages: [],
					summary: '',
					department: '',
					updatedAt: ''
				},
				viewType: 'order',
				loading: false
			}
		},
		computed: {
			heroSummary() {
				return this.record.chiefComplaint || this.record.resultSummary || '等待医生面诊'
			},
			diagnosisDescription() {
				if (this.record.status === 'pending') {
					return '当前记录待诊断，请以医生到院面诊后的正式结果为准。'
				}

				return this.record.diagnosisBasis || ''
			},
			ingredientsLabel() {
				return Array.isArray(this.record.ingredients) && this.record.ingredients.length
					? this.record.ingredients.join('、')
					: '待补充'
			},
			doctorAdviceLabel() {
				return this.record.doctorAdvice || '待补充'
			},
			noticeSummary() {
				return this.visibleNotices.length ? this.visibleNotices.join('；') : '待补充'
			},
			visibleAdvice() {
				if (Array.isArray(this.record.advice) && this.record.advice.length) {
					return this.record.advice
				}

				return this.record.status === 'pending'
					? ['请按预约时间提前到院，携带必要就诊资料。']
					: ['暂无额外调理建议。']
			},
			visibleNotices() {
				if (this.record.status === 'pending') {
					return [
						'当前页面仅展示预约安排，正式诊断需以面诊结果为准。',
						'请按预约时间提前到院，如需改期请在就诊前完成调整。'
					]
				}

				return Array.isArray(this.record.notices) && this.record.notices.length
					? this.record.notices
					: ['本记录来自线上挂号系统，正式结论以线下面诊为准。']
			}
		},
		onLoad(options) {
			this.syncRecord(options)
		},
		methods: {
			syncRecord(options) {
				const type = options.type || 'order'
				if (type === 'ai') {
					this.viewType = 'ai'
					this.loadAiSession(options)
					return
				}

				this.viewType = 'order'
				const id = options.id ? decodeURIComponent(options.id) : ''
				const status = options.status || ''
				const department = options.department ? decodeURIComponent(options.department) : ''
				if (!id) {
					return
				}

				const appt = uni.getStorageSync('cm_appt_' + id)
				const ctx = { status, department, id }
				if (appt && appt.label) {
					ctx.apptLabel = appt.label
				}

				this.loading = true
				getOrderDetail(id)
					.then((data) => {
						this.record = buildOrderDetail(data, ctx)
					})
					.catch(() => {
						this.record = buildOrderDetail({}, { ...ctx, status: status || 'pending' })
					})
					.finally(() => {
						this.loading = false
					})
			},
			loadAiSession(options) {
				const payload = options.payload ? decodeURIComponent(options.payload) : ''
				this.loading = true
				try {
					const parsed = payload ? JSON.parse(payload) : {}
					this.aiSession = {
						messages: Array.isArray(parsed.messages) ? parsed.messages : [],
						summary: parsed.summary || 'AI 智能挂号会话',
						department: parsed.department || '',
						updatedAt: parsed.updatedAt || ''
					}
				} catch (error) {
					this.aiSession = {
						messages: [],
						summary: 'AI 智能挂号会话',
						department: '',
						updatedAt: ''
					}
				}
				this.loading = false
			},
			goBack() {
				uni.navigateBack({
					fail: () => {
						uni.redirectTo({
							url: '/pages/user/history'
						})
					}
				})
			}
		}
	}
</script>

<style lang="scss">
	.detail-page {
		position: relative;
		min-height: 100vh;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx calc(46rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.detail-page__orb {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.detail-page__orb--top {
		top: 126rpx;
		right: -90rpx;
		width: 226rpx;
		height: 226rpx;
	}

	.detail-page__orb--bottom {
		left: -78rpx;
		bottom: 150rpx;
		width: 194rpx;
		height: 194rpx;
		background: rgba(108, 146, 181, 0.08);
	}

	.detail-shell {
		position: relative;
		z-index: 1;
	}

	.detail-loading {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 120rpx 0;
	}

	.detail-loading__text {
		font-size: 26rpx;
		color: $cm-text-secondary;
	}

	.back-btn {
		position: absolute;
		top: 28rpx;
		top: calc(28rpx + env(safe-area-inset-top));
		left: 26rpx;
		z-index: 5;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64rpx;
		height: 64rpx;
		margin: 0;
		padding: 0;
		border: 1rpx solid rgba(47, 69, 56, 0.12);
		border-radius: 20rpx;
		background: rgba(255, 255, 255, 0.86);
		box-shadow: 0 6rpx 18rpx rgba(47, 69, 56, 0.1);
	}

	.back-btn::after {
		border: 0;
	}

	.back-btn:active {
		transform: scale(0.96);
	}

	.back-btn__icon {
		width: 28rpx;
		height: 28rpx;
	}

	.hero-card,
	.section-card {
		position: relative;
	}

	.hero-card {
		margin: calc(-28rpx - env(safe-area-inset-top)) -26rpx 0;
		padding: calc(118rpx + env(safe-area-inset-top)) 28rpx 30rpx;
		border-radius: 0 0 56rpx 56rpx;
		background: linear-gradient(180deg, #31473a 0%, #3b5644 58%, #415e49 100%);
		box-shadow: $cm-shadow-lg;
	}

	.hero-card__head,
	.hero-card__badge,
	.advice-item,
	.notice-item {
		display: flex;
	}

	.hero-card__head {
		align-items: center;
		justify-content: space-between;
		min-height: 48rpx;
	}

	.hero-card__eyebrow,
	.hero-card__label,
	.hero-card__desc,
	.section-card__title,
	.info-item__label,
	.info-item__value,
	.copy-block__label,
	.copy-block__text,
	.advice-item__text,
	.notice-item__text,
	.detail-grid__label,
	.detail-grid__value {
		display: block;
	}

	.hero-card__eyebrow {
		font-size: 34rpx;
		font-weight: 700;
		line-height: 48rpx;
		color: #ffffff;
	}

	.hero-card__badge {
		align-items: center;
		justify-content: center;
		height: 48rpx;
		padding: 0 18rpx;
		border-radius: 999rpx;
		font-size: 20rpx;
		font-weight: 700;
	}

	.hero-card__badge--finished {
		background: rgba(89, 169, 106, 0.18);
		color: #d8f4df;
	}

	.hero-card__badge--pending {
		background: rgba(243, 212, 107, 0.18);
		color: #fff0b8;
	}

	.hero-card__label {
		margin-top: 28rpx;
		font-size: 22rpx;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.72);
	}

	.hero-card__desc {
		margin-top: 12rpx;
		font-size: 24rpx;
		line-height: 1.7;
		color: rgba(255, 255, 255, 0.8);
	}

	.section-card {
		margin-top: 24rpx;
		padding: 26rpx;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
	}

	.section-card--notice {
		background: linear-gradient(180deg, #ffffff 0%, #fbfaf5 100%);
	}

	.section-card__title {
		font-size: 32rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.info-grid,
	.detail-grid {
		display: flex;
		flex-wrap: wrap;
		margin: 18rpx -8rpx 0;
	}

	.info-item,
	.detail-grid__item {
		width: calc(50% - 16rpx);
		margin: 8rpx;
		padding: 20rpx;
		border-radius: 24rpx;
		background: linear-gradient(180deg, #f6faee 0%, #ffffff 100%);
	}

	.detail-grid__item--full {
		width: calc(100% - 16rpx);
	}

	.info-item__label,
	.detail-grid__label {
		font-size: 22rpx;
		color: $cm-text-secondary;
	}

	.info-item__value,
	.detail-grid__value {
		margin-top: 12rpx;
		font-size: 24rpx;
		font-weight: 700;
		line-height: 1.6;
		color: $cm-text-title;
	}

	.copy-block + .copy-block {
		margin-top: 18rpx;
	}

	.copy-block__label {
		margin-top: 18rpx;
		font-size: 22rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.copy-block__text {
		margin-top: 10rpx;
		font-size: 24rpx;
		line-height: 1.75;
		color: $cm-text-secondary;
	}

	.advice-list,
	.notice-list {
		margin-top: 18rpx;
	}

	.advice-item + .advice-item,
	.notice-item + .notice-item {
		margin-top: 14rpx;
	}

	.advice-item__index {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		width: 42rpx;
		height: 42rpx;
		margin-right: 14rpx;
		border-radius: 50%;
		background: rgba(132, 214, 13, 0.16);
		font-size: 22rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.advice-item__text,
	.notice-item__text {
		flex: 1;
		font-size: 23rpx;
		line-height: 1.75;
		color: $cm-text-body;
	}

	.notice-item__dot {
		flex-shrink: 0;
		width: 12rpx;
		height: 12rpx;
		margin-top: 12rpx;
		margin-right: 14rpx;
		border-radius: 50%;
		background: $cm-warning;
	}

	.hero-card__badge--ai {
		background: rgba(132, 214, 13, 0.22);
		color: #e8f7d4;
	}

	.chat-thread {
		margin-top: 18rpx;
	}

	.chat-bubble {
		max-width: 80%;
		padding: 18rpx 22rpx;
		margin-top: 18rpx;
		border-radius: 24rpx;
	}

	.chat-bubble:first-child {
		margin-top: 0;
	}

	.chat-bubble--user {
		margin-left: auto;
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
		color: #ffffff;
		border-bottom-right-radius: 6rpx;
	}

	.chat-bubble--assistant {
		margin-right: auto;
		background: #f4f7ef;
		color: $cm-text-title;
		border-bottom-left-radius: 6rpx;
	}

	.chat-bubble__label {
		display: block;
		margin-bottom: 8rpx;
		font-size: 18rpx;
		font-weight: 700;
		opacity: 0.7;
	}

	.chat-bubble--user .chat-bubble__label {
		color: rgba(255, 255, 255, 0.92);
	}

	.chat-bubble--assistant .chat-bubble__label {
		color: $cm-color-brand-deep;
	}

	.chat-bubble__text {
		display: block;
		font-size: 24rpx;
		line-height: 1.7;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.chat-empty {
		display: flex;
		justify-content: center;
		padding: 32rpx 0;
	}

	.chat-empty__text {
		font-size: 22rpx;
		color: $cm-text-secondary;
	}
</style>
