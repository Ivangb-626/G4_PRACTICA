import random
import math
import time
from datetime import datetime
from app.services.game_service import find_system, get_empire, find_fleet, SHIP_TYPES, BUILDINGS

def _get_planet_and_colony(game_state, planet_id):
    """Auxiliary to find planet and its colony across all star systems."""
    for system in game_state.get("galaxy", {}).get("star_systems", []):
        for planet in system.get("planets", []):
            if planet.get("name") == planet_id or planet.get("id") == planet_id:
                # Find colony if it exists
                colony = None
                for empire_id in ["player"] + [ai["id"] for ai in game_state.get("ai_players", [])]:
                    empire = get_empire(game_state, empire_id)
                    colony = next((c for c in empire.get("colonies", []) if c.get("star_system_id") == system["id"] and c.get("planet_index") == planet.get("index")), None)
                    if colony:
                        break
                return system, planet, colony
    return None, None, None

def _get_tech_modifier(empire, field):
    """Calculates tech multiplier: 100 + (max_level * 10) / 100."""
    if not empire:
        return 1.0
    researched = empire.get("technologies", {}).get("researched", [])
    max_level = 0
    for t in researched:
        if t.get("field") == field:
            max_level = max(max_level, t.get("level", 0))
    return (100 + max_level * 10) / 100.0

def verificar_capacidad_ataque(game_state, id_planeta, id_flota_atacante, id_imperio_atacante):
    system, planet, colony = _get_planet_and_colony(game_state, id_planeta)
    
    # 1. ¿Existe el planeta?
    if not planet:
        return {"error": "Planeta no encontrado", "codigo": 404}
    
    # 2. ¿Pertenece a otro imperio?
    if not colony or colony.get("owner") == id_imperio_atacante:
        return {"error": "Planeta ya conquistado o no colonizado", "codigo": 400}
    
    # 3. ¿La flota existe y está en órbita?
    flota = find_fleet(game_state, id_flota_atacante)
    if not flota or flota.get("star_system_id") != system["id"]:
        return {"error": "Flota no disponible", "codigo": 400}
    
    # 4. ¿La flota tiene suficientes naves de combate? (min 5)
    total_combat_ships = sum(s.get("count", 0) for s in flota.get("ships", []) if SHIP_TYPES.get(s["type"], {}).get("category") == "warship")
    if total_combat_ships < 5:
        return {"error": "Fuerzas insuficientes", "codigo": 400}
    
    # 5. ¿El planeta está bajo asedio ya? (Simulated by checking combat log or state)
    if colony.get("in_combat"):
        return {"error": "Planeta en combate", "codigo": 409}

    # CÁLCULOS
    empire_atacante = get_empire(game_state, id_imperio_atacante)
    tech_weapons = _get_tech_modifier(empire_atacante, "physics") * 100 # Scaling to match formula (usually 100-180)
    
    poder_fuego = 0
    for s in flota.get("ships", []):
        st = SHIP_TYPES.get(s["type"], {})
        if st.get("category") == "warship":
            poder_fuego += (s.get("count", 0) * st.get("attack", 0) * tech_weapons) / 100

    enemy_empire = get_empire(game_state, colony.get("owner"))
    tech_defensa_rival = _get_tech_modifier(enemy_empire, "force_fields") * 100
    
    bases_estelares = 0
    defensa_superficie = 0
    for b_id in colony.get("buildings", []):
        bid = b_id if isinstance(b_id, str) else b_id.get("id")
        b_data = BUILDINGS.get(bid, {})
        if bid in ["star_base", "battlestation", "star_fortress"]:
            bases_estelares += 1
        if b_data.get("effects", {}).get("orbital_defense", 0) > 0:
            defensa_superficie += b_data["effects"]["orbital_defense"]

    defensa_planeta = (bases_estelares * 50 + defensa_superficie * 25 / 25) # simplified to match logic: surface defense as items
    # Adjusting formula to: (bases * 50 + surface_count * 25) * (tech / 100)
    # surface_count is not clearly defined in prompt, assuming 1 per defense building
    surface_count = sum(1 for b_id in colony.get("buildings", []) if BUILDINGS.get(b_id if isinstance(b_id, str) else b_id.get("id"), {}).get("effects", {}).get("orbital_defense", 0) > 0)
    defensa_planeta = (bases_estelares * 50 + surface_count * 25) * (tech_defensa_rival / 100)

    posibilidad_exito = (poder_fuego / (poder_fuego + defensa_planeta)) * 100 if (poder_fuego + defensa_planeta) > 0 else 100
    
    riesgo = "BAJO"
    if posibilidad_exito < 40: riesgo = "ALTO"
    elif posibilidad_exito < 70: riesgo = "MODERADO"

    return {
        "valido": True,
        "posibilidad_exito": round(posibilidad_exito, 2),
        "riesgo": riesgo,
        "poder_fuego": round(poder_fuego, 2),
        "defensa_enemiga": round(defensa_planeta, 2),
        "poblacion_planeta": colony.get("population", {}).get("total", 0),
        "tech_enemiga": "Advanced" if tech_defensa_rival > 130 else "Standard",
        "recomendacion": "Atacar - chances favorables" if posibilidad_exito > 60 else "Riesgoso - proceder con cautela"
    }

