<template>
	<view class="user-page">
		<view class="user-page__orb user-page__orb--top"></view>
		<view class="user-page__orb user-page__orb--bottom"></view>
		<view class="user-nav">
			<button class="user-nav__button" aria-label="返回" @tap="goBack">
				<image class="user-nav__icon" src="/static/design-assets/icons/lucide/arrow-left.svg" mode="aspectFit"></image>
			</button>
			<button class="user-nav__button user-nav__button--logout" aria-label="退出登录" @tap="handleLogout">
				<image class="user-nav__logout-icon" src="/static/design-assets/icons/lucide/log-out.svg" mode="aspectFit"></image>
			</button>
		</view>

		<view class="profile-hero">
			<image class="profile-hero__background" src="/static/userBackGround.png" mode="aspectFill"></image>
		</view>

		<view class="profile-head">
			<view class="profile-avatar">
				<image class="profile-avatar__image" :src="userProfile.avatar" mode="aspectFill"></image>
			</view>
			<text class="profile-name">{{ userProfile.name }}</text>
			<text class="profile-subtitle">欢迎回来，今天也要照顾好自己</text>
		</view>

		<view class="content-stack">
			<view class="menu-card">
				<button class="menu-row" @tap="goProfile">
					<view class="menu-row__icon">
						<image class="menu-row__icon-image" src="/static/design-assets/icons/lucide/user-round.svg" mode="aspectFit"></image>
					</view>
					<view class="menu-row__copy">
						<text class="menu-row__title">个人信息</text>
						<text class="menu-row__desc">查看和修改个人资料</text>
					</view>
					<text class="menu-row__arrow">›</text>
				</button>
			</view>

			<view class="menu-card menu-card--secondary">
				<button class="menu-row" @tap="goDiagnosisHistory">
					<view class="menu-row__icon menu-row__icon--history">
						<image class="menu-row__icon-image" src="/static/design-assets/icons/lucide/notebook-pen.svg" mode="aspectFit"></image>
					</view>
					<view class="menu-row__copy">
						<text class="menu-row__title">历史记录</text>
						<text class="menu-row__desc">查看挂号诊断与 AI 问诊记录</text>
					</view>
					<text class="menu-row__arrow">›</text>
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
						uni.reLaunch({ url: '/pages/main/main' })
					}
				})
			},
			handleLogout() {
				uni.showModal({
					title: '退出账户',
					content: '确认退出当前账户吗？',
					cancelText: '取消',
					confirmText: '确认',
					confirmColor: '#84D60D',
					success: ({ confirm }) => {
						if (!confirm) return
						resetCurrentUserProfile()
						clearAuth()
						uni.reLaunch({ url: '/pages/login/login' })
					}
				})
			},
			goProfile() {
				uni.navigateTo({
					url: '/pages/user/profile'
				})
			},
			goDiagnosisHistory() {
				uni.navigateTo({
					url: '/pages/user/history'
				})
			}
		}
	}
</script>

<style lang="scss">
	.user-page {
		position: relative;
		min-height: 100vh;
		padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.user-page__orb {
		position: absolute;
		border-radius: 38rpx;
		background: rgba(132, 214, 13, 0.08);
		filter: blur(6rpx);
	}

	.user-page__orb--top {
		top: 240rpx;
		right: -72rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.user-page__orb--bottom {
		left: -86rpx;
		bottom: 48rpx;
		width: 200rpx;
		height: 200rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.user-nav,
	.profile-hero,
	.profile-head,
	.content-stack {
		position: relative;
		z-index: 1;
	}

	.user-nav {
		position: absolute;
		top: calc(28rpx + env(safe-area-inset-top));
		left: 24rpx;
		right: 24rpx;
		display: flex;
		align-items: center;
		justify-content: space-between;
		z-index: 3;
	}

	.user-nav__button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64rpx;
		height: 64rpx;
		margin: 0;
		padding: 0;
		border: 1rpx solid rgba(47, 69, 56, 0.12);
		border-radius: 20rpx;
		background: rgba(255, 255, 255, 0.86);
		box-shadow: 0 6rpx 18rpx rgba(47, 69, 56, 0.1);
	}

	.user-nav__button::after {
		border: 0;
	}

	.user-nav__button:active {
		transform: scale(0.96);
	}

	.user-nav__icon {
		width: 28rpx;
		height: 28rpx;
	}

	.user-nav__button--logout {
		background: rgba(255, 255, 255, 0.92);
	}

	.user-nav__logout-icon {
		width: 28rpx;
		height: 28rpx;
		opacity: 0.78;
	}

	.profile-hero {
		height: calc(332rpx + env(safe-area-inset-top));
		padding-top: env(safe-area-inset-top);
		overflow: hidden;
		border-radius: 0 0 88rpx 88rpx;
	}

	.profile-hero__background {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}

	.profile-head {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-top: -58rpx;
		padding: 0 32rpx;
	}

	.profile-avatar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 130rpx;
		height: 130rpx;
		padding: 8rpx;
		border-radius: 50%;
		background: #ffffff;
		box-shadow: 0 12px 30px rgba(47, 69, 56, 0.14);
	}

	.profile-avatar__image {
		width: 100%;
		height: 100%;
		border-radius: 50%;
	}

	.profile-name,
	.profile-subtitle,
	.menu-row__title,
	.menu-row__desc {
		display: block;
	}

	.profile-name {
		margin-top: 22rpx;
		font-size: 42rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.profile-subtitle {
		margin-top: 12rpx;
		font-size: 24rpx;
		line-height: 1.6;
		text-align: center;
		color: $cm-text-secondary;
	}

	.content-stack {
		margin-top: 28rpx;
		padding: 0 20rpx;
	}

	.menu-card {
		padding: 26rpx;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
	}

	.menu-card {
		margin-top: 22rpx;
	}

	.menu-card--secondary {
		margin-top: 18rpx;
	}

	.menu-row {
		display: flex;
	}

	.menu-row {
		align-items: center;
		width: 100%;
		padding: 0;
		border: 0;
		background: transparent;
		line-height: 1.2;
		text-align: left;
	}

	.menu-row::after {
		border: 0;
	}

	.menu-row__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 88rpx;
		height: 88rpx;
		border-radius: 28rpx;
		background: rgba(132, 214, 13, 0.12);
	}

	.menu-row__icon-image {
		width: 36rpx;
		height: 36rpx;
	}

	.menu-row__icon--history {
		background: rgba(108, 146, 181, 0.14);
	}

	.menu-row__copy {
		flex: 1;
		margin-left: 18rpx;
	}

	.menu-row__title {
		font-size: 30rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.menu-row__desc {
		margin-top: 8rpx;
		font-size: 22rpx;
		line-height: 1.6;
		color: $cm-text-secondary;
	}

	.menu-row__arrow {
		font-size: 42rpx;
		line-height: 1;
		color: #94a09b;
	}

</style>
