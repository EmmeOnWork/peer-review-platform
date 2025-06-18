import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError # Per testare gli errori di validazione Pydantic

from handlers import auth_handler
from models import User 

from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker

# --- Fixtures ---
@pytest.fixture(scope="function")
def app_instance(monkeypatch):
    # Patch the database configuration BEFORE importing create_app
    test_engine = sqlalchemy_create_engine("sqlite:///:memory:")
    monkeypatch.setattr("db.engine", test_engine)
    test_session_factory = sqlalchemy_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("db.session", test_session_factory)
    
    # Mock init_db to prevent it from trying to create tables with production DB
    monkeypatch.setattr("db.init_db", MagicMock())
    
    # Now import and create the app
    from app import create_app
    connexion_app = create_app()
    return connexion_app.app  # Return the underlying Flask app for testing

@pytest.fixture
def client(app_instance): 
    return app_instance.test_client()

@pytest.fixture
def mock_db_session(monkeypatch):
    mock_session = MagicMock()
    monkeypatch.setattr(auth_handler, "get_db", MagicMock(return_value=iter([mock_session])))
    return mock_session

# --- Test per la registrazione (esistente) ---
def test_register_user_success(app_instance, mock_db_session, monkeypatch):
    """Testa la registrazione di un nuovo utente con successo."""
    monkeypatch.setattr(auth_handler, "hash_password", MagicMock(return_value="hashed_password_value"))
    mock_db_session.query(User).filter().first.return_value = None # Simula che l'utente non esista
    
    mock_user_instance = MagicMock(spec=User)
    registration_data = {
        "name": "Test", "surname": "User", "email": "test.user@example.com",
        "password": "password123", "role": "student", "fiscalCode": "RSSMRA80A01H501U",
        "birthDate": "1980-01-01", "residence": "Test City"
    }
    
    mock_user_instance.name = registration_data["name"]
    mock_user_instance.surname = registration_data["surname"]
    mock_user_instance.email = registration_data["email"]
    mock_user_instance.role = registration_data["role"]
    mock_user_instance.fiscal_code = registration_data["fiscalCode"]
    mock_user_instance.birth_date = date(1980, 1, 1) 
    mock_user_instance.residence = registration_data["residence"]
    mock_user_instance.serial_number = "1234567890"

    def mock_refresh(user_obj):
        user_obj.name = mock_user_instance.name
        user_obj.surname = mock_user_instance.surname
        user_obj.email = mock_user_instance.email
        user_obj.role = mock_user_instance.role
        user_obj.fiscal_code = mock_user_instance.fiscal_code
        user_obj.birth_date = mock_user_instance.birth_date
        user_obj.residence = mock_user_instance.residence
        user_obj.serial_number = mock_user_instance.serial_number
    
    mock_db_session.refresh = MagicMock(side_effect=mock_refresh)

    with app_instance.test_request_context():
        response_data, status_code = auth_handler.register_user(registration_data)
    
    assert status_code == 201
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    added_user = mock_db_session.add.call_args[0][0]
    assert added_user.name == registration_data["name"]
    assert added_user.hashed_password == "hashed_password_value"
    assert response_data["email"] == registration_data["email"]
    assert response_data["name"] == registration_data["name"]
    assert response_data["surname"] == registration_data["surname"]
    assert response_data["role"] == registration_data["role"]
    assert response_data["fiscalCode"] == registration_data["fiscalCode"]
    assert isinstance(response_data["birthDate"], date)
    assert response_data["birthDate"].isoformat() == registration_data["birthDate"]
    assert response_data["residence"] == registration_data["residence"]
    assert "serialNumber" in response_data
    assert len(response_data["serialNumber"]) == 10

# ---  TEST PER LA REGISTRAZIONE ---

def test_register_user_already_exists(app_instance, mock_db_session, monkeypatch):
    """Testa la registrazione fallita se l'utente esiste già."""
    
    # Simula che l'utente esista già
    mock_db_session.query(User).filter().first.return_value = User(email="existing.user@example.com") 
    
    registration_data = {
        "name": "Test", "surname": "User", "email": "existing.user@example.com", # Email esistente
        "password": "password123", "role": "student", "fiscalCode": "RSSMRA80A01H501U",
        "birthDate": "1980-01-01", "residence": "Test City"
    }
    
    with app_instance.test_request_context():
        response_data, status_code = auth_handler.register_user(registration_data)
        
    assert status_code == 400
    assert response_data["error"] == "User already exists"
    mock_db_session.add.assert_not_called() # L'utente non dovrebbe essere aggiunto
    mock_db_session.commit.assert_not_called() # Nessun commit

