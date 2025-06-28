# Questo codice gestisce le operazioni di aggregazione e generazione dei report.
#
# Il servizio Report NON utilizza un database locale: aggrega i dati chiamando via REST gli altri microservizi (Assignment, Review, ecc.).
#
# 1. get_teacher_reports_by_serial(serialNumber)
#    - Input: Il serial number del teacher.
#    - Funzionamento:
#      - Recupera tutti gli assignment del docente specificato dal servizio Assignment.
#      - Per ciascun assignment, genera il report aggregato.
#      - Restituisce la lista dei report e status 200.
#
# 2. get_student_report(serialNumber, assignmentId)
#    - Input: Il serial number dello studente e l'ID dell'assignment.
#    - Funzionamento:
#      - Recupera i dati dell'assignment dal servizio Assignment.
#      - Recupera tutte le review relative alla submission dello studente dal servizio Review.
#      - Aggrega i dati (es. calcolo della media, dettagli peer review) secondo lo schema StudentReport.
#      - Restituisce il report dettagliato e status 200.
#
# 3. get_student_reports()
#    - Funzionamento:
#      - Recupera tutti gli assignment a cui lo studente autenticato ha partecipato dal servizio Assignment.
#      - Per ciascun assignment, genera il report dettagliato come in get_student_report.
#      - Restituisce la lista dei report e status 200.
#
# Tutte le funzioni validano il JWT e i permessi tramite chiamata al servizio di autenticazione.
# Non viene mai effettuato accesso diretto a un database.

import os
import requests
from flask import request
from .utils import decode_token, get_auth_header

ASSIGNMENT_SERVICE_URL = os.getenv('ASSIGNMENT_SERVICE_URL', 'http://assignment-app-service:5001')
REVIEW_SERVICE_URL = os.getenv('REVIEW_SERVICE_URL', 'http://review-app-service:5003')
SUBMISSION_SERVICE_URL = os.getenv('SUBMISSION_SERVICE_URL', 'http://submission-app-service:5002')

