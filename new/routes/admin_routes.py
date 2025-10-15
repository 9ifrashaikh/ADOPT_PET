from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models.pet_model import PetModel
from models.medical_model import MedicalModel
from models.shelter_model import ShelterModel
from models.auth_decorators import admin_required, get_current_user


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required  # 🔒 NOW PROTECTED - Only admins can access
def new_page():
    """Admin dashbo - PROTECTED"""
    current_user = get_current_user()
    return render_template('admin/admin_dashboard.html', user=current_user)

@admin_bp.route('/notadopted_pets')
@admin_required  # 🔒 Only admins can see all pets
def not_adopted():
    """Display not adopted pets - PROTECTED"""
    not_adopted_pets = PetModel.get_not_adopted_pets()
    return render_template('notadopted.html', not_adopted_pets=not_adopted_pets)

@admin_bp.route('/adopted_pets')
@admin_required  # 🔒 Only admins can see adoption data
def adopted_peardts():
    """Display adopted pets - PROTECTED"""
    adopted_pets_data = PetModel.get_adopted_pets()
    return render_template('adopted_pets.html', adopted_pets=adopted_pets_data)

@admin_bp.route('/add_pet_form')
@admin_required  # 🔒 Only admins can add pets
def add_pet_form():
    """Display add pet form - PROTECTED"""
    return render_template('add_pet.html')

@admin_bp.route('/add_pet', methods=['POST'])
@admin_required  # 🔒 Only admins can add pets
def add_pet():
    """Handle add pet form submission - PROTECTED"""
    try:
        current_user = get_current_user()
        
        # Extract pet information from the form
        category = request.form['category']
        name = request.form['name']
        species = request.form['species']
        gender = request.form['gender']
        age = request.form['age']
        breed = request.form['breed']
        image = request.form['image']
        
        # Medical record data
        in_date_of_visit = request.form['in_date_of_visit']
        in_medicines_or_vaccinations = request.form['in_medicines_or_vaccinations']
        in_diagnosis = request.form['in_diagnosis']
        in_dr_name = request.form['in_dr_name']
        in_dr_number = request.form['in_dr_number']
        
        # Add pet to database
        pet_id = PetModel.add_pet(category, name, species, gender, age, breed, image)
        
        if pet_id:
            # Update medical records
            MedicalModel.update_medical_records(
                pet_id, in_date_of_visit, in_medicines_or_vaccinations, 
                in_diagnosis, in_dr_name, in_dr_number
            )
            return jsonify({'success': True, 'message': 'Pet added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add pet'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@admin_bp.route('/delete')
@admin_required  # 🔒 Only admins can access delete page
def delete():
    """Display delete pet form - PROTECTED"""
    return render_template('delete_pet.html')

@admin_bp.route('/delete_pet', methods=['POST'])
@admin_required  # 🔒 CRITICAL - Only admins can delete pets!
def delete_pet():
    """Handle delete pet request - PROTECTED"""
    try:
        current_user = get_current_user()
        pet_id = request.form['pet_id']
        
        # Log who deleted what (good practice)
        print(f"Admin {current_user['email']} deleting pet {pet_id}")
        
        success = PetModel.delete_pet(pet_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Pet deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Pet not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Delete error: {str(e)}'}), 500
    
@admin_bp.route('/shelters')
@admin_required  # 🔒 Only admins can manage all shelters
def shelters():
    """Display all shelters - PROTECTED"""
    all_shelters = ShelterModel.get_all_shelters()
    return render_template('shelters.html', shelters=all_shelters)

@admin_bp.route('/pending-users')
@admin_required
def pending_users():
    """Show all users waiting for approval"""
    from models.auth_model import AuthModel
    from models.shelter_model import ShelterModel
    
    current_user = get_current_user()
    pending = AuthModel.get_users_by_status('pending')
    
    # Clean ALL user objects to remove bytes/datetime objects
    def clean_user_data(user):
        if not user:
            return None
        user_clean = {}
        for key, value in user.items():
            # Skip password fields
            if key in ('password_hash', 'password'):
                continue
            # Convert datetime to string
            elif hasattr(value, 'isoformat'):
                user_clean[key] = value.isoformat()
            # Skip bytes objects
            elif isinstance(value, bytes):
                continue
            else:
                user_clean[key] = value
        return user_clean
    
    # Clean current user
    current_user = clean_user_data(current_user)
    
    # Clean and process pending users
    cleaned_pending = []
    for user in pending:
        clean_user = clean_user_data(user)
        
        # Add shelter name for shelter_staff users
        if clean_user['role'] == 'shelter_staff' and clean_user.get('shelter_id'):
            shelter = ShelterModel.get_shelter_by_id(clean_user['shelter_id'])
            clean_user['shelter_name'] = shelter[1] if shelter else 'Unknown'
        
        cleaned_pending.append(clean_user)
    
    return render_template('admin/pending_users.html', users=cleaned_pending, user=current_user)
@admin_bp.route('/approve-user/<int:user_id>', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Approve a pending user"""
    from models.auth_model import AuthModel
    
    print(f"DEBUG: approve_user called with user_id={user_id}")  # Debug line
    
    try:
        AuthModel.update_user_status(user_id, 'active')
        return jsonify({
            'success': True,
            'message': 'User approved successfully'
        })
    except Exception as e:
        print(f"ERROR in approve_user: {str(e)}")  # Debug line
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@admin_bp.route('/reject-user/<int:user_id>', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Reject a pending user"""
    from models.auth_model import AuthModel
    
    print(f"DEBUG: reject_user called with user_id={user_id}")  # Debug line
    
    try:
        AuthModel.update_user_status(user_id, 'rejected')
        return jsonify({
            'success': True,
            'message': 'User rejected'
        })
    except Exception as e:
        print(f"ERROR in reject_user: {str(e)}")  # Debug line
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500