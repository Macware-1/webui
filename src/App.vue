<template>
  <div class="app">

    <!-- ── SIDEBAR ─────────────────────────────────────────────────────── -->
    <Sidebar
      :page="page"
      :pages="pages"
      :icons="ICONS"
      :saveState="saveState"
      :defaultState="defaultState"
      :system="system"
      :formatUptime="formatUptime"
      :collapsed="sidebarCollapsed"
      @save="saveAndApply"
      @confirm-default="defaultState = 'confirming'"
      @apply-defaults="applyDefaults"
      @cancel-default="defaultState = 'idle'"
      @update:page="page = $event"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
    />

    <!-- Mobile fixed toggle (outside sidebar transform) -->
    <Button
      class="mobile-collapse-toggle"
      :class="{ collapsed: sidebarCollapsed }"
      variant="primary"
      size="lg"
      @click="sidebarCollapsed = !sidebarCollapsed"
      :aria-label="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      {{ sidebarCollapsed ? '»' : '«' }}
    </Button>

    <main class="main">
      <TopBar :page="page" :system="system" />

      <GaugesPage v-if="page === 'Gauges'" :smooth="smooth" :telemetry="telemetry" />
      <DiagnosticsPage v-else-if="page === 'Diagnostics'" :dtc="dtc" :severityClass="severityClass" />
      <ControlsPage
        v-else-if="page === 'Controls'"
        :throttle="throttle"
        :tx="tx"
        @update:throttle="val => throttle.value = val"
        @update:tx="val => Object.assign(tx, val)"
        @send-throttle="sendThrottle"
        @send-control="send"
        @send-frame="sendCanFrame"
      />
      <NodesPage v-else-if="page === 'Nodes'" :nodes="nodes" />
      <SystemInfoPage v-else-if="page === 'System Info'" :system="system" :cfg="cfg" :formatUptime="formatUptime" />
      <LoggingPage v-else-if="page === 'Logging'" :cfg="cfg" :system="system" @open-channel="openChanPopup" @open-ethernet="openEthernetPopup" />
      <CANBusPage
        v-else-if="page === 'CAN Bus'"
        :cfg="cfg"
        :nomBitrate="nomBitrate"
        :nomSamplePt="nomSamplePt"
        :dataBitrate="dataBitrate"
        :dataSamplePt="dataSamplePt"
        @apply-nom-preset="applyNomPreset"
        @apply-data-preset="applyDataPreset"
      />
      <CANReplayPage v-else-if="page === 'CAN Replay'" :inject="inject" :injectDlc="injectDlc" :system="system" @send-can-frame="sendCanFrame" />
      <FilteringPage v-else-if="page === 'Filtering'" :cfg="cfg" :RULE_SLOTS="RULE_SLOTS" :activeRuleCount="activeRuleCount" />
      <RadxaPage
        v-else-if="page === 'Wifi'"
        :radxa="radxa"
        :radxaEdit="radxaEdit"
        :wifiStatusText="wifiStatusText"
        :wifiStatusClass="wifiStatusClass"
        :formatUptime="formatUptime"
        :radxaRebootState="radxaRebootState"
        @wifi-toggle="radxaSendWifiEnable"
        @wifi-connect="radxaWifiConnect"
        @apply-data="radxaApplyData"
        @request-reboot="requestRadxaReboot"
        @confirm-reboot="doRadxaReboot"
        @cancel-reboot="cancelRadxaReboot"
        @reset-reboot-state="resetRadxaRebootState"
      />
    </main>
  </div>

    <ChannelConfigPopup
      :chanPopup="chanPopup"
      :popupEdit="popupEdit"
      @close="chanPopup.open = false"
      @apply="saveChanPopup"
      @open-ethernet="openEthernetPopup"
    />
    <EthernetConfigPopup
      :ethPopup="ethPopup"
      :ethPopupEdit="ethPopupEdit"
      @close="ethPopup.open = false"
      @apply="saveEthernetPopup"
    />
</template>

