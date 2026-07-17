<template>
	<view class="profile-page">
		<view class="profile-page__orb profile-page__orb--top"></view>
		<view class="profile-page__orb profile-page__orb--bottom"></view>

		<view class="profile-shell">
			<button class="back-btn" @tap="goBack">
				<view class="back-btn__arrow"></view>
			</button>

			<view class="title-block">
				<text class="title-block__title">个人信息</text>
				<text class="title-block__desc">完善基础资料，便于后续问诊推荐更贴合你的状态。</text>
			</view>

			<view class="form-card">
				<view class="field-block field-block--avatar">
					<text class="field-label">更换头像</text>
					<text class="field-helper">点击下方头像即可切换。</text>
					<view class="avatar-preview">
						<image class="avatar-preview__image" :src="form.avatar" mode="aspectFill"></image>
						<view class="avatar-preview__copy">
							<text class="avatar-preview__title">当前头像</text>
						</view>
					</view>
					<text class="avatar-grid__title">可选头像</text>
					<view class="avatar-grid">
						<button
							v-for="item in avatars"
							:key="item"
							class="avatar-option"
							:class="{ 'avatar-option--active': form.avatar === item }"
							@tap="selectAvatar(item)"
						>
							<image class="avatar-option__image" :src="item" mode="aspectFill"></image>
						</button>
					</view>
				</view>

				<view class="field-block">
					<text class="field-label">姓名</text>
					<input
						v-model.trim="form.name"
						class="field-input"
						type="text"
						placeholder="请输入姓名"
						placeholder-class="field-placeholder"
					/>
				</view>

				<view class="field-block">
					<text class="field-label">性别</text>
					<view class="choice-row">
						<button
							v-for="item in genders"
							:key="item"
							class="choice-pill"
							:class="{ 'choice-pill--active': form.gender === item }"
							@tap="form.gender = item"
						>
							{{ item }}
						</button>
					</view>
				</view>

				<view class="field-block">
					<text class="field-label">出生日期</text>
					<picker mode="date" :value="form.birth" start="1900-01-01" :end="maxBirthDate" @change="handleBirthChange">
						<view class="field-picker">
							<text :class="['field-picker__text', { 'field-picker__text--placeholder': !form.birth }]">
								{{ form.birth || '请选择出生日期' }}
							</text>
							<text class="field-picker__arrow">></text>
						</view>
					</picker>
					<text class="field-helper">生日使用日期滚轮选择，年龄会根据生日自动更新。</text>
				</view>

				<view class="field-block">
					<text class="field-label">年龄</text>
					<view class="field-display">
						<text :class="['field-display__text', { 'field-display__text--placeholder': !form.age }]">
							{{ ageLabel }}
						</text>
					</view>
				</view>

				<view class="field-block">
					<text class="field-label">手机号</text>
					<input
						v-model.trim="form.phone"
						class="field-input"
						type="number"
						placeholder="请输入手机号"
						placeholder-class="field-placeholder"
					/>
				</view>

				<view class="field-block">
					<text class="field-label">过敏史</text>
					<input
						v-model.trim="form.allergyHistory"
						class="field-input"
						type="text"
						placeholder="例如 麻黄、桂枝 / 无"
						placeholder-class="field-placeholder"
					/>
				</view>

				<view class="field-block">
					<text class="field-label">新密码</text>
					<input
						v-model="form.password"
						class="field-input"
						:class="{ 'field-input--error': passwordMismatch }"
						type="password"
						placeholder="不修改请留空"
						placeholder-class="field-placeholder"
					/>
				</view>

				<view class="field-block">
					<text class="field-label">确认新密码</text>
					<input
						v-model="form.confirmPassword"
						class="field-input"
						:class="{ 'field-input--error': passwordMismatch }"
						type="password"
						placeholder="不修改请留空"
						placeholder-class="field-placeholder"
					/>
					<text v-if="passwordMismatch" class="field-helper field-helper--error">确认密码和新密码不匹配</text>
				</view>
			</view>

			<button class="save-btn" :class="{ 'save-btn--disabled': loading }" :disabled="loading" @tap="handleSave">
				<text class="save-btn__text">{{ loading ? '保存中...' : '保存设置' }}</text>
				<text class="save-btn__arrow">></text>
			</button>
		</view>
	</view>
</template>

