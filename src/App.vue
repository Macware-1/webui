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

        <!-- ── Bootloader / OTA card ──────────────────────────────────────── -->
        <div class="boot-card">
          <div class="boot-card-title">Firmware Update</div>

          <!-- idle -->
          <template v-if="bootState === 'idle'">
            <p class="boot-desc">
              Reboot the device into bootloader mode to upload a new firmware
              image via the OTA web interface at <span class="boot-url">192.168.1.100</span>.
            </p>
            <button class="btn btn-danger boot-btn" @click="bootState = 'confirming'">
              ↩ Enter Bootloader Mode
            </button>
          </template>

          <!-- confirming -->
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

          <!-- sending -->
          <template v-else-if="bootState === 'sending'">
            <div class="boot-spinner-row">
              <div class="boot-spinner"></div>
              <span class="boot-sending-txt">Sending reset command…</span>
            </div>
          </template>

          <!-- done -->
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

          <!-- error -->
          <template v-else-if="bootState === 'error'">
            <p class="boot-err">✕ {{ bootMsg }}</p>
            <button class="btn btn-neutral boot-btn" style="margin-top:10px"
                    @click="bootState = 'idle'">Retry</button>
          </template>
        </div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from "vue"
import axios from "axios"

// ── Config ───────────────────────────────────────────────────────────────────
const MCU   = "http://10.104.3.64"
const ICONS = { Gauges:'📊', Diagnostics:'🚨', Controls:'🎛', Nodes:'🔌', 'System Info':'🖧' }

// ── Navigation ────────────────────────────────────────────────────────────────
const pages = ["Gauges", "Diagnostics", "Controls", "Nodes", "System Info"]
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
const tx = reactive({ pgn: '', data: '' })

const bootState = ref('idle')   // idle | confirming | sending | done | error
const bootMsg   = ref('')

// ── Smoothing (exponential moving average) ────────────────────────────────────
setInterval(() => {
  for (const k in smooth) {
    const t = telemetry[k]
    if (typeof t === 'number') smooth[k] += (t - smooth[k]) * 0.15
  }
}, 50)

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

onMounted(() => {
  fetchTelemetry(); fetchDTC(); fetchNodes(); fetchSystemInfo()
  setInterval(fetchTelemetry,  200)
  setInterval(fetchDTC,       2000)
  setInterval(fetchNodes,     5000)
  setInterval(fetchSystemInfo,5000)
})

// ── Helpers ───────────────────────────────────────────────────────────────────
function severityClass(fmi) {
  if ([3,4,5,6].includes(+fmi)) return 'sev-high'
  if ([0,1,2,7].includes(+fmi)) return 'sev-med'
  return 'sev-low'
}

function formatUptime(s) {
  if (!s) return '0s'
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60
  if (h) return `${h}h ${m}m`
  if (m) return `${m}m ${sec}s`
  return `${sec}s`
}

function send(obj) { console.log('J1939 TX:', obj) }
function sendThrottle() { send({ type: 'control', throttle: throttle.value }) }

async function confirmBootloader() {
  bootState.value = 'sending'
  try {
    await axios.post(`${MCU}/api/bootloader`, {}, { timeout: 2000 })
    bootState.value = 'done'
  } catch (e) {
    // A network error here likely means the device already reset — treat as success.
    if (!e.response) {
      bootState.value = 'done'
    } else {
      bootState.value = 'error'
      bootMsg.value = e.message || 'Unknown error'
    }
  }
}

// ── Components ────────────────────────────────────────────────────────────────
//
//  Arc gauge geometry:
//    viewBox 200×165, center (100, 98), r=76
//    270° arc: start 135°→ end 45° (clockwise, large-arc-flag=1)
//    Endpoints: M 46.3 151.7  A 76 76 0 1 1  153.7 151.7
//    Arc length = 2π × 76 × 0.75 ≈ 358.1
//
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
      <!-- Track -->
      <path :d="ARC_PATH" fill="none" stroke="#1a2a3a" stroke-width="10" stroke-linecap="round"/>
      <!-- Value arc -->
      <path :d="ARC_PATH" fill="none" :stroke="color" stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="dashArray" :stroke-dashoffset="dashOffset" class="arc-fill"/>
      <!-- Value -->
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
  padding: 0 8px 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}
.brand-icon { font-size: 26px; }
.brand-name { font-weight: 700; font-size: 15px; letter-spacing: 0.3px; }
.brand-sub  { font-size: 11px; color: var(--muted); margin-top: 1px; }

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
  width: 8px;
  height: 8px;
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
.conn-badge .conn-dot {
  width: 7px; height: 7px; border-radius: 50%;
}
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

/* ── Gauge card ──────────────────────────────────────────────────────────── */
.gauge-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 8px 8px;
}
.gauge-svg { width: 100%; display: block; }

/* Arc animation */
.arc-fill {
  transition: stroke-dashoffset 0.7s cubic-bezier(0.4, 0, 0.2, 1),
              stroke 0.4s ease;
}

