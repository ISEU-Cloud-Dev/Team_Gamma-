"""
Pruebas de GET /api/v1/surveys/{survey_id}.
"""


async def test_get_survey_by_id_success(client, survey_payload):
    """Consultar una encuesta existente por su id devuelve 200 con el detalle completo."""
    create_response = await client.post("/api/v1/surveys", json=survey_payload)
    survey_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/surveys/{survey_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == survey_id
    assert len(body["questions"]) == 2
    assert len(body["questions"][0]["options"]) == 2


async def test_get_survey_by_id_not_found(client):
    """Consultar una encuesta que no existe devuelve 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/surveys/{fake_id}")
    assert response.status_code == 404


async def test_get_survey_does_not_break_list_route(client, survey_payload):
    """
    GET /surveys/{id} y GET /surveys (listado) no deben chocar entre sí
    a nivel de enrutamiento de FastAPI.
    """
    await client.post("/api/v1/surveys", json=survey_payload)

    list_response = await client.get("/api/v1/surveys")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1