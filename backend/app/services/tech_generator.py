import random

def generate_available_techs(all_techs):
    """
    Availability Engine: ~50% random generation probability.
    Ensures that a balanced tech tree is available.
    """
    available = {"fields": []}
    for field in all_techs.get("fields", []):
        new_field = {"field": field["field"], "levels": []}
        for level in field.get("levels", []):
            # 50% probability check per technology option
            filtered_options = [opt for opt in level.get("options", []) if random.random() < 0.5]
            
            # Ensure at least one option if level has tech, to prevent dead ends
            if not filtered_options and level.get("options", []):
                filtered_options = [random.choice(level["options"])]
            
            if filtered_options:
                new_field["levels"].append({
                    "level": level["level"],
                    "options": filtered_options
                })
        available["fields"].append(new_field)
    return available
