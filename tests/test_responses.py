"""
Pruebas de POST /api/v1/surveys/{survey_id}/responses.
"""


async def _create_survey_and_get_ids(client, survey_payload):
    """Helper: crea una encuesta y devuelve los IDs que las pruebas necesitan."""
    r = await client.post("/api/v1/surveys", json=survey_payload)
    survey = r.json()
    return {
        "survey_id": survey["id"],
        "choice_question_id": survey["questions"][0]["id"],
        "red_option_id": survey["questions"][0]["options"][0]["id"],
        "text_question_id": survey["questions"][1]["id"],
    }


async def test_submit_response_success(client, survey_payload):
    """Responder con una opción válida y un texto libre debe dar 201."""
    ids = await _create_survey_and_get_ids(client, survey_payload)

    response_payload = {
        "answers": [
            {"question_id": ids["choice_question_id"], "option_ids": [ids["red_option_id"]]},
            {"question_id": ids["text_question_id"], "option_ids": [], "text": "Todo bien"},
        ]
    }
    response = await client.post(
        f"/api/v1/surveys/{ids['survey_id']}/responses", json=response_payload
    )

    assert response.status_code == 201
    body = response.json()
    assert body["survey_id"] == ids["survey_id"]
    assert body["text_answers"][ids["text_question_id"]] == "Todo bien"


async def test_submit_response_survey_not_found(client, survey_payload):
    """Responder a una encuesta que no existe debe dar 404."""
    fake_survey_id = "00000000-0000-0000-0000-000000000000"
    fake_question_id = "11111111-1111-1111-1111-111111111111"
    response = await client.post(
        f"/api/v1/surveys/{fake_survey_id}/responses",
        json={"answers": [{"question_id": fake_question_id, "option_ids": []}]},
    )
    assert response.status_code == 404


async def test_submit_response_question_not_in_survey(client, survey_payload):
    """
    Responder con un question_id que no existe en ninguna pregunta de la
    encuesta debe dar 400 (no 500 ni un guardado silencioso incorrecto).
    """
    ids = await _create_survey_and_get_ids(client, survey_payload)
    fake_question_id = "00000000-0000-0000-0000-000000000000"

    response_payload = {"answers": [{"question_id": fake_question_id, "option_ids": []}]}
    response = await client.post(
        f"/api/v1/surveys/{ids['survey_id']}/responses", json=response_payload
    )
    assert response.status_code == 400


async def test_submit_response_option_not_in_question(client, survey_payload):
    """
    Elegir una opción que existe, pero que pertenece a OTRA pregunta,
    debe ser rechazado con 400 (esta es la validación clave del ticket).
    """
    ids = await _create_survey_and_get_ids(client, survey_payload)

    # red_option_id pertenece a choice_question_id, no a text_question_id
    response_payload = {
        "answers": [
            {"question_id": ids["text_question_id"], "option_ids": [ids["red_option_id"]]}
        ]
    }
    response = await client.post(
        f"/api/v1/surveys/{ids['survey_id']}/responses", json=response_payload
    )
    assert response.status_code == 400


async def test_submit_response_does_not_save_on_validation_error(client, survey_payload):
    """
    Si la validación falla, no debe quedar ninguna respuesta guardada
    a medias en la base de datos.
    """
    ids = await _create_survey_and_get_ids(client, survey_payload)
    fake_question_id = "00000000-0000-0000-0000-000000000000"

    await client.post(
        f"/api/v1/surveys/{ids['survey_id']}/responses",
        json={"answers": [{"question_id": fake_question_id, "option_ids": []}]},
    )

    listing = await client.get("/api/v1/surveys")
    assert listing.json()["total"] == 1