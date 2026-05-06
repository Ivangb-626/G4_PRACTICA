export function renderTacticalCombat(
    ctx: CanvasRenderingContext2D,
    state: any,
    width: number,
    height: number
) {
    ctx.clearRect(0, 0, width, height);
    
    // Grid background
    ctx.strokeStyle = '#1a1a3e';
    ctx.lineWidth = 1;
    const gridSize = 50;
    
    for (let x = 0; x <= width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    for (let y = 0; y <= height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Ships (Placeholders)
    if (state.ships) {
        state.ships.forEach((ship: any) => {
            ctx.fillStyle = ship.owner === 'player' ? '#44ee44' : '#ee4444';
            ctx.beginPath();
            ctx.arc(ship.x * gridSize + gridSize/2, ship.y * gridSize + gridSize/2, 10, 0, Math.PI * 2);
            ctx.fill();
        });
    }
}
