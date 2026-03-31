import json

FALLBACK_STAR_NAMES = [
    "Sol", "Alpha Centauri", "Proxima", "Sirius", "Vega",
    "Arcturos", "Betelgeuse", "Rigel", "Aldebaran", "Antares",
    "Polaris", "Deneb", "Altair", "Capella", "Procyon",
    "Spica", "Regulus", "Canopus", "Mira", "Bellatrix",
    "Fomalhaut", "Achernar", "Hadar", "Mintaka", "Alnilam",
    "Saiph", "Castor", "Pollux", "Mizar", "Alkaid"
]

class ContentGenerator:
    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def generate_star_names(self, count: int) -> list[str]:
        system_prompt = "You are a creative sci-fi data generator."
        user_prompt = f"Generate {count} unique sci-fi star system names. Return strictly a JSON array of strings."
        
        try:
            # We assume AI service has an accessible call_with_fallback, or we just use groq directly
            raw_response = await self.ai_service.call_with_fallback(system_prompt, user_prompt)
            data = json.loads(raw_response)
            if isinstance(data, list) and len(data) >= count:
                return data[:count]
            elif isinstance(data, dict) and "names" in data:
                return data["names"][:count]
        except Exception:
            pass
            
        # Fallback
        return FALLBACK_STAR_NAMES[:count]

    async def generate_planet_names(self, star_name: str, count: int) -> list[str]:
        system_prompt = "You are a creative sci-fi data generator."
        user_prompt = f"Generate {count} unique planet names for the star system '{star_name}'. Include numerals like I, Prime, Secundus if appropriate. Return strictly a JSON array of strings."
        
        try:
            raw_response = await self.ai_service.call_with_fallback(system_prompt, user_prompt)
            data = json.loads(raw_response)
            if isinstance(data, list) and len(data) >= count:
                return data[:count]
            elif isinstance(data, dict) and "names" in data:
                return data["names"][:count]
        except Exception:
            pass

        return [f"{star_name} {self._roman(i+1)}" for i in range(count)]
        
    def _roman(self, num: int) -> str:
        roman_numerals = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'}
        return roman_numerals.get(num, str(num))
