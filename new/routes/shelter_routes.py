from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from models.shelter_model import ShelterModel
from models.auth_decorators import login_required, shelter_staff_required, admin_required, get_current_user

# Create blueprint with consistent naming
shelter_bp = Blueprint('shelters', __name__)

@shelter_bp.route('/api/shelters')
def get_shelters_api():
    """API endpoint to get all shelters - PUBLIC"""
    shelters = ShelterModel.get_all_shelters()
    shelters_list = [{'shelter_id': s[0], 'shelter_name': s[1]} for s in shelters]
    return {'shelters': shelters_list}

@shelter_bp.route('/shelters')
@login_required
def shelters_list():
    """Display all shelters - PROTECTED"""
    current_user = get_current_user()
    
    try:
        shelters = ShelterModel.get_all_shelters()
        # Convert tuple results to dictionaries for easier template usage
        shelters_data = []
        for shelter in shelters:
            shelters_data.append({
                'shelter_id': shelter[0],
                'shelter_name': shelter[1],
                'location': shelter[2],
                'contact_person': shelter[3],
                'contact_phone': shelter[4],
                'email': shelter[5],
                'manager_user_id': shelter[6]
            })
    except Exception as e:
        shelters_data = []
    
    return render_template('shelter/shelters.html', shelters=shelters_data, user=current_user)

@shelter_bp.route('/shelter/<int:shelter_id>')
@login_required
def shelter_detail(shelter_id):
    """Display specific shelter details - PROTECTED"""
    current_user = get_current_user()
    
    try:
        shelter = ShelterModel.get_shelter_by_id(shelter_id)
        if not shelter:
            return jsonify({'message': 'Shelter not found'}), 404
        
        # Convert tuple to dictionary
        shelter_data = {
            'shelter_id': shelter[0],
            'shelter_name': shelter[1],
            'location': shelter[2],
            'contact_person': shelter[3],
            'contact_phone': shelter[4],
            'email': shelter[5],
            'manager_user_id': shelter[6]
        }
        
        # Get pets in this shelter
        pets = ShelterModel.get_shelter_pets(shelter_id)
        pets_data = []
        for pet in pets:
            pets_data.append({
                'pet_id': pet[0],
                'pet_name': pet[1],
                'species': pet[2],
                'breed': pet[3],
                'age': pet[4],
                'adoption_status': pet[5]
            })
        
        return render_template('shelter_detail.html', 
                             shelter=shelter_data, 
                             pets=pets_data, 
                             user=current_user)
    except Exception as e:
        return jsonify({'message': f'Error loading shelter: {str(e)}'}), 500

