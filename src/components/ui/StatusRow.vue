<template>
  <div class="status-row">
    <span :class="['s-dot', { 's-on': on }]" />
    <span class="s-label">{{ label }}</span>
    <span :class="['s-pill', { 's-pill-on': on }]">{{ on ? 'ON' : 'OFF' }}</span>
  </div>
</template>

<script setup>
const props = defineProps({
  label: String,
  on: Boolean,
})
</script>

<style scoped>
.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.s-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  flex-shrink: 0;
}
.s-dot.s-on { background: var(--success); box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.s-label { flex: 1; font-size: 13px; color: var(--text); }
.s-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  background: rgba(239,68,68,0.15);
  color: #f87171;
}
.s-pill.s-pill-on { background: rgba(16,185,129,0.15); color: #34d399; }
</style>
