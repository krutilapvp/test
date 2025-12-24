from datetime import datetime
from typing import Any, Dict, List, Union

from flask import Blueprint, jsonify, request

from models import Client, ClientParking, Parking, db

bp = Blueprint("api", __name__)


@bp.route("/clients", methods=["GET"])
def get_clients() -> List[Dict[str, Union[int, str, None]]]:
    clients = Client.query.all()
    result = []
    for c in clients:
        result.append(
            {
                "id": c.id,
                "name": c.name,
                "surname": c.surname,
                "credit_card": c.credit_card,
                "car_number": c.car_number,
            }
        )
    return jsonify(result), 200


@bp.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id) -> List[Dict[str, Union[int, str, None]]]:
    client = Client.query.get_or_404(client_id)
    return (
        jsonify(
            {
                "id": client.id,
                "name": client.name,
                "surname": client.surname,
                "credit_card": client.credit_card,
                "car_number": client.car_number,
            }
        ),
        200,
    )


@bp.route("/clients", methods=["POST"])
def create_client() -> List[Dict[str, Union[int, str, None]]]:
    data = request.get_json()
    name = data.get("name")
    surname = data.get("surname")
    credit_card = data.get("credit_card")
    car_number = data.get("car_number")
    if not name or not surname:
        return jsonify({"error": "Missing required fields"}), 400
    new_client = Client(
        name=name, surname=surname, credit_card=credit_card, car_number=car_number
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify({"message": "Client created", "id": new_client.id}), 201


@bp.route("/parkings", methods=["POST"])
def create_parking() -> List[Dict[str, Union[int, str, None]]]:
    data = request.get_json()
    address = data.get("address")
    opened = data.get("opened", True)
    count_places = data.get("count_places")
    if not address or count_places is None:
        return jsonify({"error": "Missing required fields"}), 400
    new_parking = Parking(
        address=address,
        opened=opened,
        count_places=count_places,
        count_available_places=count_places,
    )
    db.session.add(new_parking)
    db.session.commit()
    return jsonify({"message": "Parking zone created", "id": new_parking.id}), 201


@bp.route("/client_parkings", methods=["POST"])
def client_parking_in() -> List[Dict[str, Union[int, str, None]]]:
    data = request.get_json()
    client_id = data.get("client_id")
    parking_id = data.get("parking_id")
    if not client_id or not parking_id:
        return jsonify({"error": "Missing client_id or parking_id"}), 400

    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    parking = Parking.query.get(parking_id)
    if not parking:
        return jsonify({"error": "Parking not found"}), 404

    if not parking.opened:
        return jsonify({"error": "Parking is closed"}), 400

    if parking.count_available_places <= 0:
        return jsonify({"error": "No available places"}), 400

    log = ClientParking(
        client_id=client.id, parking_id=parking.id, time_in=datetime.now()
    )

    parking.count_available_places -= 1

    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Car checked in", "log_id": log.id}), 200


@bp.route("/client_parkings", methods=["DELETE"])
def client_parking_out() -> List[Dict[str, Union[int, str, None]]]:
    data = request.get_json()
    client_id = data.get("client_id")
    parking_id = data.get("parking_id")
    if not client_id or not parking_id:
        return jsonify({"error": "Missing client_id or parking_id"}), 400

    log = ClientParking.query.filter_by(
        client_id=client_id, parking_id=parking_id, time_out=None
    ).first()

    if not log:
        return jsonify({"error": "Active parking log not found"}), 404

    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    if not client.credit_card:
        return jsonify({"error": "Client has no credit card attached"}), 400

    log.time_out = datetime.now()

    parking = Parking.query.get(parking_id)
    if parking:
        parking.count_available_places += 1

    db.session.commit()
    return jsonify({"message": "Car checked out"}), 200
