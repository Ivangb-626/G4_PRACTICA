import json
from pathlib import Path

# Load tech data
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
with (DATA_DIR / "tech_tree.json").open("r", encoding="utf-8") as f:
    TECHS = json.load(f)

class ResearchService:
    @staticmethod
    def calculate_rp_production(colony, player_state):
        scientists = colony.get("scientists", 0)
        bonus = player_state.get("research_bonus", 1.0)
        return scientists * bonus

    @staticmethod
    def apply_miniaturization_bonus(base_value, level):
        """Miniaturization: -5% per level, min 30%."""
        reduction = 1 - (level * 0.05)
        return base_value * max(reduction, 0.3)

    @staticmethod
    def apply_tech_effect(player_state, tech):
        """Applies building unlocks, weapon mods, and global bonuses."""
        effects = tech.get("effects", [])
        for effect in effects:
            if effect["type"] == "building_unlock":
                player_state["unlocked_buildings"].append(effect["target"])
            elif effect["type"] == "achievement":
                player_state["achievements"].append(effect["target"])
                # Handle specific achievement bonuses (e.g., +RP)
                if effect["target"] == "heightened_intelligence":
                    player_state["research_bonus"] += 0.2
        return True

    @staticmethod
    def process_research(player_state, rp_generated):
        if not player_state.get("current_research"):
            return None
        player_state["research_accumulated"] += rp_generated
        tech = _find_tech(player_state["current_research"])
        if not tech: return None
        
        chance = _get_breakthrough_chance(player_state["research_accumulated"], tech["base_cost"])
        if chance >= 100 or (chance > 0 and random.random() < (chance / 100)):
            return _complete_tech(player_state, tech)
        return {"status": "in_progress", "chance": chance}

def _find_tech(tech_id):
    for field in TECHS.get("fields", []):
        for level in field.get("levels", []):
            for opt in level.get("options", []):
                if opt.get("tech_id") == tech_id:
                    return opt
    return None

def _get_breakthrough_chance(accumulated_rp, base_cost):
    if accumulated_rp < base_cost: return 0
    progress = accumulated_rp - base_cost
    return min((progress / base_cost) * 100, 100)

def _complete_tech(player_state, tech):
    player_state["researched"].append(tech["tech_id"])
    player_state["research_accumulated"] = 0
    player_state["current_research"] = None
    ResearchService.apply_tech_effect(player_state, tech)
    return {"status": "completed", "tech": tech["tech_id"]}
