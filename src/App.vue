<template>
  <div class="app">

    <!-- ── SIDEBAR ─────────────────────────────────────────────────────── -->
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-icon">⚙</div>
        <div>
          <div class="brand-name">J1939 GW</div>
          <div class="brand-sub">STM32H755</div>
        </div>
      </div>

      <!-- Save & Apply button -->
      <button :class="['save-btn', `save-${saveState}`]" @click="saveAndApply"
              :disabled="saveState === 'saving' || saveState === 'rebooting'">
        <span v-if="saveState === 'idle'">💾 Save &amp; Apply Config</span>
        <span v-else-if="saveState === 'saving'" class="save-spinner-row">
          <span class="save-spin"></span>Saving…
        </span>
        <span v-else-if="saveState === 'rebooting'" class="save-spinner-row">
          <span class="save-spin"></span>Rebooting…
        </span>
        <span v-else-if="saveState === 'done'">✓ Config Applied</span>
        <span v-else>✕ Save Failed</span>
      </button>

      <!-- Default Config button -->
      <template v-if="defaultState === 'idle'">
        <button class="save-btn save-default" @click="defaultState = 'confirming'">
          🔄 Reset to Defaults
        </button>
      </template>
      <template v-else-if="defaultState === 'confirming'">
        <div class="default-confirm">
          <span class="default-warn">Reset all config to factory defaults?</span>
          <div class="default-row">
            <button class="btn-half btn-danger-sm" @click="applyDefaults">Yes, Reset</button>
            <button class="btn-half btn-neutral-sm" @click="defaultState = 'idle'">Cancel</button>
          </div>
        </div>
      </template>

      <nav class="nav">
        <button v-for="p in pages" :key="p"
                :class="['nav-btn', { active: page === p }]"
                @click="page = p">
          <span class="nav-icon">{{ ICONS[p] }}</span>
          <span class="nav-label">{{ p }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="live-badge">
          <span class="live-dot"></span>LIVE
        </div>
        <div class="uptime-label">{{ formatUptime(system.uptime) }}</div>
      </div>
    </aside>

    <!-- ── MAIN ───────────────────────────────────────────────────────── -->
    <main class="main">

      <header class="topbar">
        <div>
          <h1 class="topbar-title">{{ page }}</h1>
          <p class="topbar-sub">J1939 → Ethernet Gateway</p>
        </div>
        <div :class="['conn-badge', system.link_up ? 'conn-up' : 'conn-down']">
          <span class="conn-dot"></span>
          {{ system.link_up ? 'Connected' : 'Disconnected' }}
        </div>
      </header>

      <!-- GAUGES ────────────────────────────────────────────────────── -->
      <section v-if="page === 'Gauges'" class="gauges-page">
        <div class="gauges-grid">
          <Gauge title="Engine RPM"    :value="smooth.engine_speed"    :max="3000" unit="rpm"  color="#3b82f6"/>
          <Gauge title="Vehicle Speed" :value="smooth.vehicle_speed"   :max="140"  unit="km/h" color="#10b981"/>
          <Gauge title="Fuel Level"    :value="smooth.fuel_level"      :max="100"  unit="%"    color="#f59e0b"/>
          <Gauge title="Engine Load"   :value="smooth.engine_load"     :max="100"  unit="%"    color="#8b5cf6"/>
        </div>

        <div class="bottom-row">
          <MetricCard icon="🌡" label="Coolant"  :value="smooth.coolant_temp.toFixed(1)"    unit="°C" :warn="smooth.coolant_temp > 100"/>
          <MetricCard icon="🔋" label="Battery"  :value="smooth.battery_voltage.toFixed(2)" unit="V"  :warn="smooth.battery_voltage < 11.5 && smooth.battery_voltage > 0"/>
          <MetricCard icon="🎯" label="Throttle" :value="(telemetry.throttle_pct||0).toFixed(1)" unit="%"/>

          <div class="status-card">
            <div class="status-card-title">Status</div>
            <StatusRow label="Engine"  :on="telemetry.status.engine_running"/>
            <StatusRow label="Brake"   :on="telemetry.status.brake"/>
            <StatusRow label="PTO"     :on="telemetry.status.pto"/>
            <StatusRow label="Cruise"  :on="telemetry.status.cruise"/>
          </div>
        </div>
      </section>

      <!-- DIAGNOSTICS ───────────────────────────────────────────────── -->
      <section v-if="page === 'Diagnostics'" class="content-panel">
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

      <!-- CONTROLS ──────────────────────────────────────────────────── -->
      <section v-if="page === 'Controls'" class="content-panel">
        <div class="panel-head"><h2 class="panel-title">Control Panel</h2></div>
        <div class="controls-grid">

          <div class="ctrl-card">
            <div class="ctrl-title">Throttle</div>
            <div class="ctrl-bigval">{{ throttle }}<span class="ctrl-unit">%</span></div>
            <input type="range" v-model="throttle" min="0" max="100" class="slider"/>
            <button class="btn btn-primary" @click="sendThrottle">Send Throttle</button>
          </div>

          <div class="ctrl-card">
            <div class="ctrl-title">Engine Control</div>
            <button class="btn btn-success" @click="send({type:'control',engine:'start'})">▶ Start Engine</button>
            <button class="btn btn-danger"  @click="send({type:'control',engine:'stop'})">■ Stop Engine</button>
          </div>

          <div class="ctrl-card">
            <div class="ctrl-title">Raw J1939 TX</div>
            <input v-model="tx.pgn"  class="text-input" placeholder="PGN  e.g. 61444"/>
            <input v-model="tx.data" class="text-input" placeholder="8-byte hex data"/>
            <button class="btn btn-primary" @click="send({type:'j1939_tx',...tx})">📡 Send Frame</button>
          </div>

        </div>
      </section>

      <!-- NODES ─────────────────────────────────────────────────────── -->
      <section v-if="page === 'Nodes'" class="content-panel">
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

      <!-- SYSTEM INFO ────────────────────────────────────────────────── -->
      <section v-if="page === 'System Info'" class="content-panel">
        <div class="panel-head"><h2 class="panel-title">System Information</h2></div>
        <div class="info-grid">

          <div class="info-card">
            <div class="info-card-title">Network</div>
            <InfoRow label="IP Address"  :value="system.ip"/>
            <InfoRow label="MAC Address" :value="system.mac"/>
            <InfoRow label="Gateway"     :value="system.gateway"/>
          </div>

          <div class="info-card">
            <div class="info-card-title">Ethernet PHY</div>
            <InfoRow label="Chip"   :value="system.phy"/>
            <InfoRow label="Link">
              <template #val>
                <span :class="system.link_up ? 'pill-up' : 'pill-down'">
                  {{ system.link_up ? 'UP' : 'DOWN' }}
                </span>
              </template>
            </InfoRow>
            <InfoRow label="Speed"  :value="system.speed"/>
            <InfoRow label="Duplex" :value="system.duplex"/>
          </div>

          <div class="info-card">
            <div class="info-card-title">Device</div>
            <div :class="['device-status', system.link_up ? 'dev-online' : 'dev-offline']">
              {{ system.link_up ? 'ONLINE' : 'OFFLINE' }}
            </div>
            <InfoRow label="Uptime" :value="formatUptime(system.uptime)"/>
            <InfoRow label="Heap"   :value="system.heap ? `${system.heap} B` : '—'"/>
            <InfoRow label="Tasks"  :value="system.tasks || '—'"/>
            <InfoRow label="Clock"  :value="system.clock || '—'"/>
          </div>

        </div>

        <!-- PTP Control -->
        <div class="ptp-card">
          <div class="boot-card-title">Precision Time Protocol (PTP / IEEE 802.1AS)</div>
          <div class="ptp-row">
            <div>
              <div class="ptp-label">{{ cfg.board.ptp_enable ? 'Enabled' : 'Disabled' }}</div>
              <div class="ptp-desc">
                {{ cfg.board.ptp_enable
                   ? 'Hardware timestamp sync active — sending Pdelay_Req every 1 s'
                   : 'No PTP frames sent — task is idle' }}
              </div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="cfg.board.ptp_enable" :true-value="1" :false-value="0"/>
              <span class="toggle-slider"></span>
            </label>
          </div>
          <p class="boot-desc" style="margin-top:6px">
            Toggle takes effect after <strong>Save &amp; Apply Config</strong> in the sidebar.
          </p>
        </div>

        <div class="boot-card">
          <div class="boot-card-title">Firmware Update</div>

          <template v-if="bootState === 'idle'">
            <p class="boot-desc">
              Reboot the device into bootloader mode to upload a new firmware
              image via the OTA web interface at <span class="boot-url">192.168.1.100</span>.
            </p>
            <button class="btn btn-danger boot-btn" @click="bootState = 'confirming'">
              ↩ Enter Bootloader Mode
            </button>
          </template>

          <template v-else-if="bootState === 'confirming'">
            <p class="boot-warn">
              ⚠ The device will reboot immediately. The Ethernet connection will
              drop and the app will be unreachable until the bootloader starts.
            </p>
            <div class="boot-row">
              <button class="btn btn-danger  boot-btn-half" @click="confirmBootloader">Confirm reboot</button>
              <button class="btn btn-neutral boot-btn-half" @click="bootState = 'idle'">Cancel</button>
            </div>
          </template>

          <template v-else-if="bootState === 'sending'">
            <div class="boot-spinner-row">
              <div class="boot-spinner"></div>
              <span class="boot-sending-txt">Sending reset command…</span>
            </div>
          </template>

          <template v-else-if="bootState === 'done'">
            <p class="boot-ok">✓ Device is rebooting into bootloader mode.</p>
            <p class="boot-desc" style="margin-top:6px">
              Connect to
              <a class="boot-link" href="http://192.168.1.100" target="_blank">
                http://192.168.1.100
              </a>
              to upload the <code>.fwu</code> package.
            </p>
            <button class="btn btn-neutral boot-btn" style="margin-top:12px"
                    @click="bootState = 'idle'">Dismiss</button>
          </template>

          <template v-else-if="bootState === 'error'">
            <p class="boot-err">✕ {{ bootMsg }}</p>
            <button class="btn btn-neutral boot-btn" style="margin-top:10px"
                    @click="bootState = 'idle'">Retry</button>
          </template>
        </div>
      </section>

      <!-- FILTERING / CONFIG ─────────────────────────────────────────── -->
      <section v-if="page === 'Filtering'" class="content-panel">

        <!-- Network config -->
        <div class="cfg-card">
          <div class="info-card-title">Network Configuration</div>
          <div class="cfg-grid">
            <CfgField label="ETH IP"      v-model="cfg.board.eth_ip"   placeholder="10.104.3.64"/>
            <CfgField label="Subnet Mask" v-model="cfg.board.eth_mask" placeholder="255.255.255.0"/>
            <CfgField label="Gateway"     v-model="cfg.board.eth_gw"   placeholder="10.104.3.1"/>
            <CfgField label="USB IP"      v-model="cfg.board.usb_ip"   placeholder="192.168.7.1"/>
          </div>
        </div>

        <!-- CAN config -->
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
              <input v-model.number="cfg.can.dlc" type="number" min="0" max="8" class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Default CAN ID (hex)</label>
              <input v-model="cfg.can.id_hex" class="text-input mono" placeholder="00000000"/>
            </div>
          </div>
        </div>

        <!-- USB config -->
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

        <!-- Filter rules -->
        <div class="panel-head" style="margin-top:24px;margin-bottom:12px">
          <h2 class="panel-title">CAN Filter Rules</h2>
          <span class="count-badge">{{ activeRuleCount }} active</span>
        </div>
        <p class="mode-desc" style="margin-bottom:16px">
          Rules are evaluated in slot order; first match wins. Set Action to
          <em>Disabled</em> to skip a slot. Click
          <strong>Save &amp; Apply Config</strong> (sidebar) to persist and reboot.
        </p>

        <div v-for="(slot, idx) in RULE_SLOTS" :key="slot" class="rule-card">
          <div class="rule-card-head">
            <span class="rule-slot-num">Slot {{ idx }}</span>
            <select v-model.number="cfg.filters[slot].action" class="text-input rule-action-sel">
              <option :value="0">Disabled</option>
              <option :value="1">DROP</option>
              <option :value="2">REMAP</option>
            </select>
            <span v-if="cfg.filters[slot].action === 0" class="rule-disabled-lbl">— not active —</span>
          </div>

          <div v-if="cfg.filters[slot].action !== 0" class="rule-fields-grid">
            <div class="rule-field">
              <label class="field-label">CAN ID (hex)</label>
              <input v-model="cfg.filters[slot].can_id_hex" class="text-input mono" placeholder="00000000"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Mask (hex)</label>
              <input v-model="cfg.filters[slot].mask_hex" class="text-input mono" placeholder="1FFFFFFF"/>
            </div>

            <template v-if="cfg.filters[slot].action === 2">
              <div class="rule-field">
                <label class="field-label">Remap CAN ID (hex)</label>
                <input v-model="cfg.filters[slot].remap_id_hex" class="text-input mono" placeholder="00000000"/>
              </div>
              <div class="rule-field">
                <label class="field-label">Remap Payload (hex, opt.)</label>
                <input v-model="cfg.filters[slot].rpayload_hex" class="text-input mono" placeholder="0000000000000000"/>
              </div>
              <div class="rule-field">
                <label class="field-label">Remap DLC (0=keep)</label>
                <input v-model.number="cfg.filters[slot].rdlc" type="number" min="0" max="8" class="text-input" style="max-width:90px"/>
              </div>
            </template>
          </div>
        </div>

      </section>

    </main>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from "vue"
import axios from "axios"

// ── Config ────────────────────────────────────────────────────────────────────
// Empty string → relative URLs; page is served by the MCU itself so all
// API calls go to the same host regardless of which interface (ETH or USB) is used.
const MCU   = ""
const ICONS = { Gauges:'📊', Diagnostics:'🚨', Controls:'🎛', Nodes:'🔌', 'System Info':'🖧', Filtering:'⚙' }
const RULE_SLOTS = ['r0','r1','r2','r3','r4','r5','r6','r7']

// ── Navigation ────────────────────────────────────────────────────────────────
const pages = ["Gauges", "Diagnostics", "Controls", "Nodes", "System Info", "Filtering"]
const page  = ref("Gauges")

// ── Reactive state ────────────────────────────────────────────────────────────
const telemetry = reactive({
  engine_speed: 0, vehicle_speed: 0, fuel_level: 0,
  engine_load: 0,  coolant_temp: 0,  battery_voltage: 0, throttle_pct: 0,
  status: { engine_running: false, brake: false, pto: false, cruise: false }
})
const smooth = reactive({
  engine_speed: 0, vehicle_speed: 0, fuel_level: 0,
  engine_load: 0,  coolant_temp: 0,  battery_voltage: 0
})
const system = reactive({
  ip: '—', mac: '—', gateway: '—', phy: '—',
  link_up: false, speed: '—', duplex: '—',
  uptime: 0, heap: null, tasks: null, clock: null
})
const dtc      = ref([])
const nodes    = ref([])
const throttle = ref(0)
const tx       = reactive({ pgn: '', data: '' })
const bootState = ref('idle')
const bootMsg   = ref('')

// ── Save & Apply state ────────────────────────────────────────────────────────
const saveState    = ref('idle')   // idle | saving | done | error
const defaultState = ref('idle')   // idle | confirming

// ── Local config (mirrors Config container structure) ─────────────────────────
function makeRule() {
  return { action: 0, can_id_hex: '00000000', mask_hex: '1FFFFFFF',
           remap_id_hex: '00000000', rpayload_hex: '0000000000000000', rdlc: 0 }
}
const cfg = reactive({
  board: { eth_ip: '10.104.3.64', eth_mask: '255.255.255.0', eth_gw: '10.104.3.1', usb_ip: '192.168.7.1', ptp_enable: 0 },
  can:   { j1939: 0, dlc: 8, id_hex: '00000000' },
  usb:   { usbmode: 0 },
  filters: Object.fromEntries(RULE_SLOTS.map(s => [s, makeRule()]))
})

const activeRuleCount = computed(() =>
  RULE_SLOTS.filter(s => cfg.filters[s].action !== 0).length
)

// ── Smoothing ─────────────────────────────────────────────────────────────────
setInterval(() => {
  for (const k in smooth) {
    const t = telemetry[k]
    if (typeof t === 'number') smooth[k] += (t - smooth[k]) * 0.15
  }
}, 50)

// ── Helpers ───────────────────────────────────────────────────────────────────
function severityClass(fmi) {
  if ([3,4,5,6].includes(+fmi)) return 'sev-high'
  if ([0,1,2,7].includes(+fmi)) return 'sev-med'
  return 'sev-low'
}
function formatUptime(s) {
  if (!s) return '0s'
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60
  if (h) return `${h}h ${m}m`
  if (m) return `${m}m ${sec}s`
  return `${sec}s`
}
function send(obj)    { console.log('J1939 TX:', obj) }
function sendThrottle() { send({ type: 'control', throttle: throttle.value }) }

function parseIp(s) {
  return (s || '0.0.0.0').split('.').map(n => Math.max(0, Math.min(255, parseInt(n)||0)))
}
function fmtIp(arr) { return (arr || [0,0,0,0]).join('.') }
function parseHex32(s) { return parseInt((s||'0').replace(/^0x/i,''), 16) >>> 0 }
function parseHexBytes(s, len) {
  const h = (s||'').replace(/[^0-9a-fA-F]/g,'').padEnd(len*2,'0').slice(0, len*2)
  return Array.from({length:len}, (_,i) => parseInt(h.slice(i*2,i*2+2)||'0',16))
}

// ── Inline msgpack encoder ─────────────────────────────────────────────────────
function msgpackEncode(value) {
  const out = []
  const wu8  = v => out.push(v & 0xff)
  const wu16 = v => { out.push((v>>8)&0xff, v&0xff) }
  const wu32 = v => { out.push((v>>>24)&0xff,(v>>>16)&0xff,(v>>>8)&0xff,v&0xff) }
  function enc(v) {
    if (v === null || v === undefined) { wu8(0xc0); return }
    if (typeof v === 'boolean') { wu8(v ? 0xc3 : 0xc2); return }
    if (typeof v === 'number') {
      const i = v >>> 0
      if (v >= 0 && v <= 127) { wu8(v); return }
      if (v >= 0 && v <= 255) { wu8(0xcc); wu8(v); return }
      if (v >= 0 && v <= 65535) { wu8(0xcd); wu16(v); return }
      wu8(0xce); wu32(i >>> 0); return
    }
    if (typeof v === 'string') {
      const b = new TextEncoder().encode(v)
      if (b.length <= 31) wu8(0xa0|b.length); else { wu8(0xd9); wu8(b.length) }
      for (const x of b) wu8(x)
      return
    }
    if (Array.isArray(v)) {
      if (v.length <= 15) wu8(0x90|v.length); else { wu8(0xdc); wu16(v.length) }
      for (const x of v) enc(x)
      return
    }
    const keys = Object.keys(v)
    if (keys.length <= 15) wu8(0x80|keys.length); else { wu8(0xde); wu16(keys.length) }
    for (const k of keys) { enc(k); enc(v[k]) }
  }
  enc(value)
  return new Uint8Array(out)
}

// ── Inline msgpack decoder ─────────────────────────────────────────────────────
function msgpackDecode(buf) {
  const ab = buf instanceof ArrayBuffer ? buf : buf.buffer
  const view = new DataView(ab, buf.byteOffset || 0)
  let pos = 0
  const rb  = () => view.getUint8(pos++)
  const ru16 = () => { const v=view.getUint16(pos,false); pos+=2; return v }
  const ru32 = () => { const v=view.getUint32(pos,false); pos+=4; return v }
  const rstr = n => {
    const b = new Uint8Array(ab, (buf.byteOffset||0)+pos, n); pos+=n
    return new TextDecoder().decode(b)
  }
  function read() {
    const b = rb()
    if (b <= 0x7f) return b
    if (b >= 0xe0) return b - 256
    if ((b&0xf0)===0x90) { const n=b&0x0f; return Array.from({length:n},read) }
    if ((b&0xf0)===0x80) { const n=b&0x0f; const o={}; for(let i=0;i<n;i++){const k=read();o[k]=read();} return o }
    if ((b&0xe0)===0xa0) return rstr(b&0x1f)
    switch(b) {
      case 0xc2: return false
      case 0xc3: return true
      case 0xcc: return rb()
      case 0xcd: return ru16()
      case 0xce: return ru32()
      case 0xcf: { ru32(); return ru32() }   // uint64 — drop high word
      case 0xd0: { const v=rb(); return v>=128?v-256:v }
      case 0xd9: return rstr(rb())
      case 0xda: return rstr(ru16())
      case 0xdc: { const n=ru16(); return Array.from({length:n},read) }
      case 0xde: { const n=ru16(); const o={}; for(let i=0;i<n;i++){const k=read();o[k]=read();} return o }
      default: throw new Error(`Unknown msgpack byte 0x${b.toString(16)} at ${pos-1}`)
    }
  }
  return read()
}

// ── Fetch current config from MCU (msgpack) ───────────────────────────────────
// Retries up to `retries` times on failure (device may be finishing boot).
async function fetchConfig(retries = 3) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const resp = await axios.get(`${MCU}/api/config/values`,
                                   { responseType: 'arraybuffer', timeout: 3000 })
      const decoded = msgpackDecode(new Uint8Array(resp.data))
      applyDecodedConfig(decoded)
      return // success
    } catch (_) {
      if (attempt < retries)
        await new Promise(r => setTimeout(r, 2000))
    }
  }
}

