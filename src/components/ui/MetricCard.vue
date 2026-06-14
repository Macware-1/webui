<template>
  <div :class="['metric-card', { 'metric-warn': warn }]">
    <div class="metric-icon">{{ icon }}</div>
    <div class="metric-val">{{ value }}<span class="metric-unit"> {{ unit }}</span></div>
    <div class="metric-label">{{ label }}</div>
  </div>
</template>

<script setup>
const props = defineProps({
  icon: String,
  label: String,
  value: [String, Number],
  unit: String,
  warn: Boolean,
})
</script>

<style scoped>
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color 0.3s;
}
.metric-card.metric-warn { border-color: var(--warning); }
.metric-icon { font-size: 22px; }
.metric-val { font-size: 26px; font-weight: 700; line-height: 1; }
.metric-unit { font-size: 14px; font-weight: 400; color: var(--muted); }
.metric-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
</style>