def test_register_user_invalid_email_format(app_instance):
    """Testa la registrazione fallita con formato email invalido (validazione Pydantic)."""
    registration_data = {
        "name": "Test", "surname": "User", "email": "test.user-no-at-sign.com", # Email invalida
        "password": "password123", "role": "student", "fiscalCode": "RSSMRA80A01H501U",
        "birthDate": "1980-01-01", "residence": "Test City"
    }
    

    with app_instance.test_request_context():
        with pytest.raises(ValidationError) as excinfo:
            auth_handler.register_user(registration_data) 
    

    assert len(excinfo.value.errors()) > 0
    assert any(err['type'] == 'value_error' and 'email' in err['loc'] for err in excinfo.value.errors())


@pytest.mark.parametrize("invalid_field, invalid_value, expected_error_part", [
    ("email", "plainaddress", "email"),
    ("role", "administrator", "role"), # Il pattern ^(student|teacher)$ dovrebbe fallire
    ("fiscalCode", "INVALIDCODE", "fiscalCode"), # Il pattern [A-Z0-9]{16} dovrebbe fallire
    ("birthDate", "not-a-date", "birthDate"), # Formato data non valido
])
def test_register_user_invalid_data_fields(app_instance, invalid_field, invalid_value, expected_error_part):
    """Testa la registrazione fallita con vari campi invalidi (validazione Pydantic)."""
    base_data = {
        "name": "Test", "surname": "User", "email": "valid.email@example.com",
        "password": "password123", "role": "student", "fiscalCode": "RSSMRA80A01H501U",
        "birthDate": "1980-01-01", "residence": "Test City"
    }
    invalid_registration_data = base_data.copy()
    invalid_registration_data[invalid_field] = invalid_value
    
    with app_instance.test_request_context():
        with pytest.raises(ValidationError) as excinfo:
            auth_handler.register_user(invalid_registration_data)
            
    assert any(expected_error_part in err.get('loc', ()) or 
               (err.get('input', {}).get(invalid_field) == invalid_value if isinstance(err.get('input'), dict) else False) or
               expected_error_part in str(err.get('msg','')).lower() or # Per il fiscalCode validator
               (err.get('type') == 'value_error.date' and invalid_field == 'birthDate') or # Pydantic date error
               (err.get('type') == 'string_pattern_mismatch' and invalid_field in ['role', 'fiscalCode']) or # Pydantic pattern error
               (err.get('type') == 'value_error.email' and invalid_field == 'email') # Pydantic email error
               for err in excinfo.value.errors())


# Test per login_user:
def test_login_user_success(app_instance, mock_db_session, monkeypatch):
    """Testa il login utente con successo."""
    mock_user = User(
        serial_number="1234567890", name="Test", surname="User",
        email="test.login@example.com", hashed_password="hashed_password_from_db",
        role="student", fiscal_code="RSSMRA80A01H501U",
        birth_date=date(1980, 1, 1), residence="Test City"
    )
    mock_db_session.query(User).filter().first.return_value = mock_user
    monkeypatch.setattr(auth_handler, "verify_password", MagicMock(return_value=True))
    monkeypatch.setattr(auth_handler, "generate_jwt_token", MagicMock(return_value="mock_jwt_token"))

    login_data = {"email": "test.login@example.com", "password": "password123"}

    with app_instance.test_request_context():
        response_data, status_code = auth_handler.login_user(login_data)

    assert status_code == 200
    assert response_data["token"] == "mock_jwt_token"
    assert response_data["user"]["email"] == mock_user.email
    assert response_data["user"]["serialNumber"] == mock_user.serial_number

def test_login_user_invalid_credentials_wrong_password(app_instance, mock_db_session, monkeypatch):
    """Testa il login fallito con password errata."""
    mock_user = User(email="test.login@example.com", hashed_password="hashed_password_from_db")
    mock_db_session.query(User).filter().first.return_value = mock_user
    monkeypatch.setattr(auth_handler, "verify_password", MagicMock(return_value=False)) # Password non corrisponde

    login_data = {"email": "test.login@example.com", "password": "wrongpassword"}

    with app_instance.test_request_context():
        response_data, status_code = auth_handler.login_user(login_data)

    assert status_code == 401
    assert response_data["error"] == "Invalid credentials"

def test_login_user_not_found(app_instance, mock_db_session):
    """Testa il login fallito se l'utente non esiste."""
    mock_db_session.query(User).filter().first.return_value = None # Utente non trovato

    login_data = {"email": "nonexistent.user@example.com", "password": "password123"}

    with app_instance.test_request_context():
        response_data, status_code = auth_handler.login_user(login_data)

    assert status_code == 401
    assert response_data["error"] == "Invalid credentials"