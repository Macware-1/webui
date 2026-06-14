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
            <div class="info-card-title">Network (Live)</div>
            <InfoRow label="IP Address"  :value="system.ip"/>
            <InfoRow label="MAC Address" :value="system.mac"/>
            <InfoRow label="Gateway"     :value="system.gateway"/>
          </div>

          <div class="info-card" style="grid-column: 1 / -1">
            <div class="info-card-title">Network Configuration</div>
            <div class="cfg-grid" style="margin-top:10px">
              <div class="rule-field">
                <label class="field-label">ETH IP</label>
                <input v-model="cfg.board.eth_ip"   class="text-input mono" placeholder="10.104.3.64"/>
              </div>
              <div class="rule-field">
                <label class="field-label">Subnet Mask</label>
                <input v-model="cfg.board.eth_mask" class="text-input mono" placeholder="255.255.255.0"/>
              </div>
              <div class="rule-field">
                <label class="field-label">Gateway</label>
                <input v-model="cfg.board.eth_gw"   class="text-input mono" placeholder="10.104.3.1"/>
              </div>
              <div class="rule-field">
                <label class="field-label">USB IP</label>
                <input v-model="cfg.board.usb_ip"   class="text-input mono" placeholder="192.168.7.64"/>
              </div>
            </div>
            <p class="boot-desc" style="margin-top:8px">Changes take effect after <strong>Save &amp; Apply Config</strong>.</p>
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

        <!-- Radxa CLOG Forwarding -->
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
              <input type="checkbox" v-model="cfg.board.radxa_fwd_enable" :true-value="1" :false-value="0"/>
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="cfg-grid" style="margin-top:10px">
            <div class="rule-field">
              <label class="field-label">Destination IP</label>
              <input v-model="cfg.board.radxa_dest_ip" class="text-input mono" placeholder="192.168.1.100"
                     :disabled="!cfg.board.radxa_fwd_enable"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Destination Port</label>
              <input v-model.number="cfg.board.radxa_dest_port" type="number" min="1" max="65535"
                     class="text-input mono" placeholder="47808"
                     :disabled="!cfg.board.radxa_fwd_enable"/>
            </div>
          </div>
          <p class="boot-desc" style="margin-top:6px">
            Enter your PC's WiFi IP address. CLOG packets arrive on UDP port 47808 (same as wired).
            Configure Radxa WiFi first via <code>nmcli</code> on the Radxa.
            Takes effect after <strong>Save &amp; Apply Config</strong>.
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

      <!-- LOGGING ──────────────────────────────────────────────────────── -->
      <section v-if="page === 'Logging'" class="content-panel">
        <p class="mode-desc" style="margin-bottom:20px">
          Click a CAN channel block to configure its logging ID and output target.
          Arrows show active logging paths. Bluetooth is not yet supported.
        </p>

        <!-- Block diagram (pure SVG) -->
        <div class="log-diagram-wrap">
          <svg class="log-diagram-svg" viewBox="0 0 700 310" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <marker id="ah-on"  markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
                <polygon points="0 0, 10 4, 0 8" fill="#3b82f6"/>
              </marker>
              <marker id="ah-off" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
                <polygon points="0 0, 10 4, 0 8" fill="#243549"/>
              </marker>
              <marker id="ah-usb" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
                <polygon points="0 0, 10 4, 0 8" fill="#a78bfa"/>
              </marker>
            </defs>

            <!-- CAN Channel 1 -->
            <g @click="openChanPopup(1)" style="cursor:pointer">
              <rect x="30" y="20" width="185" height="108" rx="12"
                    :fill="cfg.logging.ch1.enabled ? '#0a1c30' : '#101e33'"
                    :stroke="cfg.logging.ch1.enabled ? '#3b82f6' : '#1b2d47'"
                    stroke-width="2"/>
              <text x="122" y="62"  text-anchor="middle" font-size="30">📟</text>
              <text x="122" y="88"  text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="600" font-family="Inter,system-ui,sans-serif">CAN Channel 1</text>
              <text x="122" y="107" text-anchor="middle" fill="#64748b" font-size="12" font-family="Inter,system-ui,sans-serif">Logging ID: {{ cfg.logging.ch1.logging_id }}</text>
              <text x="122" y="122" text-anchor="middle" fill="#3b82f6" font-size="10" font-family="Inter,system-ui,sans-serif">▶ click to configure</text>
            </g>

            <!-- CAN Channel 2 -->
            <g @click="openChanPopup(2)" style="cursor:pointer">
              <rect x="485" y="20" width="185" height="108" rx="12"
                    :fill="cfg.logging.ch2.enabled ? '#0a1c30' : '#101e33'"
                    :stroke="cfg.logging.ch2.enabled ? '#3b82f6' : '#1b2d47'"
                    stroke-width="2"/>
              <text x="577" y="62"  text-anchor="middle" font-size="30">📟</text>
              <text x="577" y="88"  text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="600" font-family="Inter,system-ui,sans-serif">CAN Channel 2</text>
              <text x="577" y="107" text-anchor="middle" fill="#64748b" font-size="12" font-family="Inter,system-ui,sans-serif">Logging ID: {{ cfg.logging.ch2.logging_id }}</text>
              <text x="577" y="122" text-anchor="middle" fill="#3b82f6" font-size="10" font-family="Inter,system-ui,sans-serif">▶ click to configure</text>
            </g>

            <!-- Arrow: Ch1 → ETH -->
            <line x1="122" y1="128" x2="265" y2="197"
                  :stroke="cfg.logging.ch1.enabled && cfg.logging.ch1.target===0 ? '#3b82f6' : '#243549'"
                  stroke-width="2.5"
                  :stroke-dasharray="cfg.logging.ch1.enabled && cfg.logging.ch1.target===0 ? '6,4' : '4,5'"
                  :marker-end="cfg.logging.ch1.enabled && cfg.logging.ch1.target===0 ? 'url(#ah-on)' : 'url(#ah-off)'"/>

            <!-- Arrow: Ch2 → ETH -->
            <line x1="577" y1="128" x2="395" y2="197"
                  :stroke="cfg.logging.ch2.enabled && cfg.logging.ch2.target===0 ? '#3b82f6' : '#243549'"
                  stroke-width="2.5"
                  :stroke-dasharray="cfg.logging.ch2.enabled && cfg.logging.ch2.target===0 ? '6,4' : '4,5'"
                  :marker-end="cfg.logging.ch2.enabled && cfg.logging.ch2.target===0 ? 'url(#ah-on)' : 'url(#ah-off)'"/>

            <!-- Arrow: Ch1 → USB ECM -->
            <line x1="215" y1="128" x2="468" y2="197"
                  :stroke="cfg.logging.ch1.enabled && cfg.logging.ch1.target===1 ? '#a78bfa' : '#243549'"
                  stroke-width="2.5"
                  :stroke-dasharray="cfg.logging.ch1.enabled && cfg.logging.ch1.target===1 ? '6,4' : '4,5'"
                  :marker-end="cfg.logging.ch1.enabled && cfg.logging.ch1.target===1 ? 'url(#ah-usb)' : 'url(#ah-off)'"/>

            <!-- Arrow: Ch2 → USB ECM -->
            <line x1="577" y1="128" x2="558" y2="197"
                  :stroke="cfg.logging.ch2.enabled && cfg.logging.ch2.target===1 ? '#a78bfa' : '#243549'"
                  stroke-width="2.5"
                  :stroke-dasharray="cfg.logging.ch2.enabled && cfg.logging.ch2.target===1 ? '6,4' : '4,5'"
                  :marker-end="cfg.logging.ch2.enabled && cfg.logging.ch2.target===1 ? 'url(#ah-usb)' : 'url(#ah-off)'"/>

            <!-- Ethernet block -->
            <rect x="175" y="197" width="260" height="100" rx="12"
                  :fill="system.link_up ? '#081a10' : '#1a0909'"
                  :stroke="system.link_up ? '#10b981' : '#ef4444'"
                  stroke-width="2"/>
            <text x="305" y="241" text-anchor="middle" font-size="30">🌐</text>
            <text x="305" y="265" text-anchor="middle" fill="#e2e8f0" font-size="14" font-weight="600" font-family="Inter,system-ui,sans-serif">100 Mbps Ethernet</text>
            <circle cx="258" cy="283" r="5" :fill="system.link_up ? '#10b981' : '#ef4444'"/>
            <text x="268" y="287" :fill="system.link_up ? '#10b981' : '#ef4444'" font-size="12" font-family="Inter,system-ui,sans-serif">
              {{ system.link_up ? 'Connected' : 'Disconnected' }}
            </text>

            <!-- USB ECM block -->
            <rect x="458" y="197" width="110" height="100" rx="12"
                  :fill="(cfg.logging.ch1.enabled && cfg.logging.ch1.target===1) || (cfg.logging.ch2.enabled && cfg.logging.ch2.target===1) ? '#1a0f2e' : '#101e33'"
                  :stroke="(cfg.logging.ch1.enabled && cfg.logging.ch1.target===1) || (cfg.logging.ch2.enabled && cfg.logging.ch2.target===1) ? '#a78bfa' : '#1b2d47'"
                  stroke-width="2"/>
            <text x="513" y="244" text-anchor="middle" font-size="28">🔌</text>
            <text x="513" y="267" text-anchor="middle" fill="#e2e8f0" font-size="13" font-weight="600" font-family="Inter,system-ui,sans-serif">USB ECM</text>
            <text x="513" y="284" text-anchor="middle" fill="#64748b" font-size="10" font-family="Inter,system-ui,sans-serif">192.168.7.x</text>

            <!-- Bluetooth block (disabled / coming soon) -->
            <g opacity="0.38">
              <rect x="580" y="197" width="100" height="100" rx="12" fill="#101e33" stroke="#1b2d47" stroke-width="1.5"/>
              <text x="630" y="244" text-anchor="middle" font-size="28">🔷</text>
              <text x="630" y="267" text-anchor="middle" fill="#e2e8f0" font-size="13" font-weight="600" font-family="Inter,system-ui,sans-serif">BLE</text>
              <text x="630" y="284" text-anchor="middle" fill="#64748b" font-size="10" font-family="Inter,system-ui,sans-serif">Coming soon</text>
            </g>
          </svg>
        </div>

        <!-- Legend -->
        <div class="log-legend">
          <span class="leg-item"><svg width="28" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6,4"/><polygon points="22,1 28,5 22,9" fill="#3b82f6"/></svg> Active logging path</span>
          <span class="leg-item"><svg width="28" height="10"><line x1="0" y1="5" x2="22" y2="5" stroke="#243549" stroke-width="2.5" stroke-dasharray="4,5"/><polygon points="22,1 28,5 22,9" fill="#243549"/></svg> Inactive / not configured</span>
        </div>
      </section>

      <!-- CAN BUS ──────────────────────────────────────────────────────── -->
      <section v-if="page === 'CAN Bus'" class="content-panel">

        <!-- Speed presets -->
        <div class="cfg-card">
          <div class="info-card-title">Nominal Speed Preset (PLL2Q = 80 MHz)</div>
          <div class="preset-row">
            <button class="preset-btn" @click="applyNomPreset(8,59,20,20)">125 kbps</button>
            <button class="preset-btn" @click="applyNomPreset(4,59,20,20)">250 kbps</button>
            <button class="preset-btn" @click="applyNomPreset(2,59,20,20)">500 kbps</button>
            <button class="preset-btn" @click="applyNomPreset(1,59,20,20)">1 Mbps</button>
          </div>
          <div class="info-card-title" style="margin-top:16px">Data Speed Preset (CAN FD)</div>
          <div class="preset-row">
            <button class="preset-btn" @click="applyDataPreset(2,31,8,4)">1 Mbps</button>
            <button class="preset-btn" @click="applyDataPreset(2,15,4,4)">2 Mbps</button>
            <button class="preset-btn" @click="applyDataPreset(1,15,4,4)">4 Mbps</button>
            <button class="preset-btn" @click="applyDataPreset(1,12,3,2)">5 Mbps</button>
          </div>
        </div>

        <!-- Computed bit rate display -->
        <div class="cfg-card">
          <div class="info-card-title">Computed Parameters</div>
          <div class="timing-info-grid">
            <div class="timing-info-item">
              <span class="timing-info-label">Nominal bit rate</span>
              <span class="timing-info-val">{{ nomBitrate }}</span>
            </div>
            <div class="timing-info-item">
              <span class="timing-info-label">Nominal sample point</span>
              <span class="timing-info-val">{{ nomSamplePt }}</span>
            </div>
            <div class="timing-info-item">
              <span class="timing-info-label">Data bit rate</span>
              <span class="timing-info-val">{{ dataBitrate }}</span>
            </div>
            <div class="timing-info-item">
              <span class="timing-info-label">Data sample point</span>
              <span class="timing-info-val">{{ dataSamplePt }}</span>
            </div>
          </div>
        </div>

        <!-- Nominal timing -->
        <div class="cfg-card">
          <div class="info-card-title">Nominal Phase Timing</div>
          <div class="cfg-grid">
            <div class="rule-field">
              <label class="field-label">Prescaler (NBRP) 1–512</label>
              <input v-model.number="cfg.can.nbrp"   type="number" min="1" max="512" class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Tseg1 (NTSEG1) 1–255</label>
              <input v-model.number="cfg.can.ntseg1" type="number" min="1" max="255" class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Tseg2 (NTSEG2) 1–127</label>
              <input v-model.number="cfg.can.ntseg2" type="number" min="1" max="127" class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">SJW (NSJW) 1–127</label>
              <input v-model.number="cfg.can.nsjw"   type="number" min="1" max="127" class="text-input"/>
            </div>
          </div>
        </div>

        <!-- Data timing -->
        <div class="cfg-card">
          <div class="info-card-title">Data Phase Timing (CAN FD)</div>
          <div class="cfg-grid">
            <div class="rule-field">
              <label class="field-label">Prescaler (DBRP) 1–32</label>
              <input v-model.number="cfg.can.dbrp"   type="number" min="1" max="32"  class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Tseg1 (DTSEG1) 1–32</label>
              <input v-model.number="cfg.can.dtseg1" type="number" min="1" max="32"  class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Tseg2 (DTSEG2) 1–16</label>
              <input v-model.number="cfg.can.dtseg2" type="number" min="1" max="16"  class="text-input"/>
            </div>
            <div class="rule-field">
              <label class="field-label">SJW (DSJW) 1–16</label>
              <input v-model.number="cfg.can.dsjw"   type="number" min="1" max="16"  class="text-input"/>
            </div>
          </div>
        </div>

        <!-- Mode flags -->
        <div class="cfg-card">
          <div class="info-card-title">Frame Mode</div>
          <div class="cfg-grid">
            <div class="rule-field">
              <label class="field-label">CAN FD</label>
              <select v-model.number="cfg.can.fd_mode" class="text-input">
                <option :value="1">Enabled</option>
                <option :value="0">Disabled (classic CAN)</option>
              </select>
            </div>
            <div class="rule-field">
              <label class="field-label">Bit-Rate Switching (BRS)</label>
              <select v-model.number="cfg.can.brs" class="text-input" :disabled="!cfg.can.fd_mode">
                <option :value="1">Enabled</option>
                <option :value="0">Disabled</option>
              </select>
            </div>
            <div class="rule-field">
              <label class="field-label">ACK Mode</label>
              <select v-model.number="cfg.can.listen_only" class="text-input">
                <option :value="0">Active (ACK frames)</option>
                <option :value="1">Listen-only (no ACK, passive)</option>
              </select>
            </div>
          </div>
          <p class="mode-desc" style="margin-top:8px">
            Click <strong>Save &amp; Apply Config</strong> in the sidebar to write these settings to flash and reboot.
          </p>
        </div>

      </section>

      <!-- CAN REPLAY ───────────────────────────────────────────────────── -->
      <section v-if="page === 'CAN Replay'" class="content-panel">
        <div class="panel-head">
          <h2 class="panel-title">CAN Replay</h2>
          <span class="count-badge">Inject frames onto CAN bus</span>
        </div>

        <div class="cfg-card" style="max-width:540px">

          <!-- CAN ID -->
          <div class="cfg-row">
            <label class="cfg-label">CAN ID (hex)</label>
            <input v-model="inject.id" class="text-input mono"
                   placeholder="0x123" maxlength="12" spellcheck="false"/>
          </div>

          <!-- Frame type -->
          <div class="cfg-row">
            <label class="cfg-label">Frame Type</label>
            <div class="radio-row">
              <label class="radio-opt">
                <input type="radio" v-model="inject.fd" :value="false"/> Classic CAN
              </label>
              <label class="radio-opt" style="margin-left:16px">
                <input type="radio" v-model="inject.fd" :value="true"/> CAN FD
              </label>
            </div>
          </div>

          <!-- BRS (only relevant for FD) -->
          <div class="cfg-row" v-if="inject.fd">
            <label class="cfg-label">Bit-Rate Switch</label>
            <label class="toggle-switch">
              <input type="checkbox" v-model="inject.brs"/>
              <span class="toggle-slider"></span>
            </label>
          </div>

          <!-- Data -->
          <div class="cfg-row">
            <label class="cfg-label">Data (hex bytes)</label>
            <input v-model="inject.data" class="text-input mono"
                   :placeholder="inject.fd ? 'up to 64 bytes, e.g. 0102030405060708' : 'up to 8 bytes, e.g. 0102030405060708'"
                   maxlength="128" spellcheck="false"/>
          </div>

          <!-- DLC indicator -->
          <div class="cfg-row">
            <label class="cfg-label">DLC (auto)</label>
            <span class="mono" style="color:var(--accent)">{{ injectDlc }}</span>
          </div>

          <!-- Send button -->
          <div style="margin-top:16px">
            <button class="btn btn-primary" @click="sendCanFrame"
                    :disabled="inject.sending">
              {{ inject.sending ? 'Sending…' : 'Send Frame' }}
            </button>
          </div>

          <!-- Result -->
          <div v-if="inject.result" :class="['inject-result', inject.ok ? 'inject-ok' : 'inject-err']"
               style="margin-top:12px">
            {{ inject.result }}
          </div>

        </div>

        <!-- UDP inject spec -->
        <div class="cfg-card" style="max-width:540px;margin-top:16px">
          <div class="info-card-title">UDP Injection (port 4000)</div>
          <p class="boot-desc">
            Send a raw binary UDP datagram to <strong>{{ system.ip }}:4000</strong> to
            inject a CAN frame without HTTP overhead. Wire format:
          </p>
          <table class="data-table" style="margin-top:8px">
            <thead><tr><th>Offset</th><th>Size</th><th>Field</th></tr></thead>
            <tbody>
              <tr><td class="mono">0–3</td><td>4 B</td><td>CAN ID (LE, bit30=extended)</td></tr>
              <tr><td class="mono">4</td><td>1 B</td><td>DLC (0–15)</td></tr>
              <tr><td class="mono">5</td><td>1 B</td><td>Flags (bit0=FD, bit1=BRS)</td></tr>
              <tr><td class="mono">6–7</td><td>2 B</td><td>Reserved (0x0000)</td></tr>
              <tr><td class="mono">8+</td><td>N B</td><td>Payload (dlc_to_len(DLC) bytes)</td></tr>
            </tbody>
          </table>
        </div>

      </section>

      <!-- FILTERING / CONFIG ─────────────────────────────────────────── -->
      <section v-if="page === 'Filtering'" class="content-panel">

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
              <option :value="3">EVENT</option>
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

            <template v-if="cfg.filters[slot].action === 3">
              <div class="rule-field">
                <label class="field-label">Event Logging ID (0–255)</label>
                <input v-model.number="cfg.filters[slot].event_lid" type="number" min="0" max="255" class="text-input" style="max-width:90px"/>
              </div>
            </template>
          </div>
        </div>

      </section>

      <!-- RADXA ───────────────────────────────────────────────────────── -->
      <section v-if="page === 'Radxa'" class="content-panel">

        <!-- Status + WiFi row -->
        <div class="radxa-top-grid">

          <!-- Status card -->
          <div class="info-card">
            <div class="info-card-title">Co-Processor Status</div>
            <div :class="['device-status', radxa.alive ? 'dev-online' : 'dev-offline']">
              {{ radxa.alive ? 'ONLINE' : 'OFFLINE' }}
            </div>
            <InfoRow label="Heartbeat">
              <template #val>
                <span class="ir-value mono">
                  {{ radxa.alive ? `0x${radxa.heartbeat.toString(16).padStart(2,'0').toUpperCase()}` : '—' }}
                </span>
              </template>
            </InfoRow>
            <InfoRow label="Version"  :value="radxa.version || '—'"/>
            <InfoRow label="Uptime"   :value="radxa.uptime ? formatUptime(radxa.uptime) : '—'"/>
            <InfoRow label="Flags">
              <template #val>
                <div style="display:flex;gap:6px">
                  <span :class="['s-pill', radxa.status & 0x01 ? 's-pill-on' : '']">BOOT</span>
                  <span :class="['s-pill', radxa.status & 0x02 ? 's-pill-on' : '']">WiFi</span>
                  <span :class="['s-pill', radxa.status & 0x04 ? 's-pill-on' : '']">FWD</span>
                </div>
              </template>
            </InfoRow>
          </div>

          <!-- WiFi card -->
          <div class="info-card">
            <div class="info-card-title">WiFi</div>

            <div class="ptp-row">
              <div>
                <div class="ptp-label">WiFi Radio</div>
                <div class="ptp-desc">Enable / disable the WiFi radio</div>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" v-model="radxaEdit.wifiEnable" @change="radxaSendWifiEnable"/>
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div style="display:flex;align-items:center;gap:8px;margin-top:10px">
              <span :class="['wifi-status-dot', wifiStatusClass]"></span>
              <span class="ptp-desc">{{ wifiStatusText }}</span>
              <span v-if="radxa.wifi_ip" class="ir-value mono" style="margin-left:auto">{{ radxa.wifi_ip }}</span>
            </div>
            <div v-if="radxa.wifi_rssi && radxa.wifi_status >= 1" class="ptp-desc" style="margin-top:4px">
              RSSI: {{ radxa.wifi_rssi }} dBm
            </div>

            <div style="height:1px;background:var(--border);margin:14px 0"></div>

            <div class="rule-field">
              <label class="field-label">SSID</label>
              <input v-model="radxaEdit.ssid" class="text-input" placeholder="MyNetwork" autocomplete="off"/>
            </div>
            <div class="rule-field" style="margin-top:8px">
              <label class="field-label">Password</label>
              <input v-model="radxaEdit.password" type="password" class="text-input" placeholder="••••••••" autocomplete="new-password"/>
            </div>
            <button class="btn btn-primary" style="margin-top:10px" @click="radxaWifiConnect">
              Connect
            </button>
            <div v-if="radxaEdit.wifiResult"
                 :class="['inject-result', radxaEdit.wifiOk ? 'inject-ok' : 'inject-err']"
                 style="margin-top:8px">
              {{ radxaEdit.wifiResult }}
            </div>
          </div>
        </div>

        <!-- Data forwarding card -->
        <div class="cfg-card" style="margin-top:16px">
          <div class="info-card-title">CLOG Data Forwarding</div>
          <p class="mode-desc" style="margin:8px 0 16px">
            When enabled, Radxa receives CLOG frames on the USB ECM link and
            relays them to the destination over WiFi.
          </p>

          <div class="ptp-row" style="margin-bottom:16px">
            <div>
              <div class="ptp-label">Forwarding</div>
              <div class="ptp-desc">{{ radxaEdit.dataEnable ? 'Active — relaying CLOG frames via WiFi' : 'Inactive' }}</div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="radxaEdit.dataEnable"/>
              <span class="toggle-slider"></span>
            </label>
          </div>

          <div class="cfg-grid" style="margin-top:0">
            <div class="rule-field">
              <label class="field-label">Destination IP</label>
              <input v-model="radxaEdit.destIp" class="text-input mono" placeholder="192.168.1.10"/>
            </div>
            <div class="rule-field">
              <label class="field-label">Destination Port</label>
              <input v-model.number="radxaEdit.destPort" type="number" min="1" max="65535" class="text-input"/>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:10px;margin-top:14px">
            <button class="btn btn-primary" style="max-width:160px" @click="radxaApplyData">
              Apply
            </button>
            <div v-if="radxaEdit.dataResult"
                 :class="['inject-result', radxaEdit.dataOk ? 'inject-ok' : 'inject-err']">
              {{ radxaEdit.dataResult }}
            </div>
          </div>

          <div class="radxa-stats-row" style="margin-top:20px">
            <div class="radxa-stat">
              <div class="radxa-stat-val">{{ radxa.pkts_fwd.toLocaleString() }}</div>
              <div class="radxa-stat-label">Forwarded</div>
            </div>
            <div class="radxa-stat" :class="{ 'radxa-stat-warn': radxa.pkts_drop > 0 }">
              <div class="radxa-stat-val">{{ radxa.pkts_drop.toLocaleString() }}</div>
              <div class="radxa-stat-label">Dropped</div>
            </div>
          </div>
        </div>

        <!-- Power card -->
        <div class="boot-card" style="margin-top:16px;max-width:none">
          <div class="boot-card-title">Power Control</div>

          <template v-if="radxaRebootState === 'idle'">
            <p class="boot-desc">Reboot the Radxa co-processor. The USB ECM link will drop for ~15 seconds.</p>
            <button class="btn btn-danger boot-btn" style="max-width:200px;margin-top:4px"
                    :disabled="!radxa.alive" @click="radxaRebootState = 'confirming'">
              ↺ Reboot Radxa
            </button>
          </template>

          <template v-else-if="radxaRebootState === 'confirming'">
            <p class="boot-warn">⚠ Radxa will reboot immediately. The connection will drop for ~15 s.</p>
            <div class="boot-row" style="margin-top:10px">
              <button class="btn btn-danger  boot-btn-half" @click="doRadxaReboot">Confirm</button>
              <button class="btn btn-neutral boot-btn-half" @click="radxaRebootState = 'idle'">Cancel</button>
            </div>
          </template>

          <template v-else-if="radxaRebootState === 'sending'">
            <div class="boot-spinner-row">
              <div class="boot-spinner"></div>
              <span class="boot-sending-txt">Sending reboot command…</span>
            </div>
          </template>

          <template v-else-if="radxaRebootState === 'done'">
            <p class="boot-ok">✓ Reboot command sent. Radxa is restarting.</p>
            <button class="btn btn-neutral boot-btn" style="max-width:160px;margin-top:10px"
                    @click="radxaRebootState = 'idle'">Dismiss</button>
          </template>

          <template v-else-if="radxaRebootState === 'error'">
            <p class="boot-err">✕ Failed to send reboot command.</p>
            <button class="btn btn-neutral boot-btn" style="max-width:160px;margin-top:10px"
                    @click="radxaRebootState = 'idle'">Retry</button>
          </template>
        </div>

      </section>

    </main>
  </div>

  <!-- ── Channel config popup ─────────────────────────────────────────── -->
  <Teleport to="body">
    <div v-if="chanPopup.open" class="popup-overlay" @click.self="chanPopup.open = false">
      <div class="popup-card">
        <div class="popup-header">
          <span class="popup-title">CAN Channel {{ chanPopup.ch }}</span>
          <button class="popup-close" @click="chanPopup.open = false">✕</button>
        </div>

        <label class="field-label" style="display:block;margin-bottom:6px">Logging ID (0–255)</label>
        <input v-model.number="popupEdit.logging_id" type="number" min="0" max="255"
               class="text-input" style="width:120px"/>
        <p class="mode-desc" style="margin-top:4px;margin-bottom:20px">
          This ID is embedded in every forwarded frame so the host can identify the source channel.
        </p>

        <label class="field-label" style="display:block;margin-bottom:10px">Logging Target</label>
        <div class="target-row">
          <button :class="['target-btn', { 'target-active': popupEdit.target === 0 }]"
                  @click="popupEdit.target = 0">
            <span class="target-icon">🌐</span>
            <span class="target-name">Ethernet</span>
          </button>
          <button :class="['target-btn', { 'target-active': popupEdit.target === 1 }]"
                  @click="popupEdit.target = 1">
            <span class="target-icon">🔌</span>
            <span class="target-name">USB ECM</span>
          </button>
          <button class="target-btn target-disabled" disabled title="Coming soon">
            <span class="target-icon">🔷</span>
            <span class="target-name">Bluetooth</span>
            <span class="target-soon">Soon</span>
          </button>
        </div>

        <label class="field-label" style="display:block;margin:20px 0 6px">Logging</label>
        <select v-model.number="popupEdit.enabled" class="text-input" style="width:160px">
          <option :value="1">Enabled</option>
          <option :value="0">Disabled</option>
        </select>

        <div class="popup-actions">
          <button class="preset-btn" style="background:var(--primary);color:#fff;border-color:var(--primary)"
                  @click="saveChanPopup">Apply</button>
          <button class="preset-btn" @click="chanPopup.open = false">Cancel</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch, nextTick } from "vue"
