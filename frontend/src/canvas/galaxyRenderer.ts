export function renderGalaxy(
  ctx: CanvasRenderingContext2D,
  galaxy: any,
  width: number,
  height: number,
  selectedStarIndex: number | null,
  playerFleets: any[],
  zoom: number,
  panX: number,
  panY: number
) {
  ctx.clearRect(0, 0, width, height);

  // 1. Deep-space background
  const grad = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, Math.max(width, height));
  grad.addColorStop(0, '#0a0a2e');
  grad.addColorStop(1, '#000000');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  ctx.save();
  ctx.translate(width / 2 + panX, height / 2 + panY);
  ctx.scale(zoom, zoom);

  // 2. Stars (FOW filtering should happen before calling this or inside)
  const stars = galaxy?.stars || [];
  stars.forEach((star: any) => {
    const isExplored = star.explored_by?.includes('player') || star.explored === true;
    
    // Draw star circle
    ctx.beginPath();
    ctx.arc(star.x, star.y, isExplored ? 4 : 2, 0, Math.PI * 2);
    ctx.fillStyle = getStarColor(star.type);
    ctx.fill();

    // Draw selection ring
    if (star.index === selectedStarIndex) {
      ctx.strokeStyle = '#00ffff';
      ctx.lineWidth = 1 / zoom;
      ctx.beginPath();
      ctx.arc(star.x, star.y, 8, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Draw name label if explored
    if (isExplored) {
      ctx.fillStyle = star.owner === 'player' ? '#44ee44' : (star.owner ? '#ee4444' : '#aaaacc');
      ctx.font = `${10 / zoom}px monospace`;
      ctx.textAlign = 'center';
      ctx.fillText(star.name, star.x, star.y + 12);
    }
  });

  // 3. Fleets
  playerFleets.forEach((fleet: any) => {
    // Draw fleet icon
    ctx.fillStyle = '#44ee44';
    ctx.fillRect(fleet.x - 2, fleet.y - 2, 4, 4);
  });

  ctx.restore();
}

function getStarColor(type: string) {
  switch (type) {
    case 'red': return '#ff4444';
    case 'orange': return '#ffaa44';
    case 'yellow': return '#ffff44';
    case 'white': return '#ffffff';
    case 'blue': return '#4444ff';
    default: return '#ffffff';
  }
}
