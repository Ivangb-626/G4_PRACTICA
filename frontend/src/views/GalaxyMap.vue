<template>
  <div :style="styles.container" ref="containerRef">
    <canvas
      ref="canvasRef"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @wheel="handleWheel"
      :style="styles.canvas"
    ></canvas>
    
    <!-- UI Overlays -->
    <div :style="styles.zoomOverlay">
      ZOOM: {{ Math.round(zoom * 100) }}%
    </div>
    
    <div v-if="error" :style="styles.error">
      {{ error }}
    </div>

    <div v-if="loading" :style="styles.loading">
      SCANNING SECTOR...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useGameStore } from '../store/gameStore';
import { useUIStore } from '../store/uiStore';
import { renderGalaxy } from '../canvas/galaxyRenderer';

const gameStore = useGameStore();
const uiStore = useUIStore();

const containerRef = ref<HTMLDivElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);

const zoom = ref(1.0);
const panX = ref(0);
const panY = ref(0);
const loading = ref(false);
const error = ref('');

const isDragging = ref(false);
const lastMouseX = ref(0);
const lastMouseY = ref(0);

const styles = {
  container: {
    position: 'relative' as const,
    width: '100%',
    height: '100%',
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  canvas: {
    display: 'block',
    cursor: isDragging.value ? 'grabbing' : 'crosshair',
  },
  zoomOverlay: {
    position: 'absolute' as const,
    bottom: '1rem',
    right: '1rem',
    backgroundColor: 'rgba(0,0,0,0.6)',
    padding: '0.4rem 0.8rem',
    borderRadius: '4px',
    border: '1px solid #00ffff',
    color: '#00ffff',
    fontSize: '0.8rem',
    pointerEvents: 'none' as const,
  },
  error: {
    position: 'absolute' as const,
    top: '1rem',
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: 'rgba(255,0,0,0.8)',
    padding: '1rem',
    color: '#fff',
  },
  loading: {
    position: 'absolute' as const,
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontSize: '1.5rem',
    color: '#00ffff',
    textShadow: '0 0 10px #00ffff',
  }
};

const handleMouseDown = (e: MouseEvent) => {
  if (e.button === 0 || e.button === 1) { // Left or Middle
    isDragging.value = true;
    lastMouseX.value = e.clientX;
    lastMouseY.value = e.clientY;
  }
};

const handleMouseMove = (e: MouseEvent) => {
  if (isDragging.value) {
    panX.value += e.clientX - lastMouseX.value;
    panY.value += e.clientY - lastMouseY.value;
    lastMouseX.value = e.clientX;
    lastMouseY.value = e.clientY;
    requestRender();
  }
};

const handleMouseUp = () => {
  isDragging.value = false;
};

const handleWheel = (e: WheelEvent) => {
  e.preventDefault();
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const newZoom = Math.max(0.3, Math.min(6, zoom.value * delta));
  zoom.value = newZoom;
  requestRender();
};

const requestRender = () => {
  const canvas = canvasRef.value;
  if (!canvas || !gameStore.galaxy) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  renderGalaxy(
    ctx,
    gameStore.galaxy,
    canvas.width,
    canvas.height,
    uiStore.selectedStarIndex,
    gameStore.fleets,
    zoom.value,
    panX.value,
    panY.value
  );
};

const resize = () => {
  if (containerRef.value && canvasRef.value) {
    canvasRef.value.width = containerRef.value.clientWidth;
    canvasRef.value.height = containerRef.value.clientHeight;
    requestRender();
  }
};

onMounted(() => {
  window.addEventListener('resize', resize);
  resize();
  if (!gameStore.galaxy) {
    gameStore.fetchGalaxy().catch(err => error.value = err.message);
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', resize);
});

watch(() => gameStore.galaxy, requestRender);
watch(() => uiStore.selectedStarIndex, requestRender);
</script>
