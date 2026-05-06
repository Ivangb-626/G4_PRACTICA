<template>
  <div :style="styles.panel">
    <div :style="styles.head">
      <h2 :style="styles.title">SHIP DESIGN STUDIO</h2>
      <button :style="styles.btn" @click="uiStore.setScreen('galaxy')">RETURN</button>
    </div>

    <div :style="styles.designerGrid">
      <!-- Parts Selection -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">COMPONENTS</h3>
        <div v-for="cat in categories" :key="cat">
          <h4 :style="{ color: '#00ffff', fontSize: '0.8rem', marginTop: '1rem' }">{{ cat }}</h4>
          <div :style="styles.partGrid">
            <button v-for="part in parts[cat]" :key="part.id" :style="styles.partBtn" @click="selectPart(part)">
              {{ part.name }}
            </button>
          </div>
        </div>
      </div>

      <!-- Preview -->
      <div :style="styles.innerPanel">
        <h3 :style="styles.innerTitle">DESIGN PREVIEW</h3>
        <div :style="styles.stats">
          <p>SIZE: {{ currentDesign.size }}</p>
          <p>COST: {{ currentDesign.cost }} BC</p>
          <p>WEAPONS: {{ currentDesign.weapons.length }}</p>
        </div>
        <button :style="styles.btn" @click="saveDesign">SAVE DESIGN</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useUIStore } from '../store/uiStore';

const uiStore = useUIStore();

type Part = { id: string; name: string };

const currentDesign = reactive<{ size: number; cost: number; weapons: Part[] }>({
  size: 100,
  cost: 500,
  weapons: [],
});

const categories = ['HULLS', 'WEAPONS', 'SPECIALS'] as const;
type Category = typeof categories[number];

const parts: Record<Category, Part[]> = {
  HULLS: [{ id: 'frigate', name: 'Frigate' }, { id: 'destroyer', name: 'Destroyer' }],
  WEAPONS: [{ id: 'laser', name: 'Laser' }, { id: 'fusion', name: 'Fusion' }],
  SPECIALS: [{ id: 'shield', name: 'Shield' }],
};

const styles = {
  panel: { padding: '1.5rem', backgroundColor: '#070f24', color: '#e0e0ff', fontFamily: 'monospace' },
  head: { display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', borderBottom: '2px solid #00ffff', paddingBottom: '1rem' },
  title: { margin: 0, fontSize: '2rem', color: '#00ffff', letterSpacing: '0.2em' },
  btn: { backgroundColor: '#1a1a3e', color: '#00ffff', border: '2px solid #00ffff', padding: '0.6rem 1.2rem', cursor: 'pointer', fontWeight: 'bold' as const },
  designerGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' },
  innerPanel: { padding: '1.2rem', backgroundColor: '#1a1a3e', border: '1px solid rgba(0, 255, 255, 0.3)', borderRadius: '8px' },
  innerTitle: { margin: '0 0 1rem', fontSize: '1.2rem', color: '#ffd700' },
  partGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' },
  partBtn: { padding: '0.5rem', backgroundColor: '#070f24', border: '1px solid #00ffff', color: '#fff', cursor: 'pointer', fontSize: '0.8rem' },
  stats: { padding: '1rem', backgroundColor: '#070f24', marginBottom: '1rem', borderRadius: '4px' }
};

function selectPart(part: Part) { currentDesign.weapons.push(part); }
function saveDesign() { /* API call */ }
</script>
