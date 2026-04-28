<template>
  <button 
    class="retro-btn" 
    :class="[`retro-btn-${variant}`, { 'retro-btn-loading': isLoading }]"
    :disabled="disabled || isLoading"
    v-bind="$attrs"
  >
    <slot v-if="!isLoading" />
    <span v-else class="loading-text">{{ loadingText }}</span>
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'success'
  disabled?: boolean
  isLoading?: boolean
  loadingText?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'secondary',
  disabled: false,
  isLoading: false,
  loadingText: 'Cargando...'
})
</script>

<style scoped>
.retro-btn {
  border: 1px solid var(--primary);
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.2), rgba(79, 180, 255, 0.05));
  color: var(--text);
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.72rem;
  transition: all 0.2s ease;
}

.retro-btn:hover:not(:disabled) {
  border-color: var(--primary-strong);
  box-shadow: 0 0 0.65rem rgba(103, 240, 255, 0.45);
}

.retro-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.retro-btn-primary {
  background: linear-gradient(180deg, rgba(79, 180, 255, 0.4), rgba(79, 180, 255, 0.18));
}

.retro-btn-primary:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(103, 240, 255, 0.45), rgba(79, 180, 255, 0.22));
}

.retro-btn-danger {
  border-color: var(--danger);
  color: #ffdbe3;
}

.retro-btn-danger:hover:not(:disabled) {
  background: rgba(255, 107, 138, 0.14);
  box-shadow: 0 0 0.65rem rgba(255, 107, 138, 0.4);
}

.retro-btn-success {
  border-color: var(--success, #67f088);
  color: var(--success, #67f088);
}

.retro-btn-success:hover:not(:disabled) {
  background: rgba(103, 240, 136, 0.14);
  box-shadow: 0 0 0.65rem rgba(103, 240, 136, 0.4);
}

.loading-text {
  display: inline-block;
}
</style>
