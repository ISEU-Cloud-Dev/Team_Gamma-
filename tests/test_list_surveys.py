"""
Pruebas de GET /api/v1/surveys.
"""


async def test_list_surveys_empty(client):
    """Sin encuestas creadas, debe devolver una lista vacía con total=0."""
    response = await client.get("/api/v1/surveys")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_surveys_includes_nested_relations(client, survey_payload):
    """El listado debe incluir preguntas y opciones anidadas, no solo IDs."""
    await client.post("/api/v1/surveys", json=survey_payload)

    response = await client.get("/api/v1/surveys")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    survey = body["items"][0]
    assert len(survey["questions"]) == 2
    assert len(survey["questions"][0]["options"]) == 2


async def test_list_surveys_pagination(client, survey_payload):
    """Con 3 encuestas y size=2, la página 1 trae 2 y la página 2 trae 1."""
    for _ in range(3):
        await client.post("/api/v1/surveys", json=survey_payload)

    page1 = await client.get("/api/v1/surveys?page=1&size=2")
    page2 = await client.get("/api/v1/surveys?page=2&size=2")

    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 1


async def test_list_surveys_rejects_invalid_size(client):
    """size=0 o size>100 deben ser rechazados por la validación de Query."""
    response = await client.get("/api/v1/surveys?size=0")
    assert response.status_code == 422

    response = await client.get("/api/v1/surveys?size=101")
    assert response.status_code == 422