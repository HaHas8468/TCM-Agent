<template>
	<view class="forgot-page">
		<view class="forgot-lock"></view>

		<view class="forgot-shell">
			<button class="back-btn" @tap="goBack">
				<image class="back-btn__icon" src="/static/design-assets/icons/lucide/arrow-left.svg" mode="aspectFit"></image>
			</button>

			<view class="title-block">
				<text class="title-block__title">忘记密码</text>
				<text class="title-block__desc">选择要重置的方法</text>
			</view>

			<view class="option-list">
				<button
					v-for="item in options"
					:key="item.value"
					class="option-card"
					:class="{ 'option-card--active': selectedMethod === item.value }"
					@tap="selectedMethod = item.value"
				>
					<view class="option-card__icon" :class="`option-card__icon--${item.icon}`">
						<view v-if="item.icon === 'mail'" class="mini-mail">
							<view class="mini-mail__body"></view>
							<view class="mini-mail__flap"></view>
						</view>
						<view v-else-if="item.icon === 'shield'" class="mini-shield">
							<view class="mini-shield__body"></view>
							<view class="mini-shield__dot"></view>
						</view>
						<view v-else class="mini-lock">
							<view class="mini-lock__arch"></view>
							<view class="mini-lock__body"></view>
						</view>
					</view>
					<view class="option-card__copy">
						<text class="option-card__title">{{ item.title }}</text>
						<text class="option-card__desc">{{ item.desc }}</text>
					</view>
				</button>
			</view>

			<button class="reset-btn" @tap="handleReset">
				<text class="reset-btn__text">重置密码</text>
				<text class="reset-btn__arrow">→</text>
			</button>
		</view>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				selectedMethod: 'shield',
				options: [
					{
						value: 'mail',
						title: '电子邮件地址',
						desc: '通过电子邮件地址安全发送',
						icon: 'mail'
					},
					{
						value: 'shield',
						title: '双重认证',
						desc: '通过 2FA 安全发送',
						icon: 'shield'
					},
					{
						value: 'sms',
						title: '短信验证',
						desc: '通过发送短信验证码验证',
						icon: 'lock'
					}
				]
			}
		},
		methods: {
			goBack() {
				uni.navigateBack({
					fail: () => {
						uni.redirectTo({
							url: '/pages/login/login'
						})
					}
				})
			},
			handleReset() {
				const selected = this.options.find((item) => item.value === this.selectedMethod)
				// 当前 API 规范未提供"忘记密码"接口，此处仅做占位提示
				uni.showToast({
					title: `${selected.title} 暂未开放`,
					icon: 'none'
				})
			}
		}
	}
</script>

<style lang="scss">
	.forgot-page {
		position: relative;
		min-height: 100vh;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx calc(40rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.forgot-lock {
		position: absolute;
		left: -20rpx;
		bottom: -10rpx;
		width: 220rpx;
		height: 220rpx;
		border-radius: 80rpx;
		border: 18rpx solid rgba(36, 49, 44, 0.05);
		border-top-width: 30rpx;
		background: transparent;
	}

	.forgot-lock::before,
	.forgot-lock::after {
		content: '';
		position: absolute;
		background: rgba(36, 49, 44, 0.05);
	}

	.forgot-lock::before {
		left: 52rpx;
		top: -88rpx;
		width: 98rpx;
		height: 110rpx;
		border: 18rpx solid rgba(36, 49, 44, 0.05);
		border-bottom: 0;
		border-radius: 60rpx 60rpx 0 0;
		background: transparent;
	}

	.forgot-lock::after {
		left: 80rpx;
		bottom: 42rpx;
		width: 44rpx;
		height: 44rpx;
		border-radius: 50%;
	}

	.forgot-shell {
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

	.title-block {
		padding-top: 110rpx;
	}

	.title-block__title,
	.title-block__desc,
	.option-card__title,
	.option-card__desc {
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

	.option-list {
		margin-top: 34rpx;
	}

	.option-card {
		display: flex;
		align-items: center;
		width: 100%;
		padding: 24rpx;
		border: 3rpx solid transparent;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.94);
		box-shadow: $cm-shadow-sm;
	}

	.option-card + .option-card {
		margin-top: 22rpx;
	}

	.option-card--active {
		border-color: rgba(132, 214, 13, 0.6);
		box-shadow: 0 10px 24px rgba(132, 214, 13, 0.16);
	}

	.option-card__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 88rpx;
		height: 88rpx;
		border-radius: 28rpx;
		background: #f1f3ed;
	}

	.option-card--active .option-card__icon {
		background: rgba(132, 214, 13, 0.18);
	}

	.option-card__copy {
		flex: 1;
		margin-left: 20rpx;
		text-align: left;
	}

	.option-card__title {
		font-size: 32rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.option-card__desc {
		margin-top: 8rpx;
		font-size: 24rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.mini-mail,
	.mini-shield,
	.mini-lock {
		position: relative;
	}

	.mini-mail {
		width: 30rpx;
		height: 20rpx;
	}

	.mini-mail__body {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		height: 18rpx;
		border: 3rpx solid #66736b;
		border-top: 0;
		border-radius: 8rpx;
	}

	.mini-mail__flap {
		position: absolute;
		left: 4rpx;
		top: 2rpx;
		width: 18rpx;
		height: 12rpx;
		border-left: 3rpx solid #66736b;
		border-bottom: 3rpx solid #66736b;
		transform: skewY(-28deg) rotate(-45deg);
	}

	.mini-shield {
		width: 28rpx;
		height: 34rpx;
	}

	.mini-shield__body {
		position: absolute;
		inset: 0;
		border-radius: 14rpx 14rpx 12rpx 12rpx;
		background: #84d60d;
	}

	.mini-shield__body::after {
		content: '';
		position: absolute;
		left: 8rpx;
		right: 8rpx;
		top: -4rpx;
		height: 10rpx;
		border-radius: 999rpx;
		background: #cfe98f;
	}

	.mini-shield__dot {
		position: absolute;
		left: 50%;
		top: 14rpx;
		width: 6rpx;
		height: 6rpx;
		margin-left: -3rpx;
		border-radius: 50%;
		background: #ffffff;
	}

	.mini-lock {
		width: 26rpx;
		height: 28rpx;
	}

	.mini-lock__arch {
		position: absolute;
		left: 5rpx;
		top: 0;
		width: 16rpx;
		height: 12rpx;
		border: 3rpx solid #66736b;
		border-bottom: 0;
		border-radius: 14rpx 14rpx 0 0;
	}

	.mini-lock__body {
		position: absolute;
		left: 1rpx;
		right: 1rpx;
		bottom: 0;
		height: 18rpx;
		border-radius: 8rpx;
		background: #66736b;
	}

	.reset-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		min-height: 98rpx;
		margin-top: 46rpx;
		border-radius: $cm-radius-pill;
		background: $cm-color-brand;
		box-shadow: 0 10px 22px rgba(132, 214, 13, 0.22);
	}

	.reset-btn__text,
	.reset-btn__arrow {
		font-size: 30rpx;
		font-weight: 700;
		color: #ffffff;
	}

	.reset-btn__arrow {
		margin-left: 16rpx;
	}
</style>