def bombardear_planeta(game_state, id_planeta, id_flota, intensidad_bombardeo="moderado"):
    system, planet, colony = _get_planet_and_colony(game_state, id_planeta)
    flota = find_fleet(game_state, id_flota)
    
    if not colony or not flota:
        return {"exito": False, "mensaje": "Datos invalidos para bombardeo"}

    # PASO 1 - Generar resultado aleatorio
    numero_aleatorio = random.random() * 100
    
    # Cargar defensa para combate (reutilizando lógica de verificar)
    enemy_empire = get_empire(game_state, colony.get("owner"))
    tech_defensa_rival = _get_tech_modifier(enemy_empire, "force_fields") * 100
    bases_estelares_count = sum(1 for b in colony.get("buildings", []) if (b if isinstance(b, str) else b.get("id")) in ["star_base", "battlestation", "star_fortress"])
    surface_count = sum(1 for b in colony.get("buildings", []) if BUILDINGS.get(b if isinstance(b, str) else b.get("id"), {}).get("effects", {}).get("orbital_defense", 0) > 0)
    defensa_planeta = (bases_estelares_count * 50 + surface_count * 25) * (tech_defensa_rival / 100)

    # PASO 2 - Simular combate orbital
    daño_base = 50
    if intensidad_bombardeo == "devastador": daño_base = 75
    elif intensidad_bombardeo == "ligero": daño_base = 25
    
    resultado_combate = numero_aleatorio - (defensa_planeta / 2)
    
    # PASO 3 - Aplicar resultados
    if resultado_combate > 0:
        poblacion_anterior = colony.get("population", {}).get("total", 1)
        pop_lost = int(poblacion_anterior * (daño_base / 100.0))
        colony["population"]["total"] = max(1, poblacion_anterior - pop_lost)
        
        # Ground defense reduction (simulated via buildings or custom field)
        if "ground_defense" in colony:
            colony["ground_defense"] = int(colony["ground_defense"] * (1 - daño_base / 100.0))
        
        # Bases dañadas (removed from buildings list)
        bases_danadas = math.floor(numero_aleatorio / 20)
        removed_count = 0
        new_buildings = []
        for b in colony.get("buildings", []):
            bid = b if isinstance(b, str) else b.get("id")
            if bid in ["star_base", "battlestation", "star_fortress"] and removed_count < bases_danadas:
                removed_count += 1
                continue
            new_buildings.append(b)
        colony["buildings"] = new_buildings
        
        # Pérdida de naves atacantes
        if not flota.get("invincible"):
            naves_perdidas = math.floor(numero_aleatorio / 30)
            total_lost = 0
            for s in flota.get("ships", []):
                if SHIP_TYPES.get(s["type"], {}).get("category") == "warship":
                    lost = min(s["count"], naves_perdidas - total_lost)
                    s["count"] -= lost
                    total_lost += lost
                if total_lost >= naves_perdidas: break
            flota["ships"] = [s for s in flota["ships"] if s["count"] > 0]
        else:
            total_lost = 0

        return {
            "exito": True,
            "poblacion_anterior": poblacion_anterior,
            "poblacion_nueva": colony["population"]["total"],
            "defensa_anterior": round(defensa_planeta, 2),
            "defensa_nueva": round(defensa_planeta * (1 - daño_base / 100.0), 2),
            "bases_dañadas": removed_count,
            "naves_perdidas": total_lost,
            "mensaje": f"Bombardeo {intensidad_bombardeo} - planeta debilitado"
        }
    else:
        # BOMBARDEO FALLA
        if not flota.get("invincible"):
            naves_perdidas = math.floor(numero_aleatorio / 15)
            total_lost = 0
            for s in flota.get("ships", []):
                if SHIP_TYPES.get(s["type"], {}).get("category") == "warship":
                    lost = min(s["count"], naves_perdidas - total_lost)
                    s["count"] -= lost
                    total_lost += lost
                if total_lost >= naves_perdidas: break
            flota["ships"] = [s for s in flota["ships"] if s["count"] > 0]
        else:
            total_lost = 0
        # Retirada: En esta implementación simplificada, el fracaso implica no hacer daño.
        
        return {
            "exito": False,
            "poblacion": colony.get("population", {}).get("total", 0),
            "defensa": round(defensa_planeta, 2),
            "naves_perdidas": total_lost,
            "mensaje": "Defensa planetaria repelió el ataque"
        }


