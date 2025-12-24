import factory
from factory import fuzzy

from models import Client, Parking, db


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    credit_card = fuzzy.FuzzyChoice([None, factory.Faker("credit_card_number")])
    car_number = factory.Faker("license_plate")


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    address = factory.Faker("address")
    opened = fuzzy.FuzzyChoice([True, False])
    count_places = fuzzy.FuzzyInteger(5, 50)
    count_available_places = factory.SelfAttribute('count_places')
