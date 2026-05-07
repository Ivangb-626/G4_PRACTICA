/**
 * BFS auxiliar — calcula los sistemas accesibles desde origin dentro de
 * `maxJumps` saltos siguiendo las conexiones de la galaxia.
 */
export function reachableSystems(
  starSystems: any[] | undefined,
  originId: string | null,
  maxJumps: number,
): Set<string> {
  const result = new Set<string>()
  if (!starSystems || !originId || maxJumps <= 0) return result
  const byId = new Map<string, any>()
  for (const s of starSystems) byId.set(s.id, s)
  if (!byId.has(originId)) return result

  // Rango ilimitado (Interphased Drive): cualquier sistema vale.
  if (!Number.isFinite(maxJumps)) {
    for (const s of starSystems) {
      if (s.id !== originId) result.add(s.id)
    }
    return result
  }

  let frontier: string[] = [originId]
  const visited = new Set<string>([originId])
  for (let i = 0; i < maxJumps; i += 1) {
    const next: string[] = []
    for (const sid of frontier) {
      const sys = byId.get(sid)
      if (!sys) continue
      const conns: string[] = sys.connections || []
      for (const conn of conns) {
        if (visited.has(conn)) continue
        visited.add(conn)
        result.add(conn)
        next.push(conn)
      }
    }
    frontier = next
  }
  return result
}
