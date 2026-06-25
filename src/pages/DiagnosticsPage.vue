<template>
  <section class="diag-page">

    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <div class="diag-header">
      <div class="tab-group">
        <button :class="['tab', tab === 'dm1' && 'active']" @click="tab = 'dm1'">
          Active (DM1)
          <span v-if="dtc.length"  class="pill pill-red">{{ dtc.length }}</span>
        </button>
        <button :class="['tab', tab === 'dm2' && 'active']" @click="tab = 'dm2'">
          History (DM2)
          <span v-if="dtc2.length" class="pill pill-yellow">{{ dtc2.length }}</span>
        </button>
      </div>

      <div class="action-group">
        <button class="btn-action btn-danger"
                :disabled="!dtc.length"
                @click="$emit('clear-dm11')"
                title="Send DM11 — ECU clears its active fault list">
          Clear Active
        </button>
        <button class="btn-action btn-warn"
                :disabled="!dtc2.length"
                @click="$emit('clear-dm3')"
                title="Send DM3 — ECU clears its fault history">
          Clear History
        </button>
      </div>
    </div>

    <!-- ── Lamp status bar ────────────────────────────────────────────────── -->
    <div class="lamp-bar" v-if="tab === 'dm1'">
      <div :class="['lamp', currentData.red_stop_lamp   ? 'lamp-on lamp-red'    : 'lamp-off']">
        ● Red Stop
      </div>
      <div :class="['lamp', currentData.amber_warn_lamp ? 'lamp-on lamp-amber'  : 'lamp-off']">
        ● Amber Warn
      </div>
    </div>

    <!-- ── Empty state ────────────────────────────────────────────────────── -->
    <div v-if="!currentList.length" class="empty-state">
      <div class="empty-icon">{{ tab === 'dm1' ? '✅' : '🗂' }}</div>
      <p>{{ tab === 'dm1' ? 'No active diagnostic trouble codes' : 'No fault history recorded' }}</p>
    </div>

    <!-- ── Fault table ────────────────────────────────────────────────────── -->
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>SPN</th>
          <th>FMI</th>
          <th>Description</th>
          <th>Count</th>
          <th>ECU</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(d, i) in currentList" :key="i" :class="severityClass(d.fmi)">
          <td class="mono bold">{{ d.spn }}</td>
          <td><span :class="['fmi-pill', severityClass(d.fmi)]">{{ d.fmi }}</span></td>
          <td>{{ d.desc }}</td>
          <td>{{ d.count }}</td>
          <td class="mono">{{ d.ecu }}</td>
        </tr>
      </tbody>
    </table>

  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  dtc:           Array,
  dtc2:          Array,
  dtcMeta:       Object,
  severityClass: Function,
})
defineEmits(['clear-dm11', 'clear-dm3'])

const tab = ref('dm1')

const currentList = computed(() => tab.value === 'dm1' ? props.dtc : props.dtc2)
const currentData = computed(() => props.dtcMeta ?? { red_stop_lamp: false, amber_warn_lamp: false })
</script>

<style scoped>
.diag-page { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }

/* ── Header ──────────────────────────────────────────────────────────────── */
.diag-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.tab-group { display: flex; gap: 4px; }
.tab {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
}
.tab:hover  { border-color: var(--accent); color: var(--text); }
.tab.active { background: color-mix(in srgb, var(--accent) 15%, transparent); border-color: var(--accent); color: var(--accent); }

.pill {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
}
.pill-red    { background: rgba(239,68,68,0.2);   color: #f87171; }
.pill-yellow { background: rgba(245,158,11,0.2);  color: #fbbf24; }

.action-group { display: flex; gap: 8px; }
.btn-action {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-action:disabled { opacity: 0.35; cursor: not-allowed; }
.btn-danger { background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.3); }
.btn-danger:not(:disabled):hover { background: rgba(239,68,68,0.28); }
.btn-warn   { background: rgba(245,158,11,0.15); color: #fbbf24; border-color: rgba(245,158,11,0.3); }
.btn-warn:not(:disabled):hover   { background: rgba(245,158,11,0.28); }

/* ── Lamp bar ─────────────────────────────────────────────────────────────── */
.lamp-bar { display: flex; gap: 12px; }
.lamp { font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 20px; }
.lamp-off  { color: var(--muted); background: color-mix(in srgb, var(--muted) 10%, transparent); }
.lamp-on   { }
.lamp-red  { color: #f87171; background: rgba(239,68,68,0.15); }
.lamp-amber{ color: #fbbf24; background: rgba(245,158,11,0.15); }

/* ── Table ───────────────────────────────────────────────────────────────── */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 10px 12px;
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
  color: var(--muted); border-bottom: 1px solid var(--border);
}
.data-table td { padding: 11px 12px; font-size: 14px; border-bottom: 1px solid var(--dim); }
.data-table tbody tr:hover { background: rgba(255,255,255,0.02); }
.data-table tbody tr.sev-high { border-left: 3px solid var(--danger); }
.data-table tbody tr.sev-med  { border-left: 3px solid var(--warning); }
.data-table tbody tr.sev-low  { border-left: 3px solid var(--muted); }
.mono { font-family: monospace; }
.bold { font-weight: 600; }
.fmi-pill { padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 700; }
.fmi-pill.sev-high { background: rgba(239,68,68,0.2);  color: #f87171; }
.fmi-pill.sev-med  { background: rgba(245,158,11,0.2); color: #fbbf24; }
.fmi-pill.sev-low  { background: rgba(100,116,139,0.2);color: #94a3b8; }

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; color: var(--muted); gap: 12px; }
.empty-icon  { font-size: 48px; }
.empty-state p { font-size: 15px; }
</style>