<script setup>
import { reactive, ref, computed, onMounted } from "vue"
import axios from "axios"
import Sidebar from "./components/views/Sidebar.vue"
import TopBar from "./components/views/TopBar.vue"
import GaugesPage from "./pages/GaugesPage.vue"
import DiagnosticsPage from "./pages/DiagnosticsPage.vue"
import ControlsPage from "./pages/ControlsPage.vue"
import NodesPage from "./pages/NodesPage.vue"
import SystemInfoPage from "./pages/SystemInfoPage.vue"
import LoggingPage from "./pages/LoggingPage.vue"
import CANBusPage from "./pages/CANBusPage.vue"
import CANReplayPage from "./pages/CANReplayPage.vue"
import FilteringPage from "./pages/FilteringPage.vue"
import RadxaPage from "./pages/RadxaPage.vue"
import ChannelConfigPopup from "./components/views/ChannelConfigPopup.vue"
import EthernetConfigPopup from "./components/views/EthernetConfigPopup.vue"
import Button from "./components/ui/Button.vue"

// ── Config ────────────────────────────────────────────────────────────────────
// Empty string → relative URLs; page is served by the MCU itself so all
// API calls go to the same host regardless of which interface (ETH or USB) is used.
const MCU   = ""
const ICONS = { Gauges:'📊', Diagnostics:'🚨', Controls:'🎛', Nodes:'🔌', 'System Info':'🖧', Logging:'📋', 'CAN Bus':'📡', 'CAN Replay':'▶', Filtering:'⚙', Wifi:'📶' }
const RULE_SLOTS = ['r0','r1','r2','r3','r4','r5','r6','r7']

// ── Navigation ────────────────────────────────────────────────────────────────
const pages = ["Gauges", "Diagnostics", "Controls", "Nodes", "System Info", "Logging", "CAN Bus", "CAN Replay", "Filtering", "Wifi"]
const page  = ref("Gauges")
const sidebarCollapsed = ref(false)

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

// ── Radxa state ────────────────────────────────────────────────────────────────
const radxa = reactive({
  alive: false, heartbeat: 0, status: 0, version: '', uptime: 0,
  wifi_status: 0, wifi_ip: '', wifi_rssi: 0, wifi_enable: false,
  data_enable: false, dest_ip: '', dest_port: 47808,
  pkts_fwd: 0, pkts_drop: 0,
})
const radxaEdit = reactive({
  wifiEnable: false, ssid: '', password: '',
  wifiResult: '', wifiOk: false,
  dataEnable: false, destIp: '', destPort: 47808,
  dataResult: '', dataOk: false,
})
const radxaRebootState = ref('idle')

const wifiStatusText = computed(() =>
  (['Off / Down', 'Connecting…', 'Connected', 'Hotspot'])[radxa.wifi_status] ?? 'Unknown'
)
const wifiStatusClass = computed(() => {
  if (radxa.wifi_status === 2) return 'wifi-dot-connected'
  if (radxa.wifi_status === 1) return 'wifi-dot-connecting'
  return 'wifi-dot-down'
})

// ── CAN Replay state ──────────────────────────────────────────────────────────
const inject = reactive({ id: '0x123', data: '0102030405060708', fd: false, brs: false, sending: false, result: '', ok: false })

const injectDlc = computed(() => {
  const hex = inject.data.replace(/\s/g, '')
  const byteCount = Math.floor(hex.length / 2)
  const maxBytes  = inject.fd ? 64 : 8
  const clamped   = Math.min(byteCount, maxBytes)
  const lenTab    = [0,1,2,3,4,5,6,7,8,12,16,20,24,32,48,64]
  let dlc = 0
  for (let i = 0; i < 16; i++) { if (lenTab[i] >= clamped) { dlc = i; break; } }
  return `${dlc} (${clamped} byte${clamped !== 1 ? 's' : ''})`
})

