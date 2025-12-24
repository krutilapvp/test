from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, request

from models import Client, ClientParking, Parking, db

bp = Blueprint("routes", __name__)


@bp.route("/api/clients", methods=["GET"])
def get_clients() -> List[Dict[str, Optional[int | str]]]:
    clients = Client.query.all()
    return [
        {
            "id": client.id,
            "name": client.name,
            "surname": client.surname,
            "credit_card": client.credit_card,
            "car_number": client.car_number,
        }
        for client in clients
    ]


@bp.route("/api/clients", methods=["POST"])
def create_client() -> tuple[Response, int]:
    data: Dict[str, Any] = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["name", "surname", "credit_card", "car_number"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_client = Client(
        name=data["name"],
        surname=data["surname"],
        credit_card=data["credit_card"],
        car_number=data["car_number"],
    )

    db.session.add(new_client)
    db.session.commit()

    return jsonify({"message": "Client created"}), 201


@bp.route("/api/parkings", methods=["GET"])
def get_parkings() -> List[Dict[str, Optional[int | str | bool]]]:
    parkings = Parking.query.all()
    return [
        {
            "id": parking.id,
            "address": parking.address,
            "opened": parking.opened,
            "count_places": parking.count_places,
            "count_available_places": parking.count_available_places,
        }
        for parking in parkings
    ]


@bp.route("/api/parkings", methods=["POST"])
def create_parking() -> tuple[Response, int]:
    data: Dict[str, Any] = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["address", "opened", "count_places"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_parking = Parking(
        address=data["address"],
        opened=data["opened"],
        count_places=data["count_places"],
        count_available_places=data["count_places"],
    )

    db.session.add(new_parking)
    db.session.commit()

    return jsonify({"message": "Parking zone created"}), 201


@bp.route("/api/client_parkings", methods=["POST"])
def client_parking_in() -> tuple[Response, int]:
    data: Dict[str, Any] = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["client_id", "parking_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    client_id = data["client_id"]
    parking_id = data["parking_id"]

    client = Client.query.get(client_id)
    parking = Parking.query.get(parking_id)

    if not client:
        return jsonify({"error": "Client not found"}), 404

    if not parking:
        return jsonify({"error": "Parking not found"}), 404

    if not parking.opened:
        return jsonify({"error": "Parking is closed"}), 400

    if parking.count_available_places <= 0:
        return jsonify({"error": "No available places"}), 400

    new_log = ClientParking(
        client_id=client_id, parking_id=parking_id, time_in=datetime.now()
    )
    db.session.add(new_log)

    parking.count_available_places -= 1
    db.session.commit()

    return jsonify({"message": "Car checked in"}), 200


@bp.route("/api/client_parkings", methods=["DELETE"])
def client_parking_out() -> tuple[Response, int]:
    data: Dict[str, Any] = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["client_id", "parking_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    client_id = data["client_id"]
    parking_id = data["parking_id"]

    client = Client.query.get(client_id)
    parking = Parking.query.get(parking_id)

    if not client:
        return jsonify({"error": "Client not found"}), 404

    if not parking:
        return jsonify({"error": "Parking not found"}), 404

    if not client.credit_card:
        return jsonify({"error": "Client has no credit card attached"}), 400

    log_entry = ClientParking.query.filter_by(
        client_id=client_id, parking_id=parking_id, time_out=None
    ).first()

    if not log_entry:
        return jsonify({"error": "No active parking session found"}), 400

    log_entry.time_out = datetime.now()
    parking.count_available_places += 1
    db.session.commit()

    return jsonify({"message": "Car checked out"}), 200
