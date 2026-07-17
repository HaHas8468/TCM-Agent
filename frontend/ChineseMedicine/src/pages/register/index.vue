<template>
	<view class="register-page">
		<view class="register-page__orb register-page__orb--top"></view>
		<view class="register-page__orb register-page__orb--bottom"></view>

		<view class="register-hero">
			<text class="register-hero__eyebrow">挂号中心</text>
			<text class="register-hero__title">选择科室与医生</text>
			<text class="register-hero__hint">如果暂时拿不准该挂哪个科室，可先使用智能挂号获得推荐；如果你已经知道目标科室，可以直接选择。</text>
		</view>

		<view class="mode-list">
			<button class="mode-card" @tap="goSmartRegister">
				<view class="mode-card__badge">
					<image class="mode-card__badge-icon" src="/static/design-assets/icons/lucide/messages-square.svg" mode="aspectFit"></image>
					<text class="mode-card__badge-text">智能挂号</text>
				</view>
				<view class="mode-card__copy">
					<text class="mode-card__title">描述症状获取推荐科室</text>
					<text class="mode-card__desc">描述不适症状、持续时间和担心的问题，系统会给出建议科室与就诊方向。</text>
				</view>
				<view class="mode-card__footer">
					<text class="mode-card__arrow">进入</text>
				</view>
			</button>
		</view>

		<view class="direct-section">
			<view class="filter-card">
				<text class="filter-card__title">选择科室</text>
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
				<text class="time-card__title">选择时间</text>
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
		</view>

		<button class="primary-btn" :class="{ 'primary-btn--loading': submitting }" :disabled="submitting" @tap="confirmRegister">
			{{ submitting ? '正在提交挂号…' : '确认挂号' }}
		</button>

		<common-tab-bar active-tab="registration"></common-tab-bar>
	</view>
</template>

