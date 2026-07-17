<template>
	<view class="info-page">
		<view class="info-page__orb info-page__orb--top"></view>
		<view class="info-page__orb info-page__orb--bottom"></view>

		<view class="info-hero">
			<view class="info-hero__head">
				<view class="info-hero__copy">
					<text class="info-hero__eyebrow">信息中心</text>
					<text class="info-hero__title">最近一次诊断结果</text>
				</view>
				<view class="info-hero__avatar">
					<image class="info-hero__avatar-image" :src="userProfile.avatar" mode="aspectFill"></image>
				</view>
			</view>

			<text class="info-hero__desc">智能挂号生成的诊断建议会同步到这里，方便你继续查看、对照和挂号。</text>

			<view class="info-hero__meta">
				<view class="info-hero__pill">
					<text class="info-hero__pill-label">最近同步</text>
					<text class="info-hero__pill-value">{{ result.updatedAt }}</text>
				</view>
				<view class="info-hero__pill info-hero__pill--soft">
					<text class="info-hero__pill-label">状态</text>
					<text class="info-hero__pill-value">{{ hasDiagnosisResult ? '已生成' : '待生成' }}</text>
				</view>
			</view>
		</view>

		<view class="result-card">
			<view class="result-card__badge">
				<image class="result-card__badge-icon" src="/static/design-assets/icons/lucide/leaf.svg" mode="aspectFit"></image>
				<text class="result-card__badge-text">诊断概览</text>
			</view>
			<text class="result-card__title">{{ result.title }}</text>
			<text class="result-card__summary">{{ result.summary }}</text>

			<view class="result-card__tags">
				<view class="result-card__tag">
					<text class="result-card__tag-label">建议科室</text>
					<text class="result-card__tag-value">{{ result.department }}</text>
				</view>
			</view>
			<button class="result-card__detail-btn" @tap="goResultDetail">
				{{ hasDiagnosisResult ? '继续智能挂号' : '去智能挂号生成结果' }}
			</button>
		</view>
	</view>
</template>

<script>
	
	import { getCurrentUserProfile } from '../../config/user-profile'
	import { defaultDiagnosisResult, getLatestDiagnosisResult, saveLatestDiagnosisResult } from '../../config/diagnosis-result'
	import { getLatestDiagnosis } from '../../api'

	export default {
		data() {
			return {
				userProfile: getCurrentUserProfile(),
				result: {
					...defaultDiagnosisResult
				}
			}
		},
		computed: {
			hasDiagnosisResult() {
				return this.result.title !== defaultDiagnosisResult.title
			}
		},
		onShow() {
			this.syncUserProfile()
			this.syncLatestDiagnosisResult()
			this.syncLatestDiagnosis()
		},
		methods: {
			syncUserProfile() {
				this.userProfile = getCurrentUserProfile()
			},
			syncLatestDiagnosisResult() {
				const latestResult = getLatestDiagnosisResult()
				this.result = latestResult
			},
			syncLatestDiagnosis() {
				getLatestDiagnosis()
					.then((mapped) => {
						if (mapped) {
							this.result = saveLatestDiagnosisResult(mapped)
						}
					})
					.catch(() => {
						// 无最新诊断或请求失败，保持本地结果
					})
			},
			goSmartRegister() {
				uni.navigateTo({
					url: '/pages/register/smart'
				})
			},
			goResultDetail() {
				this.goSmartRegister()
			}
		}
	}
</script>