async function sendCanFrame() {
  inject.sending = true
  inject.result  = ''
  try {
    const body = JSON.stringify({ id: inject.id, data: inject.data.replace(/\s/g,''), fd: inject.fd, brs: inject.brs })
    const r = await fetch(`${MCU}/api/send/can`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body
    })
    const j = await r.json()
    inject.ok     = j.status === 'ok'
    inject.result = inject.ok ? `Sent (${j.dlc} bytes)` : `Error: ${j.msg}`
  } catch (e) {
    inject.ok     = false
    inject.result = `Network error: ${e.message}`
  } finally {
    inject.sending = false
  }
}

// ── Save & Apply state ────────────────────────────────────────────────────────
const saveState    = ref('idle')   // idle | saving | done | error
const defaultState = ref('idle')   // idle | confirming

// ── Local config (mirrors Config container structure) ─────────────────────────
function makeRule() {
  return { action: 0, can_id_hex: '00000000', mask_hex: '1FFFFFFF',
           remap_id_hex: '00000000', rpayload_hex: '0000000000000000', rdlc: 0,
           event_lid: 0 }
}
const cfg = reactive({
  board: { eth_ip: '10.104.3.64', eth_mask: '255.255.255.0', eth_gw: '10.104.3.1', usb_ip: '192.168.7.64', ptp_enable: 0,
           radxa_fwd_enable: 0, radxa_dest_ip: '0.0.0.0', radxa_dest_port: 47808 },
  can:   { j1939: 0, dlc: 8, id_hex: '00000000',
           nbrp: 2, ntseg1: 59, ntseg2: 20, nsjw: 20,
           dbrp: 2, dtseg1: 15, dtseg2: 4,  dsjw: 4,
           fd_mode: 1, brs: 1, listen_only: 0 },
  logging: {
    ch1: { enabled: 0, logging_id: 0, target: 0 },
    ch2: { enabled: 0, logging_id: 0, target: 0 }
  },
  usb:   { usbmode: 0 },
  filters: Object.fromEntries(RULE_SLOTS.map(s => [s, makeRule()]))
})

const activeRuleCount = computed(() =>
  RULE_SLOTS.filter(s => cfg.filters[s].action !== 0).length
)

// ── Logging diagram state ─────────────────────────────────────────────────────
// target encoding: 0=Ethernet, 1=WiFi, 2=BLE  (matches LoggingChanCfg::target in firmware)
const chanPopup = reactive({ open: false, ch: 1 })
const popupEdit = reactive({
  logging_id: 0,
  target: 0,
  enabled: 0,
  j1939: 0,
  dlc: 8,
  id_hex: '00000000',
  nbrp: 2,
  ntseg1: 59,
  ntseg2: 20,
  nsjw: 20,
  dbrp: 2,
  dtseg1: 15,
  dtseg2: 4,
  dsjw: 4,
  fd_mode: 1,
  brs: 1,
  listen_only: 0,
})
const ethPopup = reactive({ open: false })
const ethPopupEdit = reactive({ eth_ip: '', eth_mask: '', eth_gw: '', usb_ip: '', ptp_enable: 0 })

function openChanPopup(ch) {
  chanPopup.ch = ch
  const src = cfg.logging[`ch${ch}`]
  popupEdit.logging_id = src.logging_id
  popupEdit.target     = src.target
  popupEdit.enabled    = src.enabled
  popupEdit.j1939      = cfg.can.j1939
  popupEdit.dlc        = cfg.can.dlc
  popupEdit.id_hex     = cfg.can.id_hex
  popupEdit.nbrp       = cfg.can.nbrp
  popupEdit.ntseg1     = cfg.can.ntseg1
  popupEdit.ntseg2     = cfg.can.ntseg2
  popupEdit.nsjw       = cfg.can.nsjw
  popupEdit.dbrp       = cfg.can.dbrp
  popupEdit.dtseg1     = cfg.can.dtseg1
  popupEdit.dtseg2     = cfg.can.dtseg2
  popupEdit.dsjw       = cfg.can.dsjw
  popupEdit.fd_mode    = cfg.can.fd_mode
  popupEdit.brs        = cfg.can.brs
  popupEdit.listen_only= cfg.can.listen_only
  chanPopup.open = true
}
function saveChanPopup() {
  const dst = cfg.logging[`ch${chanPopup.ch}`]
  dst.logging_id = popupEdit.logging_id
  dst.target     = popupEdit.target
  dst.enabled    = popupEdit.enabled
  Object.assign(cfg.can, {
    j1939: popupEdit.j1939,
    dlc: popupEdit.dlc,
    id_hex: popupEdit.id_hex,
    nbrp: popupEdit.nbrp,
    ntseg1: popupEdit.ntseg1,
    ntseg2: popupEdit.ntseg2,
    nsjw: popupEdit.nsjw,
    dbrp: popupEdit.dbrp,
    dtseg1: popupEdit.dtseg1,
    dtseg2: popupEdit.dtseg2,
    dsjw: popupEdit.dsjw,
    fd_mode: popupEdit.fd_mode,
    brs: popupEdit.brs,
    listen_only: popupEdit.listen_only,
  })
  chanPopup.open = false
}