function applyDecodedConfig(d) {
  if (!d) return
  if (d.board) {
    if (d.board.eth_ip)            cfg.board.eth_ip    = fmtIp(d.board.eth_ip)
    if (d.board.eth_mask)          cfg.board.eth_mask  = fmtIp(d.board.eth_mask)
    if (d.board.eth_gw)            cfg.board.eth_gw    = fmtIp(d.board.eth_gw)
    if (d.board.usb_ip)            cfg.board.usb_ip    = fmtIp(d.board.usb_ip)
    if (d.board.ptp_enable !== undefined) cfg.board.ptp_enable = d.board.ptp_enable
  }
  if (d.can) {
    if (d.can.j1939 !== undefined) cfg.can.j1939  = d.can.j1939
    if (d.can.dlc   !== undefined) cfg.can.dlc    = d.can.dlc
    if (d.can.id    !== undefined) cfg.can.id_hex = d.can.id.toString(16).padStart(8,'0').toUpperCase()
  }
  if (d.usb && d.usb.usbmode !== undefined) cfg.usb.usbmode = d.usb.usbmode
  if (d.filters) {
    for (const slot of RULE_SLOTS) {
      const r = d.filters[slot]
      if (!r) continue
      const fc = cfg.filters[slot]
      fc.action      = r.action      ?? 0
      fc.can_id_hex  = (r.can_id    ?? 0).toString(16).padStart(8,'0').toUpperCase()
      fc.mask_hex    = (r.mask      ?? 0x1FFFFFFF).toString(16).padStart(8,'0').toUpperCase()
      fc.remap_id_hex= (r.remap_id  ?? 0).toString(16).padStart(8,'0').toUpperCase()
      fc.rdlc        = r.rdlc ?? 0
      fc.rpayload_hex= (r.rpayload ?? [0,0,0,0,0,0,0,0])
                        .map(b => b.toString(16).padStart(2,'0')).join('').toUpperCase()
    }
  }
}

