# 17 — Modos de dificultad

## Lo que ya está implementado

- 3 niveles de dificultad: `["easy", "normal", "hard"]` en escenarios.
- Campo `difficulty` en game_state.
- **Sin** modificadores de IA aplicados en ningún servicio.

## Cambios necesarios

### Renombrar / extender niveles
- [ ] Reemplazar `easy/normal/hard` por los 5 oficiales: `gardener`, `officer`, `commander`, `lord`, `impossible`.
- [ ] Mantener compatibilidad con saves antiguos: si `difficulty == "easy"` interpretar como `gardener`, etc.

### Tabla de modificadores
Crear [backend/app/data/difficulty.json](../backend/app/data/difficulty.json):
```json
{
  "gardener": {
    "ai_production_mult": 0.75,
    "ai_research_mult": 0.75,
    "ai_combat_mult": 0.85,
    "ai_starting_bc": 50,
    "ai_aggression": 0.3,
    "antaran_strength_mult": 0.7
  },
  "officer": {
    "ai_production_mult": 1.0,
    "ai_research_mult": 1.0,
    "ai_combat_mult": 1.0,
    "ai_starting_bc": 100,
    "ai_aggression": 0.5,
    "antaran_strength_mult": 1.0
  },
  "commander": {
    "ai_production_mult": 1.15,
    "ai_research_mult": 1.15,
    "ai_combat_mult": 1.05,
    "ai_starting_bc": 150,
    "ai_aggression": 0.65,
    "antaran_strength_mult": 1.15
  },
  "lord": {
    "ai_production_mult": 1.30,
    "ai_research_mult": 1.30,
    "ai_combat_mult": 1.10,
    "ai_starting_bc": 250,
    "ai_starting_techs": 3,
    "ai_aggression": 0.80,
    "antaran_strength_mult": 1.30
  },
  "impossible": {
    "ai_production_mult": 1.50,
    "ai_research_mult": 1.50,
    "ai_combat_mult": 1.20,
    "ai_starting_bc": 500,
    "ai_starting_techs": 6,
    "ai_starting_extra_colony": true,
    "ai_aggression": 1.0,
    "antaran_strength_mult": 1.50
  }
}
```

### Aplicación
- [ ] Al generar el estado del juego, aplicar `ai_starting_bc` y `ai_starting_techs` a cada IA.
- [ ] En `lord`/`impossible`, dar a la IA una colonia adicional (planeta cercano ya colonizado al inicio).
- [ ] [colony_service.py](../backend/app/services/colony_service.py) → al calcular producción de un imperio IA, multiplicar por `ai_production_mult`.
- [ ] [research_service.py](../backend/app/services/research_service.py) → similar con `ai_research_mult`.
- [ ] [tactical_combat.py](../backend/app/services/tactical_combat.py) → multiplicar attack/defense de naves IA por `ai_combat_mult`.
- [ ] [ai_service.py](../backend/app/services/ai_service.py) → `ai_aggression` controla la frecuencia de declaraciones de guerra y la prioridad de construcción militar.
- [ ] [antaran_service.py](../backend/app/services/antaran_service.py) → escalar la flota Antarana por `antaran_strength_mult`.

### Frontend
- [ ] Selector con los 5 niveles en el formulario de creación de partida con descripción de cada uno.
- [ ] Indicador del nivel de dificultad en la pantalla de imperio (visible siempre).
- [ ] Aviso al jugador en niveles altos: "La IA está jugando en modo Lord/Impossible y recibe bonificaciones."
