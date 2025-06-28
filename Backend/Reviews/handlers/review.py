# api/review.py
import logging
from flask import request 
from bson import ObjectId
from datetime import datetime, timezone 
import random
import sys 
import json 
from typing import Optional, List 

        # Aggiungi l'import del nuovo modello
from models import (
            ReviewSubmission,
            PeerReviewResponseWithDetails as PeerReviewResponse, 
            PeerReviewAssignmentWithDetails as PeerReviewAssignment,
            AnonymousPeerReviewResponse,
            AnonymousPeerReviewAssignment,
            ManualAssignmentRequestModel,
            AutoAssignmentRequestModel
        )
        
from db import collection 

from .auth_utils import decode_token
from .inter_service_clients import (
    get_assignment_details_api,
    get_submission_details_by_id_api, 
    get_all_submissions_for_assignment_api,
    get_user_details_api
)

logger = logging.getLogger(__name__)

# _format_datetime_iso non è più necessario se json_encoders in Pydantic models funziona bene

def _prepare_review_data_for_pydantic(review_doc_from_db: dict, author_api_details: dict = None, reviewer_api_details: dict = None) -> dict:
    if not review_doc_from_db:
        logger.warning("_prepare_review_data_for_pydantic received None for review_doc_from_db")
        return {} 
    
    data_for_pydantic = review_doc_from_db.copy()

    if "_id" in data_for_pydantic and isinstance(data_for_pydantic["_id"], ObjectId):
        data_for_pydantic["_id"] = str(data_for_pydantic["_id"]) 
    
    if "assignmentId" in data_for_pydantic and isinstance(data_for_pydantic.get("assignmentId"), ObjectId): 
        data_for_pydantic["assignmentId"] = str(data_for_pydantic["assignmentId"])
    
    # submissionId è già stringa
    
    # Popola i dettagli dell'autore, usando setdefault per assicurare che le chiavi esistano
    # anche se author_api_details è None o manca di alcuni campi.
    data_for_pydantic["authorName"] = author_api_details.get("name") if author_api_details else None
    data_for_pydantic["authorSurname"] = author_api_details.get("surname") if author_api_details else None
    if "authorSerialNumber" not in data_for_pydantic and author_api_details and author_api_details.get("serialNumber"):
        data_for_pydantic["authorSerialNumber"] = author_api_details.get("serialNumber")
    elif "authorSerialNumber" not in data_for_pydantic: # Assicura che il campo esista se non fornito
         data_for_pydantic.setdefault("authorSerialNumber", review_doc_from_db.get("authorSerialNumber"))


    # Popola i dettagli del revisore
    data_for_pydantic["reviewerName"] = reviewer_api_details.get("name") if reviewer_api_details else None
    data_for_pydantic["reviewerSurname"] = reviewer_api_details.get("surname") if reviewer_api_details else None
    if "reviewerserialNumber" not in data_for_pydantic and reviewer_api_details and reviewer_api_details.get("serialNumber"):
        data_for_pydantic["reviewerserialNumber"] = reviewer_api_details.get("serialNumber")
    elif "reviewerserialNumber" not in data_for_pydantic: # Assicura che il campo esista se non fornito
         data_for_pydantic.setdefault("reviewerserialNumber", review_doc_from_db.get("reviewerserialNumber"))


    # Gestione datetime: passa oggetti datetime o stringhe ISO valide a Pydantic
    for date_field in ["createdAt", "updatedAt", "submittedAt"]:
        if date_field in data_for_pydantic and data_for_pydantic[date_field] is not None:
            if isinstance(data_for_pydantic[date_field], str):
                try: 
                    parsed_dt = datetime.fromisoformat(data_for_pydantic[date_field].replace('Z', '+00:00'))
                    # Assicura che sia timezone-aware (UTC)
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                    data_for_pydantic[date_field] = parsed_dt
                except ValueError:
                    logger.warning(f"Could not parse date string for {date_field}: {data_for_pydantic[date_field]}. Keeping as string for Pydantic to attempt.")
            elif not isinstance(data_for_pydantic[date_field], datetime):
                 logger.warning(f"Field {date_field} in prepared_data has unexpected type: {type(data_for_pydantic[date_field])}")
            elif isinstance(data_for_pydantic[date_field], datetime) and data_for_pydantic[date_field].tzinfo is None:
                # Se è un datetime naive, rendilo aware (UTC)
                data_for_pydantic[date_field] = data_for_pydantic[date_field].replace(tzinfo=timezone.utc)


    logger.debug(f"DEBUG PREPARE: Final data prepared for Pydantic instantiation: {json.dumps(data_for_pydantic, default=str, indent=2)}")
    return data_for_pydantic