// ── Build msgpack payload from cfg state ──────────────────────────────────────
function buildConfigPayload() {
  const filters = {}
  for (const slot of RULE_SLOTS) {
    const fc = cfg.filters[slot]
    filters[slot] = {
      can_id:   parseHex32(fc.can_id_hex),
      mask:     parseHex32(fc.mask_hex),
      remap_id: parseHex32(fc.remap_id_hex),
      action:   fc.action,
      rflags:   (fc.action === 2 ? ((fc.remap_id_hex !== '00000000' ? 1 : 0) | (fc.rpayload_hex && fc.rpayload_hex !== '0000000000000000' ? 2 : 0)) : 0),
      rdlc:     fc.rdlc,
      rpayload: parseHexBytes(fc.rpayload_hex, 8)
    }
  }
  return {
    board: {
      eth_ip:     parseIp(cfg.board.eth_ip),
      eth_mask:   parseIp(cfg.board.eth_mask),
      eth_gw:     parseIp(cfg.board.eth_gw),
      usb_ip:     parseIp(cfg.board.usb_ip),
      ptp_enable: cfg.board.ptp_enable
    },
    can: {
      dlc:   cfg.can.dlc,
      id:    parseHex32(cfg.can.id_hex),
      j1939: cfg.can.j1939
    },
    usb:     { usbmode: cfg.usb.usbmode },
    filters
  }
}

