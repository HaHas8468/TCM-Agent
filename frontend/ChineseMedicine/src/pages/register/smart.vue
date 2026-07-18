<template>
	<view class="chat-page">
		<!-- 顶栏 -->
		<view class="chat-nav">
			<button class="chat-nav__back" @tap="goBack">
				<image class="chat-nav__action-icon" src="/static/design-assets/icons/lucide/arrow-left.svg" mode="aspectFit"></image>
			</button>
			<view class="chat-nav__center">
				<view class="chat-nav__meta">
					<text class="chat-nav__title">问方挂号助手</text>
					<text class="chat-nav__status">{{ sending ? '正在回复…' : '在线' }}</text>
				</view>
			</view>
			<view class="chat-nav__actions">
				<button class="chat-nav__action" aria-label="历史对话" @tap="toggleSessionPanel">
					<image class="chat-nav__action-icon" src="/static/design-assets/icons/lucide/clock-3.svg" mode="aspectFit"></image>
				</button>
				<button class="chat-nav__action chat-nav__action--new" aria-label="新建对话" @tap="createNewConversation">
					<image class="chat-nav__action-icon" src="/static/design-assets/icons/lucide/plus.svg" mode="aspectFit"></image>
				</button>
			</view>
		</view>

		<!-- 历史记录仅在当前聊天页中展开，不跳转到其他页面 -->
		<view v-if="showSessionPanel" class="session-overlay" @tap="closeSessionPanel">
			<view class="session-panel" @tap.stop>
				<view class="session-panel__head">
					<text class="session-panel__title">历史对话</text>
					<view class="session-panel__head-actions">
						<text class="session-panel__count">{{ aiSessions.length }} 条</text>
						<button v-if="aiSessions.length" class="session-panel__clear" @tap="confirmClearAiSessions">清空</button>
					</view>
				</view>
				<scroll-view v-if="aiSessions.length" class="session-panel__list" scroll-y :show-scrollbar="false">
					<view
						v-for="session in aiSessions"
						:key="session.id"
						class="session-panel__item"
						:class="{ 'session-panel__item--active': session.id === sessionId }"
						@tap="loadSession(session)"
					>
						<view class="session-panel__item-head">
							<text class="session-panel__summary">{{ session.summary }}</text>
							<button class="session-panel__delete" @tap.stop="confirmRemoveAiSession(session)">删除</button>
						</view>
						<view class="session-panel__meta">
							<text>{{ session.department || '智能挂号咨询' }}</text>
							<text>{{ formatSessionTime(session.updatedAt) }}</text>
						</view>
					</view>
				</scroll-view>
				<view v-else class="session-panel__empty">
					<text>暂时没有历史对话</text>
				</view>
			</view>
		</view>

		<!-- 消息区 -->
		<scroll-view
			class="chat-scroll"
			scroll-y
			:scroll-into-view="scrollIntoView"
			scroll-with-animation
			:show-scrollbar="false"
		>
			<view class="chat-scroll__inner">
				<!-- 欢迎区：仅首条助手问候时展示 -->
				<view v-if="showWelcome" class="welcome">
					<view class="welcome__mark">
						<image
							class="welcome__mark-icon"
							src="/static/design-assets/icons/lucide/leaf.svg"
							mode="aspectFit"
						></image>
					</view>
					<text class="welcome__title">你好，我是挂号助手</text>
					<text class="welcome__desc">
						描述不适部位、持续时间、是否反复，以及你最想优先解决的问题，我会帮你推荐更合适的就诊科室。
					</text>
					<view class="welcome__chips">
						<view
							v-for="chip in suggestionChips"
							:key="chip"
							class="welcome__chip"
							@tap="useSuggestion(chip)"
						>
							<text class="welcome__chip-text">{{ chip }}</text>
						</view>
					</view>
				</view>

				<!-- 消息列表 -->
				<view
					v-for="(item, index) in displayMessages"
					:key="item.id"
					:id="`msg-${item.id}`"
					class="msg-row"
					:class="`msg-row--${item.role}`"
				>
					<!-- 助手 -->
					<template v-if="item.role === 'assistant'">
						<view class="msg-assistant">
							<view class="msg-assistant__avatar">
								<image
									class="msg-assistant__avatar-icon"
									src="/static/design-assets/icons/lucide/leaf.svg"
									mode="aspectFit"
								></image>
							</view>
							<view class="msg-assistant__body">
								<text class="msg-assistant__name">问方助手</text>
								<view v-if="item.trace && (item.trace.steps || item.trace.tools)" class="agent-trace" :class="{ 'agent-trace--thinking': item.thinking }">
									<view class="agent-trace__header" @tap="toggleTrace(item)">
										<view class="agent-trace__head-left">
											<text class="agent-trace__icon">✦</text>
											<text class="agent-trace__title" :class="{ 'agent-trace__title--thinking': item.thinking }">思考</text>
											<view v-if="item.thinking" class="agent-trace__loading" aria-label="正在分析">
												<view class="agent-trace__dot"></view>
												<view class="agent-trace__dot"></view>
												<view class="agent-trace__dot"></view>
											</view>
										</view>
										<view class="agent-trace__toggle" :class="{ 'agent-trace__toggle--open': item.traceOpen }"></view>
									</view>
									<view v-if="item.traceOpen" class="agent-trace__body">
										<view v-for="(step, stepIndex) in item.trace.steps || []" :key="`step-${stepIndex}`" class="agent-trace__row">
											<text class="agent-trace__label">{{ step.title }}</text>
											<text class="agent-trace__detail">{{ step.detail }}</text>
										</view>
								<view v-for="(tool, toolIndex) in item.trace.tools || []" v-if="Array.isArray(item.trace.tools) && item.trace.tools.length" :key="`tool-${toolIndex}`" class="agent-trace__row agent-trace__row--tool">
											<text class="agent-trace__label">工具：{{ tool.name }}（{{ tool.status }}）</text>
											<text class="agent-trace__detail">{{ tool.detail }}</text>
										</view>
									</view>
								</view>
								<view v-if="!item.thinking || !item.trace" class="msg-assistant__bubble">
									<!-- 思考中 -->
									<view v-if="item.thinking" class="typing">
										<view class="typing__dot"></view>
										<view class="typing__dot"></view>
										<view class="typing__dot"></view>
									</view>
									<text v-else class="msg-assistant__text">{{ item.text }}</text>
								</view>
							</view>
						</view>
					</template>

					<!-- 用户 -->
					<template v-else>
						<view class="msg-user">
							<text class="msg-user__text">{{ item.text }}</text>
						</view>
					</template>
				</view>

				<!-- 推荐结果卡片（内嵌在对话流底部） -->
				<view v-if="recommendation" id="msg-result" class="result-block">
					<view class="result-card">
						<view class="result-card__head">
							<view class="result-card__head-left">
								<view class="result-card__dot"></view>
								<text class="result-card__title">推荐结果</text>
							</view>
							<text class="result-card__badge">已生成</text>
						</view>
						<view class="result-pill">
							<text class="result-pill__label">建议科室</text>
							<text class="result-pill__value">{{ recommendation.department }}</text>
						</view>
						<text v-if="recommendation.therapy" class="result-card__therapy">
							{{ recommendation.therapy }}
						</text>
					</view>
				</view>

				<!-- 底部锚点，用于滚到底 -->
				<view id="msg-bottom" class="chat-scroll__anchor"></view>
			</view>
		</scroll-view>

		<!-- 推荐科室快捷入口（在输入框上方） -->
		<view v-if="recommendation" class="recommend-bar">
			<view class="recommend-bar__content" @tap="goHomeWithRecommendation">
				<view class="recommend-bar__icon">
					<image src="/static/design-assets/icons/lucide/stethoscope.svg" mode="aspectFit" class="recommend-bar__icon-img"></image>
				</view>
				<view class="recommend-bar__text">
					<text class="recommend-bar__label">推荐挂号</text>
					<text class="recommend-bar__department">{{ recommendation.department }}</text>
				</view>
				<view class="recommend-bar__arrow"></view>
			</view>
		</view>

		<!-- 底部输入栏 -->
		<view class="composer-wrap">
			<view class="composer">
				<textarea
					v-model="draft"
					class="composer__input"
					:auto-height="true"
					:maxlength="500"
					:disabled="sending"
					:show-confirm-bar="false"
					:adjust-position="true"
					:cursor-spacing="20"
					disable-default-padding
					placeholder="描述症状"
					placeholder-class="composer__placeholder"
					@confirm="sendMessage"
				/>
				<button
					class="composer__send"
					:disabled="!canSend"
					:class="{ 'composer__send--active': canSend }"
					@tap="sendMessage"
				>
					<view class="composer__send-arrow"></view>
				</button>
			</view>
			<text class="composer__hint">内容仅用于挂号推荐，不构成诊疗意见</text>
		</view>
	</view>