@shelter_bp.route('/shelter_dashboard')
@shelter_staff_required
def shelter_dashboard():
    """Shelter staff dashboard - PROTECTED (Shelter Staff Only)"""
    current_user = get_current_user()
    
    try:
        current_user = get_current_user()
        print(f"✅ Current user: {current_user}")
        
        # Get shelter managed by current user
        shelter = ShelterModel.get_shelter_by_user_id(current_user['id'])
        print(f"✅ Shelter found: {shelter}")
        if not shelter:
            return jsonify({'message': 'No shelter assigned to your account'}), 404
        
        shelter_data = {
            'shelter_id': shelter[0],
            'shelter_name': shelter[1],
            'location': shelter[2],
            'contact_person': shelter[3],
            'contact_phone': shelter[4],
            'email': shelter[5],
            'manager_user_id': shelter[6]
        }
        
        # Get shelter statistics
        statistics = ShelterModel.get_shelter_statistics(shelter_data['shelter_id'])
        
        # Get pets in this shelter
        pets = ShelterModel.get_shelter_pets(shelter_data['shelter_id'])
        pets_data = []
        for pet in pets:
            pets_data.append({
                'pet_id': pet[0],
                'pet_name': pet[1],
                'species': pet[2],
                'breed': pet[3],
                'age': pet[4],
                'adoption_status': pet[5]
            })
        
        return render_template('shelter/shelter_dashboard.html',
                             shelter=shelter_data,
                             statistics=statistics,
                             pets=pets_data,
                             user=current_user)
    except Exception as e:
        print(f"💥 ERROR in shelter_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
        #return jsonify({'message': f'Error loading dashboard: {str(e)}'}), 500

@shelter_bp.route('/add_shelter', methods=['GET', 'POST'])
@admin_required
def add_shelter():
    """Add new shelter - PROTECTED (Admin Only)"""
    current_user = get_current_user()
    
    if request.method == 'POST':
        try:
            shelter_name = request.form.get('shelter_name')
            location = request.form.get('location')
            contact_person = request.form.get('contact_person')
            contact_phone = request.form.get('contact_phone')
            email = request.form.get('email')
            manager_user_id = request.form.get('manager_user_id')
            
            if not all([shelter_name, location, contact_person]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            shelter_id = ShelterModel.add_shelter(
                shelter_name, location, contact_person, 
                contact_phone, email, manager_user_id
            )
            
            if shelter_id:
                return jsonify({
                    'success': True,
                    'message': 'Shelter added successfully',
                    'shelter_id': shelter_id
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to add shelter'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error adding shelter: {str(e)}'
            }), 500
    
    # GET request - render form
    return render_template('add_shelter.html', user=current_user)

@shelter_bp.route('/edit_shelter/<int:shelter_id>', methods=['GET', 'POST'])
@login_required
def edit_shelter(shelter_id):
    """Edit shelter information - PROTECTED (Admin or Shelter Manager)"""
    current_user = get_current_user()
    
    # Check if user can manage this shelter
    can_manage = ShelterModel.can_user_manage_shelter(
        current_user['id'], current_user['role'], shelter_id
    )
    
    if not can_manage:
        return jsonify({'message': 'Access denied'}), 403
    
    if request.method == 'POST':
        try:
            shelter_name = request.form.get('shelter_name')
            location = request.form.get('location')
            contact_person = request.form.get('contact_person')
            contact_phone = request.form.get('contact_phone')
            email = request.form.get('email')
            
            success = ShelterModel.update_shelter(
                shelter_id, shelter_name, location, 
                contact_person, contact_phone, email
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Shelter updated successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No changes made or failed to update'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error updating shelter: {str(e)}'
            }), 500
    
    # GET request - load shelter data and render form
    try:
        shelter = ShelterModel.get_shelter_by_id(shelter_id)
        if not shelter:
            return jsonify({'message': 'Shelter not found'}), 404
        
        shelter_data = {
            'shelter_id': shelter[0],
            'shelter_name': shelter[1],
            'location': shelter[2],
            'contact_person': shelter[3],
            'contact_phone': shelter[4],
            'email': shelter[5],
            'manager_user_id': shelter[6]
        }
        
        return render_template('edit_shelter.html', 
                             shelter=shelter_data, 
                             user=current_user)
    except Exception as e:
        return jsonify({'message': f'Error loading shelter: {str(e)}'}), 500

@shelter_bp.route('/delete_shelter/<int:shelter_id>', methods=['POST'])
@admin_required
def delete_shelter(shelter_id):
    """Delete shelter - PROTECTED (Admin Only)"""
    try:
        success, message = ShelterModel.delete_shelter(shelter_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting shelter: {str(e)}'
        }), 500

@shelter_bp.route('/api/shelter/<int:shelter_id>/statistics')
@login_required
def get_shelter_statistics(shelter_id):
    """API endpoint to get shelter statistics - PROTECTED"""
    current_user = get_current_user()
    
    # Check if user can access this shelter's data
    can_manage = ShelterModel.can_user_manage_shelter(
        current_user['id'], current_user['role'], shelter_id
    )
    
    if not can_manage and current_user['role'] != 'admin':
        return jsonify({'message': 'Access denied'}), 403
    
    try:
        statistics = ShelterModel.get_shelter_statistics(shelter_id)
        if statistics:
            return jsonify({'success': True, 'statistics': statistics})
        else:
            return jsonify({'success': False, 'message': 'Failed to get statistics'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@shelter_bp.route('/api/shelter/<int:shelter_id>/pets')
@login_required
def get_shelter_pets_api(shelter_id):
    """API endpoint to get pets in shelter - PROTECTED"""
    current_user = get_current_user()
    
    # Check if user can access this shelter's data
    can_manage = ShelterModel.can_user_manage_shelter(
        current_user['id'], current_user['role'], shelter_id
    )
    
    if not can_manage and current_user['role'] != 'admin':
        return jsonify({'message': 'Access denied'}), 403
    
    try:
        pets = ShelterModel.get_shelter_pets(shelter_id)
        pets_list = []
        for pet in pets:
            pets_list.append({
                'pet_id': pet[0],
                'pet_name': pet[1],
                'species': pet[2],
                'breed': pet[3],
                'age': pet[4],
                'adoption_status': pet[5]
            })
        return jsonify({'success': True, 'pets': pets_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@shelter_bp.route('/my_shelter')
@shelter_staff_required
def my_shelter():
    """View and manage own shelter - PROTECTED (Shelter Staff Only)"""
    current_user = get_current_user()
    
    try:
        shelter = ShelterModel.get_shelter_by_user_id(current_user['id'])
        if not shelter:
            return jsonify({'message': 'No shelter assigned to your account'}), 404
        
        shelter_data = {
            'shelter_id': shelter[0],
            'shelter_name': shelter[1],
            'location': shelter[2],
            'contact_person': shelter[3],
            'contact_phone': shelter[4],
            'email': shelter[5],
            'manager_user_id': shelter[6]
        }
        
        return render_template('my_shelter.html', 
                             shelter=shelter_data, 
                             user=current_user)
    except Exception as e:
        return jsonify({'message': f'Error loading shelter: {str(e)}'}), 500
    
    