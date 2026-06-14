<template>
  <section class="content-panel">
    <div class="panel-head">
      <h2 class="panel-title">Active Faults (DM1)</h2>
      <span :class="['fault-badge', dtc.length ? 'fault-active' : 'fault-clear']">
        {{ dtc.length ? `${dtc.length} active` : 'No faults' }}
      </span>
    </div>

    <div v-if="!dtc.length" class="empty-state">
      <div class="empty-icon">✅</div>
      <p>No active diagnostic trouble codes</p>
    </div>

    <table v-else class="data-table">
      <thead>
        <tr><th>SPN</th><th>FMI</th><th>Description</th><th>Count</th><th>ECU</th></tr>
      </thead>
      <tbody>
        <tr v-for="(d, i) in dtc" :key="i" :class="severityClass(d.fmi)">
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
const props = defineProps({
  dtc: Array,
  severityClass: Function,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.panel-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }
.fault-badge, .count-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.fault-active { background: rgba(239,68,68,0.15); color: #f87171; }
.fault-clear { background: rgba(16,185,129,0.15); color: #34d399; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}
.data-table td { padding: 11px 12px; font-size: 14px; border-bottom: 1px solid var(--dim); }
.data-table tbody tr:hover { background: rgba(255,255,255,0.02); }
.tr.sev-high { border-left: 3px solid var(--danger); }
.tr.sev-med { border-left: 3px solid var(--warning); }
.tr.sev-low { border-left: 3px solid var(--muted); }
.fmi-pill { padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 700; }
.fmi-pill.sev-high { background: rgba(239,68,68,0.2); color: #f87171; }
.fmi-pill.sev-med { background: rgba(245,158,11,0.2); color: #fbbf24; }
.fmi-pill.sev-low { background: rgba(100,116,139,0.2); color: #94a3b8; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; color: var(--muted); gap: 12px; }
.empty-icon { font-size: 48px; }
.empty-state p { font-size: 15px; }
</style>
