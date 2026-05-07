/**
 * Compatibility shim. The canonical API client is in `services/api.ts`.
 * This module re-exports it under the legacy nested structure used by
 * older views (auth/game/galaxy/colony/fleet/cheat/leaders/diplomacy/research/espionage).
 */
import { api as flatApi } from '../services/api'

export const api = {
  auth: {
    login: flatApi.login,
    register: flatApi.register,
    profile: flatApi.getProfile,
  },
  game: {
    new: (config: Record<string, unknown>) => flatApi.createGame(config),
    list: flatApi.listGames,
    get: flatApi.loadGame,
    delete: flatApi.deleteGame,
    endTurn: flatApi.endTurn,
    score: flatApi.getScore,
    getTopHallOfFame: flatApi.getHallOfFame,
    scenarios: flatApi.getScenarios,
  },
  galaxy: {
    get: flatApi.getGalaxy,
    getSystem: flatApi.getSystem,
  },
  colony: {
    list: flatApi.listColonies,
    get: flatApi.getColony,
    assign: (gameId: string, colonyId: string, payload: { farmers: number; workers: number; scientists: number }) =>
      flatApi.assignPopulation(gameId, colonyId, payload),
    buildQueue: (gameId: string, colonyId: string, item: { item_type: 'building' | 'ship'; item_id: string }) =>
      flatApi.addBuildQueueItem(gameId, colonyId, item.item_type, item.item_id),
    removeQueueItem: flatApi.removeBuildQueueItem,
  },
  fleet: {
    list: flatApi.listFleets,
    move: flatApi.moveFleet,
    colonize: flatApi.colonizePlanet,
    split: flatApi.splitFleet,
    merge: flatApi.mergeFleets,
    disband: flatApi.disbandFleet,
    range: flatApi.getFleetRange,
    reachable: flatApi.getFleetReachable,
  },
  research: {
    get: flatApi.getResearch,
    select: (gameId: string, payload: { field: string; level: number; tech_id: string } | string) => {
      if (typeof payload === 'string') {
        return flatApi.selectResearch(gameId, { field: '', level: 1, tech_id: payload })
      }
      return flatApi.selectResearch(gameId, payload)
    },
  },
  diplomacy: {
    list: flatApi.getDiplomacy,
    propose: (gameId: string, body: any) => flatApi.proposeTreaty(gameId, body.target, body.type || body.treaty_type, body.terms),
    accept: flatApi.acceptTreaty,
    reject: flatApi.rejectTreaty,
    declareWar: flatApi.declareWar,
    surrender: flatApi.surrender,
    gift: flatApi.giveGift,
    demand: flatApi.makeDemand,
    techTrade: flatApi.techTrade,
    blackmail: flatApi.blackmail,
    aiEvaluate: flatApi.aiEvaluateProposal,
  },
  espionage: {
    list: flatApi.listSpies,
    recruit: flatApi.recruitSpy,
    mission: flatApi.assignSpyMission,
  },
  leaders: {
    list: flatApi.listHiredLeaders,
    available: flatApi.listAvailableLeaders,
    hire: flatApi.hireLeader,
    assign: flatApi.assignLeader,
    unassign: flatApi.unassignLeader,
    dismiss: flatApi.dismissLeader,
  },
  shipDesign: {
    catalog: flatApi.getShipDesignCatalog,
    list: flatApi.listShipDesigns,
    create: flatApi.createShipDesign,
    delete: flatApi.deleteShipDesign,
  },
  council: {
    votes: flatApi.getCouncilVotes,
    convene: flatApi.conveneCouncil,
    vote: flatApi.voteCouncil,
  },
  combat: {
    auto: flatApi.combatAuto,
    monster: flatApi.fightMonster,
    defeatGuardian: flatApi.defeatGuardian,
    buildPortal: flatApi.buildDimensionalPortal,
    assaultAntaran: flatApi.assaultAntaranHomeworld,
    tacticalStart: flatApi.combatTacticalStart,
    tacticalAuto: flatApi.combatTacticalAuto,
    tacticalAction: flatApi.combatTacticalAction,
  },
  ground: {
    assault: flatApi.groundAssault,
    mindControl: flatApi.mindControl,
    bombard: flatApi.bombardColony,
  },
  raceDesign: {
    options: flatApi.getRaceDesignOptions,
    validate: flatApi.validateRaceDesign,
  },
  cheat: {
    apply: (gameId: string, code: string, target?: Record<string, unknown>) => flatApi.applyCheat(gameId, code, target),
    codes: flatApi.listCheatCodes,
  },
}

export default api
