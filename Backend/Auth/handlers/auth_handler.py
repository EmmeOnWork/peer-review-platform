from datetime import datetime, timezone
from models import User, LoginRequest, RegisterRequest, UpdateOwnProfileRequest, UserProfileFull, StudentDetails, StudentPublicProfile, StudentTeacherView, TeacherPublicProfile # Aggiungi TeacherPublicProfile
from db import get_db
from sqlalchemy import or_, and_ 
from .utils import hash_password, verify_password, generate_jwt_token, decode_token
from .blacklist import blacklisted_tokens, is_token_blacklisted 
from connexion import request 

# 1. Login user
# in handlers/auth_handler.py
def login_user(body, request=None):
    db = next(get_db())
    login_data = LoginRequest(**body)
    user = db.query(User).filter(User.email == login_data.email).first()

    # 1. PRIMO CONTROLLO: l'utente esiste?
    # Questa è una "guard clause". Se l'utente non esiste, esci subito.
    if not user:
        return {"error": "Invalid credentials"}, 401

    # 2. SECONDO CONTROLLO: la password è corretta?
    # Questa riga viene eseguita SOLO SE il primo controllo è stato superato,
    # quindi siamo SICURI che 'user' non è None.
    if not verify_password(login_data.password, user.hashed_password):
        return {"error": "Invalid credentials"}, 401

    # Se arriviamo qui, l'utente esiste e la password è corretta.
    token = generate_jwt_token(user)
    user_profile = UserProfileFull(
        name=user.name, 
        surname=user.surname,
        serialNumber=user.serial_number,
        email=user.email,
        role=user.role,
        fiscalCode=user.fiscal_code,
        birthDate=user.birth_date,
        residence=user.residence
    )
    return {"token": token, "user": user_profile.model_dump()}, 200

