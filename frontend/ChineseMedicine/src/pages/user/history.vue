<template>
	<view class="history-page">
		<view class="history-page__orb history-page__orb--top"></view>
		<view class="history-page__orb history-page__orb--bottom"></view>

		<view class="history-shell">
			<button class="back-btn" @tap="goBack">
				<view class="back-btn__arrow"></view>
			</button>

			<view class="title-block">
				<text class="title-block__title">历史记录</text>
				<text class="title-block__desc">查看挂号诊断与本次登录的 AI 问诊记录</text>
			</view>

			<view class="header-actions">
				<view class="header-actions__meta">
					<text class="header-actions__meta-label">最近同步</text>
					<text class="header-actions__meta-value">{{ lastSyncedLabel }}</text>
				</view>
				<button class="header-actions__refresh" :class="{ 'header-actions__refresh--loading': loading }" :disabled="loading" @tap="manualRefresh">
					<view class="header-actions__refresh-icon"></view>
					<text class="header-actions__refresh-text">{{ loading ? '同步中…' : '刷新' }}</text>
				</button>
			</view>

			<view class="filter-bar">
				<button
					v-for="tab in tabs"
					:key="tab.value"
					class="filter-bar__tab"
					:class="{ 'filter-bar__tab--active': activeTab === tab.value }"
					@tap="activeTab = tab.value"
				>
					{{ tab.label }}
				</button>
			</view>

			<view v-if="activeTab === 'orders'" class="tab-panel">
				<view v-if="loading" class="history-loading">
					<text class="history-loading__text">加载中...</text>
				</view>

				<view v-else-if="records.length === 0" class="history-empty">
					<text class="history-empty__text">暂无挂号记录</text>
				</view>

				<template v-else>
					<view class="overview-card">
						<view class="overview-card__item">
							<text class="overview-card__label">全部记录</text>
							<text class="overview-card__value">{{ records.length }}</text>
						</view>
						<view class="overview-card__item">
							<text class="overview-card__label">已结束</text>
							<text class="overview-card__value overview-card__value--finished">{{ finishedCount }}</text>
						</view>
						<view class="overview-card__item">
							<text class="overview-card__label">未开始</text>
							<text class="overview-card__value overview-card__value--pending">{{ pendingCount }}</text>
						</view>
					</view>

					<view class="history-list">
						<button
							v-for="item in records"
							:key="item.id"
							class="history-card"
							@tap="goDetail(item)"
						>
							<view class="history-card__head">
								<text class="history-card__title">{{ getVisitTitle(item) }}</text>
								<view
									class="history-card__badge"
									:class="item.status === 'finished' ? 'history-card__badge--finished' : 'history-card__badge--pending'"
								>
									{{ item.statusLabel }}
								</view>
							</view>

							<view class="history-card__footer">
								<view class="history-card__date">
									<text class="history-meta__label">预约日期</text>
									<text class="history-meta__value">{{ item.appointmentDate }}</text>
								</view>
								<text class="history-card__action">查看详情 ›</text>
							</view>
						</button>
					</view>
				</template>
			</view>

			<view v-else class="tab-panel">
				<view v-if="aiSessions.length === 0" class="history-empty">
					<text class="history-empty__text">本次登录暂无 AI 会话记录</text>
					<text class="history-empty__hint">在主页进入智能挂号与助手沟通后，会话会自动保存到这里。</text>
				</view>

				<view v-else class="history-list">
					<button
						v-for="session in aiSessions"
						:key="session.id"
						class="session-card"
						@tap="goAiSession(session)"
					>
						<view class="session-card__head">
							<view class="session-card__icon">
								<image
									class="session-card__icon-image"
									src="/static/design-assets/icons/lucide/messages-square.svg"
									mode="aspectFit"
								></image>
							</view>
							<view class="session-card__copy">
								<text class="session-card__title">AI 智能挂号 · {{ session.summary }}</text>
								<text class="session-card__meta">{{ session.updatedAt }}</text>
							</view>
							<text class="session-card__arrow">›</text>
						</view>
						<view v-if="session.department" class="session-card__pill">
							<text class="session-card__pill-label">建议科室</text>
							<text class="session-card__pill-value">{{ session.department }}</text>
						</view>
					</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { getDiagnosisHistory } from '../../api'
	import { getAiSessions } from '../../config/ai-sessions'

	export default {
		data() {
			return {
				activeTab: 'orders',
				tabs: [
					{ value: 'orders', label: '挂号记录' },
					{ value: 'ai', label: 'AI 会话' }
				],
				records: [],
				aiSessions: [],
				loading: false,
				lastSyncedAt: 0
			}
		},
		computed: {
			finishedCount() {
				return this.records.filter((item) => item.status === 'finished').length
			},
			pendingCount() {
				return this.records.filter((item) => item.status === 'pending').length
			},
			lastSyncedLabel() {
				if (!this.lastSyncedAt) return '尚未同步'
				const date = new Date(this.lastSyncedAt)
				const hh = String(date.getHours()).padStart(2, '0')
				const mm = String(date.getMinutes()).padStart(2, '0')
				const ss = String(date.getSeconds()).padStart(2, '0')
				return `今天 ${hh}:${mm}:${ss}`
			}
		},
		onShow() {
			this.syncRecords()
			this.syncAiSessions()
		},
		onPullDownRefresh() {
			this.syncRecords().finally(() => {
				uni.stopPullDownRefresh()
			})
		},
		methods: {
			syncRecords() {
				this.loading = true
				return getDiagnosisHistory('all')
					.then((list) => {
					this.records = list
						.map((item) => {
							const appt = uni.getStorageSync('cm_appt_' + item.id)
							return appt && appt.label ? { ...item, appointmentDate: appt.label } : item
						})
						.sort((a, b) => {
							// 挂号记录按预约日期降序：日期越晚的排在越上面
							const va = a.appointmentDate || ''
							const vb = b.appointmentDate || ''
							if (va === vb) return 0
							return vb > va ? 1 : -1
						})
						this.lastSyncedAt = Date.now()
					})
					.catch(() => {
						this.records = []
					})
					.finally(() => {
						this.loading = false
					})
			},
			syncAiSessions() {
				this.aiSessions = getAiSessions()
			},
			manualRefresh() {
				this.syncRecords()
			},
			getVisitTitle(item) {
				return `${item.doctorName} ${item.department} 面诊`
			},
			goBack() {
				if (getCurrentPages().length > 1) {
					uni.navigateBack()
					return
				}
				uni.reLaunch({
					url: '/pages/user/user'
				})
			},
			goDetail(item) {
				uni.navigateTo({
					url: `/pages/user/history-detail?id=${encodeURIComponent(item.id)}&status=${item.status}&department=${encodeURIComponent(item.department)}`
				})
			},
			goAiSession(session) {
				const payload = encodeURIComponent(JSON.stringify(session))
				uni.navigateTo({
					url: `/pages/user/history-detail?type=ai&payload=${payload}`
				})
			}
		}
	}
