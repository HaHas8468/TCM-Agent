<template>
	<view class="main-page">
		<view class="main-page__orb main-page__orb--top"></view>
		<view class="main-page__orb main-page__orb--bottom"></view>

		<view class="hero-card">
			<view class="hero-card__meta">
				<view class="hero-card__date">
					<image class="hero-card__date-icon" src="/static/design-assets/icons/lucide/calendar-days.svg" mode="aspectFit"></image>
					<text class="hero-card__date-text">{{ dateLabel }}</text>
				</view>
				<view class="hero-card__profile-button" aria-label="个人中心" @tap="goUser">
					<image class="hero-card__profile-icon" src="/static/design-assets/icons/lucide/menu.svg" mode="aspectFit"></image>
				</view>
			</view>

			<view class="hero-card__main">
				<view class="hero-card__avatar">
					<image class="hero-card__avatar-image" :src="userProfile.avatar" mode="aspectFill"></image>
				</view>
				<view class="hero-card__copy">
					<text class="hero-card__title">你好，{{ userProfile.name }}</text>
					<text class="hero-card__subtitle">今天也要照顾好自己</text>
				</view>
			</view>

			<view class="hero-card__bottom-space"></view>
		</view>

		<view class="content-stack">
			<view class="section-card section-card--smart">
				<view class="section-head">
					<view class="section-head__copy">
						<text class="section-head__title">智能挂号</text>
						<text class="section-head__subtitle">描述症状获取推荐科室</text>
					</view>
					<button class="section-head__action" @tap="goSmartRegister">进入</button>
				</view>

				<view class="smart-card" @tap="goSmartRegister">
					<image class="smart-card__image" src="/static/bot.png" mode="aspectFill"></image>
					<text class="smart-card__title">描述不适症状、持续时间和担心的问题，系统会给出建议科室与就诊方向。</text>
				</view>
			</view>

			<view class="section-card section-card--direct">
				<view class="section-head">
					<view class="section-head__copy">
						<text class="section-head__title">直接挂号</text>
						<text class="section-head__subtitle">选择科室与医生进行挂号</text>
					</view>
				</view>

				<view class="filter-card">
					<picker
						class="select-picker"
						mode="selector"
						:range="departments"
						:value="selectedDepartmentIndex"
						@change="handleDepartmentChange"
					>
						<view class="select-row">
							<text class="select-row__value">{{ selectedDepartment || '请选择科室' }}</text>
							<view class="select-row__arrow"></view>
						</view>
					</picker>
				</view>

				<view class="time-card">
					<view class="time-grid">
						<picker class="time-picker" mode="date" :value="selectedDate" :start="todayDate" @change="handleDateChange">
							<view class="time-select">
								<text class="time-select__label">预约日期</text>
								<text class="time-select__value">{{ selectedDate }}</text>
							</view>
						</picker>
						<picker class="time-picker" mode="time" :value="selectedTime" @change="handleTimeChange">
							<view class="time-select">
								<text class="time-select__label">预约时间</text>
								<text class="time-select__value">{{ selectedTime }}</text>
							</view>
						</picker>
					</view>
				</view>

				<view class="doctor-list">
					<button
						v-for="doctor in filteredDoctors"
						:key="doctor.id"
						class="doctor-card"
						:class="{ 'doctor-card--active': selectedDoctorId === doctor.id }"
						@tap="selectDoctor(doctor)"
					>
						<view class="doctor-card__head">
							<view>
								<text class="doctor-card__name">{{ doctor.name }}</text>
								<text class="doctor-card__meta">{{ doctor.title }} · {{ doctor.department }}</text>
							</view>
							<view class="doctor-card__status">
								<view class="doctor-card__state">{{ doctor.state }}</view>
								<view v-if="selectedDoctorId === doctor.id" class="doctor-card__selected">
									<view class="doctor-card__check">✓</view>
									<text>已选择</text>
								</view>
							</view>
						</view>
						<text class="doctor-card__desc">{{ doctor.desc }}</text>
					</button>
				</view>

				<button class="primary-btn" :class="{ 'primary-btn--loading': submitting }" :disabled="submitting" @tap="confirmRegister">
					{{ submitting ? '正在提交挂号…' : '确认挂号' }}
				</button>
			</view>
		</view>

	</view>
</template>

