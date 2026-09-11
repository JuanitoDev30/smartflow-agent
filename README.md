# Asistente de pedidos

Agente conversacional que responde dudas, arma pedidos y da seguimiento a los mismos.
Integrado al software administrativo SmartFlow.

# Arquitectura

Puertos y adaptadores. Cuatro capas, con dependencias siempre hacia adentro

**El modelo es intercambiable** El agente habla contra `LLMProvider`
(`app/llm/base.py`) usando tipos neutros
(`anthropic_provider.py`) y cualquier endpoint compatible con OpenAi
(`openai_compatible.py`) que cubre NVIDIA NIM, vLLM, Ollama, Groq
Cambiar de proveedor son dos variables de entorno. Los tests corren con un proveedor guionado, sin llamar a ninguna api

## Correr

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

```

Conversar con el agente desde la terminal:

```bash

```

Conversaciones de prueba guionadas:

```bash

```

Levantar la API:

```bash

```
