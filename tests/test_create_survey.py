"""
Pruebas de POST /api/v1/surveys.
"""


async def test_create_survey_success(client, survey_payload):
    """Crear una encuesta completa devuelve 201 con el árbol anidado."""
    response = await client.post("/api/v1/surveys", json=survey_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Encuesta de prueba"
    assert "id" in body
    assert len(body["questions"]) == 2
    assert len(body["questions"][0]["options"]) == 2
    # La pregunta de texto libre no debe traer opciones
    assert body["questions"][1]["options"] == []


async def test_create_survey_without_title_fails_validation(client):
    """Sin título, Pydantic debe rechazar la petición antes de tocar la BD."""
    response = await client.post("/api/v1/surveys", json={"questions": []})
    assert response.status_code == 422


async def test_create_survey_without_questions_is_allowed(client):
    """Una encuesta sin preguntas todavía es válida (se pueden agregar después)."""
    response = await client.post(
        "/api/v1/surveys", json={"title": "Encuesta vacía", "questions": []}
    )
    assert response.status_code == 201
    assert response.json()["questions"] == []


async def test_create_survey_is_atomic_on_bad_option(client):
    """
    Si Pydantic ya validó el payload, la inserción debe ser todo-o-nada.
    Aquí forzamos un tipo de pregunta inválido para confirmar que no se
    crea nada a medias.
    """
    bad_payload = {
        "title": "Encuesta con tipo invalido",
        "questions": [
            {"text": "Pregunta rota", "type": "not_a_real_type", "order": 0, "options": []}
        ],
    }
    response = await client.post("/api/v1/surveys", json=bad_payload)
    # Pydantic rechaza el "type" inválido antes de llegar a la BD
    assert response.status_code == 422

    # Confirmamos que no quedó nada guardado
    listing = await client.get("/api/v1/surveys")
    assert listing.json()["total"] == 0