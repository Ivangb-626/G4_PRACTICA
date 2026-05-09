// components/Tooltip.vue
<template>
  <div
    class="tooltip-container"
    tabindex="0"
    @mouseenter="showTooltip"
    @mouseleave="hideTooltip"
    @focusin="showTooltip"
    @focusout="hideTooltip"
  >
    <slot></slot>
    <div v-if="visible" class="tooltip-content" :style="tooltipStyles" role="tooltip">
      <h4 class="tooltip-title">{{ title }}</h4>
      <p class="tooltip-description">{{ description || 'Sin detalles disponibles.' }}</p>
      <div v-if="details" class="tooltip-details">
        <div v-for="(value, key) in details" :key="key">
          <span class="detail-key">{{ key }}:</span>
          <span class="detail-value">{{ value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  title: string;
  description?: string;
  details?: Record<string, string | number>;
  position?: 'top' | 'bottom' | 'left' | 'right';
}>();

const visible = ref(false);
const tooltipStyles = computed(() => {
  const base = {
    position: 'absolute' as const,
    backgroundColor: '#070f24',
    border: '1px solid #00ffff',
    padding: '0.5rem',
    borderRadius: '4px',
    zIndex: 1000,
    minWidth: '200px',
    maxWidth: '300px',
    color: '#e0e0ff',
    fontSize: '0.8rem',
    pointerEvents: 'none' as const,
    boxShadow: '0 8px 24px rgba(0,0,0,0.55), 0 0 18px rgba(0,255,255,0.18)',
  };

  switch (props.position) {
    case 'top': return { ...base, bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '5px' };
    case 'left': return { ...base, right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: '5px' };
    case 'right': return { ...base, left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: '5px' };
    case 'bottom':
    default: return { ...base, top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '5px' };
  }
});

function showTooltip() {
  visible.value = true;
}

function hideTooltip() {
  visible.value = false;
}
</script>

<style scoped>
.tooltip-container {
  position: relative;
  display: inline-block;
  outline: none;
}

.tooltip-content {
  animation: tooltip-in 0.12s ease-out both;
}

@keyframes tooltip-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.tooltip-title {
  color: #00ffff;
  font-size: 1rem;
  margin-top: 0;
  margin-bottom: 0.3rem;
  border-bottom: 1px solid rgba(0, 255, 255, 0.3);
  padding-bottom: 0.2rem;
}

.tooltip-description {
  margin-top: 0;
  margin-bottom: 0.5rem;
  line-height: 1.35;
}

.tooltip-details {
  margin-top: 0.5rem;
  border-top: 1px dashed rgba(224, 224, 255, 0.1);
  padding-top: 0.3rem;
}

.detail-key {
  color: #88aaff;
  font-weight: bold;
  margin-right: 0.3rem;
}

.detail-value {
  color: #e0e0ff;
}
</style>
