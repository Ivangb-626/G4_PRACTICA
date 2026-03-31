<template>
  <section>
    <h2>Dashboard</h2>
    <button @click="loadGames">Refrescar</button>
    <button @click="newGame">Nueva Partida</button>

    <table v-if="games.length">
      <thead><tr><th>Nombre</th><th>Turno</th><th>Azte</th><th>Acciones</th></tr></thead>
      <tbody>
        <tr v-for="g in games" :key="g.game_id">
          <td>{{ g.name }}</td>
          <td>{{ g.turn }}</td>
          <td>{{ g.player_race }}</td>
          <td>
            <button @click="loadGame(g.game_id)">Cargar</button>
            <button @click="deleteGame(g.game_id)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else>No hay partidas guardadas aún.</p>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'

const games = ref<any[]>([])
const router = useRouter()

async function loadGames() {
  try {
    const response = await api.listGames()
    games.value = response.games
  } catch (error) {
    console.error(error)
  }
}

async function newGame() {
  const name = prompt('Nombre de la nueva partida:', 'Partida 1')
  if (!name) return
  const scenario = { galaxy_size: 'small', num_opponents: 1, difficulty: 'normal', player_race: 'humans' }
  const response = await api.createGame(name, scenario)
  router.push(`/game/${response.game_id}/galaxy`)
}

async function loadGame(id: string) {
  await api.loadGame(id)
  router.push(`/game/${id}/galaxy`)
}

async function deleteGame(id: string) {
  await api.deleteGame(id)
  await loadGames()
}

onMounted(loadGames)
</script>
