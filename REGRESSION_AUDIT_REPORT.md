# Informe de Auditoría de Regresión - MasterDeHostias

**Fecha:** 2026-05-08  
**Estado:** Finalizado  
**QA Lead:** Antigravity (Advanced Agentic Coding Division)

## 1. Resumen Ejecutivo
Se ha realizado un ciclo de pruebas de regresión completo sobre el build actual. Se confirma la corrección de fallos críticos históricos en el sistema de flotas y espionaje, pero se ha detectado una **regresión crítica en la inteligencia artificial** que impide el progreso de los imperios rivales.

---

## 2. Regresiones y Fixes Validados

| Sistema | Descripción del Cambio | Resultado del Test | Estado |
| :--- | :--- | :--- | :--- |
| **Gestión de Flotas** | Corrección del bug de borrado/fusión tras combate. | Las flotas individuales ahora sobreviven proporcionalmente al daño. | ✅ Corregido |
| **IA (Economía)** | Asignación de población a roles (farmers/workers/scis). | La IA asigna 100% a Comida, ignorando Industria y Ciencia. | ❌ REGRESIÓN |
| **Espionaje** | Metadatos de tecnologías robadas. | Las techs robadas ahora heredan correctamente su campo y nivel. | ✅ Corregido |
| **Persistencia** | Guardado y carga de estado complejo. | No se detectaron desincronizaciones tras el Load Game. | ✅ Estable |

---

## 3. Hallazgos Detallados

### 3.1. IA Inoperante (Gravedad: Crítica)
- **Causa Probable:** Bug en `ai-service/ai/strategic.py` donde el acceso a los datos de la colonia falla, provocando que la IA no vea a sus trabajadores y los asigne por defecto a agricultura.
- **Impacto:** Las IAs no investigan ni construyen naves, resultando en una galaxia estática.
- **Evidencia (DB Query):** `ai_0 colony pop: {"total":8,"farmers":8,"workers":0,"scientists":0}`.

### 3.2. Economía y Balance (Gravedad: Media)
- **Starvation:** La pérdida de población es instantánea si el excedente de comida es `< 0`. Se recomienda un buffer o aviso previo.
- **Production Overflow:** El exceso de producción en la cola de construcción se pierde. Si un edificio cuesta 50 y produces 100, se desperdician 50 PP.

### 3.3. Interfaz y UX (Gravedad: Baja)
- **Panel de Trucos:** Sigue visible en el Dashboard de Tester, permitiendo saltar el balance del juego fácilmente.
- **Tooltips:** Faltan descripciones en algunos edificios de late-game en la vista de colonia.

---

## 4. Pruebas de Estabilidad (Stress Testing)
- **Navegación Rápida:** OK. Sin crashes al cambiar entre el mapa galáctico y la vista de tecnología repetidamente.
- **Spam de Turnos:** OK. El motor procesa los turnos en serie sin corromper el estado, aunque con una latencia de ~2s debido a llamadas a la API de IA.
- **Carga de Assets:** OK. Todos los iconos y retratos de líderes cargan correctamente.

---

## 5. Próximos Pasos Recomendados
1. **Urgente:** Corregir el mapeo de población en el servicio de IA para restaurar la competitividad.
2. **Mejora:** Implementar el acarreo (*overflow*) de producción en la cola de construcción.
3. **Seguridad:** Ocultar el panel de Tester en builds de producción.

---
*Este informe ha sido generado tras una sesión de exploratory testing agresivo.*
