<template>
  <Teleport to="body">
    <div v-if="ethPopup.open" class="popup-overlay" @click.self="close">
      <div class="popup-card">
        <div class="popup-header">
          <span class="popup-title">Ethernet Configuration</span>
          <button class="popup-close" @click="close">✕</button>
        </div>

        <div class="popup-section">
          <div class="popup-section-title">Network Configuration</div>
          <div class="cfg-grid">
            <div class="rule-field">
              <label class="field-label">ETH IP</label>
              <input v-model="ethPopupEdit.eth_ip" class="text-input mono" placeholder="10.104.3.64" />
            </div>
            <div class="rule-field">
              <label class="field-label">Subnet Mask</label>
              <input v-model="ethPopupEdit.eth_mask" class="text-input mono" placeholder="255.255.255.0" />
            </div>
            <div class="rule-field">
              <label class="field-label">Gateway</label>
              <input v-model="ethPopupEdit.eth_gw" class="text-input mono" placeholder="10.104.3.1" />
            </div>
            <div class="rule-field">
              <label class="field-label">USB IP</label>
              <input v-model="ethPopupEdit.usb_ip" class="text-input mono" placeholder="192.168.7.64" />
            </div>
          </div>
        </div>

        <div class="popup-section">
          <div class="popup-section-title">Precision Time Protocol</div>
          <div class="cfg-card">
            <div class="ptp-row">
              <div>
                <div class="ptp-label">{{ ptpLabel }}</div>
                <div class="ptp-desc">{{ ptpDesc }}</div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" v-model.number="props.ethPopupEdit.ptp_enable" :true-value="1" :false-value="0" />
                <span class="toggle-slider"></span>
              </label>
            </div>
            <p class="mode-desc">Toggle takes effect after <strong>Save & Apply Config</strong>.</p>
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
  ethPopup: Object,
  ethPopupEdit: Object,
})
const emit = defineEmits(['close', 'apply'])

const ptpLabel = computed(() => props.ethPopupEdit.ptp_enable ? 'Enabled' : 'Disabled')
const ptpDesc = computed(() => props.ethPopupEdit.ptp_enable
  ? 'Hardware timestamp sync active'
  : 'No PTP frames sent — task is idle')

function close() {
  emit('close')
}

function apply() {
  emit('apply')
}
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
  width: 700px;
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
.popup-close:hover { color: var(--text); }
.popup-section { margin-bottom: 22px; }
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
.cfg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.rule-field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.text-input { width: 100%; padding: 9px 12px; background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.15s; }
.text-input:focus { border-color: var(--primary); }
.text-input.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.ptp-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 8px; }
.ptp-label { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.ptp-desc { font-size: 13px; color: var(--muted); line-height: 1.5; }
.toggle-switch { position: relative; display: inline-block; width: 48px; height: 26px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; inset: 0; background: var(--dim); border: 1px solid var(--border); border-radius: 13px; transition: background 0.2s, border-color 0.2s; }
.toggle-slider::before { content: ''; position: absolute; width: 18px; height: 18px; left: 3px; top: 3px; background: var(--muted); border-radius: 50%; transition: transform 0.2s, background 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: rgba(59,130,246,0.25); border-color: var(--primary); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(22px); background: var(--primary); }
.mode-desc { font-size: 13px; color: var(--muted); line-height: 1.55; }
.popup-actions { display: flex; gap: 10px; margin-top: 24px; justify-content: flex-end; }
.preset-btn { padding: 7px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--dim); color: var(--text); font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s, border-color 0.15s; }
.preset-btn:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
</style>
