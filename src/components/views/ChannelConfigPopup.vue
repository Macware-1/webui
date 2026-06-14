<template>
  <Teleport to="body">
    <div v-if="chanPopup.open" class="popup-overlay" @click.self="close">
      <div class="popup-card">
        <div class="popup-header">
          <span class="popup-title">CAN Channel {{ chanPopup.ch }}</span>
          <button class="popup-close" @click="close">✕</button>
        </div>

        <div class="popup-section">
          <div class="popup-section-title">Channel Logging</div>
          <div class="logging-row">
            <div class="field-group">
              <label class="field-label">Logging ID (0–255)</label>
              <input v-model.number="popupEdit.logging_id" type="number" min="0" max="255"
                     class="text-input" style="width:120px"/>
              <p class="mode-desc" style="margin-top:4px;margin-bottom:0">
                This ID is embedded in every forwarded frame.
              </p>
            </div>
            <div class="field-group logging-enabled-group">
              <label class="field-label">Logging</label>
              <label class="toggle-switch">
                <input type="checkbox" v-model="enabledToggle" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <label class="field-label" style="display:block;margin:20px 0 10px">Logging Target</label>
          <div class="target-row">
            <button type="button" :class="['target-btn', { 'target-active': popupEdit.target === 0 }]"
                    @click="openEthernet()">
              <span class="target-icon">🌐</span>
              <span class="target-name">Ethernet</span>
            </button>
            <button type="button" :class="['target-btn', { 'target-active': popupEdit.target === 1 }]"
                    @click="popupEdit.target = 1">
              <span class="target-icon">🔌</span>
              <span class="target-name">USB ECM</span>
            </button>
            <button type="button" class="target-btn target-disabled" disabled title="Coming soon">
              <span class="target-icon">🔷</span>
              <span class="target-name">Bluetooth</span>
            </button>
          </div>
        </div>

        <div class="popup-section">
          <div class="popup-section-title">CAN Bus Configuration</div>

          <div class="cfg-card">
            <div class="info-card-title">General CAN Settings</div>
            <div class="cfg-grid">
              <div class="rule-field">
                <label class="field-label">Mode</label>
                <select v-model.number="popupEdit.j1939" class="text-input">
                  <option :value="0">Raw CAN</option>
                  <option :value="1">J1939</option>
                </select>
              </div>
              <div class="rule-field">
                <label class="field-label">Default CAN ID (hex)</label>
                <input v-model="popupEdit.id_hex" class="text-input mono" placeholder="00000000" />
              </div>
              <div class="rule-field">
                <label class="field-label">DLC</label>
                <input v-model.number="popupEdit.dlc" type="number" min="0" max="8" class="text-input" />
              </div>
            </div>
          </div>

          <div class="cfg-card">
            <div class="info-card-title">Nominal Speed Preset</div>
            <div class="preset-row">
              <button class="preset-btn" type="button" @click="applyNomPreset(8,59,20,20)">125 kbps</button>
              <button class="preset-btn" type="button" @click="applyNomPreset(4,59,20,20)">250 kbps</button>
              <button class="preset-btn" type="button" @click="applyNomPreset(2,59,20,20)">500 kbps</button>
              <button class="preset-btn" type="button" @click="applyNomPreset(1,59,20,20)">1 Mbps</button>
            </div>
            <div class="info-card-title" style="margin-top:16px">Data Speed Preset (CAN FD)</div>
            <div class="preset-row">
              <button class="preset-btn" type="button" @click="applyDataPreset(2,31,8,4)">1 Mbps</button>
              <button class="preset-btn" type="button" @click="applyDataPreset(2,15,4,4)">2 Mbps</button>
              <button class="preset-btn" type="button" @click="applyDataPreset(1,15,4,4)">4 Mbps</button>
              <button class="preset-btn" type="button" @click="applyDataPreset(1,12,3,2)">5 Mbps</button>
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
                <label class="field-label">Prescaler (NBRP)</label>
                <input v-model.number="popupEdit.nbrp" type="number" min="1" max="512" class="text-input" />
              </div>
              <div class="rule-field">
                <label class="field-label">Tseg1 (NTSEG1)</label>
                <input v-model.number="popupEdit.ntseg1" type="number" min="1" max="255" class="text-input" />
              </div>
              <div class="rule-field">
                <label class="field-label">Tseg2 (NTSEG2)</label>
                <input v-model.number="popupEdit.ntseg2" type="number" min="1" max="127" class="text-input" />
              </div>
              <div class="rule-field">
                <label class="field-label">SJW (NSJW)</label>
                <input v-model.number="popupEdit.nsjw" type="number" min="1" max="127" class="text-input" />
              </div>
            </div>
          </div>

          <div class="cfg-card">
            <div class="info-card-title">Data Phase Timing (CAN FD)</div>
            <div class="cfg-grid">
              <div class="rule-field">
                <label class="field-label">Prescaler (DBRP)</label>
                <input v-model.number="popupEdit.dbrp" type="number" min="1" max="32" class="text-input" />
              </div>
              <div class="rule-field">
                <label class="field-label">Tseg1 (DTSEG1)</label>
                <input v-model.number="popupEdit.dtseg1" type="number" min="1" max="32" class="text-input" />
              </div>
              <div class="rule-field">
                <label class="field-label">Tseg2 (DTSEG2)</label>
                <input v-model.number="popupEdit.dtseg2" type="number" min="1" max="16" class="text-input" />
              </div>
              <div class="rule-field">
                <label class="field-label">SJW (DSJW)</label>
                <input v-model.number="popupEdit.dsjw" type="number" min="1" max="16" class="text-input" />
              </div>
            </div>
          </div>

          <div class="cfg-card">
            <div class="info-card-title">Frame Mode</div>
            <div class="cfg-grid">
              <div class="rule-field">
                <label class="field-label">CAN FD</label>
                <select v-model.number="popupEdit.fd_mode" class="text-input">
                  <option :value="1">Enabled</option>
                  <option :value="0">Disabled</option>
                </select>
              </div>
              <div class="rule-field">
                <label class="field-label">Bit-rate Switching (BRS)</label>
                <label class="toggle-switch" :class="{ disabled: !popupEdit.fd_mode }">
                  <input type="checkbox" v-model="brsToggle" :disabled="!popupEdit.fd_mode" />
                  <span class="toggle-slider"></span>
                </label>
              </div>
              <div class="rule-field">
                <label class="field-label">ACK Mode</label>
                <select v-model.number="popupEdit.listen_only" class="text-input">
                  <option :value="0">Active (ACK frames)</option>
                  <option :value="1">Listen-only</option>
                </select>
              </div>
            </div>
            <div class="mode-desc" style="margin-top: 12px">
              These CAN bus settings apply globally and are shared for both CAN Channel 1 and 2.
            </div>
          </div>
        </div>

        <div class="popup-actions">
          <button class="preset-btn" style="background:var(--primary);color:#fff;border-color:var(--primary)"
                  @click="apply">Apply</button>
          <button class="preset-btn" @click="close">Cancel</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { defineProps, defineEmits, computed } from 'vue'

