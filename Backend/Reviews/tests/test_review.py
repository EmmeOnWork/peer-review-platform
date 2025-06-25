import unittest
from unittest.mock import patch, MagicMock, ANY, call 
from bson import ObjectId
from datetime import datetime, timezone
import os
import sys
import random 

class MockRequest:
    def __init__(self, headers=None, json_data=None):
        self.headers = headers or {}
        self.json = json_data 

os.environ['AUTHENTICATION_SERVICE_URL'] = 'http://mock-auth-service'
os.environ['SUBMISSION_SERVICE_URL'] = 'http://mock-submission-service'
os.environ['ASSIGNMENT_SERVICE_URL'] = 'http://mock-assignment-service'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers import review 
from models import (
    ReviewSubmission,
    PeerReviewResponseWithDetails as PeerReviewResponse,
    PeerReviewAssignmentWithDetails as PeerReviewAssignment,
    ManualAssignmentRequestModel,
    AutoAssignmentRequestModel,
    AnnotatedObjectIdStr as ObjectIdStr,        
    AnnotatedSerialNumberStr as SerialNumberStr,
    EvaluationItem
)
class TestReviewHandlers(unittest.TestCase):

    def setUp(self):
        self.teacher_user_id = "0000000001" 
        self.student_user_id = "1111111111" 
        self.student2_user_id = "2222222222" 
        self.author_generic_serial = "3333333333" 
        self.reviewer_generic_serial = "4444444444" 
        
        self.sample_teacher_token_info = {"user_id": self.teacher_user_id, "role": "teacher"}
        self.sample_student_token_info = {"user_id": self.student_user_id, "role": "student"}
        
        self.sample_token_str = "mock_jwt_token_string_for_handler_extraction" 
        self.generic_request_token_str = "token_for_direct_use_in_mock_request"

        self.mock_assignment_id_str = "60c72b2f9b1e8b001c8e4d01" 
        self.mock_assignment_id_obj = ObjectId(self.mock_assignment_id_str)
        
        self.submission_id_from_man_assign_request = "subManSvcID001" 
        self.submission_id_from_auto_assign1 = "subAutoSvcID001"
        self.submission_id_from_auto_assign2 = "subAutoSvcID002"

        self.valid_review_id_str = "60c72b2f9b1e8b001c8e4d03" 
        self.valid_review_id_obj = ObjectId(self.valid_review_id_str)


    def test_health_check_returns_ok(self):
        response, status_code = review.health_check()
        self.assertEqual(status_code, 200)
        self.assertEqual(response["status"], "OK")

    @patch('handlers.review.collection') 
    @patch('handlers.review.get_user_details_api') 
    @patch('handlers.review.get_submission_details_by_id_api') 
    @patch('handlers.review.get_assignment_details_api') 
    @patch('handlers.review.decode_token') 
    @patch('handlers.review.logger')
    def test_manually_assign_peer_reviews_success(self, mock_logger, mock_decode_token,
                                                 mock_get_assignment_details, mock_get_submission_details,
                                                 mock_get_user_details, mock_collection):
        token_passed_in_header = self.sample_token_str
        mock_decode_token.return_value = self.sample_teacher_token_info
        
        mock_get_assignment_details.return_value = {
            "_id": self.mock_assignment_id_str, 
            "teacherSerialNumber": self.sample_teacher_token_info["user_id"],
        }

        submission_id_in_request = self.submission_id_from_man_assign_request 
        author_serial_from_submission_svc = self.author_generic_serial 
        mock_get_submission_details.return_value = { 
            "submissionId": submission_id_in_request, 
            "studentSerialNumber": author_serial_from_submission_svc,
            "studentName": "AuthorName", "studentSurname": "AuthorSurname"
        }
        
        reviewer_serial_in_request = self.reviewer_generic_serial
        mock_get_user_details.return_value = { 
            "serialNumber": reviewer_serial_in_request,
            "name": "ReviewerName", "surname": "ReviewerSurname", "role": "student"
        }

        inserted_review_id = ObjectId()
        mock_collection.insert_one.return_value = MagicMock(inserted_id=inserted_review_id)
        now_dt_man = datetime.now(timezone.utc)
        mock_collection.find_one.side_effect = [
            None, 
            { 
                "_id": inserted_review_id,
                "assignmentId": self.mock_assignment_id_obj,
                "submissionId": submission_id_in_request, 
                "reviewerserialNumber": reviewer_serial_in_request,
                "authorSerialNumber": author_serial_from_submission_svc,
                "createdAt": now_dt_man, "updatedAt": now_dt_man
            }
        ]

        request_body = {
            "assignmentId": self.mock_assignment_id_str,
            "manualAssignments": [{
                "submissionId": submission_id_in_request, 
                "reviewerserialNumber": reviewer_serial_in_request 
            }]
        }
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_passed_in_header}'})

        response_data, status_code = review.manually_assign_peer_reviews(body=request_body, request=mock_request_obj)

        self.assertEqual(status_code, 200, msg=f"Response: {response_data}")
        self.assertEqual(len(response_data), 1)
        created_review = response_data[0]
        self.assertEqual(created_review["reviewId"], str(inserted_review_id))
        self.assertEqual(created_review["submissionId"], submission_id_in_request)
        self.assertEqual(created_review["reviewerName"], "ReviewerName")
        self.assertEqual(created_review["authorName"], "AuthorName")
        
        mock_get_submission_details.assert_called_once_with(submission_id_in_request, token_passed_in_header)
        mock_get_user_details.assert_called_once_with(reviewer_serial_in_request, token_passed_in_header, requester_token_info=self.sample_teacher_token_info)


    @patch('handlers.review.get_submission_details_by_id_api')
    @patch('handlers.review.get_assignment_details_api')
    @patch('handlers.review.decode_token')
    def test_manually_assign_peer_reviews_submission_not_found(self, mock_decode_token,
                                                              mock_get_assignment_details, mock_get_submission_details):
        token_in_header = self.generic_request_token_str
        mock_decode_token.return_value = self.sample_teacher_token_info
        mock_get_assignment_details.return_value = {"teacherSerialNumber": self.sample_teacher_token_info["user_id"]}
        
        non_existent_sub_id = "nonExistentSub123"
        mock_get_submission_details.return_value = None 

        request_body = {
            "assignmentId": self.mock_assignment_id_str, 
            "manualAssignments": [{"submissionId": non_existent_sub_id, "reviewerserialNumber": self.reviewer_generic_serial}]
        }
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_in_header}'})
        
        response_data, status_code = review.manually_assign_peer_reviews(body=request_body, request=mock_request_obj)
        
        self.assertEqual(status_code, 404) 
        self.assertIn(non_existent_sub_id, response_data["error"])
        mock_get_submission_details.assert_called_once_with(non_existent_sub_id, token_in_header)

    @patch('handlers.review.collection')
    @patch('handlers.review.get_user_details_api')
    @patch('handlers.review.get_assignment_details_api') 
    @patch('handlers.review.decode_token')
    def test_get_peer_review_by_id_success_as_reviewer(self, mock_decode_token,
                                                     mock_get_assignment_details, mock_get_user_details,
                                                     mock_collection):
        token_in_header = self.sample_token_str
        mock_decode_token.return_value = self.sample_student_token_info 

        review_id_to_fetch = self.valid_review_id_obj
        reviewer_serial_in_db = self.sample_student_token_info["user_id"] 
        author_serial_in_db = self.author_generic_serial
        submission_id_in_db = "submissionForReview123"
        now_dt = datetime.now(timezone.utc)

        db_doc_found = {
            "_id": review_id_to_fetch, "assignmentId": self.mock_assignment_id_obj,
            "submissionId": submission_id_in_db, 
            "reviewerserialNumber": reviewer_serial_in_db, 
            "authorSerialNumber": author_serial_in_db,
            "evaluation": [{"criterion": "C1", "score": 90, "feedback":"Great"}], 
            "submittedAt": now_dt,
            "createdAt": now_dt, "updatedAt": now_dt 
        }
        mock_collection.find_one.return_value = db_doc_found
        
        mock_get_assignment_details.return_value = None 

        author_details_mock = {"name": "AuthorName", "surname": "AuthorSurname", "serialNumber": author_serial_in_db, "role": "student"}
        reviewer_details_mock = {"name": "ReviewerName", "surname": "ReviewerSurname", "serialNumber": reviewer_serial_in_db, "role": "student"}
        
        def mock_user_details_side_effect(serial, token, requester_token_info):
            # print(f"DEBUG get_user_details_api called with serial: {serial}", file=sys.stderr)
            if serial == author_serial_in_db: 
                return author_details_mock
            if serial == reviewer_serial_in_db: 
                return reviewer_details_mock
            # print(f"DEBUG get_user_details_api: serial {serial} NOT MATCHED, returning None", file=sys.stderr)
            return None
        mock_get_user_details.side_effect = mock_user_details_side_effect
        
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_in_header}'})
        response_data, status_code = review.get_peer_review_by_id(reviewId=str(review_id_to_fetch), request=mock_request_obj)
        
        self.assertEqual(status_code, 200, msg=f"Response: {response_data}")
        self.assertEqual(response_data["reviewId"], str(review_id_to_fetch))
        self.assertEqual(response_data["submissionId"], submission_id_in_db)
        self.assertEqual(response_data["reviewerName"], "ReviewerName")
        self.assertEqual(response_data["authorName"], "AuthorName")
        mock_get_assignment_details.assert_not_called() 
        
        expected_user_detail_calls = [
            call(author_serial_in_db, token_in_header, requester_token_info=self.sample_student_token_info),
            call(reviewer_serial_in_db, token_in_header, requester_token_info=self.sample_student_token_info)
        ]
        mock_get_user_details.assert_has_calls(expected_user_detail_calls, any_order=True)


    @patch('handlers.review.collection')
    @patch('handlers.review.decode_token')
    def test_get_peer_review_by_id_not_found_in_db(self, mock_decode_token, mock_collection):
        mock_decode_token.return_value = self.sample_student_token_info
        mock_collection.find_one.return_value = None 
        
        non_existent_review_id = "abcdef123456abcdef123456" 
        mock_request_obj = MockRequest(headers={'Authorization': 'Bearer token'})
        response_data, status_code = review.get_peer_review_by_id(reviewId=non_existent_review_id, request=mock_request_obj)
        
        self.assertEqual(status_code, 404)
        self.assertIn("not found", response_data["error"].lower())

    @patch('handlers.review.collection')
    @patch('handlers.review.get_user_details_api')
    @patch('handlers.review.get_all_submissions_for_assignment_api')
    @patch('handlers.review.get_assignment_details_api')
    @patch('handlers.review.decode_token')
    @patch('handlers.review.random.sample') 
    @patch('handlers.review.logger')
    def test_auto_assign_peer_reviews_success(self, mock_logger, mock_random_sample,
                                              mock_decode_token, mock_get_assignment_details,
                                              mock_get_all_submissions, mock_get_user_details,
                                              mock_collection):
        token_in_header = self.sample_token_str
        mock_decode_token.return_value = self.sample_teacher_token_info
        
        student_s1, student_s2, student_s3 = "7777777771", "7777777772", "7777777773"
        submission_id1, submission_id2 = self.submission_id_from_auto_assign1, self.submission_id_from_auto_assign2

        mock_get_assignment_details.return_value = {
            "teacherSerialNumber": self.sample_teacher_token_info["user_id"],
            "students": [student_s1, student_s2, student_s3] 
        }
        mock_get_all_submissions.return_value = [
            {"submissionId": submission_id1, "studentSerialNumber": student_s1, "studentName": "SubName1", "studentSurname": "SubSurname1"},
            {"submissionId": submission_id2, "studentSerialNumber": student_s2, "studentName": "SubName2", "studentSurname": "SubSurname2"}
        ]

        def mock_user_details_side_effect(serial, token, requester_token_info):
            if serial == student_s1: return {"serialNumber": serial, "name": "StudentName1", "surname": "StudentSurname1", "role": "student"}
            if serial == student_s2: return {"serialNumber": serial, "name": "StudentName2", "surname": "StudentSurname2", "role": "student"}
            if serial == student_s3: return {"serialNumber": serial, "name": "StudentName3", "surname": "StudentSurname3", "role": "student"}
            return None
        mock_get_user_details.side_effect = mock_user_details_side_effect
        mock_random_sample.side_effect = [ [student_s2], [student_s3] ] 
        mock_collection.find_one.return_value = None 

        inserted_review_ids_by_auto = [ObjectId(), ObjectId()]
        mock_collection.insert_many.return_value = MagicMock(inserted_ids=inserted_review_ids_by_auto)

        docs_that_would_be_inserted_and_then_fetched = []
        temp_now_for_auto = datetime.now(timezone.utc) 
        docs_that_would_be_inserted_and_then_fetched.append({
            "_id": inserted_review_ids_by_auto[0], 
            "assignmentId": ObjectId(self.mock_assignment_id_str), 
            "submissionId": submission_id1, 
            "reviewerserialNumber": student_s2, 
            "authorSerialNumber": student_s1,   
            "createdAt": temp_now_for_auto, 
            "updatedAt": temp_now_for_auto
        })
        docs_that_would_be_inserted_and_then_fetched.append({
            "_id": inserted_review_ids_by_auto[1], 
            "assignmentId": ObjectId(self.mock_assignment_id_str), 
            "submissionId": submission_id2, 
            "reviewerserialNumber": student_s3, 
            "authorSerialNumber": student_s2,   
            "createdAt": temp_now_for_auto,
            "updatedAt": temp_now_for_auto
        })
        mock_cursor_for_find_in_auto = MagicMock()
        mock_cursor_for_find_in_auto.__iter__.return_value = iter(docs_that_would_be_inserted_and_then_fetched)
        mock_collection.find.return_value = mock_cursor_for_find_in_auto
        
        request_body = {"assignmentId": self.mock_assignment_id_str, "minReviews": 1}
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_in_header}'})
        response_data, status_code = review.auto_assign_peer_reviews(body=request_body, request=mock_request_obj)

        self.assertEqual(status_code, 200, msg=f"Response: {response_data}")
        self.assertEqual(len(response_data), 2) 
        
        self.assertEqual(response_data[0]["reviewId"], str(inserted_review_ids_by_auto[0]))
        self.assertEqual(response_data[0]["submissionId"], submission_id1)
        self.assertEqual(response_data[0]["authorSerialNumber"], student_s1)
        self.assertEqual(response_data[0]["reviewerserialNumber"], student_s2)
        self.assertEqual(response_data[0]["reviewerName"], "StudentName2") 
        self.assertEqual(response_data[0]["authorName"], "SubName1") 
        
        self.assertEqual(response_data[1]["reviewId"], str(inserted_review_ids_by_auto[1]))
        self.assertEqual(response_data[1]["submissionId"], submission_id2)
        self.assertEqual(response_data[1]["authorSerialNumber"], student_s2)
        self.assertEqual(response_data[1]["reviewerserialNumber"], student_s3)
        self.assertEqual(response_data[1]["reviewerName"], "StudentName3")
        self.assertEqual(response_data[1]["authorName"], "SubName2") 

        mock_collection.insert_many.assert_called_once()
        docs_inserted = mock_collection.insert_many.call_args[0][0]
        self.assertEqual(docs_inserted[0]['submissionId'], submission_id1)
        self.assertIsInstance(docs_inserted[0]['assignmentId'], ObjectId)
        mock_collection.find.assert_called_once_with({"_id": {"$in": inserted_review_ids_by_auto}})


    @patch('handlers.review.collection')
    @patch('handlers.review.get_user_details_api')
    @patch('handlers.review.decode_token')
    @patch('handlers.review.logger')
    def test_list_student_peer_reviews_success(self, mock_logger, mock_decode_token,
                                               mock_get_user_details, mock_collection):
        token_in_header = self.sample_token_str
        student_serial_in_path = self.sample_student_token_info["user_id"]
        mock_decode_token.return_value = self.sample_student_token_info

        author_serial_in_db = self.author_generic_serial
        submission_id_in_db = "listedSubID001"
        review_id_in_db = ObjectId()
        now_dt = datetime.now(timezone.utc)

        reviewer_details_mock = {"serialNumber": student_serial_in_path, "name": "ReviewerListedName", "surname": "ReviewerListedSurname", "role": "student"}
        author_details_mock = {"serialNumber": author_serial_in_db, "name": "AuthorListedName", "surname": "AuthorListedSurname", "role": "student"}

        def mock_user_details_side_effect(serial, token, requester_token_info):
            # print(f"DEBUG list_student_peer_reviews - get_user_details_api called with serial: {serial}", file=sys.stderr)
            if serial == student_serial_in_path: return reviewer_details_mock
            if serial == author_serial_in_db: return author_details_mock
            return None
        mock_get_user_details.side_effect = mock_user_details_side_effect

        db_reviews_found = [{
            "_id": review_id_in_db, "assignmentId": self.mock_assignment_id_obj, 
            "submissionId": submission_id_in_db, 
            "reviewerserialNumber": student_serial_in_path, 
            "authorSerialNumber": author_serial_in_db,
            "createdAt": now_dt, "updatedAt": now_dt 
        }]
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = iter(db_reviews_found) 
        mock_collection.find.return_value = mock_cursor
        
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_in_header}'})
        response_data, status_code = review.list_student_peer_reviews(studentSerialNumber=student_serial_in_path, request=mock_request_obj)

        self.assertEqual(status_code, 200, msg=f"Response: {response_data}")
        self.assertEqual(len(response_data), 1)
        review_data = response_data[0]
        self.assertEqual(review_data["reviewId"], str(review_id_in_db))
        self.assertEqual(review_data["submissionId"], submission_id_in_db)
        self.assertEqual(review_data["reviewerserialNumber"], student_serial_in_path)
        self.assertEqual(review_data["reviewerName"], "ReviewerListedName")
        self.assertEqual(review_data["authorSerialNumber"], author_serial_in_db)
        self.assertEqual(review_data["authorName"], "AuthorListedName")

        mock_collection.find.assert_called_once_with({"reviewerserialNumber": student_serial_in_path}) # CORRETTO
        
        expected_user_detail_calls = [
            call(student_serial_in_path, token_in_header, requester_token_info=self.sample_student_token_info), 
            call(author_serial_in_db, token_in_header, requester_token_info=self.sample_student_token_info)    
        ]
        mock_get_user_details.assert_has_calls(expected_user_detail_calls, any_order=True)


    @patch('handlers.review.collection')
    @patch('handlers.review.get_user_details_api')
    @patch('handlers.review.decode_token')
    @patch('handlers.review.logger')
    def test_submit_peer_review_success(self, mock_logger, mock_decode_token,
                                        mock_get_user_details, mock_collection):
        token_in_header = self.sample_token_str
        requesting_user_info = self.sample_student_token_info
        mock_decode_token.return_value = requesting_user_info

        review_id_to_submit = self.valid_review_id_obj
        reviewer_serial_in_db = requesting_user_info["user_id"] 
        author_serial_in_db = self.author_generic_serial
        submission_id_in_db = "subForSubmit123"
        now_dt = datetime.now(timezone.utc)

        db_doc_before_submit = {
            "_id": review_id_to_submit, "assignmentId": self.mock_assignment_id_obj,
            "submissionId": submission_id_in_db, 
            "reviewerserialNumber": reviewer_serial_in_db, 
            "authorSerialNumber": author_serial_in_db, 
            "submittedAt": None, "evaluation": None,
            "createdAt": now_dt, "updatedAt": now_dt 
        }
        
        evaluation_payload = [{"criterion": "Quality", "score": 88, "feedback": "Well done"}]
        
        actual_datetime_for_submit = datetime.now(timezone.utc) 
        db_doc_after_submit = {
            **db_doc_before_submit, 
            "evaluation": evaluation_payload, 
            "submittedAt": actual_datetime_for_submit, 
            "updatedAt": actual_datetime_for_submit    
        }

        mock_collection.find_one.side_effect = [db_doc_before_submit, db_doc_after_submit]
        mock_collection.update_one.return_value = MagicMock(matched_count=1)

        author_details_mock = {"name": "AuthorSubmitName", "surname": "AuthorSubmitSurname", "serialNumber": author_serial_in_db, "role":"student"}
        reviewer_details_mock = {"name": "ReviewerSubmitName", "surname": "ReviewerSubmitSurname", "serialNumber": reviewer_serial_in_db, "role":"student"}

        def mock_user_details_side_effect(serial, token, requester_token_info):
            # print(f"DEBUG submit_peer_review - get_user_details_api called with serial: {serial}", file=sys.stderr)
            if serial == author_serial_in_db: return author_details_mock
            if serial == reviewer_serial_in_db: return reviewer_details_mock
            return None
        mock_get_user_details.side_effect = mock_user_details_side_effect
        
        request_body_for_submit = {"evaluation": evaluation_payload}
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_in_header}'})

        response_data, status_code = review.submit_peer_review(
            reviewId=str(review_id_to_submit), 
            body=request_body_for_submit, 
            request=mock_request_obj
        )
        
        self.assertEqual(status_code, 200, msg=f"Response: {response_data}")
        self.assertEqual(response_data["reviewId"], str(review_id_to_submit))
        self.assertEqual(response_data["submissionId"], submission_id_in_db)
        self.assertIsNotNone(response_data["submittedAt"])
        self.assertEqual(response_data["evaluation"], evaluation_payload)
        self.assertEqual(response_data["reviewerName"], "ReviewerSubmitName")
        self.assertEqual(response_data["authorName"], "AuthorSubmitName")

        mock_collection.update_one.assert_called_once_with(
            {"_id": review_id_to_submit},
            {"$set": {"evaluation": evaluation_payload, "submittedAt": ANY, "updatedAt": ANY}}
        )


    @patch('handlers.review.collection')
    @patch('handlers.review.get_user_details_api')
    @patch('handlers.review.get_assignment_details_api')
    @patch('handlers.review.decode_token')
    @patch('handlers.review.logger')
    def test_get_assignment_reviews_success_teacher_owner(self, mock_logger, mock_decode_token,
                                                          mock_get_assignment_details, mock_get_user_details,
                                                          mock_collection):
        token_in_header = self.sample_token_str
        teacher_info = self.sample_teacher_token_info
        mock_decode_token.return_value = teacher_info

        assignment_id_to_query = self.mock_assignment_id_str
        mock_get_assignment_details.return_value = {
            "teacherSerialNumber": teacher_info["user_id"] 
        }

        author_s = self.author_generic_serial
        reviewer_s = self.reviewer_generic_serial
        review_id_db = ObjectId()
        submission_id_db = "subForAssignmentList001"
        now_dt = datetime.now(timezone.utc)

        db_reviews_found = [{
            "_id": review_id_db, "assignmentId": ObjectId(assignment_id_to_query), 
            "submissionId": submission_id_db, 
            "reviewerserialNumber": reviewer_s, "authorSerialNumber": author_s,
            "evaluation": [{"criterion":"Test", "score":50}], "submittedAt": now_dt,
            "createdAt": now_dt, "updatedAt": now_dt 
        }]
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = iter(db_reviews_found)
        mock_collection.find.return_value = mock_cursor
        
        author_details_mock = {"name": "AuthorAssignListName", "surname": "AuthorAssignListSurname", "serialNumber": author_s, "role":"student"}
        reviewer_details_mock = {"name": "ReviewerAssignListName", "surname": "ReviewerAssignListSurname", "serialNumber": reviewer_s, "role":"student"}
        def mock_user_details_side_effect(serial, token, requester_token_info):
            # print(f"DEBUG get_assignment_reviews - get_user_details_api called with serial: {serial}", file=sys.stderr)
            if serial == author_s: return author_details_mock
            if serial == reviewer_s: return reviewer_details_mock
            return None
        mock_get_user_details.side_effect = mock_user_details_side_effect
        
        mock_request_obj = MockRequest(headers={'Authorization': f'Bearer {token_in_header}'})
        response_data, status_code = review.get_assignment_reviews(assignmentId=assignment_id_to_query, request=mock_request_obj)

        self.assertEqual(status_code, 200, msg=f"Response: {response_data}")
        self.assertEqual(len(response_data), 1)
        review_resp = response_data[0]
        self.assertEqual(review_resp["reviewId"], str(review_id_db))
        self.assertEqual(review_resp["submissionId"], submission_id_db)
        self.assertEqual(review_resp["authorName"], "AuthorAssignListName")
        self.assertEqual(review_resp["reviewerName"], "ReviewerAssignListName")
        self.assertTrue("evaluation" in review_resp) 

        mock_get_assignment_details.assert_called_once_with(assignment_id_to_query, token_in_header)
        mock_collection.find.assert_called_once_with({"assignmentId": ObjectId(assignment_id_to_query)})
        expected_user_detail_calls = [
            call(author_s, token_in_header, requester_token_info=teacher_info),
            call(reviewer_s, token_in_header, requester_token_info=teacher_info)
        ]
        mock_get_user_details.assert_has_calls(expected_user_detail_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()