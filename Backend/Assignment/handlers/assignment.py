# Questo codice  gestisce le operazioni CRUD (Create, Read, Update, Delete) per gli assignment
# 
# 1. create_assignment(body)
#    - Input: Un dizionario body con i dati dell'assignment.
#    - Funzionamento:
#      - Crea un oggetto Assignment usando i dati ricevuti.
#      - Imposta i campi createdAt e updatedAt con la data e ora attuali (in UTC).
#      - Inserisce il record nel database MongoDB.
#      - Restituisce il record creato (con l’ID convertito in stringa) e lo status HTTP 201 (Created).
#
# 2. update_assignment(assignmentId, body)
#    - Input: L’ID dell’assignment da aggiornare e i nuovi dati (body).
#    - Funzionamento:
#      - Verifica che l’ID sia valido.
#      - Crea un nuovo oggetto Assignment con i dati aggiornati.
#      - Aggiorna il campo updatedAt con la data e ora attuali.
#      - Aggiorna il documento nel database usando l’ID.
#      - Se nessun documento viene trovato, restituisce errore 404.
#      - Altrimenti, restituisce i dati aggiornati e status 200.
#
# 3. delete_assignment(assignmentId)
#    - Input: L’ID dell’assignment da eliminare.
#    - Funzionamento:
#      - Verifica che l’ID sia valido.
#      - Elimina il documento dal database.
#      - Se nessun documento viene eliminato, restituisce errore 404.
#      - Altrimenti, restituisce una risposta vuota e status 204 (No Content).
#
# 4. get_by_teacher(teacherSerialNumber)
#    - Input: Il serial number dell’insegnante.
#    - Funzionamento:
#      - Recupera tutti gli assignment associati a quell’insegnante.
#      - Converte l’ID MongoDB in stringa per ogni assignment.
#      - Restituisce la lista degli assignment e status 200.
#
# 5. get_by_student(studentSerialNumber)
#    - Input: Il serial number dello studente.
#    - Funzionamento:
#      - Recupera tutti gli assignment in cui lo studente è presente nella lista students.
#      - Converte l’ID MongoDB in stringa per ogni assignment.
#      - Restituisce la lista degli assignment e status 200.


from models import Assignment
from db import collection
from datetime import datetime, timezone
from bson import ObjectId
from flask import request
from .utils import decode_token, get_and_validate_students, get_teacher_info
import os

