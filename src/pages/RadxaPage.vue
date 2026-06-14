<template>
  <section class="content-panel">
    <div class="radxa-top-grid">
      <div class="info-card">
        <div class="info-card-title">Co-Processor Status</div>
        <div :class="['device-status', radxa.alive ? 'dev-online' : 'dev-offline']">
          {{ radxa.alive ? 'ONLINE' : 'OFFLINE' }}
        </div>
        <InfoRow label="Heartbeat">
          <template #val>
            <span class="ir-value mono">{{ radxa.alive ? `0x${radxa.heartbeat.toString(16).padStart(2,'0').toUpperCase()}` : '—' }}</span>
          </template>
        </InfoRow>
        <InfoRow label="Version" :value="radxa.version || '—'" />
        <InfoRow label="Uptime" :value="radxa.uptime ? formatUptime(radxa.uptime) : '—'" />
        <InfoRow label="Flags">
          <template #val>
            <div class="flag-row">
              <span :class="['s-pill', radxa.status & 0x01 ? 's-pill-on' : '']">BOOT</span>
              <span :class="['s-pill', radxa.status & 0x02 ? 's-pill-on' : '']">WiFi</span>
              <span :class="['s-pill', radxa.status & 0x04 ? 's-pill-on' : '']">FWD</span>
            </div>
          </template>
        </InfoRow>
      </div>

      <div class="info-card">
        <div class="info-card-title">WiFi</div>
        <div class="ptp-row">
          <div>
            <div class="ptp-label">WiFi Radio</div>
            <div class="ptp-desc">Enable / disable the WiFi radio</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" v-model="radxaEdit.wifiEnable" @change="$emit('wifi-toggle')" />
            <span class="toggle-slider"></span>
          </label>
        </div>
        <div class="wifi-status-row">
          <span :class="['wifi-status-dot', wifiStatusClass]"></span>
          <span class="ptp-desc">{{ wifiStatusText }}</span>
          <span v-if="radxa.wifi_ip" class="ir-value mono">{{ radxa.wifi_ip }}</span>
        </div>
        <div v-if="radxa.wifi_rssi && radxa.wifi_status >= 1" class="ptp-desc" style="margin-top:4px">
          RSSI: {{ radxa.wifi_rssi }} dBm
        </div>
        <div class="rule-field">
          <label class="field-label">SSID</label>
          <input v-model="radxaEdit.ssid" class="text-input" placeholder="MyNetwork" autocomplete="off" />
        </div>
        <div class="rule-field" style="margin-top:8px">
          <label class="field-label">Password</label>
          <input v-model="radxaEdit.password" type="password" class="text-input" placeholder="••••••••" autocomplete="new-password" />
        </div>
        <button class="btn btn-primary" style="margin-top:10px" @click="$emit('wifi-connect')">Connect</button>
        <div v-if="radxaEdit.wifiResult" :class="['inject-result', radxaEdit.wifiOk ? 'inject-ok' : 'inject-err']" style="margin-top:8px">
          {{ radxaEdit.wifiResult }}
        </div>
      </div>
    </div>

    <div class="cfg-card" style="margin-top:16px">
      <div class="info-card-title">CLOG Data Forwarding</div>
      <p class="mode-desc">When enabled, the WiFi module receives CLOG frames on the USB ECM link and relays them to the destination over WiFi.</p>
      <div class="ptp-row" style="margin-bottom:16px">
        <div>
          <div class="ptp-label">Forwarding</div>
          <div class="ptp-desc">{{ radxaEdit.dataEnable ? 'Active — relaying CLOG frames via WiFi' : 'Inactive' }}</div>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" v-model="radxaEdit.dataEnable" />
          <span class="toggle-slider"></span>
        </label>
      </div>
      <div class="cfg-grid" style="margin-top:0">
        <div class="rule-field">
          <label class="field-label">Destination IP</label>
          <input v-model="radxaEdit.destIp" class="text-input mono" placeholder="192.168.1.10" />
        </div>
        <div class="rule-field">
          <label class="field-label">Destination Port</label>
          <input v-model.number="radxaEdit.destPort" type="number" min="1" max="65535" class="text-input" />
        </div>
      </div>
      <div class="button-row">
        <button class="btn btn-primary" @click="$emit('apply-data')">Apply</button>
        <div v-if="radxaEdit.dataResult" :class="['inject-result', radxaEdit.dataOk ? 'inject-ok' : 'inject-err']">
          {{ radxaEdit.dataResult }}
        </div>
      </div>
      <div class="radxa-stats-row">
        <div class="radxa-stat" :class="{ 'radxa-stat-warn': radxa.pkts_drop > 0 }">
          <div class="radxa-stat-val">{{ radxa.pkts_fwd.toLocaleString() }}</div>
          <div class="radxa-stat-label">Forwarded</div>
        </div>
        <div class="radxa-stat" :class="{ 'radxa-stat-warn': radxa.pkts_drop > 0 }">
          <div class="radxa-stat-val">{{ radxa.pkts_drop.toLocaleString() }}</div>
          <div class="radxa-stat-label">Dropped</div>
        </div>
      </div>
    </div>

    <div class="boot-card">
      <div class="boot-card-title">Power Control</div>
      <template v-if="radxaRebootState === 'idle'">
        <p class="boot-desc">Reboot the WiFi module. The USB ECM link will drop for ~15 seconds.</p>
        <button class="btn btn-danger boot-btn" style="max-width:200px;margin-top:4px" :disabled="!radxa.alive" @click="$emit('request-reboot')">↺ Reboot WiFi</button>
      </template>
      <template v-else-if="radxaRebootState === 'confirming'">
        <p class="boot-warn">⚠ WiFi module will reboot immediately. The connection will drop for ~15 s.</p>
        <div class="boot-row" style="margin-top:10px">
          <button class="btn btn-danger boot-btn-half" @click="$emit('confirm-reboot')">Confirm</button>
          <button class="btn btn-neutral boot-btn-half" @click="$emit('cancel-reboot')">Cancel</button>
        </div>
      </template>
      <template v-else-if="radxaRebootState === 'sending'">
        <div class="boot-spinner-row"><div class="boot-spinner"></div><span class="boot-sending-txt">Sending reboot command…</span></div>
      </template>
      <template v-else-if="radxaRebootState === 'done'">
        <p class="boot-ok">✓ Reboot command sent. WiFi module is restarting.</p>
        <button class="btn btn-neutral boot-btn" style="max-width:160px;margin-top:10px" @click="$emit('reset-reboot-state')">Dismiss</button>
      </template>
      <template v-else-if="radxaRebootState === 'error'">
        <p class="boot-err">✕ Failed to send reboot command.</p>
        <button class="btn btn-neutral boot-btn" style="max-width:160px;margin-top:10px" @click="$emit('reset-reboot-state')">Retry</button>
      </template>
    </div>
  </section>