<script>
	import { getCurrentUserProfile } from '../../config/user-profile'
	import { getDepartments, getDoctorSlots, createOrder, DEPARTMENT_OPTIONS } from '../../api'


	const formatDate = (date) => {
		const year = date.getFullYear()
		const month = `${date.getMonth() + 1}`.padStart(2, '0')
		const day = `${date.getDate()}`.padStart(2, '0')
		return `${year}-${month}-${day}`
	}

	export default {
		data() {
			const todayDate = formatDate(new Date())
			return {
				dateLabel: '',
				dateTimer: null,
				userProfile: getCurrentUserProfile(),

				todayDate,
				selectedDate: todayDate,
				selectedTime: '09:00',
				selectedDepartment: '',
				selectedDoctorId: '',
				doctors: [],
				availableSlots: [],
				loading: false,
				submitting: false,
				source: 'direct',
				prefetchDepartment: ''
			}
		},
		computed: {
			departments() {
				const backendDepartments = this.doctors.map((item) => item.department)
				return Array.from(
					new Set(
						[...DEPARTMENT_OPTIONS, ...backendDepartments]
							.map((item) => String(item || '').trim())
							.filter(Boolean)
					)
				)
			},
			selectedDepartmentIndex() {
				const index = this.departments.indexOf(this.selectedDepartment)
				return index >= 0 ? index : 0
			},
			filteredDoctors() {
				return this.doctors.filter((item) => item.department === this.selectedDepartment)
			}
		},
		onShow() {
			this.syncUserProfile()
			this.startDateTimer()
			this.loadDepartments()
		},
		onLoad(options) {
			if (options && options.department) {
				this.prefetchDepartment = decodeURIComponent(options.department)
			}
		},
		onHide() {
			this.clearDateTimer()
		},
		onUnload() {
			this.clearDateTimer()
		},
		methods: {
			syncUserProfile() {
				this.userProfile = getCurrentUserProfile()
			},
			startDateTimer() {
				this.updateDateLabel()
				this.clearDateTimer()
				this.dateTimer = setInterval(() => {
					this.updateDateLabel()
				}, 60000)
			},
			clearDateTimer() {
				if (!this.dateTimer) {
					return
				}

				clearInterval(this.dateTimer)
				this.dateTimer = null
			},
			updateDateLabel() {
				const currentDate = new Date()
				const weekLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
				const year = currentDate.getFullYear()
				const month = currentDate.getMonth() + 1
				const day = currentDate.getDate()
				const weekLabel = weekLabels[currentDate.getDay()]

				this.dateLabel = `${year}年${month}月${day}日，${weekLabel}`
			},
			goUser() {
				uni.navigateTo({
					url: '/pages/user/user'
				})
			},
		goSmartRegister() {
				uni.navigateTo({
					url: '/pages/register/smart'
				})
			},
			loadDepartments() {
				this.loading = true
				getDepartments()
					.then((result) => {
						this.doctors = result.doctors
						let targetDepartment = ''
						if (this.prefetchDepartment) {
							const depts = this.departments
							const exactMatch = depts.find(d => d === this.prefetchDepartment)
							if (exactMatch) {
								targetDepartment = exactMatch
							} else {
								const parts = this.prefetchDepartment.split(/[/、\s]+/)
								for (const part of parts) {
									const partialMatch = depts.find(d => d.includes(part) || part.includes(d))
									if (partialMatch) {
										targetDepartment = partialMatch
										break
									}
								}
							}
							this.prefetchDepartment = ''
						}
						this.selectedDepartment = targetDepartment || this.departments[0] || ''
						this.syncSelectedDoctor()
						this.fetchSlots()
					})
					.catch(() => {
					})
					.finally(() => {
						this.loading = false
					})
			},
			fetchSlots() {
				if (!this.selectedDoctorId || !this.selectedDate) {
					return
				}
				getDoctorSlots(this.selectedDoctorId, this.selectedDate)
					.then((data) => {
						this.availableSlots = (data && data.available_slots) || []
					})
					.catch(() => {
						this.availableSlots = []
					})
			},
			handleDepartmentChange(event) {
				const nextDepartment = this.departments[Number(event.detail.value)] || ''
				if (!nextDepartment) {
					return
				}
				this.selectedDepartment = nextDepartment
				this.syncSelectedDoctor()
				this.fetchSlots()
			},
			syncSelectedDoctor() {
				const firstDoctor = this.filteredDoctors[0]
				this.selectedDoctorId = firstDoctor ? firstDoctor.id : ''
			},
			handleDateChange(event) {
				this.selectedDate = event.detail.value
				this.fetchSlots()
			},
			handleTimeChange(event) {
				this.selectedTime = event.detail.value
			},
			selectDoctor(doctor) {
				if (this.selectedDoctorId === doctor.id) {
					return
				}
				this.selectedDoctorId = doctor.id
				this.fetchSlots()
			},
			confirmRegister() {
				if (!this.selectedDoctorId || !this.selectedDate || !this.selectedTime) {
					uni.showToast({
						title: '请选择医生和时间',
						icon: 'none'
					})
					return
				}
				if (this.availableSlots.length && !this.availableSlots.includes(this.selectedTime)) {
					uni.showToast({
						title: '该时段暂不可预约，请重新选择',
						icon: 'none'
					})
					return
				}
				this.submitting = true
				createOrder({
					doctorId: this.selectedDoctorId,
					department: this.selectedDepartment,
					date: this.selectedDate,
					time: this.selectedTime,
					source: this.source
				})
					.then((data) => {
						const orderId = (data && (data.order_id || data.id)) || ''
						if (orderId) {
							uni.setStorageSync('cm_appt_' + orderId, {
								date: this.selectedDate,
								time: this.selectedTime,
								label: this.selectedDate + ' ' + this.selectedTime
							})
						}
						uni.showToast({
							title: '挂号成功',
							icon: 'success'
						})
						setTimeout(() => {
							uni.reLaunch({
								url: '/pages/user/history'
							})
						}, 600)
					})
					.catch(() => {
					})
					.finally(() => {
						this.submitting = false
					})
			}
		}
	}
