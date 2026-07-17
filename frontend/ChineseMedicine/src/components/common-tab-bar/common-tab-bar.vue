<template>
	<view class="common-tab-bar">
		<button
			v-for="item in tabs"
			:key="item.value"
			:aria-label="item.label"
			class="common-tab-bar__item"
			:class="{ 'common-tab-bar__item--active': activeTab === item.value }"
			@tap="handleTap(item)"
		>
			<view class="common-tab-bar__icon-wrap">
				<image class="common-tab-bar__icon" :src="item.icon" mode="aspectFit"></image>
			</view>
		</button>
	</view>
</template>

<script>
	import { appTabs } from '../../config/tab-bar'

	export default {
		name: 'CommonTabBar',
		props: {
			activeTab: {
				type: String,
				required: true
			}
		},
		data() {
			return {
				tabs: appTabs
			}
		},
		methods: {
			handleTap(item) {
				if (item.value === this.activeTab) {
					return
				}

				uni.reLaunch({
					url: item.url
				})
			}
		}
	}
</script>

<style lang="scss">
	.common-tab-bar {
		position: fixed;
		left: 32rpx;
		right: 32rpx;
		bottom: calc(24rpx + env(safe-area-inset-bottom));
		z-index: 10;
		display: flex;
		align-items: center;
		padding: 10rpx;
		border-radius: 999rpx;
		background: #3f5848;
		box-shadow: 0 18px 32px rgba(63, 88, 72, 0.2);
	}

	.common-tab-bar__item {
		position: relative;
		display: flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		height: 96rpx;
		border-radius: 999rpx;
		background: transparent;
		line-height: 1;
	}

	.common-tab-bar__item--active {
		background: transparent;
	}

	.common-tab-bar__icon-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 72rpx;
		height: 72rpx;
		border-radius: 50%;
		transition: background 0.18s ease, box-shadow 0.18s ease;
	}

	.common-tab-bar__item--active .common-tab-bar__icon-wrap {
		width: 72rpx;
		height: 72rpx;
		background: $cm-color-brand;
		box-shadow: 0 8rpx 18rpx rgba(132, 214, 13, 0.28);
	}

	.common-tab-bar__icon {
		width: 38rpx;
		height: 38rpx;
		filter: brightness(0) saturate(100%) invert(78%) sepia(8%) saturate(210%) hue-rotate(69deg) brightness(96%) contrast(88%);
		opacity: 0.92;
	}

	.common-tab-bar__item--active .common-tab-bar__icon {
		width: 38rpx;
		height: 38rpx;
		filter: brightness(0) invert(1);
	}

</style>
