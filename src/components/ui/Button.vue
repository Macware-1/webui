<template>
  <button
    :class="['app-btn', `variant-${variant}`, `size-${size}`, { full } , $attrs.class]"
    :type="type"
    :aria-label="ariaLabel || $attrs['aria-label']"
    v-on="$attrs"
  >
    <slot />
  </button>
</template>

<script setup>
const props = defineProps({
  variant: { type: String, default: 'primary' }, // primary | secondary | ghost
  size: { type: String, default: 'md' }, // sm | md | lg
  full: { type: Boolean, default: false },
  type: { type: String, default: 'button' },
  ariaLabel: { type: String, default: '' },
})
</script>

<style scoped>
.app-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 10px;
  border: 1px solid var(--border);
  padding: 8px 12px;
  font-weight: 700;
  cursor: pointer;
  background: transparent;
  color: var(--text);
}
.app-btn.full { width: 100%; }

/* sizes */
.size-sm { padding: 6px 10px; font-size: 13px; }
.size-md { padding: 8px 12px; font-size: 14px; }
.size-lg { padding: 12px 16px; font-size: 16px; }

/* variants */
.variant-primary { background: var(--primary); color: #fff; border-color: transparent; }
.variant-primary:hover { opacity: 0.92; }
.variant-secondary { background: var(--dim); color: var(--text); border-color: var(--border); }
.variant-ghost { background: transparent; color: var(--text); border-color: transparent; }

.variant-primary:disabled { opacity: 0.6; cursor: not-allowed; }

</style>