function openEthernetPopup() {
  ethPopupEdit.eth_ip = cfg.board.eth_ip
  ethPopupEdit.eth_mask = cfg.board.eth_mask
  ethPopupEdit.eth_gw = cfg.board.eth_gw
  ethPopupEdit.usb_ip = cfg.board.usb_ip
  ethPopupEdit.ptp_enable = cfg.board.ptp_enable
  ethPopup.open = true
}

function saveEthernetPopup() {
  cfg.board.eth_ip = ethPopupEdit.eth_ip
  cfg.board.eth_mask = ethPopupEdit.eth_mask
  cfg.board.eth_gw = ethPopupEdit.eth_gw
  cfg.board.usb_ip = ethPopupEdit.usb_ip
  cfg.board.ptp_enable = ethPopupEdit.ptp_enable
  ethPopup.open = false
}

// ── CAN Bus timing helpers ────────────────────────────────────────────────────
const CAN_CLK = 80e6  // PLL2Q = 80 MHz

function fmtHz(hz) {
  if (hz >= 1e6)  return (hz / 1e6).toFixed(3).replace(/\.?0+$/, '') + ' Mbps'
  if (hz >= 1e3)  return (hz / 1e3).toFixed(1).replace(/\.?0+$/, '') + ' kbps'
  return hz + ' bps'
}

const nomBitrate = computed(() => {
  const tq = 1 + cfg.can.ntseg1 + cfg.can.ntseg2
  return fmtHz(CAN_CLK / (cfg.can.nbrp * tq))
})
const nomSamplePt = computed(() => {
  const tq = 1 + cfg.can.ntseg1 + cfg.can.ntseg2
  return ((1 + cfg.can.ntseg1) / tq * 100).toFixed(1) + '%'
})
const dataBitrate = computed(() => {
  const tq = 1 + cfg.can.dtseg1 + cfg.can.dtseg2
  return fmtHz(CAN_CLK / (cfg.can.dbrp * tq))
})
const dataSamplePt = computed(() => {
  const tq = 1 + cfg.can.dtseg1 + cfg.can.dtseg2
  return ((1 + cfg.can.dtseg1) / tq * 100).toFixed(1) + '%'
})

function applyNomPreset(nbrp, ntseg1, ntseg2, nsjw) {
  cfg.can.nbrp = nbrp; cfg.can.ntseg1 = ntseg1
  cfg.can.ntseg2 = ntseg2; cfg.can.nsjw = nsjw
}
function applyDataPreset(dbrp, dtseg1, dtseg2, dsjw) {
  cfg.can.dbrp = dbrp; cfg.can.dtseg1 = dtseg1
  cfg.can.dtseg2 = dtseg2; cfg.can.dsjw = dsjw
}

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
// ── J1939 TX helpers ──────────────────────────────────────────────────────────
// All frames sent to FDCAN1 (channel 0) via /api/send/can.
// SA = 0xFE (null/tester address), Priority = 3.