</template>

<script>
	import { clearAiSessions, getAiSessions, removeAiSession, saveAiSession } from '../../config/ai-sessions'
	import { sendAgentMessageStream, buildDiagnosisResult } from '../../api'
	import { getPatientId } from '../../config/http'

	let msgSeq = 0
	function nextMsgId() {
		msgSeq += 1
		return `m${Date.now()}_${msgSeq}`
	}

	export default {
		data() {
			return {
				draft: '',
				sending: false,
				sessionId: '',
				scrollIntoView: '',
				streamAbort: null,
				messages: [],
				recommendation: null,
				showSessionPanel: false,
				aiSessions: [],
				suggestionChips: [
					'最近胃胀、食欲差，已经两周',
					'反复咳嗽咽痛，夜间加重',
					'头晕乏力，想知道挂什么科'
				]
			}
		},
		computed: {
			canSend() {
				return !!(this.draft && this.draft.trim()) && !this.sending
			},
			// 欢迎区展示时，首条问候隐藏在列表中，避免重复
			showWelcome() {
				return (this.messages.length === 0 || (this.messages.length === 1 && this.messages[0].role === 'assistant')) && !this.sending
			},
			displayMessages() {
				if (this.showWelcome) return []
				return this.messages
			}
		},
		beforeDestroy() {
			this.abortStream()
			this.persistCurrentSession()
		},
		// #ifdef VUE3
		beforeUnmount() {
			this.abortStream()
			this.persistCurrentSession()
		},
		// #endif
		onUnload() {
			this.persistCurrentSession()
		},
		onHide() {
			this.persistCurrentSession()
		},
		onShow() {
			this.syncAiSessions()
		},
		methods: {
			syncAiSessions() {
				this.aiSessions = getAiSessions()
			},
			toggleSessionPanel() {
				if (this.sending) {
					uni.showToast({ title: '回复完成后再查看历史对话', icon: 'none' })
					return
				}
				if (!this.showSessionPanel) {
					this.persistCurrentSession()
					this.syncAiSessions()
				}
				this.showSessionPanel = !this.showSessionPanel
			},
			closeSessionPanel() {
				this.showSessionPanel = false
			},
			formatSessionTime(value) {
				if (!value) return ''
				return String(value).slice(5, 16)
			},
			loadSession(session) {
				if (!session || this.sending) return
				this.persistCurrentSession()
				this.sessionId = session.id
				this.messages = (session.messages || []).map((message) => ({
					...message,
					thinking: false,
					trace: null,
					traceOpen: false
				}))
				this.recommendation = session.diagnosis || null
				this.draft = ''
				this.showSessionPanel = false
				this.scrollToBottom()
			},
			confirmRemoveAiSession(session) {
				uni.showModal({
					title: '删除会话',
					content: '删除后无法恢复，确定删除这条会话吗？',
					success: ({ confirm }) => {
						if (!confirm) return
						this.aiSessions = removeAiSession(session.id)
						if (this.sessionId === session.id) {
							this.sessionId = ''
							this.messages = []
							this.recommendation = null
							this.draft = ''
							this.scrollToBottom()
						}
						uni.showToast({ title: '已删除', icon: 'success' })
					}
				})
			},
			confirmClearAiSessions() {
				uni.showModal({
					title: '清空会话记录',
					content: '将删除全部 AI 会话记录，且无法恢复。',
					success: ({ confirm }) => {
						if (!confirm) return
						clearAiSessions()
						this.aiSessions = []
						this.sessionId = ''
						this.messages = []
						this.recommendation = null
						this.draft = ''
						this.showSessionPanel = false
						uni.showToast({ title: '已清空', icon: 'success' })
					}
				})
			},
			createNewConversation() {
				if (this.sending) {
					uni.showToast({ title: '回复完成后再新建对话', icon: 'none' })
					return
				}
				this.persistCurrentSession()
				this.sessionId = ''
				this.messages = []
				this.recommendation = null
				this.draft = ''
				this.showSessionPanel = false
				this.scrollToBottom()
			},
			toggleTrace(message) {
				message.traceOpen = !message.traceOpen
			},
			abortStream() {
				if (this.streamAbort) {
					try {
						this.streamAbort()
					} catch (e) {
						/* ignore */
					}
					this.streamAbort = null
				}
			},
			persistCurrentSession() {
				if (!this.sessionId) return
				const userMessages = this.messages.filter((item) => item && item.role === 'user')
				if (userMessages.length === 0) return

				saveAiSession({
					id: this.sessionId,
					summary: this.buildSummary(),
					messages: this.messages,
					department: this.recommendation ? this.recommendation.department : '',
					diagnosis: this.recommendation || null
				})
			},
			buildSummary() {
				const firstUser = this.messages.find((item) => item && item.role === 'user')
				const text = firstUser ? String(firstUser.text || '').trim() : ''
				if (!text) return 'AI 智能挂号会话'
				return text.length > 20 ? `${text.slice(0, 20)}…` : text
			},
			goBack() {
				this.abortStream()
				this.persistCurrentSession()
				uni.navigateBack({
					fail: () => {
						uni.redirectTo({
							url: '/pages/main/main'
						})
					}
				})
			},
			scrollToBottom() {
				this.$nextTick(() => {
					// 先清空再赋值，确保同一 id 也能再次触发滚动
					this.scrollIntoView = ''
					this.$nextTick(() => {
						this.scrollIntoView = this.recommendation ? 'msg-result' : 'msg-bottom'
					})
				})
			},
			useSuggestion(text) {
				if (this.sending) return
				this.draft = text
				this.sendMessage()
			},
			sendMessage() {
				const content = (this.draft || '').trim()
				if (!content || this.sending) return

				this.messages.push({
					id: nextMsgId(),
					role: 'user',
					text: content,
					thinking: false
				})
				this.draft = ''
				this.scrollToBottom()
				this.replyByApi(content)
			},
			replyByApi(content) {
				const isFirst = !this.sessionId
				if (isFirst) {
					const patientId = getPatientId()
					this.sessionId = `S_P_${patientId || 'anon'}_${Date.now()}`
				}
				this.sending = true

				const assistantMsg = {
					id: nextMsgId(),
					role: 'assistant',
					text: '',
					thinking: true
				}
				this.messages.push(assistantMsg)
				const msgIndex = this.messages.length - 1
				this.scrollToBottom()

				const stream = sendAgentMessageStream(
					{
						sessionId: this.sessionId,
						userInput: content,
						mode: isFirst ? 'normal' : 'follow-up',
						scene: 'guide'
					},
					{
						onText: (chunk) => {
							const m = this.messages[msgIndex]
							if (!m) return
							if (m.thinking) m.thinking = false
							m.text += chunk
							this.scrollToBottom()
						},
						onPayload: (data) => {
							const m = this.messages[msgIndex]
							if (!m) return

							// 后端 SSE 数据可能为 {code, data:{...}} 或直接是 {status, response,...}，统一兼容
							const inner = (data && typeof data === 'object' && data.data && typeof data.data === 'object')
								? data.data
								: data
							const trace = inner && inner.trace
							const isRunningTrace = data && data.event === 'trace' && trace && trace.state === 'running'
							if (!isRunningTrace) m.thinking = false
							const responseText = inner && (inner.response || inner.text)
							const status = inner && inner.status
							const diagnosis = inner && inner.diagnosis
							if (trace) {
								const isFirstTrace = !m.trace
								m.trace = {
									...trace,
									steps: Array.isArray(trace.steps) ? trace.steps : [],
									tools: Array.isArray(trace.tools) ? trace.tools : []
								}
								if (isFirstTrace) m.traceOpen = false
							}

						if (responseText) {
							// 每个流式 payload 的 response 都是增量文本片段，依次累加展示；
							// 流结束以 SSE 的 [DONE] 标记为准（触发 onDone），不依赖 finish 字段
							m.text += responseText
						}

							if (status === 'diagnosed' && diagnosis) {
								// 部分诊断结果只含结构化推荐字段；为该情况提供说明，避免留下空白气泡。
								if (!m.text) {
									m.text = '已根据您提供的现有症状生成初步挂号建议。由于信息有限，建议尽快到院面诊，由医生进一步判断。'
								}
								// 始终用完整累积文本 m.text 作为诊断依据，而非当次小片段 responseText
								const result = buildDiagnosisResult(
									diagnosis,
									m.text || ''
								)
								// 如果已有完整诊断（含证型/方剂），follow-up 的不完全结果不应覆盖原有内容
								if (this.recommendation && this.recommendation.signals && this.recommendation.signals.length > 0) {
									if (!(result.signals && result.signals.length > 0)) {
										result.reason = this.recommendation.reason
										result.signals = this.recommendation.signals
										result.therapy = this.recommendation.therapy
									}
								}
								this.recommendation = result
							} else if (status === 'error') {
								if (!m.text) {
									m.text = responseText || '系统繁忙，请稍后重试。'
								}
							}

							this.scrollToBottom()
						},
						onDone: () => {
							const m = this.messages[msgIndex]
							if (m) {
								m.thinking = false
								if (!m.text) {
									m.text = '已收到，请继续补充症状细节。'
								}
							}
							if (!this.recommendation && m && m.text) {
								this.extractRecommendationFromText(m.text)
							}
							this.sending = false
							this.streamAbort = null
							this.persistCurrentSession()
							this.syncAiSessions()
							this.scrollToBottom()
						},
						onError: () => {
							const m = this.messages[msgIndex]
							if (m) {
								m.thinking = false
								if (!m.text) {
									m.text = '抱歉，刚才没有处理好，请再描述一次或稍后重试。'
								}
							}
							this.sending = false
							this.streamAbort = null
							this.persistCurrentSession()
							this.syncAiSessions()
							this.scrollToBottom()
						}
					}
				)

				this.streamAbort = stream && stream.abort ? stream.abort.bind(stream) : null
			},
			goHomeWithRecommendation() {
				if (!this.recommendation) return
				this.persistCurrentSession()
				const department = encodeURIComponent(this.recommendation.department)
				uni.redirectTo({
					url: `/pages/main/main?department=${department}`
				})
			},
			extractRecommendationFromText(text) {
				const DEPARTMENT_KEYWORDS = ['中医内科', '呼吸内科', '神经内科', '心血管内科', '消化内科', '骨伤科', '妇科', '儿科', '皮肤科', '肾病科', '泌尿外科', '内分泌科']
				let matchedDepartment = ''
				for (const dept of DEPARTMENT_KEYWORDS) {
					if (text.includes(dept)) {
						matchedDepartment = dept
						break
					}
				}
				if (!matchedDepartment) {
					const pattern = /([\u4e00-\u9fa5]+科)/g
					const matches = text.match(pattern)
					if (matches && matches.length > 0) {
						matchedDepartment = matches[0]
					}
				}
				if (matchedDepartment) {
					const result = {
						title: '初步诊断完成',
						summary: text.slice(0, 50) + (text.length > 50 ? '...' : ''),
						department: matchedDepartment,
						priority: '建议尽快预约',
						reason: text,
						signals: [],
						therapy: '',
						advice: ['可点击下方按钮按推荐科室继续挂号。'],
						notices: ['当前结果由智能体生成，仅供就诊参考，不替代正式医疗诊断。'],
						updatedAt: new Date().toLocaleString()
					}
				this.recommendation = result
			}
		}
	}
}
</script>

