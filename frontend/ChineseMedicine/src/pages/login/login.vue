<template>
	<view class="auth-page">
		<view class="auth-decor auth-decor--top"></view>
		<view class="auth-decor auth-decor--bottom"></view>

		<view class="auth-shell">
			<view class="hero-panel">
				<view class="hero-panel__inner">
					<view class="brand-icon">
						<image class="brand-icon__image" src="/static/logo.png" mode="aspectFit"></image>
					</view>
					<text class="brand-name">{{ brandName }}</text>
				</view>
			</view>

			<view class="copy-block">
				<text class="copy-block__title">欢迎登录</text>
				<text class="copy-block__desc">继续查看你的问诊建议、体质记录与恢复提醒。</text>
			</view>

			<view class="form-stack">
				<view class="field-block">
					<text class="field-label">用户名</text>
					<view class="field-control">
						<view class="field-icon field-icon--user">
							<image class="field-icon__image" src="/static/img/people.svg" mode="aspectFit"></image>
						</view>
						<input
							v-model.trim="username"
							class="field-input"
							type="text"
							placeholder="输入你的用户名..."
							placeholder-class="field-placeholder"
						/>
					</view>
				</view>

				<view class="field-block">
					<text class="field-label">密码</text>
					<view class="field-control" :class="{ 'field-control--error': passwordError }">
						<view class="field-icon field-icon--lock">
							<view class="lock-icon">
								<view class="lock-icon__arch"></view>
								<view class="lock-icon__body"></view>
								<view class="lock-icon__dot"></view>
							</view>
						</view>
						<input
							v-model.trim="password"
							class="field-input"
							password
							type="text"
							@blur="handlePasswordBlur"
							placeholder="请输入密码"
							placeholder-class="field-placeholder"
						/>
					</view>
					<view class="field-link-row">
						<text class="field-link" @tap="goForgotPassword">忘记密码</text>
					</view>
				</view>

				<view v-if="passwordError" class="error-banner">
					<view class="error-banner__icon">
						<view class="error-banner__dot"></view>
					</view>
					<text class="error-banner__text">{{ passwordErrorText }}</text>
				</view>

				<button class="primary-btn" :disabled="loading" @tap="handleLogin">
					<text class="primary-btn__text">{{ loading ? '登录中...' : '登 录' }}</text>
					<text class="primary-btn__arrow">→</text>
				</button>

				<view class="meta-row">
					<text class="meta-row__text">还没有账户？</text>
					<text class="meta-row__link" @tap="handleRegister">免费注册</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { login as apiLogin } from '../../api'
	import { setToken, setPatientId } from '../../config/http'
	import { saveCurrentUserProfile } from '../../config/user-profile'

	export default {
		data() {
			return {
				brandName: '本草问方',
				username: '',
				password: '',
				passwordError: false,
				passwordErrorText: '错误：密码无效！',
				loading: false
			}
		},
		methods: {
			validateUsername() {
				const valid = this.username.length >= 2
				if (!valid) {
					uni.showToast({
						title: '请输入有效用户名',
						icon: 'none'
					})
				}
				return valid
			},
			validatePassword(showToast = true) {
				const valid = this.password.length >= 8
				this.passwordError = !valid
				if (!valid && showToast) {
					uni.showToast({
						title: '密码至少需要 8 位',
						icon: 'none'
					})
				}
				return valid
			},
			handlePasswordBlur() {
				if (!this.password) {
					this.passwordError = false
					return
				}
				this.validatePassword(false)
			},
			handleLogin() {
				const usernameOk = this.validateUsername()
				const passwordOk = this.validatePassword()
				if (!usernameOk || !passwordOk) {
					return
				}
				if (this.loading) {
					return
				}
				this.loading = true
				this.passwordError = false
				apiLogin({
					username: this.username,
					password: this.password
				})
					.then((data) => {
						setToken(data.token)
						setPatientId(data.patient_id)
						saveCurrentUserProfile({ name: data.name })
						uni.reLaunch({
							url: '/pages/main/main'
						})
					})
					.catch((error) => {
						uni.showToast({
							title: error && error.statusCode === 0 ? '网络异常，请稍后重试' : '用户名或者密码错误',
							icon: 'none'
						})
					})
					.finally(() => {
						this.loading = false
					})
			},
			handleRegister() {
				uni.navigateTo({
					url: '/pages/login/register'
				})
			},
			goForgotPassword() {
				uni.navigateTo({
					url: '/pages/login/forgot'
				})
			}
		},
		watch: {
			password(value) {
				if (!value) {
					this.passwordError = false
				} else if (this.passwordError) {
					this.passwordError = value.length < 8
				}
			}
		}
	}
</script>