function j1939CanId(pf, ps, da = 0xFF, sa = 0xFE, priority = 3) {
  // PDU1 (PF < 0xF0): PS = destination address
  // PDU2 (PF >= 0xF0): PS = group extension (broadcast)
  const ps_ = (pf >= 0xF0) ? ps : (da & 0xFF)
  const id = ((priority & 0x7) << 26) | (pf << 16) | (ps_ << 8) | (sa & 0xFF)
  return '0x' + (id >>> 0).toString(16).toUpperCase().padStart(8, '0')
}

async function j1939Send(canId, dataHex) {
  try {
    await fetch(`${MCU}/api/send/can`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: canId, data: dataHex, fd: false, brs: false })
    })
  } catch (e) { console.error('CAN TX error:', e) }
}

// send-control event: {type:'control', engine:'start'|'stop'}
// send-throttle event: throttle value 0-100
async function send(obj) {
  if (obj.engine === 'start' || obj.engine === 'stop') {
    // ProprietaryA (PGN 0xEF00) addressed to engine ECU (DA=0x00)
    // Byte 0: 0x01 = start, 0x00 = stop  (vendor-defined)
    const canId = j1939CanId(0xEF, 0x00, /*da=*/0x00)
    const cmd   = obj.engine === 'start' ? '01' : '00'
    await j1939Send(canId, cmd + 'FFFFFFFFFFFFFF')
  } else if (obj.throttle !== undefined) {
    // TSC1 (PGN 0x0000) torque control — addressed to engine ECU (DA=0x00)
    // Byte 0: 0x0F = torque override, highest priority
    // Bytes 1-2: 0xFFFF = speed not controlled
    // Byte 3: requested torque = throttle% + 125 (offset -125%, 1%/bit)
    const canId  = j1939CanId(0x00, 0x00, /*da=*/0x00)
    const torque = Math.min(250, Math.max(0, Math.round(Number(obj.throttle)) + 125))
    const t = torque.toString(16).padStart(2, '0').toUpperCase()
    await j1939Send(canId, '0FFFFF' + t + 'FFFFFFFF')
  }
}