// ── Save & Apply ──────────────────────────────────────────────────────────────
async function saveAndApply() {
  if (saveState.value === 'saving' || saveState.value === 'rebooting') return
  saveState.value = 'saving'
  try {
    const payload = msgpackEncode(buildConfigPayload())
    await axios.post(`${MCU}/api/sendconfig`, payload, {
      headers: { 'Content-Type': 'application/octet-stream' },
      timeout: 5000
    })
  } catch (e) {
    // e.response = server returned an error; no e.response = device reset mid-request (success)
    if (e.response) {
      saveState.value = 'error'
      setTimeout(() => { saveState.value = 'idle' }, 4000)
      return
    }
  }
  // Device is rebooting — poll /api/info every 2 s until it responds, then reload
  saveState.value = 'rebooting'
  for (let i = 0; i < 25; i++) {
    await new Promise(r => setTimeout(r, 2000))
    try {
      await axios.get(`${MCU}/api/info`, { timeout: 2000 })
      window.location.reload()
      return
    } catch (_) {}
  }
  saveState.value = 'error'
  setTimeout(() => { saveState.value = 'idle' }, 6000)
}

// ── Reset to Defaults ─────────────────────────────────────────────────────────
function applyDefaults() {
  cfg.board.eth_ip     = '10.104.3.64'
  cfg.board.eth_mask   = '255.255.255.0'
  cfg.board.eth_gw     = '10.104.3.1'
  cfg.board.usb_ip     = '192.168.7.1'
  cfg.board.ptp_enable = 0
  cfg.can.j1939  = 0
  cfg.can.dlc    = 8
  cfg.can.id_hex = '00000000'
  cfg.usb.usbmode = 0
  for (const s of RULE_SLOTS) Object.assign(cfg.filters[s], makeRule())
  defaultState.value = 'idle'
  saveAndApply()
}