<style lang="scss">
	.chat-page {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
		background: #f7f5ef;
	}

	/* ===== 顶栏 ===== */
	.chat-nav {
		display: flex;
		align-items: center;
		flex-shrink: 0;
		padding: calc(28rpx + env(safe-area-inset-top)) 20rpx 16rpx;
		background: rgba(247, 245, 239, 0.92);
		border-bottom: 1rpx solid rgba(232, 236, 230, 0.9);
		backdrop-filter: blur(16px);
		z-index: 10;
	}

	.chat-nav__back {
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
		flex-shrink: 0;
	}

	.chat-nav__back::after {
		border: 0;
	}

	.chat-nav__back:active {
		transform: scale(0.96);
	}

	.chat-nav__center {
		display: flex;
		align-items: center;
		flex: 1;
		min-width: 0;
		margin-left: 12rpx;
	}

	.chat-nav__meta {
		margin-left: 16rpx;
		min-width: 0;
	}

	.chat-nav__title,
	.chat-nav__status,
	.welcome__title,
	.welcome__desc,
	.welcome__chip-text,
	.msg-assistant__name,
	.msg-assistant__text,
	.msg-user__text,
	.result-card__title,
	.result-card__badge,
	.result-pill__label,
	.result-pill__value,
	.composer__hint {
		display: block;
	}

	.chat-nav__title {
		font-size: 30rpx;
		font-weight: 700;
		line-height: 1.2;
		color: $cm-text-title;
	}

	.chat-nav__status {
		margin-top: 4rpx;
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.chat-nav__actions {
		display: flex;
		align-items: center;
		gap: 10rpx;
		margin-left: 12rpx;
		flex-shrink: 0;
	}

	.chat-nav__action {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64rpx;
		height: 64rpx;
		margin: 0;
		padding: 0;
		border: 1rpx solid rgba(47, 69, 56, 0.12);
		border-radius: 20rpx;
		background: rgba(255, 255, 255, 0.88);
	}

	.chat-nav__action::after {
		border: 0;
	}

	.chat-nav__action--new {
		border-color: rgba(111, 191, 42, 0.28);
		background: rgba(132, 214, 13, 0.14);
	}

	.chat-nav__action-icon {
		width: 28rpx;
		height: 28rpx;
		opacity: 0.74;
	}

	.chat-nav__action--new .chat-nav__action-icon {
		opacity: 1;
	}

	.chat-nav__action:active {
		transform: scale(0.96);
	}

	/* ===== 历史会话面板 ===== */
	.session-overlay {
		position: fixed;
		z-index: 20;
		top: 0;
		right: 0;
		bottom: 0;
		left: 0;
		padding: calc(112rpx + env(safe-area-inset-top)) 24rpx 24rpx;
		background: rgba(36, 49, 44, 0.12);
		box-sizing: border-box;
	}

	.session-panel {
		overflow: hidden;
		max-height: 620rpx;
		border: 1rpx solid rgba(47, 69, 56, 0.1);
		border-radius: 26rpx;
		background: #ffffff;
		box-shadow: 0 18rpx 48rpx rgba(47, 69, 56, 0.18);
	}

	.session-panel__head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 24rpx 26rpx 20rpx;
		border-bottom: 1rpx solid rgba(47, 69, 56, 0.08);
	}

	.session-panel__head-actions,
	.session-panel__item-head {
		display: flex;
		align-items: center;
	}

	.session-panel__head-actions {
		gap: 14rpx;
	}

	.session-panel__title,
	.session-panel__count,
	.session-panel__summary,
	.session-panel__meta,
	.session-panel__empty {
		display: block;
	}

	.session-panel__title {
		font-size: 30rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.session-panel__count {
		padding: 5rpx 12rpx;
		border-radius: 999rpx;
		background: #f3f7ec;
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.session-panel__list {
		max-height: 500rpx;
	}

	.session-panel__item-head {
		justify-content: space-between;
		gap: 16rpx;
	}

	.session-panel__item {
		padding: 22rpx 26rpx;
		border-bottom: 1rpx solid rgba(47, 69, 56, 0.07);
	}

	.session-panel__item--active {
		background: rgba(132, 214, 13, 0.1);
	}

	.session-panel__item:active {
		background: #f3f7ec;
	}

	.session-panel__summary {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		font-size: 26rpx;
		font-weight: 600;
		line-height: 1.45;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: $cm-text-title;
	}

	.session-panel__clear,
	.session-panel__delete {
		margin: 0;
		padding: 0;
		border: 0;
		background: transparent;
		font-size: 21rpx;
		line-height: 1.4;
		color: #d9534f;
	}

	.session-panel__clear::after,
	.session-panel__delete::after {
		border: 0;
	}

	.session-panel__delete {
		flex-shrink: 0;
	}

	.session-panel__meta {
		display: flex;
		justify-content: space-between;
		margin-top: 8rpx;
		font-size: 21rpx;
		color: $cm-text-secondary;
	}

	.session-panel__empty {
		padding: 64rpx 24rpx;
		font-size: 24rpx;
		text-align: center;
		color: $cm-text-secondary;
	}

	/* ===== 消息滚动区 ===== */
	.chat-scroll {
		flex: 1;
		min-height: 0;
		height: 0;
	}

	.chat-scroll__inner {
		padding: 24rpx 28rpx 20rpx;
		box-sizing: border-box;
	}

	.chat-scroll__anchor {
		height: 8rpx;
	}

	/* ===== 欢迎态 ===== */
	.welcome {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 80rpx 16rpx 48rpx;
		text-align: center;
	}

	.welcome__mark {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 108rpx;
		height: 108rpx;
		border-radius: 36rpx;
		background: linear-gradient(145deg, rgba(132, 214, 13, 0.22), rgba(47, 69, 56, 0.1));
		box-shadow: $cm-shadow-sm;
	}

	.welcome__mark-icon {
		width: 52rpx;
		height: 52rpx;
	}

	.welcome__title {
		margin-top: 28rpx;
		font-size: 40rpx;
		font-weight: 700;
		line-height: 1.3;
		color: $cm-text-title;
	}

	.welcome__desc {
		margin-top: 16rpx;
		max-width: 620rpx;
		font-size: 26rpx;
		line-height: 1.7;
		color: $cm-text-secondary;
	}

	.welcome__chips {
		display: flex;
		flex-direction: column;
		align-items: stretch;
		width: 100%;
		max-width: 640rpx;
		margin-top: 36rpx;
	}

	.welcome__chip {
		padding: 22rpx 26rpx;
		border-radius: 22rpx;
		background: rgba(255, 255, 255, 0.96);
		box-shadow: $cm-shadow-sm;
		border: 1rpx solid rgba(232, 236, 230, 0.95);
	}

	.welcome__chip + .welcome__chip {
		margin-top: 14rpx;
	}

	.welcome__chip:active {
		background: #f3f7ec;
	}

	.welcome__chip-text {
		font-size: 26rpx;
		line-height: 1.5;
		color: $cm-text-body;
		text-align: left;
	}

	/* ===== 消息行 ===== */
	.msg-row {
		margin-bottom: 28rpx;
	}

	.msg-row--user {
		display: flex;
		justify-content: flex-end;
	}

	/* 助手消息：左侧头像 + 对话框气泡 */
	.msg-assistant {
		display: flex;
		align-items: flex-start;
		max-width: 100%;
	}

	.msg-assistant__avatar {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 56rpx;
		height: 56rpx;
		margin-top: 36rpx;
		border-radius: 18rpx;
		background: rgba(132, 214, 13, 0.16);
		flex-shrink: 0;
	}

	.msg-assistant__avatar-icon {
		width: 28rpx;
		height: 28rpx;
	}

	.msg-assistant__body {
		flex: 0 1 auto;
		min-width: 0;
		max-width: 82%;
		margin-left: 16rpx;
	}

	.msg-assistant__name {
		margin-bottom: 8rpx;
		margin-left: 8rpx;
		font-size: 22rpx;
		font-weight: 600;
		color: $cm-text-secondary;
	}

	.msg-assistant__bubble {
		display: inline-block;
		max-width: 100%;
		box-sizing: border-box;
		padding: 20rpx 26rpx;
		border-radius: 8rpx 28rpx 28rpx 28rpx;
		background: #ffffff;
		box-shadow: 0 2rpx 12rpx rgba(47, 69, 56, 0.06);
		border: 1rpx solid rgba(232, 236, 230, 0.95);
	}

	.agent-trace {
		margin: 4rpx 0 12rpx;
		border: 1rpx solid rgba(47, 69, 56, 0.1);
		border-radius: 18rpx;
		background: rgba(245, 247, 244, 0.92);
		overflow: hidden;
	}

	.agent-trace__header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16rpx 18rpx;
		min-height: 36rpx;
	}

	.agent-trace__head-left { display: flex; align-items: center; min-width: 0; }
	.agent-trace__icon { margin-right: 10rpx; font-size: 24rpx; line-height: 1; color: #6f9f40; }
	.agent-trace--thinking .agent-trace__icon { animation: tracePulse 1.4s ease-in-out infinite; }

	.agent-trace__loading { display: flex; align-items: center; margin-left: 22rpx; height: 18rpx; }
	.agent-trace__dot { width: 6rpx; height: 6rpx; margin: 0 3rpx; border-radius: 50%; background: #8eae72; animation: traceDot 1.1s ease-in-out infinite; }
	.agent-trace__dot:nth-child(2) { animation-delay: 0.15s; }
	.agent-trace__dot:nth-child(3) { animation-delay: 0.3s; }

	@keyframes tracePulse { 0%, 100% { opacity: 0.5; transform: scale(0.92); } 50% { opacity: 1; transform: scale(1.08); } }
	@keyframes traceDot { 0%, 60%, 100% { transform: translateY(0); opacity: 0.38; } 30% { transform: translateY(-5rpx); opacity: 1; } }

	.agent-trace__title,
	.agent-trace__label,
	.agent-trace__detail {
		display: block;
	}

	.agent-trace__title { font-size: 23rpx; font-weight: 600; color: #526057; }
	.agent-trace__title--thinking { background: linear-gradient(100deg, #526057 0%, #8fb866 42%, #526057 72%); background-size: 220% 100%; background-clip: text; -webkit-background-clip: text; color: transparent; -webkit-text-fill-color: transparent; animation: traceTextShimmer 1.6s linear infinite; }
	@keyframes traceTextShimmer { from { background-position: 100% 0; } to { background-position: -120% 0; } }
	.agent-trace__toggle { width: 12rpx; height: 12rpx; margin-left: 28rpx; margin-right: 8rpx; border-right: 2rpx solid #7a877d; border-bottom: 2rpx solid #7a877d; transform: rotate(45deg) translateY(-3rpx); transition: transform 0.2s ease; }
	.agent-trace__toggle--open { transform: rotate(225deg) translateY(-3rpx); }
	.agent-trace__body { padding: 0 18rpx 16rpx; border-top: 1rpx solid rgba(47, 69, 56, 0.08); }
	.agent-trace__row { position: relative; padding: 13rpx 0 0 18rpx; }
	.agent-trace__row::before { content: ''; position: absolute; left: 0; top: 23rpx; width: 7rpx; height: 7rpx; border-radius: 50%; background: #8eae72; }
	.agent-trace__row--tool { margin-top: 8rpx; padding: 12rpx 12rpx 12rpx 28rpx; border-radius: 10rpx; background: rgba(255, 255, 255, 0.72); }
	.agent-trace__row--tool::before { left: 12rpx; top: 22rpx; background: #6f9f40; }
	.agent-trace__label { font-size: 22rpx; font-weight: 500; color: #526057; }
	.agent-trace__detail { margin-top: 4rpx; font-size: 21rpx; line-height: 1.5; color: #7a877d; }

	.msg-assistant__text {
		font-size: 30rpx;
		line-height: 1.7;
		color: $cm-text-body;
		white-space: pre-wrap;
		word-break: break-word;
	}

	/* 用户消息：右侧气泡 */
	.msg-user {
		max-width: 78%;
	}

	.msg-user__text {
		padding: 20rpx 26rpx;
		border-radius: 28rpx 8rpx 28rpx 28rpx;
		background: linear-gradient(135deg, #84d60d 0%, #6fbf2a 100%);
		font-size: 30rpx;
		line-height: 1.65;
		color: #ffffff;
		white-space: pre-wrap;
		word-break: break-word;
		box-shadow: 0 4rpx 16rpx rgba(111, 191, 42, 0.22);
	}

	/* 打字指示器 */
	.typing {
		display: flex;
		align-items: center;
		height: 48rpx;
		padding: 4rpx 0;
	}

	.typing__dot {
		width: 12rpx;
		height: 12rpx;
		margin-right: 10rpx;
		border-radius: 50%;
		background: $cm-text-secondary;
		opacity: 0.35;
		animation: typing-bounce 1.2s infinite ease-in-out;
	}

	.typing__dot:nth-child(2) {
		animation-delay: 0.15s;
	}

	.typing__dot:nth-child(3) {
		animation-delay: 0.3s;
		margin-right: 0;
	}

	@keyframes typing-bounce {
		0%,
		80%,
		100% {
			transform: translateY(0);
			opacity: 0.3;
		}
		40% {
			transform: translateY(-8rpx);
			opacity: 0.9;
		}
	}

	/* ===== 推荐结果 ===== */
	.result-block {
		margin: 8rpx 0 24rpx;
	}

	.result-card {
		padding: 28rpx;
		border-radius: 28rpx;
		background: rgba(255, 255, 255, 0.98);
		box-shadow: $cm-shadow-sm;
		border: 1rpx solid rgba(232, 236, 230, 0.95);
	}

	.result-card__head {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.result-card__head-left {
		display: flex;
		align-items: center;
	}

	.result-card__dot {
		width: 14rpx;
		height: 14rpx;
		margin-right: 12rpx;
		border-radius: 50%;
		background: $cm-color-brand;
	}

	.result-card__title {
		font-size: 30rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.result-card__badge {
		height: 42rpx;
		padding: 0 16rpx;
		border-radius: 999rpx;
		background: rgba(132, 214, 13, 0.14);
		font-size: 20rpx;
		line-height: 42rpx;
		color: $cm-color-brand-deep;
	}

	.result-pill {
		margin-top: 22rpx;
		padding: 22rpx 24rpx;
		border-radius: 20rpx;
		background: #f3f7ec;
	}

	.result-pill__label {
		font-size: 22rpx;
		color: $cm-text-secondary;
	}

	.result-pill__value {
		margin-top: 10rpx;
		font-size: 34rpx;
		font-weight: 700;
		color: $cm-text-title;
	}

	.result-card__therapy {
		display: block;
		margin-top: 18rpx;
		padding: 20rpx 22rpx;
		border-radius: 20rpx;
		background: #f7faef;
		font-size: 24rpx;
		line-height: 1.75;
		white-space: pre-wrap;
		word-break: break-word;
		color: $cm-text-body;
	}

	/* ===== 推荐科室快捷入口 ===== */
	.recommend-bar {
		flex-shrink: 0;
		padding: 0 32rpx;
		background: #f7f5ef;
	}

	.recommend-bar__content {
		display: flex;
		align-items: center;
		padding: 16rpx 20rpx;
		border-radius: 20rpx;
		background: linear-gradient(135deg, rgba(132, 214, 13, 0.18) 0%, rgba(111, 191, 42, 0.12) 100%);
		border: 2rpx solid rgba(132, 214, 13, 0.28);
	}

	.recommend-bar__content:active {
		background: linear-gradient(135deg, rgba(132, 214, 13, 0.24) 0%, rgba(111, 191, 42, 0.18) 100%);
	}

	.recommend-bar__icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 56rpx;
		height: 56rpx;
		border-radius: 16rpx;
		background: rgba(132, 214, 13, 0.22);
		flex-shrink: 0;
	}

	.recommend-bar__icon-img {
		width: 28rpx;
		height: 28rpx;
	}

	.recommend-bar__text {
		flex: 1;
		margin-left: 14rpx;
	}

	.recommend-bar__label {
		display: block;
		font-size: 20rpx;
		color: $cm-text-secondary;
	}

	.recommend-bar__department {
		display: block;
		margin-top: 4rpx;
		font-size: 28rpx;
		font-weight: 700;
		color: $cm-color-brand-deep;
	}

	.recommend-bar__arrow {
		width: 14rpx;
		height: 14rpx;
		border-right: 4rpx solid $cm-color-brand-deep;
		border-bottom: 4rpx solid $cm-color-brand-deep;
		transform: rotate(-45deg);
		flex-shrink: 0;
	}

	/* ===== 底部输入 ===== */
	.composer-wrap {
		flex-shrink: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 10rpx 40rpx calc(14rpx + env(safe-area-inset-bottom));
		background: linear-gradient(180deg, rgba(247, 245, 239, 0) 0%, #f7f5ef 28%);
	}

	.composer {
		display: flex;
		align-items: center;
		width: 100%;
		max-width: 640rpx;
		min-height: 84rpx;
		padding: 8rpx 14rpx 8rpx 28rpx;
		border-radius: 999rpx;
		background: #ffffff;
		box-shadow: 0 4rpx 20rpx rgba(47, 69, 56, 0.08);
		border: 1rpx solid rgba(232, 236, 230, 0.95);
		box-sizing: border-box;
	}

	.composer__input {
		flex: 1;
		width: 0;
		min-height: 64rpx;
		max-height: 120rpx;
		padding: 0 12rpx 0 0;
		margin: 0;
		font-size: 26rpx;
		line-height: 64rpx;
		color: $cm-text-body;
		background: transparent;
		box-sizing: border-box;
	}

	.composer__placeholder {
		font-size: 24rpx;
		line-height: 64rpx;
		color: $cm-text-placeholder;
	}

	.composer__send {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64rpx;
		height: 64rpx;
		margin: 0 0 0 0;
		padding: 0;
		border: 0;
		border-radius: 50%;
		background: #d7ddd6;
		flex-shrink: 0;
		transition: background 0.15s ease;
	}

	.composer__send--active {
		background: #3f5848;
	}

	.composer__send::after {
		border: 0;
	}

	.composer__send-arrow {
		width: 16rpx;
		height: 16rpx;
		border-top: 5rpx solid #ffffff;
		border-right: 5rpx solid #ffffff;
		transform: translateY(4rpx) rotate(-45deg);
	}

	.composer__hint {
		margin-top: 10rpx;
		font-size: 20rpx;
		text-align: center;
		color: $cm-text-placeholder;
	}
</style>