def get_teacher_reports_by_serial(serialNumber):
    token = get_auth_header(request)
    if not token:
        return {"error": "Missing or invalid Authorization header"}, 401

    token_info = decode_token(token)
    if not token_info or token_info.get('role') != 'teacher':
        return {"error": "Forbidden: Only teachers can access this resource"}, 403

    # Verifica che il teacher possa accedere ai propri report
    if token_info.get('user_id') != serialNumber:
        return {"error": "Forbidden: You can only access your own reports"}, 403

    # Recupera tutti gli assignment del docente specificato
    assignments_resp = requests.get(
        f"{ASSIGNMENT_SERVICE_URL}/assignments/teacher/mine",
        headers={"Authorization": f"Bearer {token}"}
    )
    if assignments_resp.status_code != 200:
        return [], 200

    assignments = assignments_resp.json()
    reports = []
    for assignment in assignments:
        assignment_id = assignment.get("_id")
        
        # Recupera tutte le submissions per quell'assignment
        submissions_resp = requests.get(
            f"{SUBMISSION_SERVICE_URL}/submissions/assignment/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if submissions_resp.status_code != 200:
            submissions = []
        else:
            submissions = submissions_resp.json()

        # Recupera tutte le review per quell'assignment
        reviews_resp = requests.get(
            f"{REVIEW_SERVICE_URL}/reviews/assignment/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        reviews = reviews_resp.json() if reviews_resp.status_code == 200 else []

        # Aggrega i dati secondo lo schema TeacherReport
        rubric = assignment.get("rubric", [])
        criterion_names = [c["criterion"] for c in rubric]
        criterion_totals = {name: {"sum": 0, "count": 0} for name in criterion_names}

        # Prepara mappa submissionId -> lista review
        submission_reviews = {}
        for review in reviews:
            sub_id = review.get("submissionId")
            if not sub_id:
                continue
            submission_reviews.setdefault(sub_id, []).append(review)
            for val in review.get("evaluation", []):
                crit = val.get("criterion")
                score = val.get("score")
                if crit in criterion_totals and isinstance(score, (int, float)):
                    criterion_totals[crit]["sum"] += score
                    criterion_totals[crit]["count"] += 1

        # Calcola average scores globali per l'assignment
        average_scores = []
        for crit in criterion_names:
            total = criterion_totals[crit]["sum"]
            count = criterion_totals[crit]["count"]
            avg = total / count if count else 0
            average_scores.append({
                "criterion": crit,
                "averageScore": avg
            })

        # Costruisci submissions secondo schema TeacherReport modificato
        submissions_report = []
        for sub in submissions:
            sub_id = sub.get("submissionId")
            serial_number = sub.get("studentSerialNumber")
            peer_reviews = []
            
            # Calcola averageScores per criterio per questa submission
            submission_criterion_totals = {name: {"sum": 0, "count": 0} for name in criterion_names}
            
            for review in submission_reviews.get(sub_id, []):
                peer_reviews.append({
                    "reviewerSerialNumber": review.get("reviewerserialNumber"),
                    "evaluation": review.get("evaluation", []),
                    "reviewedAt": review.get("submittedAt") or review.get("updatedAt")
                })
                
                # Calcola media per criterio per questa submission
                for val in review.get("evaluation", []):
                    crit = val.get("criterion")
                    score = val.get("score")
                    if crit in submission_criterion_totals and isinstance(score, (int, float)):
                        submission_criterion_totals[crit]["sum"] += score
                        submission_criterion_totals[crit]["count"] += 1
            
            # Calcola averageScores per criterio per questa submission
            submission_average_scores = []
            for crit in criterion_names:
                total = submission_criterion_totals[crit]["sum"]
                count = submission_criterion_totals[crit]["count"]
                avg = total / count if count else 0
                submission_average_scores.append({
                    "criterion": crit,
                    "averageScore": avg
                })
            
            submissions_report.append({
                "serialNumber": serial_number,
                "submissionId": sub_id,
                "averageScores": submission_average_scores,
                "peerReviews": peer_reviews
            })

        reports.append({
            "assignmentId": assignment_id,
            "title": assignment.get("title"),
            "averageScores": average_scores,
            "submissions": submissions_report
        })
    
    return reports, 200

def get_student_report(serialNumber, assignmentId):
    token = get_auth_header(request)
    if not token:
        return {"error": "Missing or invalid Authorization header"}, 401

    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    # Solo lo studente stesso o il docente può vedere il report
    if token_info.get('role') == 'student' and token_info.get('user_id') != serialNumber:
        return {"error": "Forbidden: You can only view your own reports"}, 403

    # Recupera assignment
    assignment_resp = requests.get(
        f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignmentId}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if assignment_resp.status_code != 200:
        return {"error": "Assignment not found"}, 404
    assignment = assignment_resp.json()

    # Recupera tutte le submissions dello studente per quell'assignment
    submissions_resp = requests.get(
        f"{SUBMISSION_SERVICE_URL}/submissions/mine",
        headers={"Authorization": f"Bearer {token}"}
    )
    submissions = submissions_resp.json() if submissions_resp.status_code == 200 else []
    submission = next((s for s in submissions if s.get("assignmentId") == assignmentId), None)
    submission_id = submission.get("submissionId") if submission else None

    # Recupera tutte le review per quella submission (come autore)
    peer_reviews = []
    average_score = 0
    count = 0

    if submission_id:
        # Recupera tutte le review per l'assignment e filtra per submissionId
        reviews_resp = requests.get(
            f"{REVIEW_SERVICE_URL}/reviews/assignment/{assignmentId}",
            headers={"Authorization": f"Bearer {token}"}
        )
        reviews = reviews_resp.json() if reviews_resp.status_code == 200 else []
        for review in reviews:
            if review.get("submissionId") == submission_id:
                peer_reviews.append({
                    "reviewerSerialNumber": review.get("reviewerserialNumber"),
                    "evaluation": review.get("evaluation", []),
                    "reviewedAt": review.get("submittedAt") or review.get("updatedAt")
                })
                for val in review.get("evaluation", []):
                    average_score += val.get("score", 0)
                    count += 1
    avg_score = average_score / count if count else 0

    return {
        "assignmentId": assignmentId,
        "title": assignment.get("title"),
        "submissionId": submission_id,
        "peerReviews": peer_reviews,
        "averageScore": avg_score
    }, 200

def get_student_reports():
    token = get_auth_header(request)
    if not token:
        return {"error": "Missing or invalid Authorization header"}, 401

    token_info = decode_token(token)
    if not token_info or token_info.get('role') != 'student':
        return {"error": "Forbidden: Only students can access this resource"}, 403

    serialNumber = token_info.get('user_id')

    # Recupera tutti gli assignment dello studente autenticato
    assignments_resp = requests.get(
        f"{ASSIGNMENT_SERVICE_URL}/assignments/student/mine",
        headers={"Authorization": f"Bearer {token}"}
    )
    if assignments_resp.status_code != 200:
        return [], 200

    assignments = assignments_resp.json()
    reports = []
    for assignment in assignments:
        report, status = get_student_report(serialNumber, assignment.get("_id"))
        if status == 200:
            reports.append(report)
    return reports, 200

def get_student_submission_reviews(serialNumber, submissionId):
    token = get_auth_header(request)
    if not token:
        return {"error": "Missing or invalid Authorization header"}, 401

    token_info = decode_token(token)
    if not token_info:
        return {"error": "Invalid or expired token"}, 401

    # Solo lo studente stesso o il docente può vedere le review
    if token_info.get('role') == 'student' and token_info.get('user_id') != serialNumber:
        return {"error": "Forbidden: You can only view reviews for your own submissions"}, 403

    # Recupera informazioni sulla submission
    submission_resp = requests.get(
        f"{SUBMISSION_SERVICE_URL}/submissions/{submissionId}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if submission_resp.status_code != 200:
        return {"error": "Submission not found"}, 404
    
    submission = submission_resp.json()
    assignment_id = submission.get("assignmentId")
    
    # Verifica che la submission appartenga allo studente specificato
    if submission.get("studentSerialNumber") != serialNumber:
        return {"error": "Submission does not belong to the specified student"}, 403

    # Recupera informazioni sull'assignment
    assignment_resp = requests.get(
        f"{ASSIGNMENT_SERVICE_URL}/assignments/{assignment_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if assignment_resp.status_code != 200:
        return {"error": "Assignment not found"}, 404
    
    assignment_details = assignment_resp.json()

    try:
        response = requests.get(
            f"{REVIEW_SERVICE_URL}/reviews/submission/{submissionId}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            return {"error": "Failed to fetch reviews"}, 500
        
        reviews = response.json()
        
        # Filtra solo le proprietà consentite per ogni review (senza reviewerSerialNumber)
        filtered_reviews = []
        for review in reviews:
            reviewed_at = review.get("reviewedAt")
            if not reviewed_at:
                reviewed_at = review.get("submittedAt") or review.get("updatedAt") or None
            filtered_review = {
                "evaluation": review.get("evaluation", []),
                "reviewedAt": reviewed_at
            }
            filtered_reviews.append(filtered_review)
        
        # Calcola il punteggio medio
        total_score = 0
        count_with_score = 0
        for review in filtered_reviews:
            if review.get("evaluation"):
                for evaluation in review.get("evaluation", []):
                    if evaluation.get("score") is not None:
                        total_score += evaluation["score"]
                        count_with_score += 1
        average_score = total_score / count_with_score if count_with_score > 0 else 0
        
        return {
            "submissionId": submissionId,
            "assignmentId": assignment_id,
            "title": assignment_details.get("title", "Unknown Assignment"),
            "reviews": filtered_reviews,
            "averageScore": round(average_score, 2)
        }, 200
        
    except requests.exceptions.RequestException as e:
        return {"error": "Failed to fetch reviews"}, 500

def health_check():
    return {"status": "healthy"}, 200