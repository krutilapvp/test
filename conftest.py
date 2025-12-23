import pytest
from datetime import datetime, timedelta
from app import create_app
from models import db, Client, Parking, ClientParking
from factories import ClientFactory, ParkingFactory

def pytest_configure(config):
    config.addinivalue_line("markers", "parking: маркер для тестов парковки")

@pytest.fixture(scope='function')
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        yield db.session