const props = defineProps({
  chanPopup: Object,
  popupEdit: Object,
})
const emit = defineEmits(['close', 'apply', 'open-ethernet'])

const enabledToggle = computed({
  get: () => props.popupEdit.enabled === 1,
  set: v => { props.popupEdit.enabled = v ? 1 : 0 }
})
const brsToggle = computed({
  get: () => props.popupEdit.brs === 1,
  set: v => { props.popupEdit.brs = v ? 1 : 0 }
})

function close() {
  emit('close')
}

function apply() {
  emit('apply')
}

function applyNomPreset(nbrp, ntseg1, ntseg2, nsjw) {
  props.popupEdit.nbrp = nbrp
  props.popupEdit.ntseg1 = ntseg1
  props.popupEdit.ntseg2 = ntseg2
  props.popupEdit.nsjw = nsjw
}

function applyDataPreset(dbrp, dtseg1, dtseg2, dsjw) {
  props.popupEdit.dbrp = dbrp
  props.popupEdit.dtseg1 = dtseg1
  props.popupEdit.dtseg2 = dtseg2
  props.popupEdit.dsjw = dsjw
}

function openEthernet() {
  props.popupEdit.target = 0
  emit('open-ethernet')
}

function fmtHz(hz) {
  if (hz >= 1e6) return (hz / 1e6).toFixed(3).replace(/\.?0+$/, '') + ' Mbps'
  if (hz >= 1e3) return (hz / 1e3).toFixed(1).replace(/\.?0+$/, '') + ' kbps'
  return hz + ' bps'
}