// ── API fetchers ──────────────────────────────────────────────────────────────
async function fetchTelemetry() {
  try {
    const d = (await axios.get(`${MCU}/api/telemetry`)).data
    telemetry.engine_speed    = d.engine_speed    ?? telemetry.engine_speed
    telemetry.vehicle_speed   = d.vehicle_speed   ?? telemetry.vehicle_speed
    telemetry.fuel_level      = d.fuel_level      ?? telemetry.fuel_level
    telemetry.engine_load     = d.engine_load     ?? telemetry.engine_load
    telemetry.coolant_temp    = d.coolant_temp    ?? telemetry.coolant_temp
    telemetry.battery_voltage = d.battery_voltage ?? telemetry.battery_voltage
    telemetry.throttle_pct    = d.throttle_pct    ?? telemetry.throttle_pct
    if (d.status) Object.assign(telemetry.status, d.status)
  } catch (_) {}
}
async function fetchDTC() {
  try { dtc.value = (await axios.get(`${MCU}/api/dtc`)).data.active ?? [] } catch (_) {}
}
async function fetchNodes() {
  try { nodes.value = (await axios.get(`${MCU}/api/nodes`)).data.nodes ?? [] } catch (_) {}
}
async function fetchSystemInfo() {
  try {
    const d = (await axios.get(`${MCU}/api/info`)).data
    Object.assign(system, d)
    if (d.uptimeSec !== undefined) system.uptime = d.uptimeSec
  } catch (_) {}
}