def conquistar_planeta(game_state, id_planeta, id_imperio_conquistador, id_flota):
    system, planet, colony = _get_planet_and_colony(game_state, id_planeta)
    flota = find_fleet(game_state, id_flota)
    
    if not colony or not flota:
        return {"exito": False, "razon": "Datos invalidos"}

    # Recalcular defensa y poder para precondiciones
    capacidad = verificar_capacidad_ataque(game_state, id_planeta, id_flota, id_imperio_conquistador)
    if not capacidad.get("valido"):
        # If not valid because already owned, check if it's ours
        if capacidad.get("error") == "Planeta ya conquistado o no colonizado":
             emp = get_empire(game_state, id_imperio_conquistador)
             if any(c["id"] == colony["id"] for c in emp.get("colonies", [])):
                 return {"exito": True, "mensaje": "Ya es tuyo"}
        return {"exito": False, "razon": capacidad.get("error")}

    defensa_actual = capacidad["defensa_enemiga"]
    poder_fuego = capacidad["poder_fuego"]
    poblacion_actual = colony.get("population", {}).get("total", 0)

    # PRECONDICIONES
    if defensa_actual < 50 and defensa_actual < poder_fuego and poblacion_actual > 0:
        old_owner_id = colony["owner"]
        old_owner = get_empire(game_state, old_owner_id)
        new_owner = get_empire(game_state, id_imperio_conquistador)
        
        # Transferir propiedad
        old_owner["colonies"] = [c for c in old_owner.get("colonies", []) if c["id"] != colony["id"]]
        colony["owner"] = id_imperio_conquistador
        colony["original_owner"] = old_owner_id
        new_owner.setdefault("colonies", []).append(colony)
        
        # Población residual: 20%
        poblacion_anterior = poblacion_actual
        colony["population"]["total"] = max(1, int(poblacion_anterior * 0.2))
        colony["population"]["farmers"] = colony["population"]["total"]
        colony["population"]["workers"] = 0
        colony["population"]["scientists"] = 0
        
        # Defensa: 0
        colony["buildings"] = [b for b in colony["buildings"] if (b if isinstance(b, str) else b.get("id")) not in ["star_base", "battlestation", "star_fortress", "missile_base"]]
        colony["ground_defense"] = 0
        
        # Colonias nuevas (basic infrastructure instead of "3 colonies")
        # In MoO2, conquest maintains some buildings. Prompt says "generar 3 colonias básicas".
        # Assuming it means adding 3 basic buildings or specific slots. 
        # I'll add 3 basic functional buildings if not present.
        basics = ["automated_factory", "research_lab", "hydroponic_farm"]
        for b in basics:
            if b not in [ (bi if isinstance(bi, str) else bi.get("id")) for bi in colony["buildings"] ]:
                colony["buildings"].append(b)
        
        # Recursos iniciales (calculados por tamaño)
        size_mult = {"tiny": 1, "small": 2, "medium": 3, "large": 4, "huge": 5}.get(planet.get("size"), 3)
        recursos = {
            "BC": 500 * size_mult,
            "RA": 250 * size_mult,
            "industria": 50 * size_mult
        }
        new_owner["resources"]["bc"] = new_owner["resources"].get("bc", 0) + recursos["BC"]
        
        return {
            "exito": True,
            "planeta": planet["name"],
            "nuevo_propietario": id_imperio_conquistador,
            "poblacion_establecida": colony["population"]["total"],
            "colonias_creadas": 3,
            "recursos_iniciales": recursos,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    else:
        return {
            "exito": False,
            "razon": "Planeta aún demasiado defendido" if defensa_actual >= 50 else "Población insuficiente",
            "defensa_actual": round(defensa_actual, 2),
            "poder_fuego_necesario": 150 # Placeholder based on prompt
        }

def asaltar_planeta(game_state, id_planeta, id_imperio_atacante, id_flota):
    """Realiza un asalto terrestre (invasión) con marines."""
    system, planet, colony = _get_planet_and_colony(game_state, id_planeta)
    flota = find_fleet(game_state, id_flota)
    if not colony or not flota:
        return {"exito": False, "razon": "Datos invalidos"}

    # Calcular fuerza de marines
    marines_atacantes = sum(s.get("count", 0) * SHIP_TYPES.get(s["type"], {}).get("marine_capacity", 0) for s in flota.get("ships", []))
    if marines_atacantes <= 0:
        return {"exito": False, "razon": "No hay tropas de asalto (marines) en la flota"}

    # Calcular defensa terrestre (población + edificios de defensa)
    poblacion = colony.get("population", {}).get("total", 1)
    defensa_terrestre = poblacion + colony.get("ground_defense", 0)
    
    # Bonus tecnológicos
    emp_atk = get_empire(game_state, id_imperio_atacante)
    emp_def = get_empire(game_state, colony["owner"])
    bonus_atk = 1 + (_get_tech_modifier(emp_atk, "sociology") - 1) * 2
    bonus_def = 1 + (_get_tech_modifier(emp_def, "sociology") - 1) * 2
    
    prob_exito = (marines_atacantes * bonus_atk) / (marines_atacantes * bonus_atk + defensa_terrestre * bonus_def)
    
    if random.random() < prob_exito:
        # ÉXITO: Conquista inmediata
        res = conquistar_planeta(game_state, id_planeta, id_imperio_atacante, id_flota)
        res["mensaje_asalto"] = f"Asalto exitoso. Probabilidad era {round(prob_exito*100)}%"
        return res
    else:
        # FALLO: Pérdida de marines (reducir naves de transporte)
        for s in flota.get("ships", []):
            if SHIP_TYPES.get(s["type"], {}).get("type") == "transport":
                s["count"] = max(0, s["count"] - random.randint(1, 3))
        flota["ships"] = [s for s in flota["ships"] if s["count"] > 0]
        return {"exito": False, "razon": "Las fuerzas de defensa repelieron la invasion", "prob_fallida": round(prob_exito*100)}

def ejecutar_campaña_automatica(game_state, id_imperio_atacante, id_flota, lista_objetivos, intervalo_ejecucion=5):
    logs = []
    lista_objetivos.sort(key=lambda x: x.get("prioridad", 0), reverse=True)
    
    for obj in lista_objetivos:
        id_planeta = obj["id_planeta"]
        max_intentos = obj.get("max_intentos", 3)
        intentos = 0
        
        cap = verificar_capacidad_ataque(game_state, id_planeta, id_flota, id_imperio_atacante)
        if "error" in cap:
            logs.append({"planeta": id_planeta, "status": "Error", "detalle": cap["error"]})
            continue
            
        exito_campana = False
        while intentos < max_intentos and not exito_campana:
            intentos += 1
            prob = cap["posibilidad_exito"]
            
            if prob > 60:
                res_bomb = bombardear_planeta(game_state, id_planeta, id_flota, "devastador")
                time.sleep(0.1)
                
                if res_bomb["exito"]:
                    cap_after = verificar_capacidad_ataque(game_state, id_planeta, id_flota, id_imperio_atacante)
                    defensa_orbital = cap_after.get("defensa_enemiga", 100)
                    
                    if defensa_orbital < 50:
                        # Intentar asalto terrestre primero si hay marines
                        res_asalto = asaltar_planeta(game_state, id_planeta, id_imperio_atacante, id_flota)
                        if res_asalto["exito"]:
                            logs.append({"planeta": id_planeta, "status": "Conquistado (Asalto)", "detalle": res_asalto})
                            exito_campana = True
                        else:
                            # Si falla asalto, intentar conquista normal por rendicion
                            res_conq = conquistar_planeta(game_state, id_planeta, id_imperio_atacante, id_flota)
                            if res_conq["exito"]:
                                logs.append({"planeta": id_planeta, "status": "Conquistado (Rendicion)", "detalle": res_conq})
                                exito_campana = True
                            else:
                                logs.append({"planeta": id_planeta, "status": "Bombardeado", "detalle": "Asalto fallido y planeta no se rindio"})
                    else:
                        logs.append({"planeta": id_planeta, "status": "Bombardeado", "detalle": "Defensa reducida, reintentando"})
                else:
                    logs.append({"planeta": id_planeta, "status": "Fallo", "detalle": res_bomb["mensaje"]})
            
            elif prob > 40:
                bombardear_planeta(game_state, id_planeta, id_flota, "ligero")
                logs.append({"planeta": id_planeta, "status": "Ligero", "detalle": f"Intento {intentos} de {max_intentos}"})
                cap = verificar_capacidad_ataque(game_state, id_planeta, id_flota, id_imperio_atacante)
            
            else:
                logs.append({"planeta": id_planeta, "status": "Ignorado", "detalle": "Poco probable exito"})
                break
        
        time.sleep(0.1)

    return REPORTE_AUTOMATICO(logs)


def REPORTE_AUTOMATICO(logs):
    conquistados = [l for l in logs if l["status"] == "Conquistado"]
    fallidos = [l for l in logs if l["status"] in ["Fallo", "Error"]]
    ignorados = [l for l in logs if l["status"] == "Ignorado"]
    
    reporte = {
        "resumen": {
            "total_objetivos": len(logs),
            "conquistados": len(conquistados),
            "fallidos": len(fallidos),
            "ignorados": len(ignorados)
        },
        "detalles": logs,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    return reporte