<script>
	import CommonTabBar from '../../components/common-tab-bar/common-tab-bar.vue'
	import { getDepartments, getDoctorSlots, createOrder, DEPARTMENT_OPTIONS } from '../../api'

	const formatDate = (date) => {
		const year = date.getFullYear()
		const month = `${date.getMonth() + 1}`.padStart(2, '0')
		const day = `${date.getDate()}`.padStart(2, '0')
		return `${year}-${month}-${day}`
	}

	export default {
		components: {
			CommonTabBar
		},
		data() {
			const todayDate = formatDate(new Date())
			return {
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
				pendingDepartment: ''
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
		onLoad(options = {}) {
			this.pendingDepartment = options.department ? decodeURIComponent(options.department) : ''
			this.loadDepartments()
		},
		methods: {
			findDepartmentMatch(value) {
				if (!value) {
					return ''
				}
				const normalizedValue = value.replace(/[\s\/、]+/g, '/').trim()
				const parts = normalizedValue.split('/').filter(Boolean)
				for (const part of parts) {
					const exactMatch = this.departments.find((item) => item === part.trim())
					if (exactMatch) {
						return exactMatch
					}
				}
				for (const part of parts) {
					const partialMatch = this.departments.find((item) => item.includes(part.trim()) || part.trim().includes(item))
					if (partialMatch) {
						return partialMatch
					}
				}
				return this.departments[0] || ''
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
						const matched = this.findDepartmentMatch(this.pendingDepartment)
						this.selectedDepartment = matched || this.departments[0] || ''
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
				const doctor = this.doctors.find((item) => item.id === this.selectedDoctorId)
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
	.register-page {
		position: relative;
		min-height: 100vh;
		padding: 0 20rpx calc(180rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.register-page__orb {
		position: absolute;
		border-radius: 38rpx;
		background: rgba(132, 214, 13, 0.1);
		filter: blur(10rpx);
	}

	.register-page__orb--top {
		top: 120rpx;
		right: -84rpx;
		width: 240rpx;
		height: 240rpx;
	}

	.register-page__orb--bottom {
		left: -90rpx;
		bottom: 180rpx;
		width: 220rpx;
		height: 220rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.register-hero,
	.mode-list,
	.direct-section {
		position: relative;
		z-index: 1;
	}

	.register-hero {
		margin: 0 -20rpx;
		padding: calc(76rpx + env(safe-area-inset-top)) 30rpx 34rpx;
		overflow: hidden;
		border-radius: 0 0 56rpx 56rpx;
		background: linear-gradient(180deg, #31473a 0%, #3b5644 58%, #415e49 100%);
		box-shadow: $cm-shadow-lg;
	}

	.register-hero__eyebrow,
	.register-hero__title,
	.register-hero__hint,
	.mode-card__badge-text,
	.mode-card__title,
	.mode-card__desc {
		display: block;
	}

	.register-hero__eyebrow {
		margin-bottom: 10rpx;
		font-size: 22rpx;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.72);
	}

	.register-hero__title {
		font-size: 42rpx;
		font-weight: 700;
		line-height: 1.2;
		color: #ffffff;
	}

	.register-hero__hint {
		margin-top: 14rpx;
		font-size: 24rpx;
		line-height: 1.65;
		color: rgba(255, 255, 255, 0.82);
	}

	.mode-list {
		margin-top: 24rpx;
	}

	.mode-card {
		width: 100%;
		padding: 28rpx;
		border: 0;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
		text-align: left;
	}

	.mode-card::after {
		border: 0;
	}

	.mode-card__badge {
		display: inline-flex;
		align-items: center;
		padding: 7rpx 18rpx;
		border-radius: 28rpx;
		background: rgba(132, 214, 13, 0.12);
	}

	.mode-card__badge-icon {
		width: 24rpx;
		height: 24rpx;
	}

	.mode-card__badge-text {
		margin-left: 10rpx;
		font-size: 20rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.mode-card__copy {
		margin-top: 18rpx;
	}

	.mode-card__title {
		margin-top: 12rpx;
		font-size: 34rpx;
		font-weight: 700;
		line-height: 1.35;
		color: $cm-text-title;
	}

	.mode-card__desc {
		margin-top: 12rpx;
		font-size: 23rpx;
		line-height: 1.65;
		color: $cm-text-secondary;
	}

	.mode-card__footer {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		margin-top: 22rpx;
	}

	.mode-card__arrow {
		font-size: 24rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.direct-section {
		margin-top: 24rpx;
	}

	.filter-card,
	.time-card {
		padding: 24rpx;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
	}

	.filter-card__title,
	.time-card__title,
	.select-row__value,
	.time-select__label,
	.time-select__value,
	.doctor-card__name,
	.doctor-card__meta,
	.doctor-card__desc {
		display: block;
	}

	.filter-card__title,
	.time-card__title {
		font-size: 30rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.time-card {
		margin-top: 22rpx;
	}

	.select-picker {
		display: block;
	}

	.select-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 86rpx;
		margin-top: 18rpx;
		padding: 0 22rpx;
		border-radius: 24rpx;
		background: #f7faf3;
	}

	.select-row__value {
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.select-row__arrow {
		width: 16rpx;
		height: 16rpx;
		border-right: 4rpx solid $cm-text-secondary;
		border-bottom: 4rpx solid $cm-text-secondary;
		transform: rotate(45deg);
	}

	.time-grid {
		display: flex;
		margin-top: 18rpx;
	}

	.time-picker {
		flex: 1;
		min-width: 0;
	}

	.time-picker + .time-picker {
		margin-left: 14rpx;
	}

	.time-select {
		padding: 18rpx 20rpx;
		border-radius: 24rpx;
		background: #f7faf3;
	}

	.time-select__label {
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.time-select__value {
		margin-top: 10rpx;
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.doctor-list {
		margin-top: 22rpx;
	}

	.doctor-card {
		position: relative;
		width: 100%;
		padding: 24rpx;
		border: 2rpx solid transparent;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
		text-align: left;
		transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
	}

	.doctor-card::after {
		border: 0;
	}

	.doctor-card + .doctor-card {
		margin-top: 16rpx;
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
		gap: 12rpx;
	}

	.doctor-card__name {
		font-size: 30rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.doctor-card__meta {
		margin-top: 8rpx;
		font-size: 22rpx;
		color: $cm-text-secondary;
	}

	.doctor-card__state {
		height: 42rpx;
		padding: 0 16rpx;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.14);
		font-size: 20rpx;
		line-height: 42rpx;
		color: $cm-color-brand-deep;
	}

	.doctor-card__selected {
		display: flex;
		align-items: center;
		padding: 5rpx 12rpx 5rpx 6rpx;
		border-radius: 999rpx;
		background: $cm-color-brand;
		font-size: 20rpx;
		font-weight: 700;
		line-height: 30rpx;
		color: #ffffff;
	}

	.doctor-card__check {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 30rpx;
		height: 30rpx;
		margin-right: 6rpx;
		border-radius: 50%;
		background: #ffffff;
		font-size: 20rpx;
		font-weight: 700;
		line-height: 1;
		color: $cm-color-brand-deep;
	}

	.doctor-card__desc {
		margin-top: 14rpx;
		font-size: 23rpx;
		line-height: 1.65;
		color: $cm-text-secondary;
	}

	.primary-btn {
		position: fixed;
		left: 20rpx;
		right: 20rpx;
		bottom: calc(28rpx + env(safe-area-inset-bottom) + 120rpx);
		z-index: 20;
		width: auto;
		height: 98rpx;
		margin-top: 0;
		border: 0;
		border-radius: $cm-radius-pill;
		background: $cm-color-brand;
		box-shadow: 0 18rpx 38rpx rgba(91, 149, 24, 0.22);
		font-size: 30rpx;
		font-weight: 700;
		line-height: 98rpx;
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
