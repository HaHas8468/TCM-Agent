<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <section class="base-card">
    <header v-if="title || subtitle" class="base-card__header">
      <div>
        <h3 v-if="title" class="base-card__title">{{ title }}</h3>
        <p v-if="subtitle" class="base-card__subtitle">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </header>

    <div class="base-card__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.base-card {
  border: 1px solid var(--border-soft);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 36px rgba(45, 106, 79, 0.08);
  backdrop-filter: blur(12px);
}

.base-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 22px 22px 0;
}

.base-card__title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
}

.base-card__subtitle {
  margin: 6px 0 0;
  color: var(--text-subtle);
  font-size: 13px;
  line-height: 1.6;
}

.base-card__body {
  padding: 22px;
}
</style>
