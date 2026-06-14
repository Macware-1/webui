<template>
  <header class="topbar">
    <div>
      <h1 class="topbar-title">{{ page }}</h1>
      <p class="topbar-sub">CAN Gateway</p>
    </div>
    <div :class="['conn-badge', system.link_up ? 'conn-up' : 'conn-down']">
      <span class="conn-dot"></span>
      {{ system.link_up ? 'Connected' : 'Disconnected' }}
    </div>
  </header>
</template>

<script setup>
const props = defineProps({
  page: String,
  system: Object,
})
</script>