# 2. Register user
def register_user(body, request=None):
    db = next(get_db())
    reg_data = RegisterRequest(**body)
    if db.query(User).filter(User.email == reg_data.email).first():
        return {"error": "User already exists"}, 400

    now = datetime.now(timezone.utc)
    import random
    serial_number = ''.join(str(random.randint(0, 9)) for _ in range(10))

    user = User(
        serial_number=serial_number,
        name=reg_data.name, 
        surname=reg_data.surname, 
        email=reg_data.email,
        hashed_password=hash_password(reg_data.password),
        role=reg_data.role,
        fiscal_code=reg_data.fiscalCode,
        birth_date=reg_data.birthDate,
        residence=reg_data.residence,
        created_at=now,
        updated_at=now
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user_profile = UserProfileFull(
        name=user.name, 
        surname=user.surname, 
        serialNumber=user.serial_number,
        email=user.email,
        role=user.role,
        fiscalCode=user.fiscal_code,
        birthDate=user.birth_date,
        residence=user.residence
    )
    return user_profile.model_dump(), 201

# 3. Get own profile
def get_own_profile(token_info):
    if not token_info:
        return {"error": "Invalid token"}, 401
    
    user_id = token_info.get('user_id')
    db = next(get_db())
    user = db.query(User).filter(User.serial_number == user_id).first()
    if not user:
        return {"error": "Unauthorized"}, 401

    user_profile = UserProfileFull(
        name=user.name, 
        surname=user.surname, 
        serialNumber=user.serial_number,
        email=user.email,
        role=user.role,
        fiscalCode=user.fiscal_code,
        birthDate=user.birth_date,
        residence=user.residence
    )
    return user_profile.model_dump(), 200 

# 4. Update own profile
def update_own_profile(body, token_info):
    if not token_info:
        return {"message": "Invalid token", "code": 401}, 401
    
    user_id = token_info.get('user_id')
    db = next(get_db())
    if not body:
        return {"message": "Invalid input", "code": 400}, 400

    update_data = UpdateOwnProfileRequest(**body)
    user = db.query(User).filter(User.serial_number == user_id).first()
    if not user:
        return {"message": "Unauthorized", "code": 401}, 401

    # Aggiorna la residenza solo se fornita e non vuota
    if getattr(update_data, "residence", None) is not None and update_data.residence.strip():
        user.residence = update_data.residence
    
    # Aggiorna la password solo se fornita e se la vecchia password è corretta
    if update_data.password:
        if not update_data.old_password:
            return {"message": "Old password is required to change password", "code": 400}, 400
        if not verify_password(update_data.old_password, user.hashed_password):
            return {"message": "Invalid old password", "code": 401}, 401
        user.hashed_password = hash_password(update_data.password)
    
    user.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    user_profile = UserProfileFull(
        name=user.name, 
        surname=user.surname, 
        serialNumber=user.serial_number,
        email=user.email,
        role=user.role,
        fiscalCode=user.fiscal_code,
        birthDate=user.birth_date,
        residence=user.residence
    )
    return user_profile.model_dump(), 200

# 5. Delete own account
def delete_own_account(token_info):
    if not token_info:
        return {"error": "Invalid token"}, 401
    
    user_id = token_info.get('user_id')
    db = next(get_db())
    user = db.query(User).filter(User.serial_number == user_id).first()
    if not user:
        return {"error": "Unauthorized"}, 401

    db.delete(user)
    db.commit()
    return "", 204


# funzione per il Logout
def logout_user(token_info):
    # token_info è il payload decodificato del token JWT.
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401
    token = auth_header.split(' ')[1]

    if not token_info: 
        return {"error": "Invalid token"}, 401

    blacklisted_tokens.add(token)
    return "", 204

def get_all_students(token_info):
    if not token_info:
        return {"error": "Invalid token"}, 401

    user_role = token_info.get('role')
    if user_role != 'teacher':
        return {"error": "Forbidden: Only teachers can access this resource"}, 403

    db = next(get_db())
    students = db.query(User).filter(User.role == 'student').all()

    student_profiles = [
        StudentDetails( 
            name=student.name,
            surname=student.surname,
            serialNumber=student.serial_number,
            email=student.email,
            role=student.role
        ).model_dump() for student in students
    ]

    return student_profiles, 200

#  FUNZIONE PER LA RICERCA STUDENTI
def search_students_by_name_surname(token_info, name: str = None, surname: str = None):
    if not token_info:
        return {"error": "Invalid token"}, 401

    if not name and not surname:
        return {"error": "Please provide name and/or surname for searching"}, 400

    requesting_user_role = token_info.get('role')
    requesting_user_id = token_info.get('user_id') # Utile per capire se l'utente sta cercando se stesso

    db = next(get_db())
    query = db.query(User).filter(or_(User.role == 'student', User.role == 'teacher'))

    search_conditions = []
    if name:
        search_conditions.append(User.name.ilike(f"%{name}%"))
    if surname:
        search_conditions.append(User.surname.ilike(f"%{surname}%"))
    
    if search_conditions:
        query = query.filter(and_(*search_conditions))

    users_found = query.limit(100).all()
    results = []

    for user in users_found:
        if user.role == 'student':
            if requesting_user_role == 'teacher':
                # I teacher vedono il profilo completo dello studente (con matricola)
                results.append(StudentTeacherView(
                    name=user.name,
                    surname=user.surname,
                    email=user.email,
                    role=user.role,
                    serialNumber=user.serial_number
                ).model_dump())
            else: # Lo studente vede il profilo pubblico di un altro studente (senza matricola)
                results.append(StudentPublicProfile(
                    name=user.name,
                    surname=user.surname,
                    email=user.email,
                    role=user.role
                ).model_dump())
        elif user.role == 'teacher':
            # Tutti vedono il profilo pubblico del teacher (senza matricola)
            results.append(TeacherPublicProfile(
                name=user.name,
                surname=user.surname,
                email=user.email,
                role=user.role
            ).model_dump())
            
    if not results:
        return {"error": "No users found matching your criteria"}, 404
    
    return results, 200

# funzione di health check
def health_check():
    return {"status": "OK"}, 200