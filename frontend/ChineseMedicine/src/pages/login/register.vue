<template>
	<view class="register-page">
		<view class="register-decor register-decor--top"></view>
		<view class="register-decor register-decor--bottom"></view>

		<view class="register-shell">
			<button class="back-btn" @tap="goBack">
				<image class="back-btn__icon" src="/static/design-assets/icons/lucide/arrow-left.svg" mode="aspectFit"></image>
			</button>

			<view class="copy-block">
				<text class="copy-block__title">免费注册</text>
				<text class="copy-block__desc">创建你的账户，继续管理问诊建议、体质记录与恢复提醒。</text>
			</view>

			<view class="form-stack">
				<view class="field-block">
					<text class="field-label">用户名</text>
					<view class="field-control">
						<view class="field-icon">
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
					<view class="field-control">
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
							placeholder="请输入密码"
							placeholder-class="field-placeholder"
						/>
					</view>
				</view>

				<view class="field-block">
					<text class="field-label">确认密码</text>
					<view class="field-control">
						<view class="field-icon field-icon--lock">
							<view class="lock-icon">
								<view class="lock-icon__arch"></view>
								<view class="lock-icon__body"></view>
								<view class="lock-icon__dot"></view>
							</view>
						</view>
						<input
							v-model.trim="confirmPassword"
							class="field-input"
							password
							type="text"
							placeholder="再次输入密码"
							placeholder-class="field-placeholder"
						/>
					</view>
				</view>

				<button class="primary-btn" @tap="handleRegister">
					<text class="primary-btn__text">注 册</text>
					<text class="primary-btn__arrow">→</text>
				</button>

				<view class="meta-row">
					<text class="meta-row__text">已经有账户？</text>
					<text class="meta-row__link" @tap="goLogin">返回登录</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { register as apiRegister } from '../../api'

	export default {
		data() {
			return {
				username: '',
				password: '',
				confirmPassword: '',
				loading: false
			}
		},
		methods: {
			goBack() {
				uni.navigateBack({
					fail: () => {
						this.goLogin()
					}
				})
			},
			goLogin() {
				uni.redirectTo({
					url: '/pages/login/login'
				})
			},
			handleRegister() {
				if (this.username.length < 2) {
					uni.showToast({
						title: '请输入有效用户名',
						icon: 'none'
					})
					return
				}
				if (this.password.length < 8) {
					uni.showToast({
						title: '密码至少需要 8 位',
						icon: 'none'
					})
					return
				}
				if (this.password !== this.confirmPassword) {
					uni.showToast({
						title: '两次输入的密码不一致',
						icon: 'none'
					})
					return
				}
				if (this.loading) {
					return
				}
				this.loading = true
				apiRegister({
					username: this.username,
					password: this.password,
					confirmPassword: this.confirmPassword
				})
					.then(() => {
						uni.showToast({
							title: '注册成功',
							icon: 'success'
						})
						setTimeout(() => {
							this.goLogin()
						}, 600)
					})
					.catch(() => {
						// 错误提示已由请求层统一 toast
					})
					.finally(() => {
						this.loading = false
					})
			}
		}
	}
</script>

<style lang="scss">
	.register-page {
		position: relative;
		min-height: 100vh;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx calc(40rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.register-decor {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.register-decor--top {
		top: 110rpx;
		right: -90rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.register-decor--bottom {
		left: -90rpx;
		bottom: 120rpx;
		width: 190rpx;
		height: 190rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.register-shell {
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
		width: 64rpx;
		height: 64rpx;
		margin: 0;
		padding: 0;
		border-radius: 20rpx;
		border: 1rpx solid rgba(47, 69, 56, 0.12);
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

	.copy-block__title,
	.copy-block__desc,
	.field-label,
	.meta-row__text,
	.meta-row__link {
		display: block;
	}

	.copy-block {
		padding: 110rpx 18rpx 0;
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
		padding-top: 34rpx;
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

	.field-control {
		display: flex;
		align-items: center;
		margin-top: 16rpx;
		padding: 0 18rpx;
		min-height: 100rpx;
		border-radius: 30rpx;
		background: #ffffff;
		box-shadow: $cm-shadow-sm;
	}

	.field-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		width: 56rpx;
		height: 56rpx;
		margin-right: 12rpx;
		border-radius: 20rpx;
		background: #f4f5f0;
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

	.primary-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-height: 98rpx;
		margin-top: 40rpx;
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
		margin-top: 48rpx;
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

	.field-input::-ms-reveal,
	.field-input::-ms-clear,
	.field-input::-webkit-credentials-auto-fill-button,
	.field-input::-webkit-contacts-auto-fill-button {
		display: none;
		visibility: hidden;
		pointer-events: none;
	}
</style>
