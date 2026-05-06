# 15 — Condiciones de victoria

## Lo que ya está implementado

- `check_victory()` en [game_service.py](../backend/app/services/game_service.py):
  - Militar: si AI colonias + flotas == 0 → "Conquest".
  - Antarana: si `antaran_homeworld_conquered` → "Antaran".
  - Diplomática: placeholder (verifica un flag pero no hay sistema de votación).
  - Defeat: si player colonias + flotas == 0.
- [council_service.py](../backend/app/services/council_service.py) **vacío**.

## Cambios necesarios

### Victoria Militar
- [ ] Verificar que `check_victory()` excluye al propio jugador y a los Antaranos del recuento (los Antaranos no son un imperio "rival" elegible para extermino — sin colonias en el mapa común).
- [ ] La **rendición** de un rival también cuenta como eliminación si todas sus colonias quedan en propiedad del vencedor.
- [ ] Si solo queda un humano y todos los demás están en alianzas con él, no debería ganar automáticamente.

### Senado Galáctico
Implementar [council_service.py](../backend/app/services/council_service.py):
- [ ] **Convocatoria**: el Senado se convoca automáticamente cada 25 turnos cuando hay al menos **3 imperios contactados**.
- [ ] **Cálculo de votos**:
  - Cada imperio tiene votos = `total_population` (suma de población de todas sus colonias).
  - Total de votos = suma de todos los imperios + 1 voto bonus por imperio que ha completado un proyecto especial (e.g. United Planets HQ).
- [ ] **Candidatos**: los 2 imperios con más votos son los candidatos. Cada otro imperio puede votar por uno o **abstenerse** (las abstenciones equivalen a votos negativos para AMBOS candidatos).
- [ ] **Necesario**: 2/3 de los votos para ser elegido Gobernante Supremo.
- [ ] **Resultado**:
  - Si ningún candidato consigue 2/3, no hay vencedor; se reconvoca en 25 turnos.
  - Si un candidato consigue 2/3 de los votos:
    - Es ofrecida la victoria diplomática.
    - Los imperios que **votaron en su contra** pueden rechazar el resultado y declarar guerra automática (lo que continúa la partida en modo "rebelión", pero el Gobernante Supremo gana si los rebeldes son eliminados o aceptan).
- [ ] **Voto del jugador humano**: pantalla modal con candidatos y opciones: votar A / votar B / abstenerse.
- [ ] **Voto de IA**: basado en relación con cada candidato y rasgos raciales.

### Conquista de Antara
- [ ] Cubierto en [14_antaranos.md](14_antaranos.md). Confirmar que `check_victory()` reconoce `antaran_homeworld_conquered == true` solo si el flag de Antaran Attacks estaba activo.

### Rendición / surrender
- [ ] La IA puede ofrecer rendición cuando su poder relativo es muy inferior. Endpoint `POST /api/diplomacy/{empire_id}/surrender_offer`.
- [ ] El humano que se rinde pierde la partida.

### Pantalla de victoria
- [ ] [VictoryScreen.vue](../frontend/src/views/VictoryScreen.vue) ya existe; ampliar para distinguir las 3 condiciones con narrativa diferente:
  - Militar: "Eliminated all rival civilizations through superior firepower."
  - Senado: "Elected Supreme Ruler of the Galaxy with X% of the vote."
  - Antara: "Defeated the Antarans on their home turf and saved the galaxy."
- [ ] Mostrar el desglose de puntuación final (ver [16_puntuacion.md](16_puntuacion.md)).
- [ ] Botones: "Continuar jugando" (post-victoria) / "Volver al menú".

### Continuar jugando
- [ ] Tras victoria, permitir seguir hasta el turno 500 para maximizar el score.
- [ ] El estado pasa a `victory_already_achieved = true` para no re-disparar la condición.

### Frontend
- [ ] Notificación al convocarse el Senado.
- [ ] Modal de votación con tabla de candidatos, votos disponibles, opciones.
- [ ] Indicador en HUD del próximo Senado.
