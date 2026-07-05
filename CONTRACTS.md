# Contrato de comunicación — Real-Time Polls API

Este documento define el formato de datos que viaja entre la API REST, 
Redis y el WebSocket. Yadira y Crystal deben seguir este formato exacto 
para que sus partes se integren sin fricción.

## 1. Mensaje publicado en Redis (por la API REST, tras guardar un voto)

**Canal:** `survey:{survey_id}` (ejemplo: `survey:42`)

```json
{
  "event": "results_updated",
  "survey_id": 42,
  "timestamp": "2026-07-05T00:42:10Z",
  "results": {
    "total_responses": 128,
    "questions": [
      {
        "question_id": 1,
        "text": "How would you rate technical support?",
        "options": [
          { "option_id": 1, "text": "Excellent", "votes": 52 },
          { "option_id": 2, "text": "Good", "votes": 41 },
          { "option_id": 3, "text": "Fair", "votes": 20 },
          { "option_id": 4, "text": "Poor", "votes": 15 }
        ]
      }
    ]
  }
}
```

## 2. Mensaje reenviado por WebSocket a los clientes

Mismo formato, sin transformación. Crystal recibe esto desde Redis y lo 
reenvía tal cual a todos los clientes conectados en `WS /ws/surveys/{id}`.

## 3. Mensajes de control (conexión/errores)

```json
{ "event": "connected", "survey_id": 42 }
```
```json
{ "event": "error", "message": "Survey not found" }
```

## Responsabilidades

- **Yadira**: calcula los resultados agregados y publica en Redis con este formato exacto, después de guardar cada voto en PostgreSQL.
- **Crystal**: se suscribe al canal Redis correspondiente y reenvía el mensaje sin modificarlo a los clientes WebSocket conectados a esa encuesta.

## Formato de payload para crear encuestas

Ver ejemplo completo en el issue de Yadira (API REST y modelos de BD).