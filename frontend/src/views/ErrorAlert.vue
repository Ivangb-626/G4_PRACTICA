<template>
  <div v-if="message" class="error-alert">
    <span class="error-icon">⚠</span>
    <div class="error-content">
      <p class="error-title">Error</p>
      <p class="error-message">{{ message }}</p>
    </div>
    <button v-if="dismissible" class="close-btn" @click="$emit('dismiss')">×</button>
  </div>
</template>

<script setup lang="ts">
interface Props {
  message?: string
  dismissible?: boolean
}

defineProps<Props>()

defineEmits<{
  dismiss: []
}>()
</script>

<style scoped>
.error-alert {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 107, 138, 0.1);
  border: 1px solid var(--danger);
  border-radius: 6px;
  color: #ffdbe3;
  position: relative;
}

.error-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  margin-top: 0.2rem;
}

.error-content {
  flex: 1;
}

.error-title {
  margin: 0 0 0.25rem;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.9rem;
}

.error-message {
  margin: 0;
  font-size: 0.85rem;
  opacity: 0.9;
}

.close-btn {
  background: none;
  border: none;
  color: #ffdbe3;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.close-btn:hover {
  opacity: 0.7;
}
</style>
