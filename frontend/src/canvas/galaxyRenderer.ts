/**
 * Renders the galaxy view onto a canvas.
 *
 * Backend payload (`/api/game/<id>/galaxy`) shape:
 *   {
 *     star_systems: [
 *       { id, name, position: {x, y}, star_type, explored, planets, connections,
 *         has_player_colony, has_player_fleet, has_enemy_fleet }
 *     ]
 *   }
 * Coordinates are percentages (0..100). Selected systems use `selectedSystemId`.
 */
export function renderGalaxy(
  ctx: CanvasRenderingContext2D,
  galaxy: any,
  width: number,
  height: number,
  selectedSystemId: string | null,
  playerFleets: any[],
  zoom: number,
  panX: number,
  panY: number,
) {
  ctx.clearRect(0, 0, width, height)

  // Backdrop
  const grad = ctx.createRadialGradient(
    width / 2, height / 2, 0,
    width / 2, height / 2, Math.max(width, height),
  )
  grad.addColorStop(0, '#0a0a2e')
  grad.addColorStop(1, '#000000')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, width, height)

  // Tiny static starfield to fill the void
  ctx.fillStyle = 'rgba(255,255,255,0.4)'
  for (let i = 0; i < 80; i += 1) {
    const sx = (Math.sin(i * 12.9898) * 43758.5453) % 1
    const sy = (Math.cos(i * 78.233) * 43758.5453) % 1
    const x = Math.abs(sx) * width
    const y = Math.abs(sy) * height
    ctx.fillRect(x, y, 1, 1)
  }

  const systems = galaxy?.star_systems || galaxy?.stars || []
  if (!systems.length) {
    ctx.fillStyle = '#88aaff'
    ctx.font = '14px monospace'
    ctx.textAlign = 'center'
    ctx.fillText('No hay datos del sector. Pulsa "RECARGAR" o crea una partida.', width / 2, height / 2)
    return
  }

  // Translate from 0..100 percentage coords into the canvas frame, with zoom + pan.
  const padX = 40
  const padY = 40
  const drawW = width - padX * 2
  const drawH = height - padY * 2

  function project(pos: { x: number; y: number }) {
    const cx = padX + (pos.x / 100) * drawW
    const cy = padY + (pos.y / 100) * drawH
    // Apply zoom around canvas centre + pan
    const zx = (cx - width / 2) * zoom + width / 2 + panX
    const zy = (cy - height / 2) * zoom + height / 2 + panY
    return { x: zx, y: zy }
  }

  // Connections first so stars overlay them
  ctx.strokeStyle = 'rgba(89, 170, 255, 0.25)'
  ctx.lineWidth = 1
  systems.forEach((sys: any) => {
    if (!sys?.connections) return
    const a = project(sys.position || { x: 0, y: 0 })
    sys.connections.forEach((connId: string) => {
      const target = systems.find((s: any) => s.id === connId)
      if (!target) return
      const b = project(target.position || { x: 0, y: 0 })
      ctx.beginPath()
      ctx.moveTo(a.x, a.y)
      ctx.lineTo(b.x, b.y)
      ctx.stroke()
    })
  })

  // Stars
  systems.forEach((sys: any) => {
    const p = project(sys.position || { x: 0, y: 0 })
    const explored = sys.explored !== false
    const isBlackHole = sys.star_type === 'black_hole' || sys.is_black_hole
    const radius = isBlackHole ? 6 : explored ? 5 : 3

    // Star core
    ctx.beginPath()
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2)
    ctx.fillStyle = getStarColor(sys.star_type)
    ctx.fill()

    if (isBlackHole) {
      ctx.strokeStyle = '#aa55ff'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(p.x, p.y, radius + 4, 0, Math.PI * 2)
      ctx.stroke()
    }

    // Glow halo for explored systems
    if (explored) {
      const halo = ctx.createRadialGradient(p.x, p.y, radius, p.x, p.y, radius * 4)
      halo.addColorStop(0, 'rgba(89, 170, 255, 0.35)')
      halo.addColorStop(1, 'rgba(89, 170, 255, 0)')
      ctx.fillStyle = halo
      ctx.beginPath()
      ctx.arc(p.x, p.y, radius * 4, 0, Math.PI * 2)
      ctx.fill()
    }

    // Selection ring
    if (sys.id && sys.id === selectedSystemId) {
      ctx.strokeStyle = '#00ffff'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(p.x, p.y, radius + 6, 0, Math.PI * 2)
      ctx.stroke()
    }

    // Owner indicator: green ring if player has colony, red if enemy fleet
    if (sys.has_player_colony) {
      ctx.strokeStyle = '#44ee44'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.arc(p.x, p.y, radius + 3, 0, Math.PI * 2)
      ctx.stroke()
    }
    if (sys.has_enemy_fleet) {
      ctx.strokeStyle = '#ee4444'
      ctx.lineWidth = 1
      ctx.setLineDash([2, 2])
      ctx.beginPath()
      ctx.arc(p.x, p.y, radius + 5, 0, Math.PI * 2)
      ctx.stroke()
      ctx.setLineDash([])
    }

    // Name label
    if (explored && sys.name) {
      ctx.fillStyle = sys.has_player_colony ? '#88ff88' : '#aaaacc'
      ctx.font = '11px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(sys.name, p.x, p.y + radius + 14)
    } else if (sys.name) {
      ctx.fillStyle = '#556677'
      ctx.font = '10px monospace'
      ctx.textAlign = 'center'
      ctx.fillText('???', p.x, p.y + radius + 14)
    }
  })

  // Player fleets — anchored to their parked star system
  playerFleets.forEach((fleet: any) => {
    const sys = systems.find((s: any) => s.id === fleet.star_system_id)
    if (!sys) return
    const p = project(sys.position || { x: 0, y: 0 })
    ctx.fillStyle = '#67f0ff'
    ctx.fillRect(p.x + 8, p.y - 8, 4, 4)
  })
}

function getStarColor(type: string) {
  switch (type) {
    case 'red':
      return '#ff6666'
    case 'orange':
      return '#ffaa44'
    case 'yellow':
      return '#ffeb66'
    case 'white':
      return '#ffffff'
    case 'blue':
      return '#88aaff'
    case 'black_hole':
      return '#220033'
    default:
      return '#cccccc'
  }
}