</template>

<script setup>
import InfoRow from '../components/ui/InfoRow.vue'
const props = defineProps({
  radxa: Object,
  radxaEdit: Object,
  wifiStatusText: String,
  wifiStatusClass: String,
  radxaRebootState: String,
  formatUptime: Function,
})
</script>

<style scoped>
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }
.radxa-top-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .radxa-top-grid { grid-template-columns: 1fr; } }
.info-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.info-card-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.device-status { font-size: 28px; font-weight: 800; text-align: center; padding: 16px; border-radius: var(--radius-sm); letter-spacing: 2px; }
.dev-online { background: rgba(16,185,129,0.1); color: #34d399; }
.dev-offline { background: rgba(239,68,68,0.1); color: #f87171; }
.flag-row { display: flex; gap: 6px; flex-wrap: wrap; }
.s-pill { font-size: 10px; font-weight: 700; padding: 2px 10px; border-radius: 10px; background: rgba(239,68,68,0.15); color: #f87171; }
.s-pill-on { background: rgba(16,185,129,0.15); color: #34d399; }
.ptp-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.ptp-label { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.ptp-desc { font-size: 13px; color: var(--muted); line-height: 1.5; }
.wifi-status-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.wifi-status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.wifi-dot-connected { background: var(--success); box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.wifi-dot-connecting { background: var(--warning); animation: pulse-warn 1.2s infinite; }
.wifi-dot-down { background: var(--muted); }
@keyframes pulse-warn { 0%,100%{box-shadow:0 0 0 0 rgba(245,158,11,0.5);}50%{box-shadow:0 0 0 5px rgba(245,158,11,0);} }
.rule-field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.text-input { width: 100%; padding: 9px 12px; background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); font-size: 13px; font-family: inherit; outline: none; transition: border-color 0.15s; }
.text-input:focus { border-color: var(--primary); }
.btn { width: 100%; padding: 11px; border: none; border-radius: var(--radius-sm); font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s, transform 0.1s; }
.btn:hover { opacity: 0.88; }
.btn-primary { background: var(--primary); color: #fff; }
.button-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
.inject-result { font-size: 14px; font-weight: 600; padding: 8px 12px; border-radius: 6px; }
.inject-ok { color: #34d399; background: rgba(52,211,153,.1); }
.inject-err { color: #f87171; background: rgba(248,113,113,.1); }
.radxa-stats-row { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 20px; }
@media (max-width: 700px) {
  .ptp-row, .radxa-stats-row { flex-direction: column; }
}
.radxa-stat { background: var(--dim); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px 24px; min-width: 130px; text-align: center; }
.radxa-stat-warn { border-color: rgba(239,68,68,0.4); background: rgba(239,68,68,0.05); }
.radxa-stat-val { font-size: 26px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.radxa-stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); margin-top: 4px; }
.boot-card { margin-top: 16px; background: var(--card); border: 1px solid rgba(239,68,68,0.3); border-radius: var(--radius); padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; max-width: none; }
.boot-card-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.boot-desc { font-size: 13px; color: var(--muted); line-height: 1.6; }
.boot-warn { font-size: 13px; color: #fbbf24; line-height: 1.6; }
.boot-ok { font-size: 14px; color: #34d399; font-weight: 600; }
.boot-err { font-size: 13px; color: #f87171; }
.boot-row { display: flex; gap: 10px; }
.boot-btn-half { flex: 1; }
.btn-danger { background: var(--danger); color: #fff; }
.btn-neutral { background: var(--dim); color: var(--muted); border: 1px solid var(--border); }
.btn-neutral:hover { color: var(--text); }
.boot-spinner-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; }
.boot-spinner { width: 20px; height: 20px; border: 2px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.boot-sending-txt { font-size: 13px; color: var(--muted); }
</style>