import axios from "axios"

// ── Config ────────────────────────────────────────────────────────────────────
// Empty string → relative URLs; page is served by the MCU itself so all
// API calls go to the same host regardless of which interface (ETH or USB) is used.
const MCU   = ""
const ICONS = { Gauges:'📊', Diagnostics:'🚨', Controls:'🎛', Nodes:'🔌', 'System Info':'🖧', Logging:'📋', 'CAN Bus':'📡', 'CAN Replay':'▶', Filtering:'⚙', Radxa:'🤖' }
const RULE_SLOTS = ['r0','r1','r2','r3','r4','r5','r6','r7']

// ── Navigation ────────────────────────────────────────────────────────────────
const pages = ["Gauges", "Diagnostics", "Controls", "Nodes", "System Info", "Logging", "CAN Bus", "CAN Replay", "Filtering", "Radxa"]
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
const popupEdit = reactive({ logging_id: 0, target: 0, enabled: 0 })

function openChanPopup(ch) {
  chanPopup.ch = ch
  const src = cfg.logging[`ch${ch}`]
  popupEdit.logging_id = src.logging_id
  popupEdit.target     = src.target
  popupEdit.enabled    = src.enabled
  chanPopup.open = true
}
function saveChanPopup() {
  const dst = cfg.logging[`ch${chanPopup.ch}`]
  dst.logging_id = popupEdit.logging_id
  dst.target     = popupEdit.target
  dst.enabled    = popupEdit.enabled
  chanPopup.open = false
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
.popup-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.65);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
}
.popup-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 28px 28px 24px;
  width: 420px; max-width: 95vw;
  box-shadow: 0 24px 64px rgba(0,0,0,0.6);
}
.popup-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.popup-title { font-size: 17px; font-weight: 700; color: var(--text); }
.popup-close {
  background: none; border: none; color: var(--muted); font-size: 16px;
  cursor: pointer; padding: 4px 8px; border-radius: 6px;
  transition: color 0.15s;
}
.popup-close:hover { color: var(--text); }
.target-row { display: flex; gap: 10px; }
.target-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  gap: 6px; padding: 12px 8px; border-radius: var(--radius-sm);
  border: 2px solid var(--border); background: var(--dim);
  color: var(--text); cursor: pointer; transition: border-color 0.15s, background 0.15s;
}
.target-btn:hover:not(:disabled) { border-color: var(--primary); }
.target-active { border-color: var(--primary) !important; background: #0d2244 !important; }
.target-disabled { opacity: 0.38; cursor: not-allowed !important; }
.target-icon { font-size: 22px; }
.target-name { font-size: 12px; font-weight: 600; }
.target-soon { font-size: 10px; color: var(--muted); }
.popup-actions { display: flex; gap: 10px; margin-top: 24px; justify-content: flex-end; }

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
</style>
