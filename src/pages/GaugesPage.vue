<template>
  <section class="gauges-page">
    <div class="ecu-panels">
      <div
        v-for="(ecu, idx) in ecus"
        :key="idx"
        class="ecu-panel"
        :class="{ inactive: ecu.sa === '0xFF' }"
      >
        <div class="ecu-header">
          <span class="ecu-label">ECU {{ idx + 1 }}</span>
          <span class="ecu-sa" :class="{ unknown: ecu.sa === '0xFF' }">
            {{ ecu.sa === '0xFF' ? 'No signal' : `SA: ${ecu.sa}` }}
          </span>
        </div>

        <div class="gauges-grid">
          <GaugeCard title="Engine RPM"    :value="ecu.smooth.engine_speed"   :max="4000" unit="rpm"  color="#3b82f6" />
          <GaugeCard title="Vehicle Speed" :value="ecu.smooth.vehicle_speed"  :max="140"  unit="km/h" color="#10b981" />
          <GaugeCard title="Fuel Level"    :value="ecu.smooth.fuel_level"     :max="100"  unit="%"    color="#f59e0b" />
          <GaugeCard title="Engine Load"   :value="ecu.smooth.engine_load"    :max="100"  unit="%"    color="#8b5cf6" />
        </div>

        <div class="bottom-row">
          <MetricCard icon="🌡" label="Coolant"  :value="ecu.smooth.coolant_temp.toFixed(1)"    unit="°C" :warn="ecu.smooth.coolant_temp > 100" />
          <MetricCard icon="🔋" label="Battery"  :value="ecu.smooth.battery_voltage.toFixed(2)" unit="V"  :warn="ecu.smooth.battery_voltage < 11.5 && ecu.smooth.battery_voltage > 0" />
          <MetricCard icon="🎯" label="Throttle" :value="(ecu.throttle_pct || 0).toFixed(1)"    unit="%" />

          <div class="status-card">
            <div class="status-card-title">Status</div>
            <StatusRow label="Engine" :on="ecu.status.engine_running" />
            <StatusRow label="Brake"  :on="ecu.status.brake" />
            <StatusRow label="PTO"    :on="ecu.status.pto" />
            <StatusRow label="Cruise" :on="ecu.status.cruise" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import GaugeCard  from '../components/ui/GaugeCard.vue'
import MetricCard from '../components/ui/MetricCard.vue'
import StatusRow  from '../components/ui/StatusRow.vue'

defineProps({ ecus: Array })
</script>

<style scoped>
.gauges-page { flex: 1; overflow-y: auto; padding: 20px 24px; }

.ecu-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 1100px) {
  .ecu-panels { grid-template-columns: 1fr; }
}

.ecu-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: opacity 0.3s;
}
.ecu-panel.inactive { opacity: 0.4; }

.ecu-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border);
}
.ecu-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
.ecu-sa {
  font-size: 12px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  padding: 2px 8px;
  border-radius: 999px;
}
.ecu-sa.unknown {
  color: var(--muted);
  background: color-mix(in srgb, var(--muted) 12%, transparent);
}

.gauges-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1.3fr;
  gap: 12px;
}
@media (max-width: 700px) {
  .gauges-grid { grid-template-columns: 1fr; }
  .bottom-row  { grid-template-columns: 1fr 1fr; }
}

.status-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.status-card-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--muted);
  margin-bottom: 2px;
}
</style>
