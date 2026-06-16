<template>
  <section class="content-panel">
    <p class="mode-desc">Click a CAN channel block to configure its logging ID, output target, and full CAN bus settings. Click the Ethernet block to configure network + PTP settings. Arrows show active logging paths.</p>
    <div class="log-diagram-wrap">
      <svg class="log-diagram-svg" viewBox="0 0 700 310" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="ah-on" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
            <polygon points="0 0, 10 4, 0 8" fill="#3b82f6" />
          </marker>
          <marker id="ah-off" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
            <polygon points="0 0, 10 4, 0 8" fill="#243549" />
          </marker>
          <marker id="ah-usb" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
            <polygon points="0 0, 10 4, 0 8" fill="#a78bfa" />
          </marker>
        </defs>

        <g @click="$emit('open-channel', 1)" style="cursor:pointer">
          <rect x="30" y="20" width="185" height="108" rx="12"
                :fill="cfg.logging.ch1.enabled ? '#0a1c30' : '#101e33'"
                :stroke="cfg.logging.ch1.enabled ? '#3b82f6' : '#1b2d47'"
                stroke-width="2"/>
          <text x="122" y="62" text-anchor="middle" font-size="30">📟</text>
          <text x="122" y="88" text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="600" font-family="Inter,system-ui,sans-serif">CAN Channel 1</text>
          <text x="122" y="107" text-anchor="middle" fill="#64748b" font-size="12" font-family="Inter,system-ui,sans-serif">Logging ID: {{ cfg.logging.ch1.logging_id }}</text>
          <text x="122" y="122" text-anchor="middle" fill="#3b82f6" font-size="10" font-family="Inter,system-ui,sans-serif">▶ click to configure</text>
        </g>

        <g @click="$emit('open-channel', 2)" style="cursor:pointer">
          <rect x="485" y="20" width="185" height="108" rx="12"
                :fill="cfg.logging.ch2.enabled ? '#0a1c30' : '#101e33'"
                :stroke="cfg.logging.ch2.enabled ? '#3b82f6' : '#1b2d47'"
                stroke-width="2"/>
          <text x="577" y="62" text-anchor="middle" font-size="30">📟</text>
          <text x="577" y="88" text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="600" font-family="Inter,system-ui,sans-serif">CAN Channel 2</text>
          <text x="577" y="107" text-anchor="middle" fill="#64748b" font-size="12" font-family="Inter,system-ui,sans-serif">Logging ID: {{ cfg.logging.ch2.logging_id }}</text>
          <text x="577" y="122" text-anchor="middle" fill="#3b82f6" font-size="10" font-family="Inter,system-ui,sans-serif">▶ click to configure</text>
        </g>

        <line x1="122" y1="128" x2="265" y2="197"
              :stroke="cfg.logging.ch1.enabled && cfg.logging.ch1.target===0 ? '#3b82f6' : '#243549'"
              stroke-width="2.5"
              :stroke-dasharray="cfg.logging.ch1.enabled && cfg.logging.ch1.target===0 ? '6,4' : '4,5'"
              :marker-end="cfg.logging.ch1.enabled && cfg.logging.ch1.target===0 ? 'url(#ah-on)' : 'url(#ah-off)'"/>

        <line x1="577" y1="128" x2="395" y2="197"
              :stroke="cfg.logging.ch2.enabled && cfg.logging.ch2.target===0 ? '#3b82f6' : '#243549'"
              stroke-width="2.5"
              :stroke-dasharray="cfg.logging.ch2.enabled && cfg.logging.ch2.target===0 ? '6,4' : '4,5'"
              :marker-end="cfg.logging.ch2.enabled && cfg.logging.ch2.target===0 ? 'url(#ah-on)' : 'url(#ah-off)'"/>

        <line x1="215" y1="128" x2="468" y2="197"
              :stroke="cfg.logging.ch1.enabled && cfg.logging.ch1.target===1 ? '#a78bfa' : '#243549'"
              stroke-width="2.5"
              :stroke-dasharray="cfg.logging.ch1.enabled && cfg.logging.ch1.target===1 ? '6,4' : '4,5'"
              :marker-end="cfg.logging.ch1.enabled && cfg.logging.ch1.target===1 ? 'url(#ah-usb)' : 'url(#ah-off)'"/>

        <line x1="577" y1="128" x2="558" y2="197"
              :stroke="cfg.logging.ch2.enabled && cfg.logging.ch2.target===1 ? '#a78bfa' : '#243549'"
              stroke-width="2.5"
              :stroke-dasharray="cfg.logging.ch2.enabled && cfg.logging.ch2.target===1 ? '6,4' : '4,5'"
              :marker-end="cfg.logging.ch2.enabled && cfg.logging.ch2.target===1 ? 'url(#ah-usb)' : 'url(#ah-off)'"/>

      <g @click="$emit('open-ethernet')" style="cursor:pointer">
        <rect x="175" y="197" width="260" height="100" rx="12"
              :fill="system.link_up ? '#081a10' : '#1a0909'"
              :stroke="system.link_up ? '#10b981' : '#ef4444'"
              stroke-width="2"/>
        <text x="305" y="241" text-anchor="middle" font-size="30">🌐</text>
        <text x="305" y="265" text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="600" font-family="Inter,system-ui,sans-serif">100 Mbps Ethernet</text>
        <circle cx="258" cy="283" r="5" :fill="system.link_up ? '#10b981' : '#ef4444'" />
        <text x="268" y="287" :fill="system.link_up ? '#10b981' : '#ef4444'" font-size="12" font-family="Inter,system-ui,sans-serif">
          {{ system.link_up ? 'Connected' : 'Disconnected' }}
        </text>
      </g>

        <rect x="458" y="197" width="110" height="100" rx="12"
              :fill="(cfg.logging.ch1.enabled && cfg.logging.ch1.target===1) || (cfg.logging.ch2.enabled && cfg.logging.ch2.target===1) ? '#1a0f2e' : '#101e33'"
              :stroke="(cfg.logging.ch1.enabled && cfg.logging.ch1.target===1) || (cfg.logging.ch2.enabled && cfg.logging.ch2.target===1) ? '#a78bfa' : '#1b2d47'"
              stroke-width="2"/>
        <text x="513" y="244" text-anchor="middle" font-size="28">🔌</text>
        <text x="513" y="267" text-anchor="middle" fill="#e2e8f0" font-size="13" font-weight="600" font-family="Inter,system-ui,sans-serif">USB ECM</text>
        <text x="513" y="284" text-anchor="middle" fill="#64748b" font-size="10" font-family="Inter,system-ui,sans-serif">192.168.7.x</text>

        <g opacity="0.38">
          <rect x="580" y="197" width="100" height="100" rx="12" fill="#101e33" stroke="#1b2d47" stroke-width="1.5" />
          <text x="630" y="244" text-anchor="middle" font-size="28">🔷</text>
          <text x="630" y="267" text-anchor="middle" fill="#e2e8f0" font-size="13" font-weight="600" font-family="Inter,system-ui,sans-serif">BLE</text>
          <text x="630" y="284" text-anchor="middle" fill="#64748b" font-size="10" font-family="Inter,system-ui,sans-serif">Coming soon</text>
        </g>
      </svg>
    </div>

    <div class="log-legend">
      <span class="leg-item">
        <svg width="28" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6,4"/><polygon points="22,1 28,5 22,9" fill="#3b82f6"/></svg>
        Active logging path
      </span>
      <span class="leg-item">
        <svg width="28" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="#243549" stroke-width="2.5" stroke-dasharray="4,5"/><polygon points="22,1 28,5 22,9" fill="#243549"/></svg>
        Inactive / not configured
      </span>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  cfg: Object,
  system: Object,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.mode-desc { font-size: 13px; color: var(--muted); line-height: 1.55; margin-bottom: 20px; }
.log-diagram-wrap {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 16px;
  margin-bottom: 16px;
}
.log-diagram-svg {
  width: 100%;
  max-width: 700px;
  display: block;
  margin: 0 auto;
}
.log-legend {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--muted);
  padding: 4px 0;
}
.leg-item { display: flex; align-items: center; gap: 8px; }
</style>