# --- HANDLERS ---

def manually_assign_peer_reviews(body, request=request):
    logger.info(f"Handler 'manually_assign_peer_reviews' called with body: {json.dumps(body, indent=2)}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing or invalid Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info: return {"error": "Invalid or expired token"}, 401
    if token_info.get('role') != 'teacher':
        return {"error": "Forbidden: Only teachers can assign reviews"}, 403

    try:
        assignment_request_data = ManualAssignmentRequestModel(**body)
    except ValueError as ve:
        logger.error(f"Pydantic validation failed for ManualAssignmentRequestModel: {ve!r}", exc_info=True)
        return {"error": f"Invalid request body: {ve.errors() if hasattr(ve, 'errors') else str(ve)}"}, 400

    assignment_id_str = assignment_request_data.assignmentId
    logger.debug(f"Processing manual assignment for assignmentId: {assignment_id_str}")

    assignment_api_details = get_assignment_details_api(assignment_id_str, token_str)
    if not assignment_api_details:
        return {"error": f"Assignment {assignment_id_str} not found or access denied from Assignment Service."}, 404
    if assignment_api_details.get('teacherSerialNumber') != token_info.get('user_id'):
        return {"error": "Forbidden: You can only assign reviews for assignments you created."}, 403

    created_reviews_for_response = []
    now = datetime.now(timezone.utc)
    logger.debug(f"Manual Assign Loop: Starting loop over {len(assignment_request_data.manualAssignments)} manual assignment items.")

    failed_submission_ids = [] # <--- NUOVA LISTA per tracciare gli ID falliti

    for item_index, manual_item in enumerate(assignment_request_data.manualAssignments):
        submission_id_str = manual_item.submissionId
        reviewer_serial_str = manual_item.reviewerserialNumber
        logger.debug(f"Manual Assign Loop (Item {item_index}): Attempting to assign reviewer {reviewer_serial_str} to submission {submission_id_str} for assignment {assignment_id_str}")

        submission_api_details = get_submission_details_by_id_api(submission_id_str, token_str) # <--- CHIAMATA API PRINCIPALE
        if not submission_api_details:
            logger.warning(f"Manual Assign Loop (Item {item_index}): Submission {submission_id_str} not found via API. Skipping this item.")
            failed_submission_ids.append(submission_id_str) # <--- AGGIUNGI ALLA LISTA
            continue

        # ... (resto della logica del ciclo come prima) ...
        author_serial_str = submission_api_details.get("studentSerialNumber")
        if not author_serial_str:
            logger.error(f"Manual Assign Loop (Item {item_index}): Could not determine author for submission {submission_id_str}. Skipping this item.")
            # Potresti voler aggiungere anche questo submission_id_str a failed_submission_ids o gestirlo diversamente
            continue

        author_details_for_prepare = {
            "name": submission_api_details.get("studentName"),
            "surname": submission_api_details.get("studentSurname"),
            "serialNumber": author_serial_str
        }

        reviewer_api_details = get_user_details_api(reviewer_serial_str, token_str, requester_token_info=token_info)
        if not reviewer_api_details or reviewer_api_details.get("role") != "student":
             logger.warning(f"Manual Assign Loop (Item {item_index}): Reviewer {reviewer_serial_str} is not a valid student or details not found. Skipping this item.")
             continue

        if reviewer_serial_str == author_serial_str:
            logger.warning(f"Manual Assign Loop (Item {item_index}): Student {reviewer_serial_str} cannot review their own submission {submission_id_str}. Skipping this item.")
            continue

        existing_check_query = {
            "submissionId": submission_id_str,
            "reviewerserialNumber": reviewer_serial_str,
            "assignmentId": ObjectId(assignment_id_str)
        }
        if collection.find_one(existing_check_query):
            logger.info(f"Manual Assign Loop (Item {item_index}): Assignment for {existing_check_query} already exists. Skipping.")
            continue

        review_to_insert_in_db = {
            "assignmentId": ObjectId(assignment_id_str),
            "submissionId": submission_id_str,
            "reviewerserialNumber": reviewer_serial_str,
            "authorSerialNumber": author_serial_str,
            "createdAt": now,
            "updatedAt": now
        }
        logger.debug(f"Manual Assign Loop (Item {item_index}): Inserting new review assignment into DB: {review_to_insert_in_db}")
        insert_result = collection.insert_one(review_to_insert_in_db)

        review_doc_from_db = collection.find_one({"_id": insert_result.inserted_id})
        if not review_doc_from_db:
            logger.error(f"Manual Assign Loop (Item {item_index}): Failed to retrieve review doc immediately after insertion for _id: {insert_result.inserted_id}. Skipping this item.")
            continue

        logger.debug(f"Manual Assign Loop (Item {item_index}): Review doc from DB after insert: {review_doc_from_db}")
        prepared_data = _prepare_review_data_for_pydantic(review_doc_from_db, author_details_for_prepare, reviewer_api_details)

        try:
            pydantic_model_instance = PeerReviewAssignment(**prepared_data)
            created_reviews_for_response.append(pydantic_model_instance.model_dump(exclude_unset=True))
            logger.info(f"Manual Assign Loop (Item {item_index}): Successfully prepared and added review (ID: {pydantic_model_instance.reviewId}) to response list.")
            logger.info(f"Manual Assign Loop (Item {item_index}): Added review. List size now: {len(created_reviews_for_response)}")
        except ValueError as ve_pydantic:
            logger.error(f"PYDANTIC VALIDATION FAILED (manually_assign_peer_reviews) for data from DB _id {review_doc_from_db.get('_id')}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)

        logger.debug(f"Manual Assign Loop: End of processing for item {item_index} with submissionId {manual_item.submissionId}.")


    logger.info(f"Handler 'manually_assign_peer_reviews' FINISHED LOOP.")

    # --- INIZIO MODIFICA ---
    # Se la richiesta originale conteneva assignments, ma nessuno è stato creato con successo
    # e ci sono stati ID di submission falliti (perché non trovati)
    if not created_reviews_for_response and assignment_request_data.manualAssignments and failed_submission_ids:
        first_failed_id = failed_submission_ids[0] # Prendi il primo ID fallito dalla lista
        logger.warning(f"Returning 404 because no reviews were created and submission {first_failed_id} (and possibly others) was not found.")
        return {"error": f"No reviews assigned. Submission with ID '{first_failed_id}' not found (or other items failed validation)."}, 404
    elif not created_reviews_for_response and assignment_request_data.manualAssignments:
        # Questo caso si verifica se ci sono stati assignments richiesti, nessuno creato,
        # ma nessun submission ID è stato specificamente marcato come "non trovato"
        # (es. tutti i reviewer erano invalidi, o l'autore non poteva essere determinato, etc.)
        logger.warning(f"Returning 400 because no reviews were created despite assignments being requested, due to other validation issues.")
        return {"error": "No reviews assigned due to validation issues with the provided items (e.g., invalid reviewers, self-review attempts)."}, 400

    logger.info(f"Returning {len(created_reviews_for_response)} review assignments with status 200.")
    return created_reviews_for_response, 200
    # --- FINE MODIFICA ---

def auto_assign_peer_reviews(body, request=request):
    logger.info(f"Handler 'auto_assign_peer_reviews' called with body: {json.dumps(body, indent=2)}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '): 
        return {"error": "Missing Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info or token_info.get('role') != 'teacher': 
        return {"error": "Forbidden or invalid token"}, 403 
    try:
        auto_request_data = AutoAssignmentRequestModel(**body)
    except ValueError as ve: 
        logger.error(f"Pydantic validation failed for AutoAssignmentRequestModel: {ve!r}", exc_info=True)
        return {"error": f"Invalid request body: {ve.errors() if hasattr(ve, 'errors') else str(ve)}"}, 400
        
    assignment_id_str = auto_request_data.assignmentId
    min_reviews_per_submission = auto_request_data.minReviews
    
    logger.debug(f"Processing auto-assignment for assignmentId: {assignment_id_str}, minReviews: {min_reviews_per_submission}")

    # ... (logica di auto_assign_peer_reviews come prima) ...
    assignment_api_details = get_assignment_details_api(assignment_id_str, token_str)
    if not assignment_api_details:
        return {"error": f"Assignment {assignment_id_str} not found or access denied."}, 404
    if assignment_api_details.get('teacherSerialNumber') != token_info.get('user_id'):
        return {"error": "Forbidden: You can only assign reviews for assignments you created."}, 403
    
    all_submissions_api_data = get_all_submissions_for_assignment_api(assignment_id_str, token_str)
    if all_submissions_api_data is None: 
        return {"error": "Failed to retrieve submissions for auto-assignment from Submission Service."}, 503
    if not all_submissions_api_data: 
         logger.info(f"No submissions found for assignment {assignment_id_str} to auto-assign reviews.")
         return {"message": "No submissions found for this assignment to auto-assign reviews."}, 200 
    
    submissions_map = { 
        sub.get("submissionId"): {
            "authorSerialNumber": sub.get("studentSerialNumber"),
            "authorName": sub.get("studentName"), 
            "authorSurname": sub.get("studentSurname") 
        }
        for sub in all_submissions_api_data if sub.get("submissionId") and sub.get("studentSerialNumber")
    }
    logger.debug(f"Found {len(submissions_map)} submissions with author info for auto-assignment.")

    potential_reviewers_serials_from_assignment = assignment_api_details.get('students', [])
    if not potential_reviewers_serials_from_assignment:
        return {"error": "No students listed in the assignment to act as reviewers."}, 400
    
    valid_potential_reviewers_details_map = {} 
    for serial in potential_reviewers_serials_from_assignment:
        user_details = get_user_details_api(serial, token_str, requester_token_info=token_info)
        if user_details and user_details.get("role") == "student":
            valid_potential_reviewers_details_map[serial] = user_details 
    
    if not valid_potential_reviewers_details_map:
        return {"error": "No valid student reviewers found for this assignment from Auth service."}, 400
    logger.debug(f"Found {len(valid_potential_reviewers_details_map)} valid student reviewers.")

    valid_reviewer_serials = list(valid_potential_reviewers_details_map.keys())
    created_review_docs_for_db = []
    now = datetime.now(timezone.utc)

    for submission_id, sub_info_from_map in submissions_map.items(): 
        author_serial = sub_info_from_map["authorSerialNumber"]
        available_reviewers = [r_serial for r_serial in valid_reviewer_serials if r_serial != author_serial]
        
        if not available_reviewers:
            logger.warning(f"Auto Assign Loop: No available reviewers for submission {submission_id} (author: {author_serial}).")
            continue
            
        num_to_assign = min(min_reviews_per_submission, len(available_reviewers))
        if num_to_assign == 0: 
            logger.warning(f"Auto Assign Loop: num_to_assign is 0 for submission {submission_id}.")
            continue
            
        selected_reviewer_serials = random.sample(available_reviewers, num_to_assign)
        logger.debug(f"Auto Assign Loop: For submission {submission_id} (author {author_serial}), selected reviewers: {selected_reviewer_serials}")
        
        for reviewer_serial in selected_reviewer_serials:
            existing_check_query = {
                "submissionId": submission_id, 
                "reviewerserialNumber": reviewer_serial,
                "assignmentId": ObjectId(assignment_id_str)
            }
            if collection.find_one(existing_check_query):
                logger.info(f"Auto Assign Loop: Review for {existing_check_query} already exists. Skipping.")
                continue
            
            review_doc = {
                "assignmentId": ObjectId(assignment_id_str), 
                "submissionId": submission_id, 
                "reviewerserialNumber": reviewer_serial, 
                "authorSerialNumber": author_serial,
                "createdAt": now, 
                "updatedAt": now
            }
            created_review_docs_for_db.append(review_doc)
            logger.debug(f"Auto Assign Loop: Prepared review doc for DB: {review_doc}")

    if not created_review_docs_for_db:
        logger.info("No new review assignments were generated by auto_assign (all might exist or no valid pairings).")
        return {"message": "No new review assignments were generated (all might exist or no valid pairings)."}, 200
    
    logger.info(f"Attempting to insert {len(created_review_docs_for_db)} new review assignments from auto_assign.")
    inserted_ids_list = [] 
    if created_review_docs_for_db: 
        insert_result = collection.insert_many(created_review_docs_for_db)
        if not insert_result or not insert_result.inserted_ids or len(insert_result.inserted_ids) != len(created_review_docs_for_db):
            logger.error(f"Mismatch in inserted documents for auto-assignment. Expected {len(created_review_docs_for_db)}, got {len(insert_result.inserted_ids) if insert_result and insert_result.inserted_ids else 'None or empty'}.")
        inserted_ids_list = insert_result.inserted_ids if insert_result and insert_result.inserted_ids else []
    
    final_response_list = []
    if inserted_ids_list:
        freshly_inserted_docs = list(collection.find({"_id": {"$in": inserted_ids_list}}))
        logger.debug(f"Retrieved {len(freshly_inserted_docs)} docs from DB after auto-assign batch insert.")
        for db_doc in freshly_inserted_docs:
            original_author_info = submissions_map.get(db_doc.get("submissionId")) 
            author_details_for_prepare = None
            if original_author_info:
                author_details_for_prepare = {
                    "name": original_author_info.get("authorName"), 
                    "surname": original_author_info.get("authorSurname"), 
                    "serialNumber": original_author_info.get("authorSerialNumber")
                }
            else: 
                logger.warning(f"Could not find original author info in submissions_map for submissionId {db_doc.get('submissionId')} during auto_assign response prep.")
                db_author_serial = db_doc.get("authorSerialNumber")
                if db_author_serial: # Tenta recupero diretto se non in mappa (costoso)
                    direct_author_details = get_user_details_api(db_author_serial, token_str, requester_token_info=token_info)
                    if direct_author_details:
                         author_details_for_prepare = {
                            "name": direct_author_details.get("name"),
                            "surname": direct_author_details.get("surname"),
                            "serialNumber": direct_author_details.get("serialNumber")
                         }

            reviewer_details_for_resp = valid_potential_reviewers_details_map.get(db_doc.get("reviewerserialNumber"))
            
            prepared_data = _prepare_review_data_for_pydantic(db_doc, author_details_for_prepare, reviewer_details_for_resp)
            try:
                pydantic_model_instance = PeerReviewAssignment(**prepared_data)
                # MODIFICA: Usa exclude_unset=True
                final_response_list.append(pydantic_model_instance.model_dump(exclude_unset=True))
                logger.debug(f"Auto Assign Loop: Successfully prepared and added review (ID: {pydantic_model_instance.reviewId}) to response list.")
            except ValueError as ve_pydantic:
                logger.error(f"PYDANTIC VALIDATION FAILED (auto_assign_peer_reviews) for data from DB _id {db_doc.get('_id')}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)
    
    logger.info(f"Handler 'auto_assign_peer_reviews' returning {len(final_response_list)} review assignments.")
    return final_response_list, 200

def list_student_peer_reviews(studentSerialNumber: str, request=request):
    logger.info(f"Handler 'list_student_peer_reviews' called for studentSerialNumber: {studentSerialNumber}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info: return {"error": "Invalid or expired token"}, 401
    
    validated_serial_from_path = studentSerialNumber
        
    if token_info.get('role') == 'student' and token_info.get('user_id') != validated_serial_from_path:
        return {"error": "Forbidden: Students can only view their own assigned reviews"}, 403
    
    reviewer_api_details = get_user_details_api(validated_serial_from_path, token_str, requester_token_info=token_info)
    if not reviewer_api_details: 
        logger.warning(f"Could not retrieve details for reviewer {validated_serial_from_path} via Auth service for list_student_peer_reviews.")

    assigned_reviews_cursor = collection.find({"reviewerserialNumber": validated_serial_from_path}).sort("createdAt", -1)
    result_list = []
    count = 0
    for review_doc_db in assigned_reviews_cursor:
        count +=1
        logger.debug(f"Processing review doc from DB (for student list): {review_doc_db.get('_id')}")
        author_api_details = get_user_details_api(review_doc_db.get("authorSerialNumber"), token_str, requester_token_info=token_info)
        prepared_data = _prepare_review_data_for_pydantic(review_doc_db, author_api_details, reviewer_api_details)
        try:
            pydantic_model_instance = PeerReviewAssignment(**prepared_data)
            # MODIFICA: Usa exclude_unset=True
            result_list.append(pydantic_model_instance.model_dump(exclude_unset=True))
        except ValueError as ve_pydantic:
            logger.error(f"PYDANTIC VALIDATION FAILED (list_student_peer_reviews) for data from DB _id {review_doc_db.get('_id')}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)
    
    logger.info(f"Handler 'list_student_peer_reviews' found {count} reviews in DB for student {studentSerialNumber}, returning {len(result_list)} valid items.")
    return result_list, 200

def submit_peer_review(reviewId: str, body: dict, request=request):
    logger.info(f"Handler 'submit_peer_review' called for reviewId: {reviewId} with body: {json.dumps(body, indent=2)}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info: return {"error": "Invalid or expired token"}, 401
    
    try:
        review_obj_id = ObjectId(reviewId)
    except Exception as e: 
        logger.warning(f"Invalid review ID format '{reviewId}': {e!r}")
        return {"error": "Invalid review ID format"}, 400
        
    try:
        submission_data_pydantic = ReviewSubmission(**body) 
    except ValueError as ve: 
        logger.error(f"Pydantic validation failed for ReviewSubmission body: {ve!r}", exc_info=True)
        return {"error": f"Invalid submission data: {ve.errors() if hasattr(ve, 'errors') else str(ve)}"}, 400
        
    existing_review_db = collection.find_one({"_id": review_obj_id})
    if not existing_review_db: 
        logger.warning(f"Review {reviewId} not found for submission.")
        return {"error": "Review not found"}, 404
        
    if existing_review_db.get('reviewerserialNumber') != token_info.get('user_id'):
        logger.warning(f"User {token_info.get('user_id')} forbidden to submit review {reviewId} (assigned to {existing_review_db.get('reviewerserialNumber')}).")
        return {"error": "Forbidden: You are not the assigned reviewer for this review."}, 403
        
    if existing_review_db.get('submittedAt'): 
        logger.warning(f"Review {reviewId} has already been submitted at {existing_review_db.get('submittedAt')}.")
        return {"error": "This review has already been submitted."}, 400
        
    now = datetime.now(timezone.utc)
    update_fields = {
        "evaluation": [item.model_dump() for item in submission_data_pydantic.evaluation], 
        "submittedAt": now, 
        "updatedAt": now
    }
    
    logger.debug(f"Updating review {reviewId} with fields: {json.dumps(update_fields, default=str, indent=2)}")
    update_result = collection.update_one({"_id": review_obj_id}, {"$set": update_fields})
    
    if update_result.matched_count == 0: 
        logger.error(f"Failed to update review {reviewId}, matched_count was 0.")
        return {"error": "Failed to update review, review may have been deleted concurrently."}, 404
        
    updated_review_doc_db = collection.find_one({"_id": review_obj_id})
    if not updated_review_doc_db: 
        logger.error(f"Failed to retrieve review {reviewId} after update.")
        return {"error": "Failed to retrieve review after update."}, 500
        
    author_api_details = get_user_details_api(updated_review_doc_db.get("authorSerialNumber"), token_str, requester_token_info=token_info)
    reviewer_api_details = get_user_details_api(updated_review_doc_db.get("reviewerserialNumber"), token_str, requester_token_info=token_info)
    
    prepared_data = _prepare_review_data_for_pydantic(updated_review_doc_db, author_api_details, reviewer_api_details)
    
    try:
        pydantic_model_instance = PeerReviewResponse(**prepared_data)
        # MODIFICA: Usa exclude_unset=True
        response_payload = pydantic_model_instance.model_dump(exclude_unset=True)
        logger.info(f"Successfully submitted and prepared response for review {reviewId}.")
        return response_payload, 200
    except ValueError as ve_pydantic:
        logger.error(f"PYDANTIC VALIDATION FAILED (submit_peer_review) for reviewId {reviewId}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)
        return {"error": f"Internal server error formatting response after submission: Pydantic validation failed. Details: {ve_pydantic.errors() if hasattr(ve, 'errors') else str(ve)}"}, 500
    except Exception as e:
        logger.error(f"Unexpected error in submit_peer_review for reviewId {reviewId}: {e!r}", exc_info=True)
        return {"error": "Unexpected internal server error after submission."}, 500

def get_peer_review_by_id(reviewId: str, request=request):
    logger.info(f"Handler 'get_peer_review_by_id' called for reviewId: {reviewId}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info: return {"error": "Invalid or expired token"}, 401
    
    try:
        review_obj_id = ObjectId(reviewId)
    except Exception as e: 
        logger.warning(f"Invalid review ID format '{reviewId}': {e!r}")
        return {"error": "Invalid review ID format"}, 400
        
    review_doc_db = collection.find_one({"_id": review_obj_id})
    if not review_doc_db: 
        logger.info(f"Review {reviewId} not found in DB.")
        return {"error": "Review not found"}, 404

    user_id_from_token = token_info.get('user_id')
    user_role_from_token = token_info.get('role')
    can_view = False
    if user_role_from_token == 'teacher':
        assignment_id_for_api = str(review_doc_db.get("assignmentId")) 
        assignment_of_review = get_assignment_details_api(assignment_id_for_api, token_str)
        if assignment_of_review and assignment_of_review.get("teacherSerialNumber") == user_id_from_token:
            can_view = True
    elif user_role_from_token == 'student':
        if review_doc_db.get('reviewerserialNumber') == user_id_from_token or \
           review_doc_db.get('authorSerialNumber') == user_id_from_token:
            can_view = True
    
    if not can_view:
         logger.warning(f"User {user_id_from_token} (role {user_role_from_token}) forbidden to view review {reviewId}.")
         return {"error": "Forbidden: You do not have permission to view this review."}, 403

    author_api_details = get_user_details_api(review_doc_db.get("authorSerialNumber"), token_str, requester_token_info=token_info)
    reviewer_api_details = get_user_details_api(review_doc_db.get("reviewerserialNumber"), token_str, requester_token_info=token_info)
    
    prepared_data = _prepare_review_data_for_pydantic(review_doc_db, author_api_details, reviewer_api_details)
    
    try:
        if prepared_data.get("evaluation") or prepared_data.get("submittedAt"): 
            logger.debug(f"Formatting review {reviewId} as PeerReviewResponse (submitted).")
            model_instance = PeerReviewResponse(**prepared_data)
        else:
            logger.debug(f"Formatting review {reviewId} as PeerReviewAssignment (not submitted).")
            model_instance = PeerReviewAssignment(**prepared_data)
        
        # MODIFICA: Usa exclude_unset=True per includere i None per i campi Optional
        response_payload = model_instance.model_dump(exclude_unset=True) 
        logger.info(f"Successfully prepared response for review {reviewId}. Handler 'get_peer_review_by_id' returning 200.")
        logger.debug(f"Payload to be returned by handler for review {reviewId}: {json.dumps(response_payload, default=str, indent=2)}")
        return response_payload, 200
        
    except ValueError as ve_pydantic: 
        logger.error(f"PYDANTIC VALIDATION FAILED (get_peer_review_by_id) for reviewId {reviewId}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)
        return {"error": f"Internal server error formatting response: Pydantic validation failed. Details: {ve_pydantic.errors() if hasattr(ve, 'errors') else str(ve)}"}, 500
    except Exception as e:
        logger.error(f"Unexpected error in get_peer_review_by_id for reviewId {reviewId} after Pydantic: {e!r}", exc_info=True)
        return {"error": "Unexpected internal server error after Pydantic processing."}, 500

def get_assignment_reviews(assignmentId: str, request=request):
    logger.info(f"Handler 'get_assignment_reviews' called for assignmentId: {assignmentId}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info: return {"error": "Invalid or expired token"}, 401
    if token_info.get('role') != 'teacher':
        return {"error": "Forbidden: Only teachers can view all reviews for an assignment."}, 403
    
    try:
        assignment_obj_id = ObjectId(assignmentId)
    except Exception as e: 
        logger.warning(f"Invalid assignment ID format '{assignmentId}': {e!r}")
        return {"error": "Invalid assignment ID format"}, 400
        
    assignment_api_details = get_assignment_details_api(assignmentId, token_str) 
    if not assignment_api_details:
        return {"error": "Assignment not found or access denied by Assignment Service."}, 404
    if assignment_api_details.get('teacherSerialNumber') != token_info.get('user_id'):
        return {"error": "Forbidden: You can only view reviews for assignments you created."}, 403
        
    reviews_cursor = collection.find({"assignmentId": assignment_obj_id}).sort("createdAt", 1) 
    result_list = []
    count_db_docs = 0
    for review_doc_db in reviews_cursor:
        count_db_docs += 1
        logger.debug(f"Processing review doc from DB (for assignment list): {review_doc_db.get('_id')}")
        author_api_details = get_user_details_api(review_doc_db.get("authorSerialNumber"), token_str, requester_token_info=token_info)
        reviewer_api_details = get_user_details_api(review_doc_db.get("reviewerserialNumber"), token_str, requester_token_info=token_info)
        prepared_data = _prepare_review_data_for_pydantic(review_doc_db, author_api_details, reviewer_api_details)
        try:
            if prepared_data.get("evaluation") or prepared_data.get("submittedAt"):
                 pydantic_model_instance = PeerReviewResponse(**prepared_data)
            else:
                 pydantic_model_instance = PeerReviewAssignment(**prepared_data)
            # MODIFICA: Usa exclude_unset=True
            result_list.append(pydantic_model_instance.model_dump(exclude_unset=True))
        except ValueError as ve_pydantic:
            logger.error(f"PYDANTIC VALIDATION FAILED (get_assignment_reviews) for data from DB _id {review_doc_db.get('_id')}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)
            
    logger.info(f"Handler 'get_assignment_reviews' found {count_db_docs} reviews in DB for assignment {assignmentId}, returning {len(result_list)} valid items.")
    return result_list, 200


def get_submission_reviews(submissionId: str, request=request):
    """Get all reviews for a specific submission without exposing reviewer serial numbers."""
    logger.info(f"Handler 'get_submission_reviews' called for submissionId: {submissionId}")
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {"error": "Missing Authorization header"}, 401
    token_str = auth_header.split(' ')[1]
    token_info = decode_token(token_str)
    if not token_info: 
        return {"error": "Invalid or expired token"}, 401
    
    # Verifica che la submission esista e che l'utente abbia accesso
    submission_api_details = get_submission_details_by_id_api(submissionId, token_str)
    if not submission_api_details:
        return {"error": "Submission not found or access denied."}, 404
    
    # Verifica autorizzazione: solo il proprietario della submission o un teacher possono vedere le review
    user_role = token_info.get('role')
    user_id = token_info.get('user_id')
    submission_author = submission_api_details.get('studentSerialNumber')
    
    if user_role != 'teacher' and user_id != submission_author:
        return {"error": "Forbidden: You can only view reviews for your own submissions."}, 403
    
    # Trova tutte le review per questa submission
    reviews_cursor = collection.find({"submissionId": submissionId}).sort("createdAt", 1)
    result_list = []
    count_db_docs = 0
    
    for review_doc_db in reviews_cursor:
        count_db_docs += 1
        logger.debug(f"Processing review doc from DB (for submission): {review_doc_db.get('_id')}")
        
        # Ottieni dettagli dell'autore della submission
        author_api_details = get_user_details_api(review_doc_db.get("authorSerialNumber"), token_str, requester_token_info=token_info)
        
        # NON ottenere dettagli del reviewer per mantenere l'anonimato
        prepared_data = _prepare_review_data_for_pydantic(review_doc_db, author_api_details, None)
        
        # Rimuovi esplicitamente i campi del reviewer per l'anonimato
        prepared_data.pop('reviewerserialNumber', None)
        prepared_data.pop('reviewerName', None)
        prepared_data.pop('reviewerSurname', None)
        

        # Nella funzione get_submission_reviews, sostituisci le righe 626-630:
        try:
            if prepared_data.get("evaluation") or prepared_data.get("submittedAt"):
                pydantic_model_instance = AnonymousPeerReviewResponse(**prepared_data)
                result_list.append(pydantic_model_instance.model_dump(exclude_unset=True))
            else:
                pydantic_model_instance = AnonymousPeerReviewAssignment(**prepared_data)
                result_list.append(pydantic_model_instance.model_dump(exclude_unset=True))
        except ValueError as ve_pydantic:
            logger.error(f"PYDANTIC VALIDATION FAILED (get_submission_reviews) for data from DB _id {review_doc_db.get('_id')}: {ve_pydantic!r}\nPROBLEMATIC PREPARED DATA: {json.dumps(prepared_data, default=str, indent=2)}", exc_info=True)
    
    logger.info(f"Handler 'get_submission_reviews' found {count_db_docs} reviews in DB for submission {submissionId}, returning {len(result_list)} valid items.")
    return result_list, 200



def health_check():
    logger.info("Review Service health check endpoint called.") 
    return {"status": "OK"}, 200