</script>

<style lang="scss">
	.history-page {
		position: relative;
		min-height: 100vh;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx calc(42rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.history-page__orb {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.history-page__orb--top {
		top: 120rpx;
		right: -88rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.history-page__orb--bottom {
		left: -72rpx;
		bottom: 160rpx;
		width: 190rpx;
		height: 190rpx;
		background: rgba(108, 146, 181, 0.08);
	}

	.history-shell {
		position: relative;
		z-index: 1;
	}

	.back-btn {
		position: absolute;
		top: 0;
		left: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 76rpx;
		height: 76rpx;
		border: 0;
		border-radius: 24rpx;
		box-shadow: inset 0 0 0 2rpx rgba(36, 49, 44, 0.22);
		background: rgba(255, 255, 255, 0.86);
	}

	.back-btn::after {
		border: 0;
	}

	.back-btn__arrow {
		width: 18rpx;
		height: 18rpx;
		border-left: 4rpx solid $cm-text-title;
		border-bottom: 4rpx solid $cm-text-title;
		transform: rotate(45deg);
	}

	.title-block {
		padding-top: 110rpx;
	}

	.title-block__title,
	.title-block__desc,
	.filter-bar__tab,
	.overview-card__label,
	.overview-card__value,
	.history-card__title,
	.history-meta__label,
	.history-meta__value,
	.history-card__action,
	.history-loading__text,
	.history-empty__text,
	.history-empty__hint,
	.session-card__title,
	.session-card__meta,
	.session-card__arrow,
	.session-card__pill-label,
	.session-card__pill-value,
	.header-actions__meta-label,
	.header-actions__meta-value,
	.header-actions__refresh-text {
		display: block;
	}

	.title-block__title {
		font-size: 60rpx;
		font-weight: 700;
		line-height: 1.2;
		color: $cm-text-title;
	}

	.title-block__desc {
		margin-top: 12rpx;
		font-size: 24rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.header-actions {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: 24rpx;
		padding: 16rpx 22rpx;
		border-radius: 24rpx;
		background: rgba(255, 255, 255, 0.92);
		box-shadow: $cm-shadow-sm;
	}

	.header-actions__meta {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.header-actions__meta-label {
		font-size: 22rpx;
		color: $cm-text-secondary;
	}

	.header-actions__meta-value {
		margin-top: 6rpx;
		font-size: 26rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.header-actions__refresh {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		margin: 0;
		padding: 0 24rpx;
		height: 56rpx;
		border: 0;
		border-radius: 999rpx;
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
		box-shadow: 0 4rpx 14rpx rgba(132, 214, 10, 0.22);
		color: #ffffff;
	}

	.header-actions__refresh::after {
		border: 0;
	}

	.header-actions__refresh[disabled] {
		opacity: 0.7;
	}

	.header-actions__refresh-icon {
		width: 24rpx;
		height: 24rpx;
		margin-right: 10rpx;
		border: 4rpx solid #ffffff;
		border-top-color: transparent;
		border-radius: 999rpx;
		box-sizing: border-box;
	}

	.header-actions__refresh--loading .header-actions__refresh-icon {
		animation: history-spin 0.9s linear infinite;
	}

	@keyframes history-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.header-actions__refresh-text {
		font-size: 24rpx;
		font-weight: 600;
		line-height: 1;
		color: #ffffff;
	}

	.filter-bar {
		display: flex;
		margin-top: 28rpx;
		padding: 6rpx;
		border-radius: 999rpx;
		background: rgba(255, 255, 255, 0.92);
		box-shadow: $cm-shadow-sm;
	}

	.filter-bar__tab {
		flex: 1;
		height: 64rpx;
		padding: 0;
		margin: 0;
		border: 0;
		border-radius: 999rpx;
		background: transparent;
		font-size: 26rpx;
		font-weight: 600;
		line-height: 64rpx;
		color: $cm-text-secondary;
	}

	.filter-bar__tab::after {
		border: 0;
	}

	.filter-bar__tab--active {
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
		color: #ffffff;
		box-shadow: 0 4rpx 14rpx rgba(132, 214, 13, 0.28);
	}

	.tab-panel {
		margin-top: 22rpx;
	}

	.history-loading,
	.history-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		margin-top: 28rpx;
		padding: 80rpx 32rpx;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.94);
		box-shadow: $cm-shadow-sm;
	}

	.history-empty__text {
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.history-empty__hint {
		margin-top: 10rpx;
		font-size: 22rpx;
		line-height: 1.6;
		text-align: center;
		color: $cm-text-secondary;
	}

	.history-loading__text {
		font-size: 26rpx;
		color: $cm-text-secondary;
	}

	.overview-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16rpx;
	}

	.overview-card__item {
		flex: 1;
		padding: 22rpx 24rpx;
		border-radius: 28rpx;
		background: rgba(255, 255, 255, 0.94);
		box-shadow: $cm-shadow-sm;
	}

	.overview-card__label {
		font-size: 22rpx;
		color: $cm-text-secondary;
	}

	.overview-card__value {
		margin-top: 10rpx;
		font-size: 36rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.overview-card__value--finished {
		color: $cm-success;
	}

	.overview-card__value--pending {
		color: $cm-warning;
	}

	.history-list {
		margin-top: 22rpx;
	}

	.history-card {
		width: 100%;
		margin-top: 18rpx;
		padding: 26rpx;
		border: 0;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
		line-height: 1.2;
		text-align: left;
	}

	.history-card::after {
		border: 0;
	}

	.history-card__head,
	.history-card__date,
	.history-card__footer {
		display: flex;
		align-items: center;
	}

	.history-card__head,
	.history-card__footer {
		justify-content: space-between;
	}

	.history-card__badge {
		flex-shrink: 0;
		margin-left: 18rpx;
		padding: 10rpx 18rpx;
		border-radius: 999rpx;
		font-size: 20rpx;
		font-weight: 700;
	}

	.history-card__badge--finished {
		background: rgba(89, 169, 106, 0.14);
		color: $cm-success;
	}

	.history-card__badge--pending {
		background: rgba(229, 174, 57, 0.16);
		color: #b37a12;
	}

	.history-card__title {
		flex: 1;
		font-size: 34rpx;
		font-weight: 700;
		line-height: 1.35;
		color: $cm-text-title;
	}

	.history-meta__label {
		flex-shrink: 0;
		font-size: 22rpx;
		color: $cm-text-secondary;
	}

	.history-meta__value {
		margin-left: 14rpx;
		font-size: 24rpx;
		font-weight: 400;
		color: #7e8f87;
	}

	.history-card__footer {
		margin-top: 18rpx;
	}

	.history-card__date {
		flex: 1;
		min-width: 0;
	}

	.history-card__action {
		flex-shrink: 0;
		margin-left: 18rpx;
		font-size: 22rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.session-card {
		display: block;
		width: 100%;
		margin-top: 18rpx;
		padding: 24rpx 26rpx;
		border: 0;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
		text-align: left;
	}

	.session-card::after {
		border: 0;
	}

	.session-card__head {
		display: flex;
		align-items: center;
	}

	.session-card__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 72rpx;
		height: 72rpx;
		border-radius: 22rpx;
		background: rgba(132, 214, 13, 0.14);
		flex-shrink: 0;
	}

	.session-card__icon-image {
		width: 36rpx;
		height: 36rpx;
	}

	.session-card__copy {
		flex: 1;
		margin-left: 16rpx;
		min-width: 0;
	}

	.session-card__title {
		font-size: 28rpx;
		font-weight: 700;
		line-height: 1.4;
		color: $cm-text-title;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.session-card__meta {
		margin-top: 6rpx;
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.session-card__arrow {
		flex-shrink: 0;
		margin-left: 12rpx;
		font-size: 40rpx;
		line-height: 1;
		color: #94a09b;
	}

	.session-card__pill {
		display: flex;
		align-items: center;
		margin-top: 14rpx;
		padding: 10rpx 18rpx;
		border-radius: 16rpx;
		background: #f3f7ec;
	}

	.session-card__pill-label {
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.session-card__pill-value {
		margin-left: 10rpx;
		font-size: 24rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}
</style>