<script>
	import {
		avatarOptions,
		defaultUserProfile,
		getCurrentUserProfile,
		saveCurrentUserProfile
	} from '../../config/user-profile'
	import { getProfile, updateProfile } from '../../api'

	function padDatePart(value) {
		return String(value).padStart(2, '0')
	}

	function formatPickerDate(date = new Date()) {
		return `${date.getFullYear()}-${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}`
	}

	function calculateAgeFromBirth(birth) {
		if (!/^\d{4}-\d{2}-\d{2}$/.test(birth || '')) {
			return ''
		}

		const [year, month, day] = birth.split('-').map(Number)
		const birthDate = new Date(year, month - 1, day)
		if (
			birthDate.getFullYear() !== year ||
			birthDate.getMonth() !== month - 1 ||
			birthDate.getDate() !== day
		) {
			return ''
		}

		const today = new Date()
		let age = today.getFullYear() - year
		const monthDiff = today.getMonth() - (month - 1)
		const dayDiff = today.getDate() - day

		if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
			age -= 1
		}

		return age >= 0 ? String(age) : ''
	}

	function buildProfileForm(profile = {}) {
		const nextForm = {
			...defaultUserProfile,
			...profile
		}
		const derivedAge = calculateAgeFromBirth(nextForm.birth)

		return {
			...nextForm,
			birth: nextForm.birth || '',
			age: derivedAge || `${nextForm.age || ''}`.trim()
		}
	}

	export default {
		data() {
			return {
				avatars: avatarOptions,
				genders: ['女', '男'],
				maxBirthDate: formatPickerDate(),
				form: buildProfileForm({
					...defaultUserProfile,
					password: '',
					confirmPassword: ''
				}),
				loading: false
			}
		},
		computed: {
			ageLabel() {
				return this.form.age ? `${this.form.age} 岁` : '根据生日自动计算'
			},
			passwordMismatch() {
				return Boolean(
					this.form.confirmPassword && this.form.password !== this.form.confirmPassword
				)
			}
		},
		onShow() {
			this.syncProfile()
		},
		methods: {
			syncProfile() {
				this.loading = true
				getProfile()
					.then((mapped) => {
						const localProfile = getCurrentUserProfile()
						this.form = buildProfileForm({
							...mapped,
							avatar: localProfile.avatar,
							password: '',
							confirmPassword: ''
						})
					})
					.catch(() => {
						this.form = buildProfileForm({
							...getCurrentUserProfile(),
							password: '',
							confirmPassword: ''
						})
					})
					.finally(() => {
						this.loading = false
					})
			},
			handleBirthChange(event) {
				const birth = event && event.detail ? event.detail.value : ''
				this.form.birth = birth
				this.form.age = calculateAgeFromBirth(birth)
			},
			selectAvatar(avatar) {
				this.form.avatar = avatar
			},
			goBack() {
				uni.navigateBack({
					fail: () => {
						uni.redirectTo({
							url: '/pages/user/setting'
						})
					}
				})
			},
			handleSave() {
				if (this.loading) {
					return
				}

				if (!this.form.name || !this.form.name.trim()) {
					uni.showToast({
						title: '请先填写姓名',
						icon: 'none'
					})
					return
				}

				if (!this.form.birth) {
					uni.showToast({
						title: '请选择出生日期',
						icon: 'none'
					})
					return
				}

				if (this.form.password || this.form.confirmPassword) {
					if (!this.form.password) {
						uni.showToast({
							title: '请输入新密码',
							icon: 'none'
						})
						return
					}
					if (!this.form.confirmPassword) {
						uni.showToast({
							title: '请输入确认新密码',
							icon: 'none'
						})
						return
					}
					if (this.passwordMismatch) {
						uni.showToast({
							title: '确认密码和新密码不匹配',
							icon: 'none'
						})
						return
					}
				}

				const profileToSave = {
					...this.form,
					name: this.form.name.trim(),
					password: this.form.password || undefined,
					confirmPassword: undefined
				}

				this.loading = true
				updateProfile(profileToSave)
					.then(() => {
						const { password, confirmPassword, ...savedProfile } = profileToSave
						this.form = buildProfileForm({
							...savedProfile,
							password: '',
							confirmPassword: ''
						})
						saveCurrentUserProfile(savedProfile)
						uni.showToast({
							title: '个人信息已保存',
							icon: 'none'
						})
						setTimeout(() => {
							this.goBack()
						}, 450)
					})
					.catch(() => {
						// 错误提示已由请求层统一处理
					})
					.finally(() => {
						this.loading = false
					})
			}
		}
	}
</script>

