<template>
  <section class="content-panel">
    <div class="panel-head">
      <h2 class="panel-title">CAN Replay</h2>
      <span class="count-badge">Inject frames onto CAN bus</span>
    </div>

    <div class="cfg-card">
      <div class="cfg-row">
        <label class="cfg-label">CAN ID (hex)</label>
        <input v-model="inject.id" class="text-input mono" placeholder="0x123" maxlength="12" spellcheck="false" />
      </div>
      <div class="cfg-row">
        <label class="cfg-label">Frame Type</label>
        <div class="radio-row">
          <label class="radio-opt"><input type="radio" v-model="inject.fd" :value="false" /> Classic CAN</label>
          <label class="radio-opt"><input type="radio" v-model="inject.fd" :value="true" /> CAN FD</label>
        </div>
      </div>
      <div class="cfg-row" v-if="inject.fd">
        <label class="cfg-label">Bit-Rate Switch</label>
        <label class="toggle-switch">
          <input type="checkbox" v-model="inject.brs" />
          <span class="toggle-slider"></span>
        </label>
      </div>
      <div class="cfg-row">
        <label class="cfg-label">Data (hex bytes)</label>
        <input v-model="inject.data" class="text-input mono"
               :placeholder="inject.fd ? 'up to 64 bytes, e.g. 0102030405060708' : 'up to 8 bytes, e.g. 0102030405060708'"
               maxlength="128" spellcheck="false" />
      </div>
      <div class="cfg-row">
        <label class="cfg-label">DLC (auto)</label>
        <span class="mono" style="color: var(--accent);">{{ injectDlc }}</span>
      </div>
      <div>
        <button class="btn btn-primary" @click="$emit('send-can-frame')" :disabled="inject.sending">
          {{ inject.sending ? 'Sending…' : 'Send Frame' }}
        </button>
      </div>
      <div v-if="inject.result" :class="['inject-result', inject.ok ? 'inject-ok' : 'inject-err']" style="margin-top:12px">
        {{ inject.result }}
      </div>
    </div>

    <div class="cfg-card" style="margin-top:16px">
      <div class="info-card-title">UDP Injection (port 4000)</div>
      <p class="boot-desc">
        Send a raw binary UDP datagram to <strong>{{ system.ip }}:4000</strong> to inject a CAN frame without HTTP overhead.
      </p>
      <table class="data-table" style="margin-top:8px">
        <thead><tr><th>Offset</th><th>Size</th><th>Field</th></tr></thead>
        <tbody>
          <tr><td class="mono">0–3</td><td>4 B</td><td>CAN ID (LE, bit30=extended)</td></tr>
          <tr><td class="mono">4</td><td>1 B</td><td>DLC (0–15)</td></tr>
          <tr><td class="mono">5</td><td>1 B</td><td>Flags (bit0=FD, bit1=BRS)</td></tr>
          <tr><td class="mono">6–7</td><td>2 B</td><td>Reserved (0x0000)</td></tr>
          <tr><td class="mono">8+</td><td>N B</td><td>Payload (dlc_to_len(DLC) bytes)</td></tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  inject: Object,
  injectDlc: String,
  system: Object,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.panel-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }
.count-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: rgba(59,130,246,0.15); color: #60a5fa; }
.cfg-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; max-width: 540px; }
.cfg-row { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.cfg-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.text-input { width: 100%; padding: 9px 12px; background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.15s; }
.text-input:focus { border-color: var(--primary); }
.radio-row { display: flex; align-items: center; gap: 8px; }
.radio-opt { display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text); cursor: pointer; }
.toggle-switch { position: relative; display: inline-block; width: 48px; height: 26px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; inset: 0; background: var(--dim); border: 1px solid var(--border); border-radius: 13px; transition: background 0.2s, border-color 0.2s; }
.toggle-slider::before { content: ''; position: absolute; width: 18px; height: 18px; left: 3px; top: 3px; background: var(--muted); border-radius: 50%; transition: transform 0.2s, background 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: rgba(59,130,246,0.25); border-color: var(--primary); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(22px); background: var(--primary); }
.btn { width: 100%; padding: 11px; border: none; border-radius: var(--radius-sm); font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s, transform 0.1s; }
.btn:hover { opacity: 0.88; }
.btn:active { transform: scale(0.98); }
.btn-primary { background: var(--primary); color: #fff; }
.inject-result { font-size: 14px; font-weight: 600; padding: 8px 12px; border-radius: 6px; }
.inject-ok { color: #34d399; background: rgba(52,211,153,.1); }
.inject-err { color: #f87171; background: rgba(248,113,113,.1); }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { text-align: left; padding: 10px 12px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); border-bottom: 1px solid var(--border); }
.data-table td { padding: 11px 12px; font-size: 14px; border-bottom: 1px solid var(--dim); }
.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.boot-desc { font-size: 13px; color: var(--muted); line-height: 1.6; }
</style>
