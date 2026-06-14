<template>
  <section class="gauges-page">
    <div class="gauges-grid">
      <GaugeCard title="Engine RPM" :value="smooth.engine_speed" :max="3000" unit="rpm" color="#3b82f6" />
      <GaugeCard title="Vehicle Speed" :value="smooth.vehicle_speed" :max="140" unit="km/h" color="#10b981" />
      <GaugeCard title="Fuel Level" :value="smooth.fuel_level" :max="100" unit="%" color="#f59e0b" />
      <GaugeCard title="Engine Load" :value="smooth.engine_load" :max="100" unit="%" color="#8b5cf6" />
    </div>

    <div class="bottom-row">
      <MetricCard icon="🌡" label="Coolant" :value="smooth.coolant_temp.toFixed(1)" unit="°C" :warn="smooth.coolant_temp > 100" />
      <MetricCard icon="🔋" label="Battery" :value="smooth.battery_voltage.toFixed(2)" unit="V" :warn="smooth.battery_voltage < 11.5 && smooth.battery_voltage > 0" />
      <MetricCard icon="🎯" label="Throttle" :value="(telemetry.throttle_pct || 0).toFixed(1)" unit="%" />

      <div class="status-card">
        <div class="status-card-title">Status</div>
        <StatusRow label="Engine" :on="telemetry.status.engine_running" />
        <StatusRow label="Brake" :on="telemetry.status.brake" />
        <StatusRow label="PTO" :on="telemetry.status.pto" />
        <StatusRow label="Cruise" :on="telemetry.status.cruise" />
      </div>
    </div>
  </section>
</template>

<script setup>
import GaugeCard from '../components/ui/GaugeCard.vue'
import MetricCard from '../components/ui/MetricCard.vue'
import StatusRow from '../components/ui/StatusRow.vue'

const props = defineProps({
  smooth: Object,
  telemetry: Object,
})
</script>

<style scoped>
.gauges-page { flex: 1; overflow-y: auto; padding: 20px 24px; }
.gauges-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 1100px) {
  .gauges-grid { grid-template-columns: repeat(2, 1fr); }
}
.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1.3fr;
  gap: 16px;
}
@media (max-width: 900px) {
  .bottom-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 700px) {
  .gauges-grid { grid-template-columns: 1fr; }
  .bottom-row { grid-template-columns: 1fr; }
}
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
</style>
