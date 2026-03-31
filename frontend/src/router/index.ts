import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '../views/LoginPage.vue'
import RegisterPage from '../views/RegisterPage.vue'
import Dashboard from '../views/Dashboard.vue'
import GameView from '../views/GameView.vue'
import GalaxyMap from '../views/GalaxyMap.vue'
import SystemView from '../views/SystemView.vue'
import ColonyView from '../views/ColonyView.vue'
import TechTree from '../views/TechTree.vue'
import FleetManager from '../views/FleetManager.vue'
import CombatResult from '../views/CombatResult.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginPage },
  { path: '/register', component: RegisterPage },
  { path: '/dashboard', component: Dashboard },
  { path: '/game/:id', component: GameView, props: true, children:[
      { path:'galaxy', component: GalaxyMap },
      { path:'system/:sysId', component: SystemView, props:true },
      { path:'colony/:colId', component: ColonyView, props:true },
      { path:'tech', component: TechTree },
      { path:'fleets', component: FleetManager },
      { path:'combat/:combatId', component: CombatResult, props:true }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
