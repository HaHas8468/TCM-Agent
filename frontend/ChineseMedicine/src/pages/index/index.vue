<template>
	<view class="splash-page" @tap="goLogin">
		<image class="splash-page__background" src="/static/indexbackground.png" mode="aspectFill"></image>
		<text class="splash-page__hint">点击以进入</text>
	</view>
</template>

<script>
	export default {
		data() {
			return {
				navigated: false
			}
		},
		methods: {
			goLogin() {
				if (this.navigated) {
					return
				}
				this.navigated = true
				uni.redirectTo({
					url: '/pages/login/login'
				})
			}
		}
	}
</script>

<style lang="scss">
	.splash-page {
		position: relative;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		min-height: 100vh;
		padding: calc(40rpx + env(safe-area-inset-top)) 32rpx calc(220rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: #eff2ea;
	}

	.splash-page__background {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}

	.splash-page__hint {
		position: relative;
		z-index: 1;
		display: block;
		font-size: 24rpx;
		letter-spacing: 4rpx;
		color: #24312c;
		text-shadow: none;
	}
</style>
