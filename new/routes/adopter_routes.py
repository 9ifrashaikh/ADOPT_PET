from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models.adopter_model import AdopterModel
from models.pet_model import PetModel
from models.auth_model import AuthModel
from models.adoption_model import AdoptionModel
from models.recommendation_model import RecommendationModel
from models.auth_decorators import adopter_required, login_required, get_current_user

adopter_bp = Blueprint('adopters', __name__)

@adopter_bp.route('/adopter_form')
@login_required  # Must be logged in to see adoption form
def adopter_form():
    """Render adopter form - PROTECTED"""
    current_user = get_current_user()
    pet_id = request.args.get('pet_id')
    
    # Only adopters can fill adoption forms
    if current_user['role'] != 'adopter':
        return jsonify({'message': 'Only adopters can access adoption forms'}), 403
    
    print("Received pet_id in adopter_form route:", pet_id)
    return render_template('form.html', pet_id=pet_id, user=current_user)

@adopter_bp.route('/adopters')
@login_required  # Must be logged in to see adopter data
def adopter():
    """Display adopter data - PROTECTED"""
    current_user = get_current_user()
    
    # Role-based data access
    if current_user['role'] == 'admin':
        # Admins can see all adopters
        adopter_data = AdopterModel.get_all_adopters()
    elif current_user['role'] == 'adopter':
        # Adopters only see their own data
        try:
            adopter_data = AdopterModel.get_adopter_by_user_id(current_user['id'])
        except:
            adopter_data = []
    else:
        return jsonify({'message': 'Access denied'}), 403
    
    return render_template('adopter.html', adopter=adopter_data, user=current_user)

@adopter_bp.route('/adopter_dashboard')
@adopter_required  # Only adopters can access their dashboard
def adopter_dashboard():
    """Adopter dashboard with recommendations - PROTECTED"""
    current_user = get_current_user()
    
    # Get adopter's available pets and recommendations
    available_pets = AuthModel.get_user_pets(current_user['id'], 'adopter')
    
    try:
        recommendations = RecommendationModel.get_recommended_pets(current_user['id'], 5)
    except:
        recommendations = {'type': 'error', 'pets': [], 'message': 'Recommendations unavailable'}
    
    return render_template('adopter/adopter_dashboard.html', 
                         user=current_user, 
                         available_pets=available_pets,
                         recommendations=recommendations)

@adopter_bp.route('/submit_adopter_form', methods=['POST'])
@adopter_required  # Only adopters can submit adoption forms
def submit_adopter_form():
    """
    UPDATED: Submit adoption APPLICATION (not instant adoption)
    What this does: Creates application that needs shelter approval
    Why: Proper adoption workflow with review process
    """
    try:
        current_user = get_current_user()
        
        # Get form data for APPLICATION
        application_data = {
            'applicant_name': request.form.get('adopter-name') or f"{current_user['first_name']} {current_user['last_name']}",
            'email': request.form.get('adopter-email') or current_user['email'],
            'phone': request.form.get('adopter-phone'),
            'address': request.form.get('adopter-address'),
            'reason_for_adoption': request.form.get('reason_for_adoption', ''),
            'experience_with_pets': request.form.get('experience_with_pets', ''),
            'living_situation': request.form.get('living_situation', '')
        }
        
        pet_id = request.args.get('pet_id') or request.form.get('pet_id')
        
        # Validation
        if not all([pet_id, application_data['phone'], application_data['address']]):
            return jsonify({
                'success': False, 
                'message': 'Missing required fields'
            }), 400
        
        # Validation: Make sure adopter info matches logged-in user
        if application_data['email'] != current_user['email']:
            return jsonify({
                'success': False, 
                'message': 'Email must match your account email'
            }), 400
        
        print("Creating adoption application for pet_id:", pet_id)
        
        # CREATE APPLICATION (not instant adoption)
        application_id = AdoptionModel.create_adoption_application(
            user_id=current_user['id'],
            pet_id=pet_id,
            application_data=application_data
        )
        
        if application_id:
            print(f"Successfully created application {application_id} for pet_id: {pet_id} by user: {current_user['id']}")
            
            return jsonify({
                'success': True,
                'message': 'Adoption application submitted successfully! The shelter will review it soon.',
                'application_id': application_id,
                'status': 'pending',
                'next_step': 'Wait for shelter staff to review your application'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to submit adoption application'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Application error: {str(e)}'
        }), 500

@adopter_bp.route('/my_adoptions')
@adopter_required  # Only adopters can see their adoptions
def my_adoptions():
    """View adopter's own adoption history - PROTECTED"""
    current_user = get_current_user()
    
    try:
        # Get applications instead of direct adoptions
        my_applications = AdoptionModel.get_user_applications(current_user['id'])
    except:
        my_applications = []
        
    return render_template('my_adoptions.html', 
                         adoptions=my_applications, 
                         user=current_user)

@adopter_bp.route('/my_applications')
@adopter_required  # Only adopters can see their applications
def my_applications():
    """
    NEW: View adopter's adoption applications with status tracking
    What this does: Shows all applications and their current status
    Why: Users need to track application progress
    """
    current_user = get_current_user()
    
    try:
        applications = AdoptionModel.get_user_applications(current_user['id'])
    except:
        applications = []
    
    return render_template('my_applications.html', 
                         applications=applications, 
                         user=current_user)

@adopter_bp.route('/recommendations')
@adopter_required  # Only adopters can see recommendations
def recommendations():
    """
    NEW: AI-powered pet recommendations page
    What this does: Shows personalized pet suggestions
    Why: Help users discover pets they might like
    """
    current_user = get_current_user()
    
    try:
        recommendations = RecommendationModel.get_recommended_pets(current_user['id'], 12)
    except:
        recommendations = {'type': 'error', 'pets': [], 'message': 'Recommendations unavailable'}
    
    return render_template('recommendations.html', 
                         recommendations=recommendations, 
                         user=current_user)