async function confirmBootloader() {
  bootState.value = 'sending'
  try {
    await axios.post(`${MCU}/api/bootloader`, {}, { timeout: 2000 })
    bootState.value = 'done'
  } catch (e) {
    if (!e.response) bootState.value = 'done'
    else { bootState.value = 'error'; bootMsg.value = e.message || 'Unknown error' }
  }
}

onMounted(() => {
  fetchTelemetry(); fetchDTC(); fetchNodes(); fetchSystemInfo(); fetchConfig()
  setInterval(fetchTelemetry,  200)
  setInterval(fetchDTC,       2000)
  setInterval(fetchNodes,     5000)
  setInterval(fetchSystemInfo,5000)
})

// ── Components ────────────────────────────────────────────────────────────────
const ARC_PATH = "M 46.3 151.7 A 76 76 0 1 1 153.7 151.7"
const ARC_LEN  = 358.1

const Gauge = {
  props: ['title', 'value', 'max', 'unit', 'color'],
  setup(props) {
    const pct        = computed(() => Math.min(Math.max((props.value || 0) / props.max, 0), 1))
    const dashOffset = computed(() => ARC_LEN * (1 - pct.value))
    const dashArray  = `${ARC_LEN} 999`
    const valText    = computed(() => (props.value || 0).toFixed(0))
    return { pct, dashOffset, dashArray, valText, ARC_PATH }
  },
  template: `
  <div class="gauge-card">
    <svg :viewBox="'0 0 200 165'" class="gauge-svg">
      <path :d="ARC_PATH" fill="none" stroke="#1a2a3a" stroke-width="10" stroke-linecap="round"/>
      <path :d="ARC_PATH" fill="none" :stroke="color" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="dashArray" :stroke-dashoffset="dashOffset" class="arc-fill"/>
      <text x="100" y="90"  text-anchor="middle" class="g-val">{{ valText }}</text>
      <text x="100" y="108" text-anchor="middle" class="g-unit">{{ unit }}</text>
      <text x="100" y="146" text-anchor="middle" class="g-title">{{ title }}</text>
      <text x="28"  y="157" text-anchor="middle" class="g-minmax">0</text>
      <text x="172" y="157" text-anchor="middle" class="g-minmax">{{ max }}</text>
    </svg>
  </div>`
}

const MetricCard = {
  props: ['icon', 'label', 'value', 'unit', 'warn'],
  template: `
  <div :class="['metric-card', { 'metric-warn': warn }]">
    <div class="metric-icon">{{ icon }}</div>
    <div class="metric-val">{{ value }}<span class="metric-unit"> {{ unit }}</span></div>
    <div class="metric-label">{{ label }}</div>
  </div>`
}

const StatusRow = {
  props: ['label', 'on'],
  template: `
  <div class="status-row">
    <span :class="['s-dot', { 's-on': on }]"></span>
    <span class="s-label">{{ label }}</span>
    <span :class="['s-pill', { 's-pill-on': on }]">{{ on ? 'ON' : 'OFF' }}</span>
  </div>`
}

const InfoRow = {
  props: ['label', 'value'],
  template: `
  <div class="info-row">
    <span class="ir-label">{{ label }}</span>
    <slot name="val"><span class="ir-value">{{ value || '—' }}</span></slot>
  </div>`
}

const CfgField = {
  props: ['label', 'modelValue', 'placeholder'],
  emits: ['update:modelValue'],
  template: `
  <div class="rule-field">
    <label class="field-label">{{ label }}</label>
    <input :value="modelValue" @input="$emit('update:modelValue', $event.target.value)"
           class="text-input mono" :placeholder="placeholder"/>
  </div>`
}
</script>

<style>
/* ── Design tokens ─────────────────────────────────────────────────────────── */
:root {
  --bg:       #070d1a;
  --surface:  #0c1525;
  --card:     #101e33;
  --card2:    #121f35;
  --border:   #1b2d47;
  --primary:  #3b82f6;
  --success:  #10b981;
  --warning:  #f59e0b;
  --danger:   #ef4444;
  --purple:   #8b5cf6;
  --text:     #e2e8f0;
  --muted:    #64748b;
  --dim:      #1e3048;
  --radius:   14px;
  --radius-sm:8px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  overflow: hidden;
}