const nomBitrate = computed(() => {
  const tq = 1 + props.popupEdit.ntseg1 + props.popupEdit.ntseg2
  return fmtHz(80e6 / (props.popupEdit.nbrp * tq))
})
const nomSamplePt = computed(() => {
  const tq = 1 + props.popupEdit.ntseg1 + props.popupEdit.ntseg2
  return ((1 + props.popupEdit.ntseg1) / tq * 100).toFixed(1) + '%'
})
const dataBitrate = computed(() => {
  const tq = 1 + props.popupEdit.dtseg1 + props.popupEdit.dtseg2
  return fmtHz(80e6 / (props.popupEdit.dbrp * tq))
})
const dataSamplePt = computed(() => {
  const tq = 1 + props.popupEdit.dtseg1 + props.popupEdit.dtseg2
  return ((1 + props.popupEdit.dtseg1) / tq * 100).toFixed(1) + '%'
})
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.popup-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 28px 24px;
  width: 720px;
  max-width: 95vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}
.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.popup-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
}
.popup-close {
  background: none;
  border: none;
  color: var(--muted);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: color 0.15s;
}
.popup-close:hover {
  color: var(--text);
}
.target-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.target-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--dim);
  color: var(--text);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
  min-width: 120px;
}
.target-btn:hover:not(:disabled) {
  border-color: var(--primary);
  transform: translateY(-1px);
}
.target-active {
  border-color: var(--primary) !important;
  background: rgba(59, 130, 246, 0.12) !important;
}
.target-disabled {
  opacity: 0.38;
  cursor: not-allowed !important;
}
.target-icon {
  font-size: 16px;
}
.target-name {
  font-size: 13px;
  font-weight: 600;
}
.target-soon {
  font-size: 10px;
  color: var(--muted);
}
.radio-row {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.radio-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
}
.radio-inline input {
  width: 14px;
  height: 14px;
}
.logging-row {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(180px, 1fr);
  gap: 16px;
  align-items: end;
}
.logging-enabled-group {
  display: flex;
  flex-direction: column;
}
.popup-section {
  margin-bottom: 22px;
}
.popup-section-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text);
}
.cfg-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 12px;
}
.info-card-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--muted);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.preset-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.preset-btn {
  padding: 7px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--dim);
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.preset-btn:hover {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.timing-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.timing-info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.timing-info-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--muted);
}
.timing-info-val {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}
.cfg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.rule-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--muted);
}
.text-input {
  width: 100%;
  padding: 9px 12px;
  background: var(--dim);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}
.text-input:focus {
  border-color: var(--primary);
}
.text-input.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
.toggle-switch { position: relative; display: inline-block; width: 48px; height: 26px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; inset: 0; background: var(--dim); border: 1px solid var(--border); border-radius: 13px; transition: background 0.2s, border-color 0.2s; }
.toggle-slider::before { content: ''; position: absolute; width: 18px; height: 18px; left: 3px; top: 3px; background: var(--muted); border-radius: 50%; transition: transform 0.2s, background 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: rgba(59,130,246,0.25); border-color: var(--primary); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(22px); background: var(--primary); }
.toggle-switch.disabled { opacity: 0.4; }
.mode-desc {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.55;
}
.popup-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
  justify-content: flex-end;
}
</style>