function sendThrottle(value = throttle.value) {
  if (value !== undefined) throttle.value = value
  send({ type: 'control', throttle: throttle.value })
}

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
    if (d.board.ptp_enable       !== undefined) cfg.board.ptp_enable       = d.board.ptp_enable
    if (d.board.radxa_fwd_enable !== undefined) cfg.board.radxa_fwd_enable = d.board.radxa_fwd_enable
    if (d.board.radxa_dest_ip)                  cfg.board.radxa_dest_ip    = fmtIp(d.board.radxa_dest_ip)
    if (d.board.radxa_dest_port  !== undefined) cfg.board.radxa_dest_port  = d.board.radxa_dest_port
  }
  if (d.can) {
    if (d.can.j1939    !== undefined) cfg.can.j1939   = d.can.j1939
    if (d.can.dlc      !== undefined) cfg.can.dlc     = d.can.dlc
    if (d.can.id       !== undefined) cfg.can.id_hex  = d.can.id.toString(16).padStart(8,'0').toUpperCase()
    if (d.can.nbrp     !== undefined) cfg.can.nbrp    = d.can.nbrp
    if (d.can.ntseg1   !== undefined) cfg.can.ntseg1  = d.can.ntseg1
    if (d.can.ntseg2   !== undefined) cfg.can.ntseg2  = d.can.ntseg2
    if (d.can.nsjw     !== undefined) cfg.can.nsjw    = d.can.nsjw
    if (d.can.dbrp     !== undefined) cfg.can.dbrp    = d.can.dbrp
    if (d.can.dtseg1   !== undefined) cfg.can.dtseg1  = d.can.dtseg1
    if (d.can.dtseg2   !== undefined) cfg.can.dtseg2  = d.can.dtseg2
    if (d.can.dsjw     !== undefined) cfg.can.dsjw    = d.can.dsjw
    if (d.can.fd_mode     !== undefined) cfg.can.fd_mode     = d.can.fd_mode
    if (d.can.brs         !== undefined) cfg.can.brs         = d.can.brs
    if (d.can.listen_only !== undefined) cfg.can.listen_only = d.can.listen_only
  }
  if (d.usb && d.usb.usbmode !== undefined) cfg.usb.usbmode = d.usb.usbmode
  if (d.logging) {
    for (const ch of ['ch1', 'ch2']) {
      const src = d.logging[ch]
      if (!src) continue
      if (src.enabled    !== undefined) cfg.logging[ch].enabled    = src.enabled
      if (src.logging_id !== undefined) cfg.logging[ch].logging_id = src.logging_id
      if (src.target     !== undefined) cfg.logging[ch].target     = src.target
    }
  }
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
      fc.event_lid   = r.event_lid ?? 0
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
      action:    fc.action,
      rflags:    (fc.action === 2 ? ((fc.remap_id_hex !== '00000000' ? 1 : 0) | (fc.rpayload_hex && fc.rpayload_hex !== '0000000000000000' ? 2 : 0)) : 0),
      rdlc:      fc.rdlc,
      rpayload:  parseHexBytes(fc.rpayload_hex, 8),
      event_lid: fc.event_lid ?? 0
    }
  }
  return {
    board: {
      eth_ip:          parseIp(cfg.board.eth_ip),
      eth_mask:        parseIp(cfg.board.eth_mask),
      eth_gw:          parseIp(cfg.board.eth_gw),
      usb_ip:          parseIp(cfg.board.usb_ip),
      ptp_enable:      cfg.board.ptp_enable,
      radxa_fwd_enable: cfg.board.radxa_fwd_enable,
      radxa_dest_ip:   parseIp(cfg.board.radxa_dest_ip),
      radxa_dest_port: cfg.board.radxa_dest_port
    },
    can: {
      dlc:    cfg.can.dlc,
      id:     parseHex32(cfg.can.id_hex),
      j1939:  cfg.can.j1939,
      nbrp:   cfg.can.nbrp,
      ntseg1: cfg.can.ntseg1,
      ntseg2: cfg.can.ntseg2,
      nsjw:   cfg.can.nsjw,
      dbrp:   cfg.can.dbrp,
      dtseg1: cfg.can.dtseg1,
      dtseg2: cfg.can.dtseg2,
      dsjw:   cfg.can.dsjw,
      fd_mode:    cfg.can.fd_mode,
      brs:        cfg.can.brs,
      listen_only:cfg.can.listen_only
    },
    usb:     { usbmode: cfg.usb.usbmode },
    logging: {
      ch1: { enabled: cfg.logging.ch1.enabled, logging_id: cfg.logging.ch1.logging_id, target: cfg.logging.ch1.target },
      ch2: { enabled: cfg.logging.ch2.enabled, logging_id: cfg.logging.ch2.logging_id, target: cfg.logging.ch2.target }
    },
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
  cfg.board.eth_ip          = '10.104.3.64'
  cfg.board.eth_mask        = '255.255.255.0'
  cfg.board.eth_gw          = '10.104.3.1'
  cfg.board.usb_ip          = '192.168.7.64'
  cfg.board.ptp_enable      = 0
  cfg.board.radxa_fwd_enable = 0
  cfg.board.radxa_dest_ip   = '0.0.0.0'
  cfg.board.radxa_dest_port = 47808
  cfg.can.j1939   = 0
  cfg.can.dlc     = 8
  cfg.can.id_hex  = '00000000'
  cfg.can.nbrp    = 2;  cfg.can.ntseg1 = 59; cfg.can.ntseg2 = 20; cfg.can.nsjw = 20
  cfg.can.dbrp    = 2;  cfg.can.dtseg1 = 15; cfg.can.dtseg2 = 4;  cfg.can.dsjw = 4
  cfg.can.fd_mode = 1;  cfg.can.brs    = 1;  cfg.can.listen_only = 0
  cfg.usb.usbmode = 0
  cfg.logging.ch1 = { enabled: 0, logging_id: 0, target: 0 }
  cfg.logging.ch2 = { enabled: 0, logging_id: 0, target: 0 }
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

// ── Radxa API ──────────────────────────────────────────────────────────────────
async function fetchRadxa() {
  try {
    const d = (await axios.get(`${MCU}/api/radxa`)).data
    radxa.alive       = d.alive       ?? false
    radxa.heartbeat   = d.heartbeat   ?? 0
    radxa.status      = d.status      ?? 0
    radxa.version     = d.version     ?? ''
    radxa.uptime      = d.uptime      ?? 0
    radxa.wifi_status = d.wifi_status ?? 0
    radxa.wifi_ip     = d.wifi_ip     ?? ''
    radxa.wifi_rssi   = d.wifi_rssi   ?? 0
    radxa.wifi_enable = d.wifi_enable ?? false
    radxa.data_enable = d.data_enable ?? false
    radxa.dest_ip     = d.dest_ip     ?? ''
    radxa.dest_port   = d.dest_port   ?? 47808
    radxa.pkts_fwd    = d.pkts_fwd    ?? 0
    radxa.pkts_drop   = d.pkts_drop   ?? 0
    radxaEdit.wifiEnable = radxa.wifi_enable
    radxaEdit.dataEnable = radxa.data_enable
    if (!radxaEdit.destIp)   radxaEdit.destIp   = radxa.dest_ip
    if (!radxaEdit.destPort) radxaEdit.destPort = radxa.dest_port
  } catch (_) {}
}

async function radxaSendWifiEnable() {
  try {
    await axios.post(`${MCU}/api/radxa/wifi`, { enable: radxaEdit.wifiEnable })
  } catch (_) {}
}

async function radxaWifiConnect() {
  radxaEdit.wifiResult = ''
  try {
    await axios.post(`${MCU}/api/radxa/wifi`,
      { enable: true, ssid: radxaEdit.ssid, password: radxaEdit.password })
    radxaEdit.wifiOk = true
    radxaEdit.wifiResult = 'Command sent — connecting…'
    radxaEdit.wifiEnable = true
  } catch (_) {
    radxaEdit.wifiOk = false
    radxaEdit.wifiResult = 'Failed to send command'
  }
}

async function radxaApplyData() {
  radxaEdit.dataResult = ''
  try {
    await axios.post(`${MCU}/api/radxa/data`, {
      enable:    radxaEdit.dataEnable,
      dest_ip:   radxaEdit.destIp,
      dest_port: radxaEdit.destPort,
    })
    radxaEdit.dataOk = true; radxaEdit.dataResult = 'Applied'
    setTimeout(() => { radxaEdit.dataResult = '' }, 2000)
  } catch (_) {
    radxaEdit.dataOk = false; radxaEdit.dataResult = 'Failed'
  }
}

async function doRadxaReboot() {
  radxaRebootState.value = 'sending'
  try {
    await axios.post(`${MCU}/api/radxa/reboot`, {}, { timeout: 3000 })
    radxaRebootState.value = 'done'
  } catch (e) {
    radxaRebootState.value = e.response ? 'error' : 'done'
  }
}

function requestRadxaReboot() {
  radxaRebootState.value = 'confirming'
}

function cancelRadxaReboot() {
  radxaRebootState.value = 'idle'
}

function resetRadxaRebootState() {
  radxaRebootState.value = 'idle'
}

onMounted(() => {
  fetchTelemetry(); fetchDTC(); fetchNodes(); fetchSystemInfo(); fetchConfig(); fetchRadxa()
  setInterval(fetchTelemetry,  200)
  setInterval(fetchDTC,       2000)
  setInterval(fetchNodes,     5000)
  setInterval(fetchSystemInfo,5000)
  setInterval(fetchRadxa,     3000)
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

/* hide mobile-only toggle by default; shown only in mobile media query */
.mobile-collapse-toggle { display: none !important; height: auto; }

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
.inject-result { font-size: 14px; font-weight: 600; padding: 8px 12px; border-radius: 6px; }
.inject-ok     { color: #34d399; background: rgba(52,211,153,.1); }
.inject-err    { color: #f87171; background: rgba(248,113,113,.1); }
.radio-row     { display: flex; align-items: center; gap: 8px; }
.radio-opt     { display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text); cursor: pointer; }
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

/* ── CAN Bus page ────────────────────────────────────────────────────────── */
.preset-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.preset-btn {
  padding: 7px 16px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--dim);
  color: var(--text); font-size: 13px; font-weight: 600; cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.preset-btn:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
.timing-info-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px; margin-top: 12px;
}
.timing-info-item { display: flex; flex-direction: column; gap: 4px; }
.timing-info-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); }
.timing-info-val { font-size: 18px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }

/* ── Logging page ────────────────────────────────────────────────────────── */
.log-diagram-wrap {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px 16px;
  margin-bottom: 16px;
}
.log-diagram-svg {
  width: 100%; max-width: 700px;
  display: block; margin: 0 auto;
}
.log-legend {
  display: flex; gap: 24px; flex-wrap: wrap;
  font-size: 12px; color: var(--muted);
  padding: 4px 0;
}
.leg-item { display: flex; align-items: center; gap: 8px; }

/* ── Channel config popup ────────────────────────────────────────────────── */

/* ── Radxa page ──────────────────────────────────────────────────────────── */
.radxa-top-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 900px) { .radxa-top-grid { grid-template-columns: 1fr; } }

