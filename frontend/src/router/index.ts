import { createRouter, createWebHistory } from 'vue-router'
import CombatResult from '../views/CombatResult.vue'
import ColonyView from '../views/ColonyView.vue'
import Dashboard from '../views/Dashboard.vue'
import DiplomacyView from '../views/DiplomacyView.vue'
import FleetManager from '../views/FleetManager.vue'
import GalaxyMap from '../views/GalaxyMap.vue'
import GameView from '../views/GameView.vue'
import LoginPage from '../views/LoginPage.vue'
import RegisterPage from '../views/RegisterPage.vue'
import SystemView from '../views/SystemView.vue'
import TechTree from '../views/TechTree.vue'
import EspionageView from '../views/EspionageView.vue'
import LeadersView from '../views/LeadersView.vue'
import CouncilView from '../views/CouncilView.vue'
import ScoreView from '../views/ScoreView.vue'
import ShipDesignerView from '../views/ShipDesignerView.vue'
import CheatsView from '../views/CheatsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: LoginPage },
    { path: '/register', component: RegisterPage },
    { path: '/dashboard', component: Dashboard },
    {
      path: '/game/:id',
      component: GameView,
      props: true,
      children: [
        { path: '', redirect: (to) => `/game/${to.params.id}/galaxy` },
        { path: 'galaxy', component: GalaxyMap },
        { path: 'system/:sysId', component: SystemView, props: true },
        { path: 'colony/:colId', component: ColonyView, props: true },
        { path: 'tech', component: TechTree },
        { path: 'fleets', component: FleetManager },
        { path: 'ships', component: ShipDesignerView },
        { path: 'diplomacy', component: DiplomacyView },
        { path: 'espionage', component: EspionageView },
        { path: 'leaders', component: LeadersView },
        { path: 'council', component: CouncilView },
        { path: 'score', component: ScoreView },
        { path: 'cheats', component: CheatsView },
        { path: 'combat/:combatId', component: CombatResult, props: true },
      ],
    },
  ],
})

export default router
