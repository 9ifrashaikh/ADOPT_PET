from flask import Blueprint, request, jsonify, render_template
from models.adoption_model import AdoptionModel
from models.recommendation_model import RecommendationModel
from models.notification_model import NotificationModel  # ADD THIS IMPORT
from models.auth_decorators import adopter_required, shelter_staff_required, get_current_user

adoption_bp = Blueprint('adoptions', __name__)

@adoption_bp.route('/apply', methods=['POST'])
@adopter_required
def submit_adoption_application():
    """
    Submit adoption application (PROPER WORKFLOW)
    What this does: Creates application that needs shelter approval
    Why: Adoption should be a reviewed process, not instant
    """
    try:
        current_user = get_current_user()
        data = request.get_json() or request.form
        
        application_data = {
            'applicant_name': data.get('applicant_name') or f"{current_user['first_name']} {current_user['last_name']}",
            'email': data.get('email') or current_user['email'],
            'phone': data.get('phone'),
            'address': data.get('address'),
            'reason_for_adoption': data.get('reason_for_adoption'),
            'experience_with_pets': data.get('experience_with_pets'),
            'living_situation': data.get('living_situation')
        }
        
        pet_id = data.get('pet_id')
        
        if not all([pet_id, application_data['phone'], application_data['address']]):
            return jsonify({'message': 'Missing required fields'}), 400
        
        application_id = AdoptionModel.create_adoption_application(
            current_user['id'], pet_id, application_data
        )
        
        if application_id:
            return jsonify({
                'success': True,
                'message': 'Application submitted successfully! Shelter will review it soon.',
                'application_id': application_id,
                'status': 'pending'
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to submit application'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Application error: {str(e)}'}), 500

@adoption_bp.route('/my-applications', methods=['GET'])
@adopter_required
def get_my_applications():
    """
    Get user's adoption applications with status tracking
    What this does: Shows adopter all their applications and statuses
    Why: Users need to track application progress
    """
    try:
        current_user = get_current_user()
        applications = AdoptionModel.get_user_applications(current_user['id'])
        
        return jsonify({
            'success': True,
            'applications': applications
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@adoption_bp.route('/pending-applications', methods=['GET'])
@shelter_staff_required
def get_pending_applications():
    """
    Get pending applications for shelter staff review
    What this does: Shows applications needing shelter staff attention
    Why: Shelter staff need to review and approve/reject applications
    """
    try:
        current_user = get_current_user()
        shelter_id = current_user.get('shelter_id')
        
        applications = AdoptionModel.get_applications_by_status(
            status='pending', 
            shelter_id=shelter_id
        )
        
        return jsonify({
            'success': True,
            'applications': applications,
            'count': len(applications)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@adoption_bp.route('/review-application', methods=['POST'])
@shelter_staff_required
def review_application():
    """
    Shelter staff approve/reject applications WITH NOTIFICATIONS
    What this does: Updates application status with reviewer notes AND sends notifications
    Why: Shelter staff need to manage adoption workflow and users need updates
    """
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        application_id = data.get('application_id')
        new_status = data.get('status')  # 'approved' or 'rejected'
        review_notes = data.get('review_notes', '')
        
        if not application_id or new_status not in ['approved', 'rejected']:
            return jsonify({'message': 'Invalid application ID or status'}), 400
        
        # Get application data BEFORE updating (for notifications)
        old_application = AdoptionModel.get_application_by_id(application_id)
        if not old_application:
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        
        # Update the application status
        success = AdoptionModel.update_application_status(
            application_id, new_status, current_user['id'], review_notes
        )
        
        if success:
            # Send notification to the applicant
            try:
                # Add review notes to application data for notification
                notification_data = old_application.copy()
                notification_data['review_notes'] = review_notes
                
                NotificationModel.send_adoption_status_notification(
                    notification_data, 'pending', new_status
                )
                notification_msg = " and user notified"
            except Exception as e:
                print(f"Notification failed: {e}")
                notification_msg = " (notification failed)"
            
            return jsonify({
                'success': True,
                'message': f'Application {new_status} successfully{notification_msg}!',
                'status': new_status
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to update application'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Review error: {str(e)}'}), 500

@adoption_bp.route('/all-applications', methods=['GET'])
@shelter_staff_required
def get_all_applications():
    """
    Get all applications for shelter (with filtering)
    What this does: Shows all application history for shelter
    Why: Shelter staff need overview of adoption activity
    """
    try:
        current_user = get_current_user()
        status_filter = request.args.get('status')
        shelter_id = current_user.get('shelter_id')
        
        applications = AdoptionModel.get_applications_by_status(
            status=status_filter,
            shelter_id=shelter_id
        )
        
        return jsonify({
            'success': True,
            'applications': applications,
            'filter': status_filter,
            'count': len(applications)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500