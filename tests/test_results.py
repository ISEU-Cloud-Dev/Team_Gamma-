"""
Pruebas de GET /api/v1/surveys/{survey_id}/results.
"""


async def _create_survey_and_vote(client, survey_payload, votes_for_red, votes_for_blue):
    """Helper: crea la encuesta y registra N votos para cada opción."""
    r = await client.post("/api/v1/surveys", json=survey_payload)
    survey = r.json()
    survey_id = survey["id"]
    question_id = survey["questions"][0]["id"]
    red_id = survey["questions"][0]["options"][0]["id"]
    blue_id = survey["questions"][0]["options"][1]["id"]

    for _ in range(votes_for_red):
        await client.post(
            f"/api/v1/surveys/{survey_id}/responses",
            json={"answers": [{"question_id": question_id, "option_ids": [red_id]}]},
        )
    for _ in range(votes_for_blue):
        await client.post(
            f"/api/v1/surveys/{survey_id}/responses",
            json={"answers": [{"question_id": question_id, "option_ids": [blue_id]}]},
        )

    return {"survey_id": survey_id, "red_id": red_id, "blue_id": blue_id}


async def test_results_counts_votes_correctly(client, survey_payload):
    """El conteo de votos por opción debe coincidir con lo registrado."""
    ids = await _create_survey_and_vote(client, survey_payload, votes_for_red=2, votes_for_blue=1)

    response = await client.get(f"/api/v1/surveys/{ids['survey_id']}/results")

    assert response.status_code == 200
    body = response.json()
    assert body["total_responses"] == 3

    votes_by_option = {
        option["option_id"]: option["votes"]
        for option in body["questions"][0]["options"]
    }
    assert votes_by_option[ids["red_id"]] == 2
    assert votes_by_option[ids["blue_id"]] == 1


async def test_results_survey_not_found(client):
    """Consultar resultados de una encuesta inexistente devuelve 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/surveys/{fake_id}/results")
    assert response.status_code == 404


async def test_results_survey_without_votes_returns_zero(client, survey_payload):
    """Una encuesta recién creada, sin respuestas, debe dar votes=0 sin error."""
    create_response = await client.post("/api/v1/surveys", json=survey_payload)
    survey_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/surveys/{survey_id}/results")

    assert response.status_code == 200
    body = response.json()
    assert body["total_responses"] == 0
    for option in body["questions"][0]["options"]:
        assert option["votes"] == 0


async def test_results_does_not_mix_votes_between_surveys(client, survey_payload):
    """
    Votos de la encuesta A no deben aparecer en el conteo de la encuesta B,
    aunque tengan preguntas y opciones con texto idéntico.
    """
    ids_a = await _create_survey_and_vote(client, survey_payload, votes_for_red=5, votes_for_blue=0)
    ids_b = await _create_survey_and_vote(client, survey_payload, votes_for_red=0, votes_for_blue=1)

    results_b = await client.get(f"/api/v1/surveys/{ids_b['survey_id']}/results")
    body_b = results_b.json()

    assert body_b["total_responses"] == 1
    votes_by_option_b = {
        option["option_id"]: option["votes"]
        for option in body_b["questions"][0]["options"]
    }
    assert votes_by_option_b[ids_b["red_id"]] == 0
    assert votes_by_option_b[ids_b["blue_id"]] == 1