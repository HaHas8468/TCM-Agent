<template>
	<view class="setting-page">
		<view class="setting-page__orb setting-page__orb--top"></view>
		<view class="setting-page__orb setting-page__orb--bottom"></view>

		<view class="setting-shell">
			<button class="back-btn" @tap="goBack">
				<view class="back-btn__arrow"></view>
			</button>

			<view class="title-block">
				<text class="title-block__title">个人设置</text>
				<text class="title-block__desc">管理你的个人资料与账户状态</text>
			</view>

			<view class="setting-card">
				<button class="setting-row" @tap="goProfile">
					<view class="setting-row__icon">
						<image class="setting-row__icon-image setting-row__icon-image--avatar" :src="userProfile.avatar" mode="aspectFill"></image>
					</view>
					<view class="setting-row__copy">
						<text class="setting-row__title">个人信息</text>
						<text class="setting-row__desc">可修改头像、名字与基础资料</text>
					</view>
					<text class="setting-row__arrow">›</text>
				</button>
			</view>

			<view class="setting-card setting-card--secondary">
				<button class="setting-row setting-row--logout" @tap="handleLogout">
					<view class="setting-row__icon setting-row__icon--logout">
						<text class="setting-row__icon-text">退</text>
					</view>
					<view class="setting-row__copy">
						<text class="setting-row__title setting-row__title--logout">退出账户</text>
						<text class="setting-row__desc">退出当前登录并返回登录页</text>
					</view>
				</button>
			</view>
		</view>
	</view>
</template>

<script>
	import { getCurrentUserProfile, resetCurrentUserProfile } from '../../config/user-profile'
	import { clearAuth } from '../../config/http'

	export default {
		data() {
			return {
				userProfile: getCurrentUserProfile()
			}
		},
		onShow() {
			this.syncUserProfile()
		},
		methods: {
			syncUserProfile() {
				this.userProfile = getCurrentUserProfile()
			},
			goBack() {
				uni.navigateBack({
					fail: () => {
						uni.redirectTo({
							url: '/pages/user/user'
						})
					}
				})
			},
			goProfile() {
				uni.navigateTo({
					url: '/pages/user/profile'
				})
			},
			handleLogout() {
				uni.showModal({
					title: '退出账户',
					content: '确认退出当前账户吗？',
					confirmColor: '#84D60D',
					success: ({ confirm }) => {
						if (!confirm) {
							return
						}
						resetCurrentUserProfile()
						clearAuth()
						uni.reLaunch({
							url: '/pages/login/login'
						})
					}
				})
			}
		}
	}
</script>

<style lang="scss">
	.setting-page {
		position: relative;
		min-height: 100vh;
		padding: calc(28rpx + env(safe-area-inset-top)) 26rpx calc(40rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.setting-page__orb {
		position: absolute;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.08);
	}

	.setting-page__orb--top {
		top: 126rpx;
		right: -90rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.setting-page__orb--bottom {
		left: -84rpx;
		bottom: 140rpx;
		width: 190rpx;
		height: 190rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.setting-shell {
		position: relative;
		z-index: 1;
	}

	.back-btn,
	.setting-row {
		display: flex;
		align-items: center;
	}

	.back-btn {
		position: absolute;
		top: 0;
		left: 0;
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
	.setting-row__title,
	.setting-row__desc,
	.setting-row__icon-text {
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

	.setting-card {
		margin-top: 34rpx;
		padding: 12rpx 22rpx;
		border-radius: 34rpx;
		background: rgba(255, 255, 255, 0.94);
		box-shadow: $cm-shadow-sm;
	}

	.setting-card--secondary {
		margin-top: 18rpx;
	}

	.setting-row {
		width: 100%;
		padding: 22rpx 0;
		border: 0;
		background: transparent;
		line-height: 1.2;
		text-align: left;
	}

	.setting-row::after {
		border: 0;
	}

	.setting-row__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 84rpx;
		height: 84rpx;
		border-radius: 26rpx;
		background: rgba(132, 214, 13, 0.12);
	}

	.setting-row__icon--logout {
		background: rgba(232, 108, 118, 0.12);
	}

	.setting-row__icon-image {
		width: 34rpx;
		height: 34rpx;
	}

	.setting-row__icon-image--avatar {
		width: 100%;
		height: 100%;
		border-radius: 22rpx;
	}

	.setting-row__icon-text {
		font-size: 26rpx;
		font-weight: 700;
		color: #d86171;
	}

	.setting-row__copy {
		flex: 1;
		margin-left: 18rpx;
	}

	.setting-row__title {
		font-size: 30rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.setting-row__title--logout {
		color: #d86171;
	}

	.setting-row__desc {
		margin-top: 8rpx;
		font-size: 22rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.setting-row__arrow {
		font-size: 42rpx;
		line-height: 1;
		color: #94a09b;
	}
</style>
