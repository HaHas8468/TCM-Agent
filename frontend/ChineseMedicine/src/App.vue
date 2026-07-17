<script>
	export default {}
</script>

<style lang="scss">
	page {
		min-height: 100%;
		background: $cm-bg-main;
		color: $cm-text-title;
		font-family: $cm-font-family;
	}

	view,
	text,
	button,
	input,
	image {
		box-sizing: border-box;
	}

	button {
		margin: 0;
		padding: 0;
		border: none;
		background: transparent;
		line-height: 1.2;
	}

	button::after {
		border: none;
	}

	button {
		transition: opacity 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
	}

	button:active {
		opacity: 0.78;
	}

	button:focus-visible {
		outline: 3rpx solid rgba(47, 69, 56, 0.72);
		outline-offset: 3rpx;
	}

	image {
		display: block;
	}

	@media (prefers-reduced-motion: reduce) {
		*,
		*::before,
		*::after {
			animation-duration: 0.01ms !important;
			animation-iteration-count: 1 !important;
			transition-duration: 0.01ms !important;
			scroll-behavior: auto !important;
		}
	}
</style>
