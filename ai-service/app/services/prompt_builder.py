import json
import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def build_system_prompt(personality: str, difficulty: str) -> str:
    system_prompt_path = PROMPTS_DIR / "system_prompt.txt"
    personality_path = PROMPTS_DIR / "personality" / f"{personality}.txt"
    
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_text = f.read()
        
    personality_text = ""
    if personality_path.exists():
        with open(personality_path, "r", encoding="utf-8") as f:
            personality_text = f.read()
            
    difficulty_text = f"You are playing on {difficulty} difficulty."
    
    return f"{system_text}\n\n{personality_text}\n\n{difficulty_text}"

def build_user_prompt(visible_state: dict, available_actions: dict) -> str:
    turn = visible_state.get('turn', 0)
    
    # Safe retrieval in case keys are missing
    ai_colonies = visible_state.get('ai_player', {}).get('colonies', [])
    ai_colonies_list = list(ai_colonies.keys()) if isinstance(ai_colonies, dict) else list(ai_colonies)

    return f"""
Here is the current game state (turn {turn}):

<game_state>
{json.dumps(visible_state, indent=2)}
</game_state>

Available actions this turn:
- Colonies you can manage: {ai_colonies_list}
- Technologies available for research: {json.dumps(available_actions.get('can_research', []))}
- Planets you can colonize: {json.dumps(available_actions.get('can_colonize', []))}
- Buildings available per colony: {json.dumps(available_actions.get('available_buildings', {}))}
- Ships you can build per colony: {json.dumps(available_actions.get('available_ships', {}))}

Analyze the game state, formulate your strategy, and provide your actions as valid JSON.
Remember to always end with an "endTurn" action.
"""
