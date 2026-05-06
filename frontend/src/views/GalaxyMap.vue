<template>
  <section class="map-layout">
    <article class="map-panel retro-panel">
      <p v-if="error" class="error">{{ error }}</p>

      <div class="map-frame" v-if="systems.length">
        <div class="space-bg" aria-hidden="true">
          <div class="nebula nebula-1"></div>
          <div class="nebula nebula-2"></div>
          <div class="nebula nebula-3"></div>
          <div class="stars stars-far"></div>
          <div class="stars stars-mid"></div>
          <div class="stars stars-near"></div>
          <div class="twinkle"></div>
          <div class="shooting-star shooting-star-1"></div>
          <div class="shooting-star shooting-star-2"></div>
          <div class="grid-overlay"></div>
        </div>
        <button
          v-for="system in systems"
          :key="system.id"
          class="system-node"
          :class="[
            `star-${system.star_type}`,
            {
              colony: system.has_player_colony,
              fleet: system.has_player_fleet,
            },
          ]"
          :style="{ left: `calc(5% + ${system.position.x * 0.9}%)`, top: `calc(5% + ${system.position.y * 0.9}%)` }"
          type="button"
          @click="openSystem(system.id)"
        >
          <span class="sr-only">{{ system.name }}</span>
          <span class="system-label">{{ system.name }}</span>
        </button>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api'
import type { GalaxySystem } from '../types/game'

const route = useRoute()
const router = useRouter()
const gameId = String(route.params.id || '')

const systems = ref<GalaxySystem[]>([])
const loading = ref(false)
const error = ref('')

async function loadGalaxy() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.getGalaxy(gameId)
    systems.value = Array.isArray(response?.star_systems) ? response.star_systems : []
    // Ensure all have a type even if unexplored
    systems.value.forEach(sys => {
      if (!sys.star_type || sys.star_type === 'unknown') {
        const types = ['red', 'orange', 'yellow', 'white', 'blue']
        sys.star_type = types[sys.id.length % types.length] // pseudo-random stable
      }
    })
  } catch (err) {
    systems.value = []
    error.value = (err as Error).message || 'No se pudo cargar el mapa galactico.'
  } finally {
    loading.value = false
  }
}

function openSystem(systemId: string) {
  router.push(`/game/${gameId}/system/${systemId}`)
}

onMounted(loadGalaxy)
</script>

<style scoped>
.map-layout {
  display: block;
  height: 100%;
}

.map-panel {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 240px);
  min-height: 540px;
  overflow: hidden;
}

.side-panel {
  padding: 0.9rem;
}

.error {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  right: 0.5rem;
  z-index: 10;
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid var(--danger);
}

.map-frame {
  position: relative;
  flex: 1 1 auto;
  min-height: 520px;
  border-radius: 0;
  border: 0;
  background: #02030a;
  overflow: hidden;
  box-shadow:
    0 0 1.5rem rgba(79, 180, 255, 0.18) inset,
    0 0 0.8rem rgba(103, 240, 255, 0.25);
}

/* === ANIMATED SPACE BACKGROUND === */
.space-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse at 20% 30%, rgba(48, 22, 92, 0.55), transparent 55%),
    radial-gradient(ellipse at 80% 70%, rgba(13, 64, 110, 0.55), transparent 55%),
    radial-gradient(ellipse at 50% 50%, rgba(6, 12, 40, 0.6), transparent 70%),
    linear-gradient(180deg, #02030a 0%, #050920 50%, #02030a 100%);
}

/* Nebula clouds */
.nebula {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.45;
  mix-blend-mode: screen;
  animation: nebula-drift 60s ease-in-out infinite alternate;
}

.nebula-1 {
  width: 50%;
  height: 50%;
  top: -10%;
  left: -10%;
  background: radial-gradient(circle, rgba(140, 60, 200, 0.6), transparent 70%);
  animation-duration: 70s;
}

