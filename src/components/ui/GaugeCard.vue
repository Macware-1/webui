<template>
  <div class="gauge-card">
    <svg viewBox="0 0 200 165" class="gauge-svg">
      <path :d="ARC_PATH" fill="none" stroke="#1a2a3a" stroke-width="10" stroke-linecap="round"/>
      <path :d="ARC_PATH" fill="none" :stroke="color" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="dashArray" :stroke-dashoffset="dashOffset" class="arc-fill"/>
      <text x="100" y="90" text-anchor="middle" class="g-val">{{ valText }}</text>
      <text x="100" y="108" text-anchor="middle" class="g-unit">{{ unit }}</text>
      <text x="100" y="146" text-anchor="middle" class="g-title">{{ title }}</text>
      <text x="28" y="157" text-anchor="middle" class="g-minmax">0</text>
      <text x="172" y="157" text-anchor="middle" class="g-minmax">{{ max }}</text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  value: Number,
  max: Number,
  unit: String,
  color: String,
})

const ARC_PATH = 'M 46.3 151.7 A 76 76 0 1 1 153.7 151.7'
const ARC_LEN = 358.1

const pct = computed(() => Math.min(Math.max((props.value || 0) / props.max, 0), 1))
const dashOffset = computed(() => ARC_LEN * (1 - pct.value))
const dashArray = `${ARC_LEN} 999`
const valText = computed(() => (props.value || 0).toFixed(0))
</script>

<style scoped>
.gauge-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 8px 8px;
}
.gauge-svg { width: 100%; display: block; }
.arc-fill {
  transition: stroke-dashoffset 0.7s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.4s ease;
}
.g-val { font-size: 34px; font-weight: 700; fill: var(--text); font-family: inherit; }
.g-unit { font-size: 13px; fill: var(--muted); font-family: inherit; }
.g-title { font-size: 12px; fill: var(--muted); font-family: inherit; }
.g-minmax { font-size: 10px; fill: #2a3f58; font-family: inherit; }
</style>
