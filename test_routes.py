from datetime import datetime
from typing import Any, Dict

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from models import Client, ClientParking, Parking


@pytest.mark.parametrize(
    "endpoint, expected_status", [("/api/clients", 200), ("/api/parkings", 405)]
)
def test_get_endpoints(
    client: FlaskClient, endpoint: str, expected_status: int
) -> None:
    response = client.get(endpoint)
    assert response.status_code == expected_status


def test_create_client(client: FlaskClient, db_session: Session) -> None:
    client_data: Dict[str, Any] = {
        "name": "TestName",
        "surname": "TestSurname",
        "credit_card": "4111111111111111",
        "car_number": "A123BC",
    }

    clients_count_before = Client.query.count()

    response = client.post("/api/clients", json=client_data)

    assert response.status_code == 201
    assert response.json is not None
    assert response.json["message"] == "Client created"

    clients_count_after = Client.query.count()
    assert clients_count_after == clients_count_before + 1

    db_session.commit()


def test_create_parking(client: FlaskClient, db_session: Session) -> None:
    parking_data: Dict[str, Any] = {
        "address": "Test Address 123",
        "opened": True,
        "count_places": 20,
    }

    parkings_count_before = Parking.query.count()

    response = client.post("/api/parkings", json=parking_data)

    assert response.status_code == 201
    assert response.json is not None
    assert response.json["message"] == "Parking zone created"

    parkings_count_after = Parking.query.count()
    assert parkings_count_after == parkings_count_before + 1

    db_session.commit()


@pytest.mark.parking
def test_client_parking_in(client: FlaskClient, db_session: Session) -> None:
    new_client = Client(
        name="Test",
        surname="Client",
        credit_card="4111111111111111",
        car_number="A123BC",
    )
    db_session.add(new_client)

    new_parking = Parking(
        address="Test Parking", opened=True, count_places=10, count_available_places=10
    )
    db_session.add(new_parking)
    db_session.commit()

    parking_data: Dict[str, Any] = {
        "client_id": new_client.id,
        "parking_id": new_parking.id,
    }

    available_places_before = new_parking.count_available_places

    response = client.post("/api/client_parkings", json=parking_data)

    assert response.status_code == 200
    assert response.json is not None
    assert response.json["message"] == "Car checked in"

    db_session.refresh(new_parking)
    assert new_parking.count_available_places == available_places_before - 1


@pytest.mark.parking
def test_client_parking_out(client: FlaskClient, db_session: Session) -> None:
    exit_client = Client(
        name="Exit",
        surname="Client",
        credit_card="4111111111111111",
        car_number="B456CD",
    )
    db_session.add(exit_client)

    exit_parking = Parking(
        address="Exit Parking", opened=True, count_places=15, count_available_places=15
    )
    db_session.add(exit_parking)
    db_session.commit()

    parking_log = ClientParking(
        client_id=exit_client.id, parking_id=exit_parking.id, time_in=datetime.now()
    )
    db_session.add(parking_log)
    db_session.commit()

    exit_parking.count_available_places -= 1
    db_session.commit()

    available_places_before = exit_parking.count_available_places

    checkin_data: Dict[str, Any] = {
        "client_id": exit_client.id,
        "parking_id": exit_parking.id,
    }

    response = client.delete("/api/client_parkings", json=checkin_data)

    assert response.status_code == 200
    assert response.json is not None
    assert response.json["message"] == "Car checked out"

    db_session.refresh(exit_parking)
    assert exit_parking.count_available_places == available_places_before + 1


@pytest.mark.parking
def test_parking_closed(client: FlaskClient, db_session: Session) -> None:
    closed_client = Client(
        name="Closed",
        surname="Client",
        credit_card="4111111111111111",
        car_number="C789EF",
    )
    db_session.add(closed_client)

    closed_parking = Parking(
        address="Closed Parking", opened=False, count_places=5, count_available_places=5
    )
    db_session.add(closed_parking)
    db_session.commit()

    parking_data: Dict[str, Any] = {
        "client_id": closed_client.id,
        "parking_id": closed_parking.id,
    }

    response = client.post("/api/client_parkings", json=parking_data)

    assert response.status_code == 400
    assert response.json is not None
    assert response.json["error"] == "Parking is closed"


@pytest.mark.parking
def test_client_without_credit_card(client: FlaskClient, db_session: Session) -> None:
    no_card_client = Client(
        name="NoCard", surname="Client", credit_card=None, car_number="D012GH"
    )
    db_session.add(no_card_client)

    parking = Parking(
        address="Test Parking", opened=True, count_places=8, count_available_places=8
    )
    db_session.add(parking)
    db_session.commit()

    parking_log = ClientParking(
        client_id=no_card_client.id, parking_id=parking.id, time_in=datetime.now()
    )
    db_session.add(parking_log)

    parking.count_available_places -= 1
    db_session.commit()

    checkin_data: Dict[str, Any] = {
        "client_id": no_card_client.id,
        "parking_id": parking.id,
    }

    response = client.delete("/api/client_parkings", json=checkin_data)

    assert response.status_code == 400
    assert response.json is not None
    assert response.json["error"] == "Client has no credit card attached"