.nebula-2 {
  width: 60%;
  height: 60%;
  bottom: -20%;
  right: -15%;
  background: radial-gradient(circle, rgba(40, 130, 220, 0.55), transparent 70%);
  animation-duration: 90s;
  animation-direction: alternate-reverse;
}

.nebula-3 {
  width: 40%;
  height: 40%;
  top: 30%;
  left: 40%;
  background: radial-gradient(circle, rgba(220, 80, 130, 0.35), transparent 70%);
  animation-duration: 110s;
}

@keyframes nebula-drift {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(4%, -3%) scale(1.08); }
  100% { transform: translate(-3%, 4%) scale(0.95); }
}

/* Star layers using radial-gradients (pixel-like dots) */
.stars {
  position: absolute;
  inset: -100% -100%;
  width: 300%;
  height: 300%;
  background-repeat: repeat;
  image-rendering: pixelated;
}

.stars-far {
  background-image:
    radial-gradient(1px 1px at 20px 30px, rgba(255, 255, 255, 0.6), transparent),
    radial-gradient(1px 1px at 60px 80px, rgba(200, 220, 255, 0.55), transparent),
    radial-gradient(1px 1px at 110px 50px, rgba(255, 255, 255, 0.5), transparent),
    radial-gradient(1px 1px at 170px 120px, rgba(180, 200, 255, 0.45), transparent),
    radial-gradient(1px 1px at 220px 30px, rgba(255, 255, 255, 0.55), transparent),
    radial-gradient(1px 1px at 280px 90px, rgba(255, 240, 220, 0.5), transparent);
  background-size: 320px 160px;
  animation: stars-drift 240s linear infinite;
  opacity: 0.55;
}

.stars-mid {
  background-image:
    radial-gradient(1.5px 1.5px at 40px 60px, rgba(255, 255, 255, 0.85), transparent),
    radial-gradient(1.5px 1.5px at 130px 110px, rgba(180, 220, 255, 0.8), transparent),
    radial-gradient(1.5px 1.5px at 220px 40px, rgba(255, 255, 255, 0.75), transparent),
    radial-gradient(1.5px 1.5px at 300px 150px, rgba(255, 220, 200, 0.7), transparent);
  background-size: 360px 200px;
  animation: stars-drift 160s linear infinite;
  opacity: 0.75;
}

.stars-near {
  background-image:
    radial-gradient(2px 2px at 50px 80px, rgba(255, 255, 255, 1), transparent),
    radial-gradient(2px 2px at 180px 30px, rgba(170, 220, 255, 0.95), transparent),
    radial-gradient(2px 2px at 310px 120px, rgba(255, 240, 200, 0.9), transparent);
  background-size: 400px 220px;
  animation: stars-drift 90s linear infinite;
  opacity: 0.9;
}

@keyframes stars-drift {
  from { transform: translate(0, 0); }
  to { transform: translate(-300px, -200px); }
}