def create_assignment(body, request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    if token_info.get('role') != 'teacher':
        return {"error": "Only teachers can create assignments"}, 403

    body["teacherSerialNumber"] = token_info["user_id"]
    
    # Ottieni informazioni del teacher
    teacher_info, error_message = get_teacher_info(token)
    if error_message:
        return {"error": error_message}, 503
    
    body["teacherName"] = teacher_info['name']
    body["teacherSurname"] = teacher_info['surname']

    if "students" in body and body["students"]:
        is_valid, error_message = get_and_validate_students(body["students"], token)
        if not is_valid:
            status_code = 400
            if "Forbidden" in error_message:
                status_code = 403
            elif "Error communicating" in error_message or "Could not connect" in error_message:
                status_code = 503
            elif "Unexpected error" in error_message:
                status_code = 500
            return {"error": error_message}, status_code

    try:
        assignment = Assignment(**body)
    except ValueError as ve:
        return {"error": str(ve)}, 400

    now = datetime.now(timezone.utc)
    record = assignment.model_dump()
    record["createdAt"] = now
    record["updatedAt"] = now

    result = collection.insert_one(record)
    record["_id"] = str(result.inserted_id)
    record["createdAt"] = record["createdAt"].isoformat()
    record["updatedAt"] = record["updatedAt"].isoformat()

    if isinstance(record.get("deadline"), datetime):
        record["deadline"] = record["deadline"].isoformat()

    return record, 201


def update_assignment(assignmentId, body, request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    if token_info.get('role') != 'teacher': # Authorization: only teachers can update
        return {"error": "Forbidden: Only teachers can update assignments"}, 403

    if not ObjectId.is_valid(assignmentId):
        return {"error": "Invalid ID"}, 400

    # Fetch the existing assignment
    existing_assignment = collection.find_one({"_id": ObjectId(assignmentId)})
    if not existing_assignment:
        return {"error": "Assignment not found"}, 404

    # Authorization: teacher can only update their own assignments
    if existing_assignment.get('teacherSerialNumber') != token_info.get('user_id'):
        return {"error": "Forbidden: You can only update assignments you created"}, 403

    # Create a temporary dict for Pydantic validation, starting with the incoming body.
    validation_data = body.copy()

    # Add teacherSerialNumber from the existing document for validation purposes
    # if it's not already in the body. This ensures the Assignment model can be instantiated.
    # The actual teacherSerialNumber will not be changed in the DB by this update.
    if 'teacherSerialNumber' not in validation_data:
        validation_data['teacherSerialNumber'] = existing_assignment.get('teacherSerialNumber')
    # If the client did send teacherSerialNumber, Pydantic will validate its format.
    # We will ensure it's not part of the $set operation later.

    try:
        # Validate the payload (title, desc, deadline, rubric, students)
        # and ensure teacherSerialNumber format is valid.
        assignment_model_instance = Assignment(**validation_data)
    except ValueError as ve: # Pydantic validation error
        return {"error": str(ve)}, 400

    # Prepare the fields to be updated in MongoDB.
    # Use model_dump from the validated instance. exclude_unset=True is good practice
    # to only include fields that were actually provided in the input body.
    update_doc = assignment_model_instance.model_dump(exclude_unset=True)

    # Ensure teacherSerialNumber and createdAt are not part of the $set operation.
    update_doc.pop("teacherSerialNumber", None)
    update_doc.pop("createdAt", None)
    
    # Set the updatedAt timestamp
    update_doc["updatedAt"] = datetime.now(timezone.utc)

    result = collection.update_one(
        {"_id": ObjectId(assignmentId)},
        {"$set": update_doc}
    )

    # Fetch the updated document to return it, ensuring it's the version from the DB.
    final_updated_assignment = collection.find_one({"_id": ObjectId(assignmentId)})
    if not final_updated_assignment: # Should ideally not happen if update was successful
        # This case might indicate a race condition or other issue if the document disappears
        # immediately after an update. For robustness, handle it.
        return {"error": "Failed to retrieve updated assignment post-update"}, 500
        
    # Serialize for response, similar to how get_assignment_by_id would do.
    final_updated_assignment["_id"] = str(final_updated_assignment["_id"])
    if isinstance(final_updated_assignment.get("createdAt"), datetime):
        final_updated_assignment["createdAt"] = final_updated_assignment["createdAt"].isoformat()
    if isinstance(final_updated_assignment.get("updatedAt"), datetime):
        final_updated_assignment["updatedAt"] = final_updated_assignment["updatedAt"].isoformat()
    if isinstance(final_updated_assignment.get("deadline"), datetime):
        final_updated_assignment["deadline"] = final_updated_assignment["deadline"].isoformat()
    
    # Rubric items are complex objects; ensure they are part of the response if they exist.
    # The AssignmentResponse schema expects rubric, students, teacherSerialNumber etc.
    # find_one returns these directly if they are in the document.

    return final_updated_assignment, 200


def delete_assignment(assignmentId, request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    if token_info.get('role') != 'teacher':
        return {"error": "Only teachers can delete assignments"}, 403

    if not ObjectId.is_valid(assignmentId):
        return {"error": "Invalid ID"}, 400

    assignment_to_delete = collection.find_one({"_id": ObjectId(assignmentId)})
    if not assignment_to_delete:
        return {"error": "Assignment not found"}, 404

    if assignment_to_delete.get('teacherSerialNumber') != token_info.get('user_id'):
        return {"error": "Forbidden: You can only delete assignments you created"}, 403

    result = collection.delete_one({"_id": ObjectId(assignmentId)})
    if result.deleted_count == 0:
        return {"error": "Assignment not found"}, 404

    return "", 204


def get_by_teacher(request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    if token_info.get('role') != 'teacher':
        return {"error": "Forbidden: Only teachers can access this resource"}, 403

    teacherSerialNumber = token_info.get('user_id')

    assignments = list(collection.find({"teacherSerialNumber": teacherSerialNumber}))
    for a in assignments:
        a["_id"] = str(a["_id"])
        if isinstance(a.get("createdAt"), datetime):
            a["createdAt"] = a["createdAt"].isoformat()
        if isinstance(a.get("updatedAt"), datetime):
            a["updatedAt"] = a["updatedAt"].isoformat()
        if isinstance(a.get("deadline"), datetime):
            a["deadline"] = a["deadline"].isoformat()
        # Ensure teacherName and teacherSurname are always present
        a["teacherName"] = a.get("teacherName", "")
        a["teacherSurname"] = a.get("teacherSurname", "")
    return assignments, 200


def get_assignment_students(assignmentId, request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    # Solo i teacher possono accedere a questa risorsa
    if token_info.get('role') != 'teacher':
        return {"error": "Forbidden: Only teachers can access this resource"}, 403

    if not ObjectId.is_valid(assignmentId):
        return {"error": "Invalid ID"}, 400

    assignment = collection.find_one({"_id": ObjectId(assignmentId)})
    if not assignment:
        return {"error": "Assignment not found"}, 404

    # Verifica che il teacher possa accedere a questo assignment
    if assignment.get('teacherSerialNumber') != token_info.get('user_id'):
        return {"error": "Forbidden: You can only access assignments you created"}, 403

    # Restituisci solo la lista degli studenti
    students = assignment.get('students', [])
    return students, 200

def get_by_student(request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    # Ensure the user is a student
    if token_info.get('role') != 'student':
        return {"error": "Forbidden: Only students can access this resource"}, 403

    studentSerialNumber = token_info.get('user_id') # GET studentSerialNumber from token
    if not studentSerialNumber:
        return {"error": "Student ID not found in token"}, 401

    assignments = list(collection.find({"students": studentSerialNumber}))
    for a in assignments:
        a["_id"] = str(a["_id"])
        if isinstance(a.get("createdAt"), datetime):
            a["createdAt"] = a["createdAt"].isoformat()
        if isinstance(a.get("updatedAt"), datetime):
            a["updatedAt"] = a["updatedAt"].isoformat()
        if isinstance(a.get("deadline"), datetime):
            a["deadline"] = a["deadline"].isoformat()
        # Remove students field for student view
        a.pop("students", None)
        # Ensure teacherName and teacherSurname are always present
        a["teacherName"] = a.get("teacherName", "")
        a["teacherSurname"] = a.get("teacherSurname", "")
    return assignments, 200


def get_assignment_by_id(assignmentId, request=request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401

    token = auth_header.split(' ')[1]
    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    if not ObjectId.is_valid(assignmentId):
        return {"error": "Invalid ID"}, 400

    assignment = collection.find_one({"_id": ObjectId(assignmentId)})

    if not assignment:
        return {"error": "Assignment not found"}, 404

    # Convert ObjectId and datetime objects to strings for JSON serialization
    assignment["_id"] = str(assignment["_id"])
    if isinstance(assignment.get("createdAt"), datetime):
        assignment["createdAt"] = assignment["createdAt"].isoformat()
    if isinstance(assignment.get("updatedAt"), datetime):
        assignment["updatedAt"] = assignment["updatedAt"].isoformat()
    if isinstance(assignment.get("deadline"), datetime):
        assignment["deadline"] = assignment["deadline"].isoformat()
    # Ensure teacherName and teacherSurname are always present
    assignment["teacherName"] = assignment.get("teacherName", "")
    assignment["teacherSurname"] = assignment.get("teacherSurname", "")

    return assignment, 200



def health_check():
    return {"status": "OK"}, 200