<style lang="scss">
	.profile-page {
		position: relative;
		min-height: 100vh;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx calc(40rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.profile-page__orb {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.profile-page__orb--top {
		top: 138rpx;
		right: -90rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.profile-page__orb--bottom {
		left: -86rpx;
		bottom: 150rpx;
		width: 192rpx;
		height: 192rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.profile-shell {
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
	.field-label,
	.field-helper,
	.avatar-preview__title,
	.avatar-grid__title,
	.save-btn__text,
	.save-btn__arrow,
	.field-picker__text,
	.field-picker__arrow,
	.field-display__text {
		display: block;
	}

	.title-block__title {
		font-size: 60rpx;
		font-weight: 700;
		line-height: 1.2;
		color: $cm-text-title;
	}

	.title-block__desc {
		margin-top: 14rpx;
		font-size: 28rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.form-card {
		margin-top: 34rpx;
		padding: 10rpx 24rpx;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
	}

	.field-block {
		padding: 22rpx 0 26rpx;
	}

	.field-block--avatar {
		padding-top: 26rpx;
	}

	.field-block + .field-block {
		border-top: 2rpx solid $cm-border;
	}

	.field-label {
		font-size: 26rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.field-helper {
		margin-top: 10rpx;
		font-size: 22rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.avatar-preview {
		display: flex;
		align-items: center;
		margin-top: 18rpx;
		padding: 20rpx 22rpx;
		border-radius: 28rpx;
		background: #f6f8f2;
	}

	.avatar-preview__image {
		width: 108rpx;
		height: 108rpx;
		border-radius: 32rpx;
	}

	.avatar-preview__copy {
		flex: 1;
		margin-left: 18rpx;
	}

	.avatar-preview__title {
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.avatar-grid {
		display: flex;
		margin-top: 18rpx;
	}

	.avatar-grid__title {
		margin-top: 18rpx;
		font-size: 24rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.avatar-option {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 120rpx;
		height: 120rpx;
		padding: 6rpx;
		border: 0;
		border-radius: 34rpx;
		background: #f2f4ee;
	}

	.avatar-option::after {
		border: 0;
	}

	.avatar-option + .avatar-option {
		margin-left: 18rpx;
	}

	.avatar-option--active {
		background: rgba(132, 214, 13, 0.16);
		box-shadow: inset 0 0 0 3rpx rgba(132, 214, 13, 0.52);
	}

	.avatar-option__image {
		width: 100%;
		height: 100%;
		border-radius: 28rpx;
	}

	.field-input,
	.field-picker,
	.field-display {
		display: flex;
		align-items: center;
		width: 100%;
		min-height: 88rpx;
		margin-top: 14rpx;
		padding: 0 22rpx;
		border-radius: 24rpx;
		background: #f6f8f2;
		box-sizing: border-box;
	}

	.field-input {
	font-size: 28rpx;
	color: $cm-text-body;
}

.field-input--error {
	box-shadow: inset 0 0 0 2rpx #c1574f;
	background: #fcf3f3;
}

.field-helper--error {
	color: #c1574f;
	font-weight: 600;
}

	.field-placeholder {
		font-size: 28rpx;
		color: $cm-text-placeholder;
	}

	.field-picker,
	.field-display {
		justify-content: space-between;
	}

	.field-picker__text,
	.field-display__text {
		font-size: 28rpx;
		color: $cm-text-body;
	}

	.field-picker__text--placeholder,
	.field-display__text--placeholder,
	.field-picker__arrow {
		color: $cm-text-placeholder;
	}

	.choice-row {
		display: flex;
		margin-top: 16rpx;
	}

	.choice-pill {
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 140rpx;
		height: 76rpx;
		padding: 0 26rpx;
		border: 0;
		border-radius: 999rpx;
		background: #f2f4ee;
		font-size: 26rpx;
		font-weight: 600;
		line-height: 1.2;
		color: $cm-text-secondary;
	}

	.choice-pill::after {
		border: 0;
	}

	.choice-pill + .choice-pill {
		margin-left: 16rpx;
	}

	.choice-pill--active {
		background: rgba(132, 214, 13, 0.16);
		color: $cm-color-brand-deep;
	}

	.save-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-height: 98rpx;
		margin-top: 40rpx;
		border: 0;
		border-radius: $cm-radius-pill;
		background: $cm-color-brand;
		box-shadow: 0 10px 22px rgba(132, 214, 13, 0.22);
	}

	.save-btn::after {
		border: 0;
	}

	.save-btn--disabled {
		opacity: 0.72;
	}

	.save-btn__text,
	.save-btn__arrow {
		font-size: 30rpx;
		font-weight: 700;
		color: #ffffff;
	}

	.save-btn__arrow {
		margin-left: 16rpx;
	}
</style>