/* ── Layout ──────────────────────────────────────────────────────────────── */
.app  { display: flex; height: 100vh; }
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
.sidebar {
  width: 220px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  gap: 4px;
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}
.brand-icon { font-size: 26px; }
.brand-name { font-weight: 700; font-size: 15px; letter-spacing: 0.3px; }
.brand-sub  { font-size: 11px; color: var(--muted); margin-top: 1px; }

/* ── Save & Apply button ─────────────────────────────────────────────────── */
.save-btn {
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  margin-bottom: 12px;
  transition: opacity 0.15s, background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
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

/* ── Topbar ──────────────────────────────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  flex-shrink: 0;
}
.topbar-title { font-size: 20px; font-weight: 700; }
.topbar-sub   { font-size: 12px; color: var(--muted); margin-top: 2px; }

.conn-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.conn-badge .conn-dot { width: 7px; height: 7px; border-radius: 50%; }
.conn-up   { background: rgba(16,185,129,0.15); color: #34d399; }
.conn-up   .conn-dot { background: #10b981; }
.conn-down { background: rgba(239,68,68,0.15);  color: #f87171; }
.conn-down .conn-dot { background: #ef4444; }

/* ── Page scroll wrapper ─────────────────────────────────────────────────── */
.gauges-page, .content-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

/* ── Gauges page ─────────────────────────────────────────────────────────── */
.gauges-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 1100px) { .gauges-grid { grid-template-columns: repeat(2, 1fr); } }

.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1.3fr;
  gap: 16px;
}
@media (max-width: 900px) { .bottom-row { grid-template-columns: 1fr 1fr; } }

