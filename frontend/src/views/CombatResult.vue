<template>
  <section>
    <h3>Combat Result {{ route.params.combatId }}</h3>
    <p>Resumen de combate (visualmente planeado).</p>
  </section>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();
</script>
