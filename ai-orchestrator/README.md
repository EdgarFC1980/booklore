# Booklore AI Orchestrator (MVP)

Servicio externo a Booklore que permite ordenar y etiquetar la biblioteca
mediante instrucciones en lenguaje natural.

## Endpoints
- POST /api/chat -> genera un plan (no aplica cambios)
- POST /api/plan/apply -> aplica el plan en Booklore
- GET /health -> healthcheck

Este es un MVP deliberadamente conservador.
