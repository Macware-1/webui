<template>
  <section class="content-panel">
    <div class="cfg-card">
      <div class="info-card-title">Nominal Speed Preset (PLL2Q = 80 MHz)</div>
      <div class="preset-row">
        <button class="preset-btn" @click="$emit('apply-nom-preset', 8,59,20,20)">125 kbps</button>
        <button class="preset-btn" @click="$emit('apply-nom-preset', 4,59,20,20)">250 kbps</button>
        <button class="preset-btn" @click="$emit('apply-nom-preset', 2,59,20,20)">500 kbps</button>
        <button class="preset-btn" @click="$emit('apply-nom-preset', 1,59,20,20)">1 Mbps</button>
      </div>
      <div class="info-card-title" style="margin-top:16px">Data Speed Preset (CAN FD)</div>
      <div class="preset-row">
        <button class="preset-btn" @click="$emit('apply-data-preset', 2,31,8,4)">1 Mbps</button>
        <button class="preset-btn" @click="$emit('apply-data-preset', 2,15,4,4)">2 Mbps</button>
        <button class="preset-btn" @click="$emit('apply-data-preset', 1,15,4,4)">4 Mbps</button>
        <button class="preset-btn" @click="$emit('apply-data-preset', 1,12,3,2)">5 Mbps</button>
      </div>
    </div>

    <div class="cfg-card">
      <div class="info-card-title">Computed Parameters</div>
      <div class="timing-info-grid">
        <div class="timing-info-item">
          <span class="timing-info-label">Nominal bit rate</span>
          <span class="timing-info-val">{{ nomBitrate }}</span>
        </div>
        <div class="timing-info-item">
          <span class="timing-info-label">Nominal sample point</span>
          <span class="timing-info-val">{{ nomSamplePt }}</span>
        </div>
        <div class="timing-info-item">
          <span class="timing-info-label">Data bit rate</span>
          <span class="timing-info-val">{{ dataBitrate }}</span>
        </div>
        <div class="timing-info-item">
          <span class="timing-info-label">Data sample point</span>
          <span class="timing-info-val">{{ dataSamplePt }}</span>
        </div>
      </div>
    </div>

    <div class="cfg-card">
      <div class="info-card-title">Nominal Phase Timing</div>
      <div class="cfg-grid">
        <div class="rule-field">
          <label class="field-label">Prescaler (NBRP) 1–512</label>
          <input v-model.number="cfg.can.nbrp" type="number" min="1" max="512" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">Tseg1 (NTSEG1) 1–255</label>
          <input v-model.number="cfg.can.ntseg1" type="number" min="1" max="255" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">Tseg2 (NTSEG2) 1–127</label>
          <input v-model.number="cfg.can.ntseg2" type="number" min="1" max="127" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">SJW (NSJW) 1–127</label>
          <input v-model.number="cfg.can.nsjw" type="number" min="1" max="127" class="text-input" />
        </div>
      </div>
    </div>

    <div class="cfg-card">
      <div class="info-card-title">Data Phase Timing (CAN FD)</div>
      <div class="cfg-grid">
        <div class="rule-field">
          <label class="field-label">Prescaler (DBRP) 1–32</label>
          <input v-model.number="cfg.can.dbrp" type="number" min="1" max="32" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">Tseg1 (DTSEG1) 1–32</label>
          <input v-model.number="cfg.can.dtseg1" type="number" min="1" max="32" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">Tseg2 (DTSEG2) 1–16</label>
          <input v-model.number="cfg.can.dtseg2" type="number" min="1" max="16" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">SJW (DSJW) 1–16</label>
          <input v-model.number="cfg.can.dsjw" type="number" min="1" max="16" class="text-input" />
        </div>
      </div>
    </div>

    <div class="cfg-card">
      <div class="info-card-title">Frame Mode</div>
      <div class="cfg-grid">
        <div class="rule-field">
          <label class="field-label">CAN FD</label>
          <select v-model.number="cfg.can.fd_mode" class="text-input">
            <option :value="1">Enabled</option>
            <option :value="0">Disabled (classic CAN)</option>
          </select>
        </div>
        <div class="rule-field">
          <label class="field-label">Bit-Rate Switching (BRS)</label>
          <select v-model.number="cfg.can.brs" class="text-input" :disabled="!cfg.can.fd_mode">
            <option :value="1">Enabled</option>
            <option :value="0">Disabled</option>
          </select>
        </div>
        <div class="rule-field">
          <label class="field-label">ACK Mode</label>
          <select v-model.number="cfg.can.listen_only" class="text-input">
            <option :value="0">Active (ACK frames)</option>
            <option :value="1">Listen-only (no ACK, passive)</option>
          </select>
        </div>
      </div>
      <p class="mode-desc">Click <strong>Save &amp; Apply Config</strong> in the sidebar to write these settings to flash and reboot.</p>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  cfg: Object,
  nomBitrate: String,
  nomSamplePt: String,
  dataBitrate: String,
  dataSamplePt: String,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.cfg-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 12px; }
.info-card-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.preset-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.preset-btn { padding: 7px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--dim); color: var(--text); font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s, border-color 0.15s; }
.preset-btn:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
.timing-info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 12px; }
.timing-info-item { display: flex; flex-direction: column; gap: 4px; }
.timing-info-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.timing-info-val { font-size: 18px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.cfg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 12px; }
.rule-field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.text-input { width: 100%; padding: 9px 12px; background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.15s; }
.text-input:focus { border-color: var(--primary); }
.mode-desc { font-size: 13px; color: var(--muted); line-height: 1.55; }
</style>
