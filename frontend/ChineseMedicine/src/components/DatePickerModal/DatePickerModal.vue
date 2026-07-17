<template>
	<view v-if="visible" class="date-picker-modal">
		<view class="date-picker-modal__mask" @tap="handleClose"></view>
		<view class="date-picker-modal__content">
			<view class="date-picker-modal__header">
				<text class="date-picker-modal__title">选择预约日期</text>
				<view class="date-picker-modal__close" @tap="handleClose">
					<text class="date-picker-modal__close-icon">×</text>
				</view>
			</view>
			<view class="date-picker-modal__body">
				<view class="date-picker-modal__weeks">
					<text class="date-picker-modal__week" v-for="week in weeks" :key="week">{{ week }}</text>
				</view>
				<view class="date-picker-modal__days">
					<view
						v-for="day in days"
						:key="day.value"
						class="date-picker-modal__day"
						:class="{
							'date-picker-modal__day--today': day.isToday,
							'date-picker-modal__day--selected': day.value === selectedValue,
							'date-picker-modal__day--disabled': day.disabled
						}"
						@tap="handleSelect(day)"
					>
						<text class="date-picker-modal__day-num">{{ day.day }}</text>
						<text v-if="day.isToday" class="date-picker-modal__day-tag">今</text>
					</view>
				</view>
			</view>
			<view class="date-picker-modal__footer">
				<button class="date-picker-modal__confirm" @tap="handleConfirm">确认</button>
			</view>
		</view>
	</view>
</template>

<script>
	const weeks = ['日', '一', '二', '三', '四', '五', '六']

	export default {
		name: 'DatePickerModal',
		props: {
			visible: {
				type: Boolean,
				default: false
			},
			selectedValue: {
				type: String,
				default: ''
			},
			startDate: {
				type: String,
				default: ''
			},
			endDate: {
				type: String,
				default: ''
			}
		},
		data() {
			return {
				weeks,
				days: [],
				tempSelected: ''
			}
		},
		watch: {
			visible(newVal) {
				if (newVal) {
					this.initDays()
					this.tempSelected = this.selectedValue
				}
			},
			selectedValue(newVal) {
				this.tempSelected = newVal
			}
		},
		methods: {
			initDays() {
				const days = []
				const today = new Date()
				const start = this.startDate ? new Date(this.startDate) : today
				const end = this.endDate ? new Date(this.endDate) : new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000)

				const startYear = start.getFullYear()
				const startMonth = start.getMonth()
				const startDay = start.getDate()

				const endYear = end.getFullYear()
				const endMonth = end.getMonth()
				const endDay = end.getDate()

				const todayStr = this.formatDate(today)

				let current = new Date(startYear, startMonth, startDay)
				while (
					current.getFullYear() < endYear ||
					(current.getFullYear() === endYear && current.getMonth() < endMonth) ||
					(current.getFullYear() === endYear && current.getMonth() === endMonth && current.getDate() <= endDay)
				) {
					const year = current.getFullYear()
					const month = current.getMonth()
					const day = current.getDate()
					const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`

					days.push({
						value: dateStr,
						year,
						month: month + 1,
						day,
						week: current.getDay(),
						isToday: dateStr === todayStr,
						disabled: false
					})

					current.setDate(current.getDate() + 1)
				}

				const firstWeek = days[0]?.week || 0
				for (let i = 0; i < firstWeek; i++) {
					days.unshift({ value: '', disabled: true })
				}

				this.days = days
			},
			formatDate(date) {
				const year = date.getFullYear()
				const month = String(date.getMonth() + 1).padStart(2, '0')
				const day = String(date.getDate()).padStart(2, '0')
				return `${year}-${month}-${day}`
			},
			handleSelect(day) {
				if (day.disabled) return
				this.tempSelected = day.value
			},
			handleConfirm() {
				if (this.tempSelected) {
					this.$emit('confirm', this.tempSelected)
				}
			},
			handleClose() {
				this.$emit('close')
			}
		}
	}
</script>

<style lang="scss" scoped>
	.date-picker-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 9999;
		display: flex;
		align-items: flex-end;
		justify-content: center;
	}

	.date-picker-modal__mask {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
	}

	.date-picker-modal__content {
		position: relative;
		width: 100%;
		border-radius: 32rpx 32rpx 0 0;
		background: #ffffff;
		transform: translateY(0);
		animation: slideUp 0.3s ease;
	}

	@keyframes slideUp {
		from {
			transform: translateY(100%);
		}
		to {
			transform: translateY(0);
		}
	}

	.date-picker-modal__header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 32rpx 36rpx;
		border-bottom: 1rpx solid #f0f0f0;
	}

	.date-picker-modal__title {
		font-size: 34rpx;
		font-weight: 700;
		color: #333333;
	}

	.date-picker-modal__close {
		width: 64rpx;
		height: 64rpx;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.date-picker-modal__close-icon {
		font-size: 48rpx;
		color: #999999;
		line-height: 1;
	}

	.date-picker-modal__body {
		padding: 24rpx 36rpx;
		max-height: 60vh;
		overflow-y: auto;
	}

	.date-picker-modal__weeks {
		display: flex;
		margin-bottom: 16rpx;
	}

	.date-picker-modal__week {
		flex: 1;
		text-align: center;
		font-size: 24rpx;
		color: #999999;
		line-height: 48rpx;
	}

	.date-picker-modal__days {
		display: flex;
		flex-wrap: wrap;
	}

	.date-picker-modal__day {
		width: calc(100% / 7);
		height: 80rpx;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border-radius: 12rpx;
		position: relative;
		box-sizing: border-box;
	}

	.date-picker-modal__day--disabled {
		visibility: hidden;
	}

	.date-picker-modal__day-num {
		font-size: 28rpx;
		color: #333333;
		line-height: 1;
	}

	.date-picker-modal__day--selected {
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
	}

	.date-picker-modal__day--selected .date-picker-modal__day-num {
		color: #ffffff;
		font-weight: 700;
	}

	.date-picker-modal__day--today:not(.date-picker-modal__day--selected) {
		background: #f3f7ec;
	}

	.date-picker-modal__day--today:not(.date-picker-modal__day--selected) .date-picker-modal__day-num {
		color: #6fbf2a;
		font-weight: 700;
	}

	.date-picker-modal__day-tag {
		position: absolute;
		bottom: 4rpx;
		font-size: 16rpx;
		color: #6fbf2a;
	}

	.date-picker-modal__day--selected .date-picker-modal__day-tag {
		color: #ffffff;
	}

	.date-picker-modal__footer {
		padding: 24rpx 36rpx calc(24rpx + env(safe-area-inset-bottom));
		border-top: 1rpx solid #f0f0f0;
	}

	.date-picker-modal__confirm {
		width: 100%;
		height: 96rpx;
		border-radius: 48rpx;
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
		font-size: 32rpx;
		font-weight: 700;
		color: #ffffff;
		border: none;
		line-height: 96rpx;
	}

	.date-picker-modal__confirm::after {
		border: none;
	}
</style>
