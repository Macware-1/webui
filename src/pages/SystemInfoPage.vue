<template>
  <section class="content-panel">
    <div class="panel-head"><h2 class="panel-title">System Information</h2></div>
    <div class="info-grid">
      <div class="info-card">
        <div class="info-card-title">Network (Live)</div>
        <InfoRow label="IP Address" :value="system.ip" />
        <InfoRow label="MAC Address" :value="system.mac" />
        <InfoRow label="Gateway" :value="system.gateway" />
      </div>

      <div class="info-card full-width">
        <div class="info-card-title">Network Configuration</div>
        <div class="cfg-grid">
          <div class="rule-field">
            <label class="field-label">ETH IP</label>
            <input v-model="cfg.board.eth_ip" class="text-input mono" placeholder="10.104.3.64" />
          </div>
          <div class="rule-field">
            <label class="field-label">Subnet Mask</label>
            <input v-model="cfg.board.eth_mask" class="text-input mono" placeholder="255.255.255.0" />
          </div>
          <div class="rule-field">
            <label class="field-label">Gateway</label>
            <input v-model="cfg.board.eth_gw" class="text-input mono" placeholder="10.104.3.1" />
          </div>
          <div class="rule-field">
            <label class="field-label">USB IP</label>
            <input v-model="cfg.board.usb_ip" class="text-input mono" placeholder="192.168.7.64" />
          </div>
        </div>
        <p class="boot-desc">Changes take effect after <strong>Save &amp; Apply Config</strong>.</p>
      </div>

      <div class="info-card">
        <div class="info-card-title">Ethernet PHY</div>
        <InfoRow label="Chip" :value="system.phy" />
        <InfoRow label="Link">
          <template #val>
            <span :class="system.link_up ? 'pill-up' : 'pill-down'">
              {{ system.link_up ? 'UP' : 'DOWN' }}
            </span>
          </template>
        </InfoRow>
        <InfoRow label="Speed" :value="system.speed" />
        <InfoRow label="Duplex" :value="system.duplex" />
      </div>

      <div class="info-card">
        <div class="info-card-title">Device</div>
        <div :class="['device-status', system.link_up ? 'dev-online' : 'dev-offline']">
          {{ system.link_up ? 'ONLINE' : 'OFFLINE' }}
        </div>
        <InfoRow label="Uptime" :value="formatUptime(system.uptime)" />
        <InfoRow label="Heap" :value="system.heap ? `${system.heap} B` : '—'" />
        <InfoRow label="Tasks" :value="system.tasks || '—'" />
        <InfoRow label="Clock" :value="system.clock || '—'" />
      </div>
    </div>

    <div class="ptp-card">
      <div class="boot-card-title">Precision Time Protocol (PTP / IEEE 802.1AS)</div>
      <div class="ptp-row">
        <div>
          <div class="ptp-label">{{ cfg.board.ptp_enable ? 'Enabled' : 'Disabled' }}</div>
          <div class="ptp-desc">
            {{ cfg.board.ptp_enable
               ? 'Hardware timestamp sync active'
               : 'No PTP frames sent — task is idle' }}
          </div>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" v-model="cfg.board.ptp_enable" :true-value="1" :false-value="0" />
          <span class="toggle-slider"></span>
        </label>
      </div>
      <p class="boot-desc">Toggle takes effect after <strong>Save &amp; Apply Config</strong> in the sidebar.</p>
    </div>

    <div class="ptp-card">
      <div class="boot-card-title">Radxa WiFi CLOG Forwarding</div>
      <div class="ptp-row">
        <div>
          <div class="ptp-label">{{ cfg.board.radxa_fwd_enable ? 'Enabled' : 'Disabled' }}</div>
          <div class="ptp-desc">
            {{ cfg.board.radxa_fwd_enable
               ? 'Radxa will forward CLOG packets to the configured destination over WiFi'
               : 'CLOG forwarding via Radxa is off' }}
          </div>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" v-model="cfg.board.radxa_fwd_enable" :true-value="1" :false-value="0" />
          <span class="toggle-slider"></span>
        </label>
      </div>
      <div class="cfg-grid">
        <div class="rule-field">
          <label class="field-label">Destination IP</label>
          <input v-model="cfg.board.radxa_dest_ip" class="text-input mono" placeholder="192.168.1.100" :disabled="!cfg.board.radxa_fwd_enable" />
        </div>
        <div class="rule-field">
          <label class="field-label">Destination Port</label>
          <input v-model.number="cfg.board.radxa_dest_port" type="number" min="1" max="65535" class="text-input mono" placeholder="47808" :disabled="!cfg.board.radxa_fwd_enable" />
        </div>
      </div>
      <p class="boot-desc">Enter your PC's WiFi IP address. Takes effect after <strong>Save &amp; Apply Config</strong>.</p>
    </div>
  </section>
</template>

<script setup>
import InfoRow from '../components/ui/InfoRow.vue'
const props = defineProps({
  system: Object,
  cfg: Object,
  formatUptime: Function,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.panel-head { margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.info-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info-card.full-width { grid-column: 1 / -1; }
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.rule-field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.text-input { width: 100%; padding: 9px 12px; background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.15s; }
.text-input:focus { border-color: var(--primary); }
.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.boot-desc { font-size: 13px; color: var(--muted); line-height: 1.6; }
.device-status { font-size: 28px; font-weight: 800; text-align: center; padding: 16px; border-radius: var(--radius-sm); letter-spacing: 2px; }
.dev-online { background: rgba(16,185,129,0.1); color: #34d399; }
.dev-offline { background: rgba(239,68,68,0.1); color: #f87171; }
.ptp-card { margin-top: 20px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; max-width: 560px; }
.ptp-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
@media (max-width: 700px) {
  .ptp-card { max-width: 100%; }
  .ptp-row { flex-direction: column; align-items: stretch; }
}
.ptp-label { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.ptp-desc { font-size: 13px; color: var(--muted); line-height: 1.5; }
.toggle-switch { position: relative; display: inline-block; width: 48px; height: 26px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; inset: 0; background: var(--dim); border: 1px solid var(--border); border-radius: 13px; transition: background 0.2s, border-color 0.2s; }
.toggle-slider::before { content: ''; position: absolute; width: 18px; height: 18px; left: 3px; top: 3px; background: var(--muted); border-radius: 50%; transition: transform 0.2s, background 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: rgba(59,130,246,0.25); border-color: var(--primary); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(22px); background: var(--primary); }
</style>
