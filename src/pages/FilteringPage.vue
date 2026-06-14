<template>
  <section class="content-panel">
    <div class="cfg-card">
      <div class="info-card-title">CAN Configuration</div>
      <div class="cfg-grid">
        <div class="rule-field">
          <label class="field-label">Mode</label>
          <select v-model.number="cfg.can.j1939" class="text-input">
            <option :value="1">J1939 Stack</option>
            <option :value="0">Raw CAN</option>
          </select>
        </div>
        <div class="rule-field">
          <label class="field-label">Default DLC (0–8)</label>
          <input v-model.number="cfg.can.dlc" type="number" min="0" max="8" class="text-input" />
        </div>
        <div class="rule-field">
          <label class="field-label">Default CAN ID (hex)</label>
          <input v-model="cfg.can.id_hex" class="text-input mono" placeholder="00000000" />
        </div>
      </div>
    </div>

    <div class="cfg-card">
      <div class="info-card-title">USB Configuration</div>
      <div class="rule-field" style="max-width:260px">
        <label class="field-label">USB Mode</label>
        <select v-model.number="cfg.usb.usbmode" class="text-input">
          <option :value="0">RNDIS (Windows)</option>
          <option :value="1">ECM (Linux / macOS)</option>
        </select>
      </div>
    </div>

    <div class="panel-head" style="margin-top:24px;margin-bottom:12px">
      <h2 class="panel-title">CAN Filter Rules</h2>
      <span class="count-badge">{{ activeRuleCount }} active</span>
    </div>
    <p class="mode-desc" style="margin-bottom:16px">
      Rules are evaluated in slot order; first match wins. Set Action to <em>Disabled</em> to skip a slot.
    </p>

    <div v-for="(slot, idx) in RULE_SLOTS" :key="slot" class="rule-card">
      <div class="rule-card-head">
        <span class="rule-slot-num">Slot {{ idx }}</span>
        <select v-model.number="cfg.filters[slot].action" class="text-input rule-action-sel">
          <option :value="0">Disabled</option>
          <option :value="1">DROP</option>
          <option :value="2">REMAP</option>
          <option :value="3">EVENT</option>
        </select>
        <span v-if="cfg.filters[slot].action === 0" class="rule-disabled-lbl">— not active —</span>
      </div>

      <div v-if="cfg.filters[slot].action !== 0" class="rule-fields-grid">
        <div class="rule-field">
          <label class="field-label">CAN ID (hex)</label>
          <input v-model="cfg.filters[slot].can_id_hex" class="text-input mono" placeholder="00000000" />
        </div>
        <div class="rule-field">
          <label class="field-label">Mask (hex)</label>
          <input v-model="cfg.filters[slot].mask_hex" class="text-input mono" placeholder="1FFFFFFF" />
        </div>

        <template v-if="cfg.filters[slot].action === 2">
          <div class="rule-field">
            <label class="field-label">Remap CAN ID (hex)</label>
            <input v-model="cfg.filters[slot].remap_id_hex" class="text-input mono" placeholder="00000000" />
          </div>
          <div class="rule-field">
            <label class="field-label">Remap Payload (hex, opt.)</label>
            <input v-model="cfg.filters[slot].rpayload_hex" class="text-input mono" placeholder="0000000000000000" />
          </div>
          <div class="rule-field">
            <label class="field-label">Remap DLC (0=keep)</label>
            <input v-model.number="cfg.filters[slot].rdlc" type="number" min="0" max="8" class="text-input" style="max-width:90px" />
          </div>
        </template>

        <template v-if="cfg.filters[slot].action === 3">
          <div class="rule-field">
            <label class="field-label">Event Logging ID (0–255)</label>
            <input v-model.number="cfg.filters[slot].event_lid" type="number" min="0" max="255" class="text-input" style="max-width:90px" />
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  cfg: Object,
  RULE_SLOTS: Array,
  activeRuleCount: Number,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.cfg-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 12px; }
.info-card-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.cfg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 12px; }
.field-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.text-input { width: 100%; padding: 9px 12px; background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.15s; }
.text-input:focus { border-color: var(--primary); }
.panel-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }
.count-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; background: rgba(59,130,246,0.15); color: #60a5fa; }
.mode-desc { font-size: 13px; color: var(--muted); line-height: 1.55; }
.rule-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 16px; margin-bottom: 8px; }
.rule-card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.rule-slot-num { font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; min-width: 44px; }
.rule-action-sel { width: 140px; flex-shrink: 0; }
@media (max-width: 900px) {
  .rule-card-head { flex-direction: column; align-items: stretch; }
  .rule-action-sel { width: 100%; }
  .rule-fields-grid { padding-left: 0; }
}
.rule-disabled-lbl { font-size: 12px; color: var(--muted); font-style: italic; }
.rule-fields-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; padding-left: 56px; }
.rule-field { display: flex; flex-direction: column; gap: 6px; }
</style>
