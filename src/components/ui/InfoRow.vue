<template>
  <div class="info-row">
    <span class="ir-label">{{ label }}</span>
    <slot name="val"><span class="ir-value">{{ value || '—' }}</span></slot>
  </div>
</template>

<script setup>
const props = defineProps({
  label: String,
  value: [String, Number],
})
</script>

<style scoped>
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.ir-label { color: var(--muted); }
.ir-value { font-weight: 600; font-family: monospace; font-size: 13px; }
</style>