<style lang="scss">
	.auth-page {
		position: relative;
		min-height: 100vh;
		padding: env(safe-area-inset-top) 26rpx calc(40rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.auth-decor {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.auth-decor--top {
		top: 108rpx;
		right: -90rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.auth-decor--bottom {
		left: -80rpx;
		bottom: 110rpx;
		width: 180rpx;
		height: 180rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.auth-shell {
		position: relative;
		z-index: 1;
	}

	.hero-panel {
		height: 280rpx;
		margin: 0 -26rpx;
		border-radius: 0 0 70rpx 70rpx;
		background: linear-gradient(180deg, #ffffff 0%, #fbfbf9 100%);
		box-shadow: $cm-shadow-sm;
	}

	.hero-panel__inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
	}

	.brand-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 148rpx;
		height: 148rpx;
		border-radius: 40rpx;
		background: rgba(132, 214, 13, 0.1);
		overflow: hidden;
	}

	.brand-icon__image {
		width: 96rpx;
		height: 96rpx;
		border-radius: 28rpx;
		overflow: hidden;
	}

	.brand-name {
		max-width: 100%;
		padding: 0 24rpx;
		margin-top: 14rpx;
		font-size: 24rpx;
		font-weight: 600;
		line-height: 1.5;
		letter-spacing: 2rpx;
		text-align: center;
		word-break: break-all;
		color: $cm-color-brand-deep;
	}

	.copy-block {
		padding: 44rpx 18rpx 0;
	}

	.copy-block__title,
	.copy-block__desc,
	.field-label,
	.error-banner__text,
	.meta-row__text,
	.meta-row__link {
		display: block;
	}

	.copy-block__title {
		font-size: 60rpx;
		font-weight: 700;
		line-height: 1.2;
		color: $cm-text-title;
	}

	.copy-block__desc {
		margin-top: 14rpx;
		font-size: 28rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.form-stack {
		padding: 34rpx 0 0;
	}

	.field-block + .field-block {
		margin-top: 30rpx;
	}

	.field-label {
		padding: 0 14rpx;
		font-size: 26rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.field-link {
		font-size: 24rpx;
		font-weight: 600;
		color: $cm-color-brand-deep;
	}

	.field-link-row {
		display: flex;
		justify-content: flex-end;
		margin-top: 14rpx;
		padding: 0 14rpx;
	}

	.field-control {
		display: flex;
		align-items: center;
		margin-top: 16rpx;
		padding: 0 18rpx;
		min-height: 100rpx;
		border: 3rpx solid transparent;
		border-radius: 30rpx;
		background: #ffffff;
		box-shadow: $cm-shadow-sm;
	}

	.field-control--error {
		border-color: rgba(232, 108, 118, 0.45);
		box-shadow: 0 6px 18px rgba(232, 108, 118, 0.14);
	}

	.field-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 56rpx;
		height: 56rpx;
		margin-right: 12rpx;
		border-radius: 20rpx;
		background: #f4f5f0;
	}

	.field-icon--mail,
	.field-icon--user,
	.field-icon--lock {
		flex-shrink: 0;
	}

	.field-icon__image {
		width: 28rpx;
		height: 28rpx;
	}

	.lock-icon {
		position: relative;
		width: 26rpx;
		height: 28rpx;
	}

	.lock-icon__arch {
		position: absolute;
		left: 5rpx;
		top: 0;
		width: 16rpx;
		height: 12rpx;
		border: 3rpx solid #5f6b64;
		border-bottom: 0;
		border-radius: 14rpx 14rpx 0 0;
	}

	.lock-icon__body {
		position: absolute;
		left: 1rpx;
		right: 1rpx;
		bottom: 0;
		height: 18rpx;
		border-radius: 8rpx;
		background: #5f6b64;
	}

	.lock-icon__dot {
		position: absolute;
		left: 50%;
		top: 14rpx;
		width: 6rpx;
		height: 6rpx;
		margin-left: -3rpx;
		border-radius: 50%;
		background: #ffffff;
	}

	.field-input {
		flex: 1;
		height: 100rpx;
		font-size: 28rpx;
		color: $cm-text-body;
	}

	.field-placeholder {
		font-size: 28rpx;
		color: #97a09b;
	}

	.field-input::-ms-reveal,
	.field-input::-ms-clear,
	.field-input::-webkit-credentials-auto-fill-button,
	.field-input::-webkit-contacts-auto-fill-button {
		display: none;
		visibility: hidden;
		pointer-events: none;
	}

	.error-banner {
		display: flex;
		align-items: center;
		min-height: 54rpx;
		margin-top: 20rpx;
		padding: 0 22rpx;
		border: 2rpx solid rgba(232, 108, 118, 0.38);
		border-radius: 18rpx;
		background: rgba(247, 231, 234, 0.72);
	}

	.error-banner__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28rpx;
		height: 28rpx;
		margin-right: 12rpx;
		border-radius: 50%;
		background: $cm-error;
	}

	.error-banner__dot {
		width: 8rpx;
		height: 8rpx;
		border-radius: 50%;
		background: #ffffff;
	}

	.error-banner__text {
		font-size: 24rpx;
		font-weight: 600;
		color: #d84e5e;
	}

	.primary-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-height: 98rpx;
		margin-top: 38rpx;
		border-radius: $cm-radius-pill;
		background: $cm-color-brand;
		box-shadow: 0 10px 22px rgba(132, 214, 13, 0.22);
	}

	.primary-btn__text,
	.primary-btn__arrow {
		color: #ffffff;
		font-size: 30rpx;
		font-weight: 700;
	}

	.primary-btn__arrow {
		margin-left: 16rpx;
	}

	.meta-row {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 54rpx;
	}

	.meta-row__text,
	.meta-row__link {
		font-size: 24rpx;
	}

	.meta-row__text {
		color: $cm-text-body;
	}

	.meta-row__link {
		margin-left: 10rpx;
		font-weight: 700;
		color: $cm-color-brand;
	}
</style>
