<template>
	<view class="direct-page">
		<view class="direct-page__orb direct-page__orb--top"></view>
		<view class="direct-page__orb direct-page__orb--bottom"></view>

		<view class="register-hero">
			<text class="register-hero__eyebrow">挂号中心</text>
			<text class="register-hero__title">选择科室与医生</text>
			<text class="register-hero__hint">如果暂时拿不准该挂哪个科室，可先使用智能挂号获得推荐；如果你已经知道目标科室，可以直接选择。</text>
		</view>

		<view class="direct-shell">
			<button class="smart-entry" @tap="goSmartRegister">
				<image class="smart-entry__icon" src="/static/design-assets/icons/lucide/messages-square.svg" mode="aspectFit"></image>
				<text class="smart-entry__text">智能挂号：描述症状获取推荐科室</text>
				<view class="smart-entry__arrow"></view>
			</button>

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
					<view class="time-picker" @tap="showDatePicker">
						<view class="time-select">
							<text class="time-select__label">预约日期</text>
							<text class="time-select__value">{{ selectedDate }}</text>
						</view>
					</view>
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

		<DatePickerModal
			:visible="showDateModal"
			:selected-value="selectedDate"
			:start-date="todayDate"
			:end-date="endDate"
			@confirm="handleDateConfirm"
			@close="handleDateClose"
		/>
	</view>
</template>

<script>
	import { getDepartments, getDoctorSlots, createOrder, DEPARTMENT_OPTIONS } from '../../api'
	import DatePickerModal from '../../components/DatePickerModal/DatePickerModal.vue'

	const formatDate = (date) => {
			const year = date.getFullYear()
			const month = `${date.getMonth() + 1}`.padStart(2, '0')
			const day = `${date.getDate()}`.padStart(2, '0')
			return `${year}-${month}-${day}`
		}

		const getEndDate = () => {
			const date = new Date()
			date.setDate(date.getDate() + 30)
			return formatDate(date)
		}

		export default {
			components: {
				DatePickerModal
			},
			data() {
				const todayDate = formatDate(new Date())

				return {
					todayDate,
					endDate: getEndDate(),
					selectedDate: todayDate,
					selectedTime: '09:00',
					selectedDepartment: '',
					selectedDoctorId: '',
					doctors: [],
					availableSlots: [],
					loading: false,
					submitting: false,
					source: 'direct',
					pendingDepartment: '',
					showDateModal: false
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
			if (options.source === 'smart') {
				this.source = 'smart'
			}
			this.loadDepartments()
		},
		methods: {
			goBack() {
				uni.navigateBack({
					fail: () => {
						uni.reLaunch({
							url: '/pages/main/main'
						})
					}
				})
			},
			goSmartRegister() {
				uni.navigateTo({
					url: '/pages/register/smart'
				})
			},
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
						// 错误提示已由请求层统一 toast
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
			showDatePicker() {
				this.showDateModal = true
			},
			handleDateConfirm(date) {
				this.selectedDate = date
				this.fetchSlots()
				this.showDateModal = false
			},
			handleDateClose() {
				this.showDateModal = false
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
						// 后端 order/record 的 date 为创建时间戳且不含预约 time，
						// 故本地缓存本次选择的预约日期/时间，供历史列表与详情页正确展示
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
						// 错误提示已由请求层统一 toast
					})
					.finally(() => {
						this.submitting = false
					})
			}
		}
	}
</script>

<style lang="scss">
	.direct-page {
		position: relative;
		min-height: 100vh;
		padding: 0 26rpx calc(176rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.register-hero {
		position: relative;
		z-index: 1;
		margin: 0 -26rpx;
		padding: calc(76rpx + env(safe-area-inset-top)) 30rpx 34rpx;
		overflow: hidden;
		border-radius: 0 0 56rpx 56rpx;
		background: linear-gradient(180deg, #31473a 0%, #3b5644 58%, #415e49 100%);
		box-shadow: $cm-shadow-lg;
	}

	.register-hero__eyebrow,
	.register-hero__title,
	.register-hero__hint,
	.smart-entry__text {
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

	.smart-entry {
		position: relative;
		z-index: 1;
		display: flex;
		align-items: center;
		width: 100%;
		margin-top: 20rpx;
		padding: 24rpx 26rpx;
		border: 2rpx dashed rgba(132, 214, 13, 0.4);
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.9);
		box-shadow: $cm-shadow-sm;
		text-align: left;
	}

	.smart-entry::after {
		border: 0;
	}

	.smart-entry:active {
		background: #f4fbe9;
	}

	.smart-entry__icon {
		width: 48rpx;
		height: 48rpx;
		flex-shrink: 0;
	}

	.smart-entry__text {
		flex: 1;
		margin-left: 16rpx;
		font-size: 26rpx;
		font-weight: 600;
		line-height: 1.5;
		color: $cm-color-brand-deep;
	}

	.smart-entry__arrow {
		width: 16rpx;
		height: 16rpx;
		border-right: 4rpx solid $cm-color-brand-deep;
		border-bottom: 4rpx solid $cm-color-brand-deep;
		transform: rotate(-45deg);
		flex-shrink: 0;
	}

	.direct-page__orb {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.direct-page__orb--top {
		top: 120rpx;
		right: -92rpx;
		width: 230rpx;
		height: 230rpx;
	}

	.direct-page__orb--bottom {
		left: -84rpx;
		bottom: 140rpx;
		width: 190rpx;
		height: 190rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.direct-shell {
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

	.title-block__title {
		font-size: 60rpx;
		font-weight: 700;
		line-height: 1.2;
		color: $cm-text-title;
	}

	.filter-card,
	.time-card {
		margin-top: 34rpx;
		padding: 24rpx;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
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
	}

	.doctor-card__head {
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
		left: 26rpx;
		right: 26rpx;
		bottom: calc(28rpx + env(safe-area-inset-bottom));
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
