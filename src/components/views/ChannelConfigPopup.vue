<template>
  <Teleport to="body">
    <div v-if="chanPopup.open" class="popup-overlay" @click.self="close">
      <div class="popup-card">
        <div class="popup-header">
          <span class="popup-title">CAN Channel {{ chanPopup.ch }}</span>
          <button class="popup-close" @click="close">✕</button>
        </div>

        <label class="field-label" style="display:block;margin-bottom:6px">Logging ID (0–255)</label>
        <input v-model.number="popupEdit.logging_id" type="number" min="0" max="255"
               class="text-input" style="width:120px"/>
        <p class="mode-desc" style="margin-top:4px;margin-bottom:20px">
          This ID is embedded in every forwarded frame so the host can identify the source channel.
        </p>

        <label class="field-label" style="display:block;margin-bottom:10px">Logging Target</label>
        <div class="target-row">
          <button :class="['target-btn', { 'target-active': popupEdit.target === 0 }]"
                  @click="popupEdit.target = 0">
            <span class="target-icon">🌐</span>
            <span class="target-name">Ethernet</span>
          </button>
          <button :class="['target-btn', { 'target-active': popupEdit.target === 1 }]"
                  @click="popupEdit.target = 1">
            <span class="target-icon">🔌</span>
            <span class="target-name">USB ECM</span>
          </button>
          <button class="target-btn target-disabled" disabled title="Coming soon">
            <span class="target-icon">🔷</span>
            <span class="target-name">Bluetooth</span>
            <span class="target-soon">Soon</span>
          </button>
        </div>

        <label class="field-label" style="display:block;margin:20px 0 6px">Logging</label>
        <select v-model.number="popupEdit.enabled" class="text-input" style="width:160px">
          <option :value="1">Enabled</option>
          <option :value="0">Disabled</option>
        </select>

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
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  chanPopup: Object,
  popupEdit: Object,
})
const emit = defineEmits(['close', 'apply'])

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
  width: 420px;
  max-width: 95vw;
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
}
.target-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--border);
  background: var(--dim);
  color: var(--text);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.target-btn:hover:not(:disabled) {
  border-color: var(--primary);
}
.target-active {
  border-color: var(--primary) !important;
  background: #0d2244 !important;
}
.target-disabled {
  opacity: 0.38;
  cursor: not-allowed !important;
}
.target-icon {
  font-size: 22px;
}
.target-name {
  font-size: 12px;
  font-weight: 600;
}
.target-soon {
  font-size: 10px;
  color: var(--muted);
}
.popup-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
  justify-content: flex-end;
}
</style>
