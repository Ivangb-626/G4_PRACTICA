from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Enviar prompt y recibir respuesta como texto."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Nombre del proveedor para logging."""
        ...