.wifi-status-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.wifi-dot-connected  { background: var(--success); box-shadow: 0 0 6px rgba(16,185,129,0.6); }
.wifi-dot-connecting { background: var(--warning); animation: pulse-warn 1.2s infinite; }
.wifi-dot-down       { background: var(--muted); }
@keyframes pulse-warn {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.5); }
  50%       { box-shadow: 0 0 0 5px rgba(245,158,11,0); }
}

.radxa-stats-row { display: flex; gap: 16px; flex-wrap: wrap; }
.radxa-stat {
  background: var(--dim); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: 14px 24px;
  min-width: 130px; text-align: center;
}
.radxa-stat-warn { border-color: rgba(239,68,68,0.4); background: rgba(239,68,68,0.05); }
.radxa-stat-val  { font-size: 26px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
.radxa-stat-warn .radxa-stat-val { color: #f87171; }
.radxa-stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--muted); margin-top: 4px; }

@media (max-width: 900px) {
  .app { flex-direction: column; }
  .main {
    width: 100%;
    min-height: 0;
    min-width: 0;
    overflow: auto;
  }
  /* mobile toggle placed outside sidebar so fixed positioning is relative to viewport */
  .mobile-collapse-toggle {
    position: fixed;
    top: 14px;
    left: calc(min(360px, 92vw) - 44px);
    display: inline-flex !important;
    width: 52px;
    height: 52px;
    border-radius: 12px;
    background: rgba(0,0,0,0.95);
    color: #fff;
    border: none;
    align-items: center;
    justify-content: center;
    z-index: 1300;
    font-size: 18px;
    transition: left 0.28s cubic-bezier(.2,.9,.2,1), background 0.18s;
  }
  .mobile-collapse-toggle.collapsed {
    left: 12px;
    background: rgba(0,0,0,1);
    width: 56px; height: 56px; border-radius: 12px; font-size: 20px;
  }

  .brand {
    width: 100%;
    border-bottom: 1px solid var(--border);
    margin-bottom: 12px;
    padding-bottom: 12px;
  }
  .save-btn,
  .save-default { width: 100%; }
  .nav { flex-direction: row; flex-wrap: wrap; gap: 8px; width: 100%; }
  .nav-btn { flex: 1 1 calc(50% - 8px); }
  .sidebar-footer {
    width: 100%;
    margin-top: 0;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    justify-content: space-between;
  }
  .topbar { padding: 14px 16px; gap: 10px; }
}

@media (max-width: 700px) {
  .nav-btn { flex: 1 1 100%; }
  .topbar { padding: 12px 14px; }
}
</style>