/* Twinkle overlay — pulses opacity over star field */
.twinkle {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 15% 25%, #ffffff, transparent),
    radial-gradient(1px 1px at 35% 75%, #aee3ff, transparent),
    radial-gradient(1px 1px at 55% 15%, #ffffff, transparent),
    radial-gradient(1px 1px at 78% 55%, #ffd9a8, transparent),
    radial-gradient(1px 1px at 88% 85%, #ffffff, transparent),
    radial-gradient(1px 1px at 25% 60%, #ffffff, transparent);
  animation: twinkle 3.6s ease-in-out infinite alternate;
}

@keyframes twinkle {
  0% { opacity: 0.25; }
  50% { opacity: 0.9; }
  100% { opacity: 0.4; }
}

/* Shooting stars */
.shooting-star {
  position: absolute;
  width: 2px;
  height: 2px;
  background: #ffffff;
  border-radius: 0;
  box-shadow: 0 0 8px 1px #ffffff, 0 0 14px 2px rgba(140, 220, 255, 0.6);
  opacity: 0;
}

.shooting-star::after {
  content: '';
  position: absolute;
  top: 0;
  right: 2px;
  width: 90px;
  height: 1px;
  background: linear-gradient(to left, #ffffff, transparent);
  transform-origin: right center;
}

.shooting-star-1 {
  top: 20%;
  left: 110%;
  animation: shoot 7s linear infinite;
  animation-delay: 1.5s;
}

.shooting-star-2 {
  top: 65%;
  left: 110%;
  animation: shoot 11s linear infinite;
  animation-delay: 5s;
}

@keyframes shoot {
  0% { transform: translate(0, 0); opacity: 0; }
  3% { opacity: 1; }
  20% { transform: translate(-130%, 50vh); opacity: 0; }
  100% { transform: translate(-130%, 50vh); opacity: 0; }
}

/* Subtle grid scanline overlay for retro CRT feel */
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(89, 170, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(89, 170, 255, 0.05) 1px, transparent 1px),
    repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.025) 0 1px, transparent 1px 3px);
  background-size: 60px 60px, 60px 60px, 100% 3px;
  pointer-events: none;
  opacity: 0.6;
}

.connection-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.system-node {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 16px;
  height: 16px;
  border-radius: 0;
  border: 0;
  cursor: pointer;
  background: transparent;
  z-index: 2;
}

.system-node:hover {
  z-index: 3;
}

.system-node:hover .system-label {
  color: var(--primary-strong);
  text-shadow: 0 0 0.6rem rgba(103, 240, 255, 0.9), 0 0 0.35rem rgba(0, 0, 0, 0.95);
}

.system-node::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 2px;
  background: var(--star-core, #ffffff);
  animation: glow-pulse 3s infinite alternate;
  box-shadow:
    /* Inner Cross */
    -2px 0 0 var(--star-core),
    2px 0 0 var(--star-core),
    0 -2px 0 var(--star-core),
    0 2px 0 var(--star-core),
    /* Main Color Cross */
    -4px 0 0 var(--star-color),
    4px 0 0 var(--star-color),
    0 -4px 0 var(--star-color),
    0 4px 0 var(--star-color),
    -2px -2px 0 var(--star-color),
    -2px 2px 0 var(--star-color),
    2px -2px 0 var(--star-color),
    2px 2px 0 var(--star-color),
    /* Outer Dim Cross */
    -6px 0 0 var(--star-dim),
    6px 0 0 var(--star-dim),
    0 -6px 0 var(--star-dim),
    0 6px 0 var(--star-dim),
    -4px -2px 0 var(--star-dim),
    -4px 2px 0 var(--star-dim),
    4px -2px 0 var(--star-dim),
    4px 2px 0 var(--star-dim),
    -2px -4px 0 var(--star-dim),
    2px -4px 0 var(--star-dim),
    -2px 4px 0 var(--star-dim),
    2px 4px 0 var(--star-dim),
    /* Deep Glow Effect */
    0 0 10px 2px var(--star-color);
}

@keyframes glow-pulse {
  0% { filter: brightness(0.8) drop-shadow(0 0 2px var(--star-color)); transform: translate(-50%, -50%) scale(0.9); }
  100% { filter: brightness(1.2) drop-shadow(0 0 6px var(--star-color)); transform: translate(-50%, -50%) scale(1.1); }
}

.system-node.selected::before {
  box-shadow:
    -4px 0 0 var(--star-core), 4px 0 0 var(--star-core),
    0 -4px 0 var(--star-core), 0 4px 0 var(--star-core),
    -8px 0 0 var(--star-color), 8px 0 0 var(--star-color),
    0 -8px 0 var(--star-color), 0 8px 0 var(--star-color),
    -4px -4px 0 var(--star-color), -4px 4px 0 var(--star-color),
    4px -4px 0 var(--star-color), 4px 4px 0 var(--star-color),
    -12px 0 0 var(--star-dim), 12px 0 0 var(--star-dim),
    0 -12px 0 var(--star-dim), 0 12px 0 var(--star-dim),
    -8px -4px 0 var(--star-dim), -8px 4px 0 var(--star-dim),
    8px -4px 0 var(--star-dim), 8px 4px 0 var(--star-dim),
    -4px -8px 0 var(--star-dim), 4px -8px 0 var(--star-dim),
    -4px 8px 0 var(--star-dim), 4px 8px 0 var(--star-dim),
    0 0 0 4px #ffe082,
    0 0 15px 4px #ffe082,
    0 0 20px 4px var(--star-color);
}

.system-node.colony::before {
  box-shadow:
    -4px 0 0 var(--star-core), 4px 0 0 var(--star-core),
    0 -4px 0 var(--star-core), 0 4px 0 var(--star-core),
    -8px 0 0 var(--star-color), 8px 0 0 var(--star-color),
    0 -8px 0 var(--star-color), 0 8px 0 var(--star-color),
    -4px -4px 0 var(--star-color), -4px 4px 0 var(--star-color),
    4px -4px 0 var(--star-color), 4px 4px 0 var(--star-color),
    -12px 0 0 var(--star-dim), 12px 0 0 var(--star-dim),
    0 -12px 0 var(--star-dim), 0 12px 0 var(--star-dim),
    -8px -4px 0 var(--star-dim), -8px 4px 0 var(--star-dim),
    8px -4px 0 var(--star-dim), 8px 4px 0 var(--star-dim),
    -4px -8px 0 var(--star-dim), 4px -8px 0 var(--star-dim),
    -4px 8px 0 var(--star-dim), 4px 8px 0 var(--star-dim),
    0 0 10px rgba(141, 246, 191, 0.9),
    0 0 15px 4px var(--star-color);
}

.system-node.fleet::after {
  content: '';
  position: absolute;
  width: 6px;
  height: 6px;
  right: -5px;
  top: -3px;
  background: var(--primary-strong);
  box-shadow: 0 0 0.5rem rgba(103, 240, 255, 0.9);
  /* Make fleet pixel-ish too */
  border-radius: 0;
}

.system-label {
  position: absolute;
  left: 50%;
  top: 130%;
  transform: translateX(-50%);
  min-width: max-content;
  color: var(--text);
  font-size: 0.74rem;
  text-shadow: 0 0 0.35rem rgba(0, 0, 0, 0.8);
  font-family: monospace; /* Retro pixel font feel */
}

.star-red {
  --star-core: #ffb8bf;
  --star-color: #ff5d6c;
  --star-dim: rgba(255, 93, 108, 0.4);
}

.star-orange {
  --star-core: #ffdcba;
  --star-color: #ff9d3a;
  --star-dim: rgba(255, 157, 58, 0.4);
}

.star-yellow {
  --star-core: #fff1bb;
  --star-color: #ffd447;
  --star-dim: rgba(255, 212, 71, 0.4);
}

.star-white {
  --star-core: #ffffff;
  --star-color: #d5ecff;
  --star-dim: rgba(213, 236, 255, 0.4);
}

.star-blue {
  --star-core: #bce3ff;
  --star-color: #4bb7ff;
  --star-dim: rgba(75, 183, 255, 0.4);
}

.star-unknown {
  --star-core: #cbd3de;
  --star-color: #6881a1;
  --star-dim: rgba(104, 129, 161, 0.4);
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin: 0.9rem 0 1rem;
}

.detail-card {
  padding: 0.75rem;
  border-radius: 10px;
  border: 1px solid rgba(89, 170, 255, 0.18);
  background: rgba(8, 15, 38, 0.72);
}

.detail-card span {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.planet-list {
  display: grid;
  gap: 0.7rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.planet-list li {
  display: grid;
  gap: 0.2rem;
  padding: 0.7rem;
  border: 1px solid rgba(112, 166, 214, 0.18);
  border-radius: 8px;
  background: rgba(7, 15, 36, 0.72);
}

.empty {
  color: var(--text-muted);
}

.error {
  color: var(--danger);
  margin-bottom: 0.75rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

@media (max-width: 1080px) {
  .map-layout {
    grid-template-columns: 1fr;
  }

  .map-panel {
    height: auto;
    min-height: 600px;
  }

  .map-frame {
    min-height: 520px;
  }
}
</style>
