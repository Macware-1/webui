<template>
  <aside :class="['sidebar', { collapsed }]">
    <div class="brand">
      <div class="brand-main">
        <div class="brand-icon">⚙</div>
        <div class="brand-copy">
          <div class="brand-name">CanX</div>
          <!-- <div class="brand-sub">CNGW175</div> -->
        </div>
      </div>
      <button class="collapse-toggle" @click="$emit('toggle-collapse')" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        {{ collapsed ? '»' : '«' }}
      </button>
    </div>

    <Button :class="['save-btn', { hidden: collapsed }]"
            :variant="'primary'" :size="'md'" :full="true"
            @click="$emit('save')"
            :disabled="saveState === 'saving' || saveState === 'rebooting'">
      <template v-if="saveState === 'idle'">💾 Save & Apply Config</template>
      <template v-else-if="saveState === 'saving'" class="save-spinner-row">
        <span class="save-spin"></span>Saving…
      </template>
      <template v-else-if="saveState === 'rebooting'" class="save-spinner-row">
        <span class="save-spin"></span>Rebooting…
      </template>
      <template v-else-if="saveState === 'done'">✓ Config Applied</template>
      <template v-else>✕ Save Failed</template>
    </Button>

    <template v-if="defaultState === 'idle'">
      <Button class="save-btn save-default" variant="secondary" size="md" :full="true"
              @click="$emit('confirm-default')" :class="{ hidden: collapsed }">
        🔄 Reset to Defaults
      </Button>
    </template>
    <template v-else-if="defaultState === 'confirming'">
      <div class="default-confirm" :class="{ hidden: collapsed }">
        <span class="default-warn">Reset all config to factory defaults?</span>
        <div class="default-row">
          <button class="btn-half btn-danger-sm" @click="$emit('apply-defaults')">Yes, Reset</button>
          <button class="btn-half btn-neutral-sm" @click="$emit('cancel-default')">Cancel</button>
        </div>
      </div>
    </template>

    <nav class="nav">
      <button v-for="p in pages" :key="p"
              :class="['nav-btn', { active: page === p }]"
              @click="$emit('update:page', p)">
        <span class="nav-icon">{{ icons[p] }}</span>
        <span class="nav-label">{{ p }}</span>
      </button>
    </nav>

    <div class="sidebar-footer" :class="{ collapsed }">
      <div class="live-badge">
        <span class="live-dot"></span>
        <span v-if="!collapsed">LIVE</span>
      </div>
      <div class="uptime-label" v-if="!collapsed">{{ formatUptime(system.uptime) }}</div>
    </div>
  </aside>
</template>

<script setup>
import Button from '../ui/Button.vue'

const props = defineProps({
  page: String,
  pages: Array,
  icons: Object,
  saveState: String,
  defaultState: String,
  system: Object,
  formatUptime: Function,
  collapsed: Boolean,
})
</script>

<style scoped>
.sidebar {
  width: 220px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  gap: 4px;
  flex-shrink: 0;
  transition: width 0.2s ease, padding 0.2s ease;
}
.sidebar.collapsed {
  width: 72px;
  padding: 20px 8px;
}
.sidebar.collapsed .nav-btn { width: 100%; }

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 8px 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}
.brand-main {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-copy { display: flex; flex-direction: column; }
.collapse-toggle {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.sidebar .collapse-toggle { position: relative; z-index: 1210; }

@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    left: 0; top: 0; bottom: 0;
    height: 100vh;
    width: min(360px, 92vw);
    background: var(--surface);
    z-index: 1200;
    padding: 20px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    transition: transform 0.28s cubic-bezier(.2,.9,.2,1), box-shadow 0.18s;
    transform: translateX(0);
    overflow: hidden;
  }
  .sidebar.collapsed {
    transform: translateX(-100%);
    box-shadow: none;
  }
  /* move toggle outside the sidebar when collapsed so it remains visible */
  .sidebar .collapse-toggle {
    position: absolute;
    top: 12px;
    right: 12px;
    transform: translateX(0);
    transition: right 0.28s cubic-bezier(.2,.9,.2,1), background 0.18s;
  }
  /* style the toggle when sidebar is collapsed so it's a dark pill outside */
  .sidebar.collapsed .collapse-toggle {
    right: -48px;
    background: rgba(0,0,0,0.72);
    color: #fff;
    border-color: rgba(255,255,255,0.08);
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}

.hidden { display: none !important; }
.save-idle  { background: var(--primary); color: #fff; }
.save-idle:hover { opacity: 0.88; }
.save-saving    { background: var(--dim); color: var(--muted); cursor: not-allowed; }
.save-rebooting { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.35); cursor: not-allowed; }
.save-done  { background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.4); }
.save-error { background: rgba(239,68,68,0.2);  color: #f87171; border: 1px solid rgba(239,68,68,0.4); }
.save-default { background: var(--dim); color: var(--muted); border: 1px solid var(--border); font-weight: 600; }
.save-default:hover { color: var(--text); border-color: var(--warning); }

.default-confirm {
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.35);
  border-radius: var(--radius-sm);
  padding: 10px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.default-warn { font-size: 12px; color: #fbbf24; line-height: 1.4; }
.default-row  { display: flex; gap: 6px; }
.btn-half     { flex: 1; padding: 7px 4px; border: none; border-radius: var(--radius-sm); font-size: 12px; font-weight: 700; cursor: pointer; }
.btn-danger-sm  { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.4); }
.btn-danger-sm:hover  { background: rgba(239,68,68,0.35); }
.btn-neutral-sm { background: var(--dim); color: var(--muted); border: 1px solid var(--border); }
.btn-neutral-sm:hover { color: var(--text); }

.save-spinner-row { display: flex; align-items: center; gap: 8px; }
.save-spin {
  width: 14px; height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.nav { display: flex; flex-direction: column; gap: 2px; }

.sidebar.collapsed .nav { align-items: center; }
.sidebar.collapsed .nav-btn {
  justify-content: center;
  padding: 10px 8px;
}
.sidebar.collapsed .nav-icon { margin: 0; }
.sidebar.collapsed .nav-label { display: none; }
.sidebar.collapsed .save-btn,
.sidebar.collapsed .save-default,
.sidebar.collapsed .default-confirm { display: none; }
.sidebar.collapsed .sidebar-footer { justify-content: center; }
.sidebar.collapsed .sidebar-footer .uptime-label { display: none; }
.sidebar.collapsed .brand-copy { display: none; }

.nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  border-left: 3px solid transparent;
  text-align: left;
}
.nav-btn:hover { background: var(--dim); color: var(--text); }
.nav-btn.active {
  background: rgba(59,130,246,0.12);
  color: #60a5fa;
  border-left-color: var(--primary);
}
.nav-icon  { font-size: 16px; width: 20px; text-align: center; }
.nav-label { flex: 1; }

.sidebar-footer {
  margin-top: auto;
  padding: 12px;
  background: var(--dim);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--success);
}
.live-dot {
  width: 8px; height: 8px;
  background: var(--success);
  border-radius: 50%;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.5); }
  50%       { box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}
.uptime-label { font-size: 11px; color: var(--muted); }

/* Branding typography */
.brand-name {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 0.2px;
  color: var(--text);
  line-height: 1;
}
.brand-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
.brand-icon { font-size: 20px; }
</style>
