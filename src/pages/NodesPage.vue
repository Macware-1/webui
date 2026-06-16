<template>
  <section class="content-panel">
    <div class="panel-head">
      <h2 class="panel-title">J1939 Network Nodes</h2>
      <span class="count-badge">{{ nodes.length }} ECU{{ nodes.length !== 1 ? 's' : '' }}</span>
    </div>

    <div v-if="!nodes.length" class="empty-state">
      <div class="empty-icon">📡</div>
      <p>No ECUs detected on the CAN bus yet</p>
    </div>

    <div v-else class="nodes-grid">
      <div v-for="n in nodes" :key="n.addr" class="node-card">
        <div class="node-online-dot"></div>
        <div class="node-addr">{{ n.addr }}</div>
        <div class="node-dec">dec {{ parseInt(n.addr, 16) }}</div>
        <div class="node-status-label">Online</div>
      </div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  nodes: Array,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.panel-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }
.count-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(59,130,246,0.15);
  color: #60a5fa;
}
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; color: var(--muted); gap: 12px; }
.empty-icon { font-size: 48px; }
.empty-state p { font-size: 15px; }
.nodes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
.node-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
  transition: border-color 0.2s;
}
.node-card:hover { border-color: var(--primary); }
.node-online-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--success); box-shadow: 0 0 8px rgba(16,185,129,0.6); margin-bottom: 4px; }
.node-addr { font-family: monospace; font-size: 20px; font-weight: 700; color: var(--primary); }
.node-dec { font-size: 12px; color: var(--muted); }
.node-status-label { font-size: 11px; color: var(--success); font-weight: 600; letter-spacing: 0.5px; }
</style>
