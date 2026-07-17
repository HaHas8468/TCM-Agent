<script setup>
defineProps({
  type: {
    type: String,
    default: ''
  },
  item: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['close'])
</script>

<template>
  <div class="dialog">
    <div class="dialog__backdrop" @click="$emit('close')" />
    <section class="dialog__panel">
      <div class="pill">{{ type }}详情</div>
      <h3>{{ item.name }}</h3>
      <p class="dialog__summary">{{ item.summary }}</p>
      <div class="dialog__detail">
        <strong>二次检索结果</strong>
        <p>{{ item.detail }}</p>
      </div>
      <button type="button" class="primary-button" @click="$emit('close')">关闭弹窗</button>
    </section>
  </div>
</template>

<style scoped>
.dialog {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
}

.dialog__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(12, 28, 43, 0.48);
}

.dialog__panel {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 16px;
  width: min(560px, calc(100vw - 32px));
  padding: 28px;
  border-radius: 28px;
  background: #fff;
  box-shadow: 0 32px 64px rgba(12, 28, 43, 0.22);
}

.dialog__panel h3,
.dialog__summary,
.dialog__detail strong,
.dialog__detail p {
  margin: 0;
  line-height: 1.8;
}

.dialog__summary,
.dialog__detail p {
  color: var(--text-subtle);
}

.dialog__detail {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: var(--bg-soft);
}
</style>