</script>

<style lang="scss">
	.main-page {
		position: relative;
		min-height: 100vh;
		padding: calc(20rpx + env(safe-area-inset-top)) 26rpx calc(48rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.main-page__orb {
		position: absolute;
		border-radius: 38rpx;
		background: rgba(132, 214, 13, 0.1);
		filter: blur(6rpx);
	}

	.main-page__orb--top {
		top: 180rpx;
		right: -76rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.main-page__orb--bottom {
		left: -86rpx;
		bottom: 48rpx;
		width: 200rpx;
		height: 200rpx;
		background: rgba(47, 69, 56, 0.06);
	}

	.hero-card,
	.section-card,
	.highlight-card,
	.quick-item {
		position: relative;
		z-index: 1;
	}

	.hero-card {
		margin: calc(-20rpx - env(safe-area-inset-top)) -26rpx 0;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx 24rpx;
		overflow: hidden;
		border-radius: 0 0 56rpx 56rpx;
		background: linear-gradient(145deg, #ffffff 0%, #f7faef 58%, #edf6e4 100%);
		box-shadow: $cm-shadow-lg;
	}

	.hero-card__main,
		.section-head,
		.quick-item {
		display: flex;
	}

	.section-head {
		align-items: center;
	}

	.hero-card__meta {
		display: flex;
		width: 100%;
		flex-direction: row;
		align-items: center;
		justify-content: space-between;
	}

	.hero-card__date {
		display: flex;
		flex: 1;
		min-width: 0;
		align-items: center;
	}

	.hero-card__date-icon {
		width: 28rpx;
		height: 28rpx;
		opacity: 0.8;
	}

	.hero-card__date-text {
		margin-left: 10rpx;
		font-size: 20rpx;
		font-weight: 600;
		color: $cm-text-secondary;
	}

	.hero-card__profile-button {
		display: flex;
		flex-shrink: 0;
		align-items: center;
		justify-content: center;
		width: 64rpx;
		height: 64rpx;
		padding: 4rpx;
		border: 2rpx solid rgba(47, 69, 56, 0.12);
		border-radius: 20rpx;
		background: rgba(255, 255, 255, 0.72);
		box-sizing: border-box;
		overflow: hidden;
	}

	.hero-card__profile-icon {
		display: block;
		width: 28rpx;
		height: 28rpx;
	}

	.hero-card__main {
		align-items: center;
		margin-top: 32rpx;
	}

	.hero-card__avatar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 102rpx;
		height: 102rpx;
		padding: 6rpx;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.92);
		box-shadow: 0 8rpx 18rpx rgba(47, 69, 56, 0.1), inset 0 0 0 2rpx rgba(255, 255, 255, 0.8);
	}

	.hero-card__avatar-image {
		width: 100%;
		height: 100%;
		border-radius: 29rpx;
	}

	.hero-card__copy {
		flex: 1;
		margin-left: 22rpx;
	}

	.hero-card__title,
	.hero-card__subtitle {
		display: block;
	}

	.hero-card__title {
		font-size: 48rpx;
		font-weight: 700;
		line-height: 1.2;
		color: $cm-text-title;
	}

	.hero-card__subtitle {
		margin-top: 10rpx;
		font-size: 24rpx;
		line-height: 1.5;
		color: $cm-text-secondary;
	}

	.hero-card__bottom-space {
		height: 50rpx;
		margin-top: 16rpx;
	}

	.content-stack {
		position: relative;
		z-index: 1;
		width: calc(100% + 20rpx);
		margin-left: -10rpx;
		margin-top: 24rpx;
		box-sizing: border-box;
	}

	.section-card {
		width: 100%;
		padding: 26rpx;
		border-radius: 32rpx;
		background: #ffffff;
		box-shadow: $cm-shadow-sm;
		box-sizing: border-box;
	}

	.section-card + .section-card {
		margin-top: 24rpx;
	}

	.section-head__title,
	.section-head__subtitle,
	.highlight-card__title,
	.quick-item__title,
		.quick-item__text {
		display: block;
	}

	.section-head__title {
		font-size: 34rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.section-head__copy {
		flex: 1;
		min-width: 0;
		padding-right: 24rpx;
	}

	.section-head__subtitle {
		margin-top: 8rpx;
		font-size: 22rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.section-head__action {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 96rpx;
		height: 56rpx;
		padding: 0 20rpx;
		border-radius: 20rpx;
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
		flex-shrink: 0;
		margin-left: auto;
		color: #ffffff;
		font-size: 22rpx;
		font-weight: 700;
	}

	.smart-card {
		position: relative;
		width: 100%;
		min-height: 340rpx;
		margin-top: 24rpx;
		padding: 24rpx;
		border-radius: 28rpx;
		background: linear-gradient(135deg, #dff4c7 0%, #bde99b 100%);
		overflow: hidden;
	}

	.smart-card__image {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}

	.smart-card__title {
		position: relative;
		z-index: 2;
		font-size: 24rpx;
		line-height: 1.6;
		color: $cm-color-brand-deep;
	}

	.filter-card,
	.time-card {
		margin-top: 22rpx;
		padding: 20rpx;
		border-radius: 24rpx;
		background: #f7faf3;
	}

	.select-picker {
		display: block;
	}

	.select-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 76rpx;
		padding: 0 20rpx;
		border-radius: 20rpx;
		background: #ffffff;
	}

	.select-row__value {
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.select-row__arrow {
		width: 14rpx;
		height: 14rpx;
		border-right: 4rpx solid $cm-text-secondary;
		border-bottom: 4rpx solid $cm-text-secondary;
		transform: rotate(45deg);
	}

	.time-grid {
		display: flex;
		gap: 14rpx;
	}

	.time-picker {
		flex: 1;
		min-width: 0;
	}

	.time-select {
		padding: 16rpx 18rpx;
		border-radius: 20rpx;
		background: #ffffff;
	}

	.time-select__label {
		display: block;
		font-size: 18rpx;
		color: $cm-text-secondary;
	}

	.time-select__value {
		display: block;
		margin-top: 8rpx;
		font-size: 26rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.doctor-list {
		margin-top: 22rpx;
	}

	.doctor-card {
		position: relative;
		width: 100%;
		padding: 22rpx;
		margin-top: 16rpx;
		border: 2rpx solid transparent;
		border-radius: 28rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
		text-align: left;
		transition: border-color 0.2s ease, background 0.2s ease;
	}

	.doctor-card::after {
		border: 0;
	}

	.doctor-card--active {
		border-color: $cm-color-brand;
		background: linear-gradient(135deg, #f4fbe9 0%, #ffffff 76%);
		box-shadow: 0 14rpx 32rpx rgba(91, 149, 24, 0.18);
	}

	.doctor-card__head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
	}

	.doctor-card__status {
		display: flex;
		align-items: center;
		gap: 10rpx;
	}

	.doctor-card__name {
		display: block;
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.doctor-card__meta {
		display: block;
		margin-top: 6rpx;
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.doctor-card__state {
		height: 38rpx;
		padding: 0 14rpx;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.14);
		font-size: 18rpx;
		line-height: 38rpx;
		color: $cm-color-brand-deep;
	}

	.doctor-card__selected {
		display: flex;
		align-items: center;
		padding: 4rpx 10rpx 4rpx 6rpx;
		border-radius: 999rpx;
		background: $cm-color-brand;
		font-size: 18rpx;
		font-weight: 700;
		line-height: 26rpx;
		color: #ffffff;
	}

	.doctor-card__check {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 26rpx;
		height: 26rpx;
		margin-right: 4rpx;
		border-radius: 50%;
		background: #ffffff;
		font-size: 18rpx;
		font-weight: 700;
		line-height: 1;
		color: $cm-color-brand-deep;
	}

	.doctor-card__desc {
		display: block;
		margin-top: 12rpx;
		font-size: 22rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.primary-btn {
		width: 100%;
		height: 88rpx;
		margin-top: 28rpx;
		border: 0;
		border-radius: $cm-radius-pill;
		background: $cm-color-brand;
		box-shadow: 0 14rpx 32rpx rgba(91, 149, 24, 0.2);
		font-size: 28rpx;
		font-weight: 700;
		line-height: 88rpx;
		color: #ffffff;
	}

	.primary-btn::after {
		border: 0;
	}

	.primary-btn--loading,
	.primary-btn[disabled] {
		background: #8aa08f;
		box-shadow: none;
		color: rgba(255, 255, 255, 0.92);
	}

</style>
