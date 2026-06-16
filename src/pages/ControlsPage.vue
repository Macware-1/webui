<template>
  <section class="content-panel">
    <div class="panel-head"><h2 class="panel-title">Control Panel</h2></div>
    <div class="controls-grid">
      <div class="ctrl-card">
        <div class="ctrl-title">Throttle</div>
        <div class="ctrl-bigval">{{ localThrottle }}<span class="ctrl-unit">%</span></div>
        <input type="range" v-model="localThrottle" min="0" max="100" class="slider" />
        <button class="btn btn-primary" @click="$emit('send-throttle', localThrottle)">Send Throttle</button>
      </div>

      <div class="ctrl-card">
        <div class="ctrl-title">Engine Control</div>
        <button class="btn btn-success" @click="$emit('send-control',{type:'control',engine:'start'})">▶ Start Engine</button>
        <button class="btn btn-danger" @click="$emit('send-control',{type:'control',engine:'stop'})">■ Stop Engine</button>
      </div>

      <div class="ctrl-card">
        <div class="ctrl-title">Raw J1939 TX</div>
        <input v-model="localTx.pgn" class="text-input" placeholder="PGN  e.g. 61444" />
        <input v-model="localTx.data" class="text-input" placeholder="8-byte hex data" />
        <button class="btn btn-primary" @click="$emit('send-frame')">📡 Send Frame</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({
  throttle: Number,
  tx: Object,
})
const emit = defineEmits(['update:throttle', 'update:tx', 'send-throttle', 'send-control', 'send-frame'])
const localThrottle = ref(props.throttle)
const localTx = ref({ pgn: props.tx?.pgn || '', data: props.tx?.data || '' })

watch(() => props.throttle, (value) => { localThrottle.value = value })
watch(localThrottle, (value) => { emit('update:throttle', value) })
watch(
  () => props.tx,
  (value) => { localTx.value = { pgn: value?.pgn || '', data: value?.data || '' } },
  { deep: true }
)
watch(
  localTx,
  (value) => { emit('update:tx', { ...(props.tx || {}), ...value }) },
  { deep: true }
)
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.panel-head { margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }
.controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.ctrl-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ctrl-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); }
.ctrl-bigval { font-size: 42px; font-weight: 700; line-height: 1; }
.ctrl-unit { font-size: 20px; font-weight: 400; color: var(--muted); }
.slider {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: var(--dim);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 8px rgba(59,130,246,0.5);
}
</style>