/* SVG text classes */
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
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.status-card-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--muted);
  margin-bottom: 2px;
}
.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.s-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #ef4444;
  flex-shrink: 0;
}
.s-dot.s-on { background: var(--success); box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.s-label { flex: 1; font-size: 13px; color: var(--text); }
.s-pill {
  font-size: 10px; font-weight: 700; padding: 2px 7px;
  border-radius: 10px; background: rgba(239,68,68,0.15); color: #f87171;
}
.s-pill.s-pill-on { background: rgba(16,185,129,0.15); color: #34d399; }

/* ── Content panel ───────────────────────────────────────────────────────── */
.content-panel { flex: 1; overflow-y: auto; padding: 24px; }

.panel-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.panel-title { font-size: 18px; font-weight: 700; }

.fault-badge, .count-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.fault-active { background: rgba(239,68,68,0.15); color: #f87171; }
.fault-clear  { background: rgba(16,185,129,0.15); color: #34d399; }
.count-badge  { background: rgba(59,130,246,0.15); color: #60a5fa; }

/* ── Table ───────────────────────────────────────────────────────────────── */
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
.data-table td {
  padding: 11px 12px;
  font-size: 14px;
  border-bottom: 1px solid var(--dim);
}
.data-table tbody tr:hover { background: rgba(255,255,255,0.02); }

.data-table tr.sev-high { border-left: 3px solid var(--danger); }
.data-table tr.sev-med  { border-left: 3px solid var(--warning); }
.data-table tr.sev-low  { border-left: 3px solid var(--muted); }

.fmi-pill {
  padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 700;
}
.fmi-pill.sev-high { background: rgba(239,68,68,0.2);  color: #f87171; }
.fmi-pill.sev-med  { background: rgba(245,158,11,0.2); color: #fbbf24; }
.fmi-pill.sev-low  { background: rgba(100,116,139,0.2);color: #94a3b8; }

.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
.bold { font-weight: 700; }

/* ── Empty state ─────────────────────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: var(--muted);
  gap: 12px;
}
.empty-icon { font-size: 48px; }
.empty-state p { font-size: 15px; }

/* ── Controls ────────────────────────────────────────────────────────────── */
.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}
.ctrl-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ctrl-title  { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); }
.ctrl-bigval { font-size: 42px; font-weight: 700; line-height: 1; }
.ctrl-unit   { font-size: 20px; font-weight: 400; color: var(--muted); }

.slider {
  -webkit-appearance: none;
  width: 100%; height: 4px;
  background: var(--dim);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 8px rgba(59,130,246,0.5);
  cursor: pointer;
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
  width: 100%; padding: 11px;
  border: none; border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s, transform 0.1s;
}
.btn:hover  { opacity: 0.88; }
.btn:active { transform: scale(0.98); }
.btn-primary { background: var(--primary); color: #fff; }
.btn-success { background: var(--success); color: #fff; }
.btn-danger  { background: var(--danger);  color: #fff; }

/* ── Nodes ───────────────────────────────────────────────────────────────── */
.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}
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
.node-online-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px rgba(16,185,129,0.6);
  margin-bottom: 4px;
}
.node-addr { font-family: monospace; font-size: 20px; font-weight: 700; color: var(--primary); }
.node-dec  { font-size: 12px; color: var(--muted); }
.node-status-label { font-size: 11px; color: var(--success); font-weight: 600; letter-spacing: 0.5px; }

/* ── System Info ─────────────────────────────────────────────────────────── */
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
.info-card-title {
  font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.8px; color: var(--muted);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.ir-label { color: var(--muted); }
.ir-value { font-weight: 600; font-family: monospace; font-size: 13px; }

.pill-up   { background: rgba(16,185,129,0.15); color: #34d399; padding: 2px 10px; border-radius: 10px; font-weight: 700; font-size: 12px; }
.pill-down { background: rgba(239,68,68,0.15);  color: #f87171; padding: 2px 10px; border-radius: 10px; font-weight: 700; font-size: 12px; }

.device-status {
  font-size: 28px; font-weight: 800;
  text-align: center; padding: 16px;
  border-radius: var(--radius-sm);
  letter-spacing: 2px;
}
.dev-online { background: rgba(16,185,129,0.1);  color: #34d399; }
.dev-offline { background: rgba(239,68,68,0.1);  color: #f87171; }

/* ── Bootloader card ──────────────────────────────────────────────────────── */
.boot-card {
  margin-top: 20px;
  background: var(--card);
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: var(--radius);
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 560px;
}
.boot-card-title {
  font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.8px; color: var(--muted);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
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

.btn-neutral {
  background: var(--dim);
  color: var(--muted);
  border: 1px solid var(--border);
}
.btn-neutral:hover { color: var(--text); }

.boot-spinner-row {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 0;
}
.boot-spinner {
  width: 20px; height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }
.boot-sending-txt { font-size: 13px; color: var(--muted); }

code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  background: var(--dim);
  padding: 1px 5px;
  border-radius: 4px;
  color: var(--text);
}
</style>
