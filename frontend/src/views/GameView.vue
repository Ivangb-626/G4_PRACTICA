<template>
  <div>
    <h2>Game ID: {{ $route.params.id }}</h2>
    <router-link :to="`/game/${$route.params.id}/galaxy`">Galaxy</router-link> |
    <router-link :to="`/game/${$route.params.id}/tech`">Tech</router-link> |
    <router-link :to="`/game/${$route.params.id}/fleets`">Fleets</router-link>
    <router-view />
  </div>
</template>

<script setup lang="ts"></script>