.gauge-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 8px 8px;
}
.gauge-svg { width: 100%; display: block; }
.arc-fill {
  transition: stroke-dashoffset 0.7s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.4s ease;
}
.g-val   { font-size: 34px; font-weight: 700; fill: var(--text); font-family: inherit; }
.g-unit  { font-size: 13px; fill: var(--muted); font-family: inherit; }
.g-title { font-size: 12px; fill: var(--muted); font-family: inherit; }
.g-minmax{ font-size: 10px; fill: #2a3f58; font-family: inherit; }

/* ── Metric cards ────────────────────────────────────────────────────────── */
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color 0.3s;
}
.metric-card.metric-warn { border-color: var(--warning); }
.metric-icon  { font-size: 22px; }
.metric-val   { font-size: 26px; font-weight: 700; line-height: 1; }
.metric-unit  { font-size: 14px; font-weight: 400; color: var(--muted); }
.metric-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Status card ─────────────────────────────────────────────────────────── */
.status-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px;
  display: flex; flex-direction: column; gap: 10px;
}
.status-card-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 2px; }
.status-row { display: flex; align-items: center; gap: 8px; }
.s-dot { width: 8px; height: 8px; border-radius: 50%; background: #ef4444; flex-shrink: 0; }
.s-dot.s-on { background: var(--success); box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.s-label { flex: 1; font-size: 13px; color: var(--text); }
.s-pill { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 10px; background: rgba(239,68,68,0.15); color: #f87171; }
.s-pill.s-pill-on { background: rgba(16,185,129,0.15); color: #34d399; }

/* ── Content panel ───────────────────────────────────────────────────────── */
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }

.panel-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.panel-title { font-size: 18px; font-weight: 700; }

.fault-badge, .count-badge {
  padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
}
.fault-active { background: rgba(239,68,68,0.15); color: #f87171; }
.fault-clear  { background: rgba(16,185,129,0.15); color: #34d399; }
.count-badge  { background: rgba(59,130,246,0.15); color: #60a5fa; }

/* ── Table ───────────────────────────────────────────────────────────────── */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 10px 12px; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted);
  border-bottom: 1px solid var(--border);
}
.data-table td { padding: 11px 12px; font-size: 14px; border-bottom: 1px solid var(--dim); }
.data-table tbody tr:hover { background: rgba(255,255,255,0.02); }
.data-table tr.sev-high { border-left: 3px solid var(--danger); }
.data-table tr.sev-med  { border-left: 3px solid var(--warning); }
.data-table tr.sev-low  { border-left: 3px solid var(--muted); }
.fmi-pill { padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 700; }
.fmi-pill.sev-high { background: rgba(239,68,68,0.2);  color: #f87171; }
.fmi-pill.sev-med  { background: rgba(245,158,11,0.2); color: #fbbf24; }
.fmi-pill.sev-low  { background: rgba(100,116,139,0.2);color: #94a3b8; }

.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.bold { font-weight: 700; }

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 60px 20px; color: var(--muted); gap: 12px; }
.empty-icon { font-size: 48px; }
.empty-state p { font-size: 15px; }

/* ── Controls ────────────────────────────────────────────────────────────── */
.controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.ctrl-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
  display: flex; flex-direction: column; gap: 12px;
}
.ctrl-title  { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); }
.ctrl-bigval { font-size: 42px; font-weight: 700; line-height: 1; }
.ctrl-unit   { font-size: 20px; font-weight: 400; color: var(--muted); }

.slider {
  -webkit-appearance: none; width: 100%; height: 4px;
  background: var(--dim); border-radius: 2px; outline: none; cursor: pointer;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none; width: 18px; height: 18px;
  border-radius: 50%; background: var(--primary);
  box-shadow: 0 0 8px rgba(59,130,246,0.5); cursor: pointer;
}

.text-input {
  width: 100%; padding: 9px 12px;
  background: var(--dim); border: 1px solid var(--border);
  border-radius: var(--radius-sm); color: var(--text);
  font-size: 13px; font-family: inherit; outline: none;
  transition: border-color 0.15s;
}
.text-input:focus { border-color: var(--primary); }

.btn {
  width: 100%; padding: 11px; border: none; border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s, transform 0.1s;
}
.btn:hover  { opacity: 0.88; }
.btn:active { transform: scale(0.98); }
.btn-primary { background: var(--primary); color: #fff; }
.btn-success { background: var(--success); color: #fff; }
.btn-danger  { background: var(--danger);  color: #fff; }

/* ── Nodes ───────────────────────────────────────────────────────────────── */
.nodes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
.node-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px 16px;
  display: flex; flex-direction: column; align-items: center;
  gap: 6px; text-align: center; transition: border-color 0.2s;
}
.node-card:hover { border-color: var(--primary); }
.node-online-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--success); box-shadow: 0 0 8px rgba(16,185,129,0.6); margin-bottom: 4px; }
.node-addr { font-family: monospace; font-size: 20px; font-weight: 700; color: var(--primary); }
.node-dec  { font-size: 12px; color: var(--muted); }
.node-status-label { font-size: 11px; color: var(--success); font-weight: 600; letter-spacing: 0.5px; }

/* ── System Info ─────────────────────────────────────────────────────────── */
.info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.info-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
  display: flex; flex-direction: column; gap: 12px;
}
.info-card-title {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted);
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}
.info-row { display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
.ir-label { color: var(--muted); }
.ir-value { font-weight: 600; font-family: monospace; font-size: 13px; }
.pill-up   { background: rgba(16,185,129,0.15); color: #34d399; padding: 2px 10px; border-radius: 10px; font-weight: 700; font-size: 12px; }
.pill-down { background: rgba(239,68,68,0.15);  color: #f87171; padding: 2px 10px; border-radius: 10px; font-weight: 700; font-size: 12px; }
.device-status { font-size: 28px; font-weight: 800; text-align: center; padding: 16px; border-radius: var(--radius-sm); letter-spacing: 2px; }
.dev-online  { background: rgba(16,185,129,0.1); color: #34d399; }
.dev-offline { background: rgba(239,68,68,0.1);  color: #f87171; }

/* ── PTP card ────────────────────────────────────────────────────────────── */
.ptp-card {
  margin-top: 20px; background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px 24px;
  display: flex; flex-direction: column; gap: 14px; max-width: 560px;
}
.ptp-row  { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.ptp-label { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.ptp-desc  { font-size: 13px; color: var(--muted); line-height: 1.5; }

.toggle-switch { position: relative; display: inline-block; width: 48px; height: 26px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute; cursor: pointer; inset: 0;
  background: var(--dim); border: 1px solid var(--border);
  border-radius: 13px; transition: background 0.2s, border-color 0.2s;
}
.toggle-slider::before {
  content: ''; position: absolute;
  width: 18px; height: 18px; left: 3px; top: 3px;
  background: var(--muted); border-radius: 50%; transition: transform 0.2s, background 0.2s;
}
.toggle-switch input:checked + .toggle-slider {
  background: rgba(59,130,246,0.25); border-color: var(--primary);
}
.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(22px); background: var(--primary);
}

/* ── Bootloader card ──────────────────────────────────────────────────────── */
.boot-card {
  margin-top: 20px; background: var(--card); border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius); padding: 20px 24px;
  display: flex; flex-direction: column; gap: 14px; max-width: 560px;
}
.boot-card-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.boot-desc  { font-size: 13px; color: var(--muted); line-height: 1.6; }
.boot-url   { color: var(--text); font-family: monospace; font-weight: 600; }
.boot-warn  { font-size: 13px; color: #fbbf24; line-height: 1.6; }
.boot-ok    { font-size: 14px; color: #34d399; font-weight: 600; }
.boot-err   { font-size: 13px; color: #f87171; }
.boot-link  { color: var(--primary); text-decoration: none; font-family: monospace; font-weight: 600; }
.boot-link:hover { text-decoration: underline; }
.boot-btn       { margin-top: 4px; }
.boot-btn-half  { flex: 1; }
.boot-row       { display: flex; gap: 10px; }
.btn-neutral { background: var(--dim); color: var(--muted); border: 1px solid var(--border); }
.btn-neutral:hover { color: var(--text); }
.boot-spinner-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; }
.boot-spinner { width: 20px; height: 20px; border: 2px solid var(--border); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.boot-sending-txt { font-size: 13px; color: var(--muted); }

code { font-family: 'JetBrains Mono', monospace; font-size: 12px; background: var(--dim); padding: 1px 5px; border-radius: 4px; color: var(--text); }

/* ── Filtering / Config page ─────────────────────────────────────────────── */
.cfg-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px;
  margin-bottom: 12px;
}
.cfg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.mode-desc { font-size: 13px; color: var(--muted); line-height: 1.55; }

/* ── Filter rule cards ───────────────────────────────────────────────────── */
.rule-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: 14px 16px;
  margin-bottom: 8px;
}
.rule-card-head {
  display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
}
.rule-slot-num {
  font-size: 12px; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.5px; min-width: 44px;
}
.rule-action-sel { width: 140px; flex-shrink: 0; }
.rule-disabled-lbl { font-size: 12px; color: var(--muted); font-style: italic; }
.rule-fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  padding-left: 56px;
}
.rule-field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
</style>