<style lang="scss">
	.info-page {
		position: relative;
		min-height: 100vh;
		padding: calc(26rpx + env(safe-area-inset-top)) 20rpx calc(188rpx + env(safe-area-inset-bottom));
		overflow: hidden;
		background: linear-gradient(180deg, #f2f4ef 0%, #f7f5ef 100%);
	}

	.info-page__orb {
		position: absolute;
		border-radius: 38rpx;
		background: rgba(132, 214, 13, 0.1);
		filter: blur(8rpx);
	}

	.info-page__orb--top {
		top: 120rpx;
		right: -78rpx;
		width: 220rpx;
		height: 220rpx;
	}

	.info-page__orb--bottom {
		left: -90rpx;
		bottom: 220rpx;
		width: 210rpx;
		height: 210rpx;
		background: rgba(47, 69, 56, 0.05);
	}

	.info-hero,
	.result-card {
		position: relative;
		z-index: 1;
	}

	.info-hero {
		margin: calc(-26rpx - env(safe-area-inset-top)) -20rpx 0;
		padding: calc(54rpx + env(safe-area-inset-top)) 24rpx 30rpx;
		overflow: hidden;
		border-radius: 0 0 56rpx 56rpx;
		background: linear-gradient(180deg, #31473a 0%, #3b5644 58%, #415e49 100%);
		box-shadow: $cm-shadow-lg;
	}

	.info-hero__head,
	.info-hero__meta,
	.result-card__badge,
	.result-card__tags {
		display: flex;
	}

	.info-hero__head {
		align-items: center;
	}

	.info-hero__copy {
		flex: 1;
	}

	.info-hero__eyebrow,
	.info-hero__title,
	.info-hero__desc,
	.info-hero__pill-label,
	.info-hero__pill-value,
	.result-card__badge-text,
	.result-card__title,
	.result-card__summary,
	.result-card__tag-label,
	.result-card__tag-value {
		display: block;
	}

	.info-hero__eyebrow {
		font-size: 22rpx;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.76);
	}

	.info-hero__title {
		margin-top: 12rpx;
		font-size: 44rpx;
		font-weight: 700;
		line-height: 1.2;
		color: #ffffff;
	}

	.info-hero__avatar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 92rpx;
		height: 92rpx;
		margin-left: 18rpx;
		padding: 5rpx;
		border-radius: 36rpx;
		background: rgba(255, 255, 255, 0.94);
	}

	.info-hero__avatar-image {
		width: 100%;
		height: 100%;
		border-radius: 26rpx;
	}

	.info-hero__desc {
		margin-top: 20rpx;
		font-size: 24rpx;
		line-height: 1.7;
		color: rgba(255, 255, 255, 0.8);
	}

	.info-hero__meta {
		margin-top: 22rpx;
	}

	.info-hero__pill {
		flex: 1;
		padding: 18rpx;
		border-radius: 24rpx;
		background: rgba(255, 255, 255, 0.1);
	}

	.info-hero__pill + .info-hero__pill {
		margin-left: 14rpx;
	}

	.info-hero__pill--soft {
		background: rgba(243, 212, 107, 0.18);
	}

	.info-hero__pill-label {
		font-size: 20rpx;
		color: rgba(255, 255, 255, 0.68);
	}

	.info-hero__pill-value {
		margin-top: 10rpx;
		font-size: 26rpx;
		font-weight: 700;
		color: #ffffff;
	}

	.result-card {
		margin-top: 24rpx;
		padding: 26rpx;
		border-radius: 32rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
	}

	.result-card__badge {
		display: inline-flex;
		align-items: center;
		padding: 10rpx 18rpx;
		border-radius: 34rpx;
		background: rgba(132, 214, 13, 0.12);
	}

	.result-card__badge-icon {
		width: 24rpx;
		height: 24rpx;
	}

	.result-card__badge-text {
		margin-left: 10rpx;
		font-size: 20rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.result-card__title {
		margin-top: 18rpx;
		font-size: 38rpx;
		font-weight: 700;
		line-height: 1.28;
		color: $cm-text-title;
	}

	.result-card__summary {
		margin-top: 14rpx;
		font-size: 23rpx;
		line-height: 1.7;
		color: $cm-text-secondary;
	}

	.result-card__tags {
		margin-top: 20rpx;
	}

	.result-card__tag {
		flex: 1;
		padding: 18rpx;
		border-radius: 24rpx;
		background: #f7faf3;
	}

	.result-card__tag-label {
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.result-card__tag-value {
		margin-top: 10rpx;
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.result-card__detail-btn {
		width: 100%;
		height: 86rpx;
		margin-top: 22rpx;
		border: 0;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.14);
		font-size: 26rpx;
		font-weight: 700;
		line-height: 86rpx;
		color: $cm-color-brand-deep;
	}

	.result-card__detail-btn::after {
		border: 0;
	}

</style>
