from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models.auth_model import AuthModel
#from models.admin_model import AdminModel
from models.shelter_model import ShelterModel
from config import Config
from models.auth_decorators import login_required, get_current_user

auth_bp = Blueprint('auth', __name__)

def get_redirect_url_by_role(role):
    """
    Determine redirect URL based on user role
    """
    print(f"🔍 get_redirect_url_by_role called with role: {role}")
    
    try:
        role_redirects = {
            'admin': url_for('admin.new_page'),
            'shelter_staff': url_for('shelters.shelter_dashboard'),
           'adopter': url_for('adopters.adopter_dashboard'),
            #'default': url_for('main.home')
        }
        
        #redirect_url = role_redirects.get(role, role_redirects['default'])
        redirect_url = role_redirects.get(role, url_for('main.home'))
        print(f"✅ Redirect URL generated: {redirect_url}")
        return redirect_url
        
    except Exception as e:
        print(f"💥 ERROR in get_redirect_url_by_role:")
        print(f"   Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    try:
        data = request.get_json() or request.form
        
        # Get form data
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'adopter')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        phone = data.get('phone')
        address = data.get('address')
        shelter_id = data.get('shelter_id') if role == 'shelter_staff' else None
        
        # Validation
        if not all([email, password, first_name, last_name]):
            return jsonify({'message': 'Missing required fields'}), 400
        
        # IMPORTANT: Prevent admin registration
        if role == 'admin':
            return jsonify({'message': 'Invalid role selection. Admin accounts must be created manually.'}), 403
        
        # Validate role
        if role not in ['adopter', 'shelter_staff']:
            return jsonify({'message': 'Invalid role selected'}), 400
        
        # Set user status based on role
        if role == 'shelter_staff':
            user_status = 'pending'
            if not shelter_id:
                return jsonify({'message': 'Shelter selection is required for shelter staff'}), 400
            
            # Verify shelter exists
            shelter = ShelterModel.get_shelter_by_id(shelter_id)
            if not shelter:
                return jsonify({'message': 'Invalid shelter selected'}), 400
            
            # Check if the shelter already has a manager
            shelter_has_manager = ShelterModel.shelter_has_manager(shelter_id)
            if shelter_has_manager:
                return jsonify({'message': 'This shelter already has a manager'}), 409
        else:
            user_status = 'active'
        
        # Check if user already exists
        existing_user = AuthModel.get_user_by_email(email)
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 409
        
        # Create new user
        user_id = AuthModel.create_user_and_link(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            shelter_id=shelter_id,
            status=user_status
        )
        
        if user_id:
            if role == 'shelter_staff':
                message = 'Registration submitted! Admin will review your request within 24 hours.'
            else:
                message = 'User created successfully'
            
            return jsonify({
                'message': message,
                'user_id': user_id,
                'role': role
            }), 201
        else:
            return jsonify({'message': 'Failed to create user'}), 500
    
    except Exception as e:
        print(f"REGISTRATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Registration error: {str(e)}'}), 500
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        # Debug logging
        print("=" * 50)
        print("LOGIN REQUEST RECEIVED")
        print("Content-Type:", request.content_type)
        print("Is JSON:", request.is_json)
        
        data = request.get_json() or request.form
        email = data.get('email')
        password = data.get('password')
        
        print(f"Email: {email}")
        print(f"Password received: {'Yes' if password else 'No'}")
        
        if not email or not password:
            print("VALIDATION FAILED")
            return jsonify({'message': 'Email and password required'}), 400
        
        # Find user
        user = AuthModel.get_user_by_email(email)
        if not user:
            print("USER NOT FOUND")
            return jsonify({'message': 'Invalid credentials'}), 401
        
        print(f"User found: {user['email']}")
        if user.get('status') == 'pending':
            print("USER STATUS: PENDING APPROVAL")
            return jsonify({
        'message': 'Your account is pending admin approval. Please wait for verification.'
    }), 403
        if user.get('status') == 'rejected':
           print("USER STATUS: REJECTED")
           return jsonify({
        'message': 'Your account request was rejected. Contact admin@petadopt.com for details.'
    }), 403
        if user.get('status') == 'suspended':
          print("USER STATUS: SUSPENDED")
          return jsonify({
        'message': 'Your account has been suspended. Contact support.'
    }), 403
        
        
        # Verify password
        if not AuthModel.verify_password(password, user['password_hash']):
            print("PASSWORD INCORRECT")
            return jsonify({'message': 'Invalid credentials'}), 401
        
        print("PASSWORD VERIFIED")
        
        # Update last login
        AuthModel.update_user_login(user['id'])
        
        # Create tokens
        access_token = create_access_token(identity=str(user['id']))
        refresh_token = create_refresh_token(identity=str(user['id']))
        
        print("TOKENS CREATED")
        
        # Prepare response data
        response_data = {
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'name': f"{user['first_name']} {user['last_name']}"
            },
            'redirect_url': get_redirect_url_by_role(user['role'])
        }
        
        print("RETURNING SUCCESS RESPONSE")
        print("=" * 50)
        
        # For form submissions, redirect directly
        if request.is_json:
            return jsonify(response_data), 200
        else:
            flash('Login successful!', 'success')
            return redirect(get_redirect_url_by_role(user['role']))
        
    except Exception as e:
        print(f"LOGIN ERROR: {str(e)}")
        print("=" * 50)
        return jsonify({'message': f'Login error: {str(e)}'}), 500

@auth_bp.route('/test-jwt', methods=['GET'])
@login_required
def test_jwt():
    current_user_id = get_jwt_identity()
    user = get_current_user()
    return jsonify({
        'message': 'JWT is working!',
        'user_id': current_user_id,
        'user_info': user
    })

@auth_bp.route('/adhere', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page (legacy session-based for admin panel)
    What this does: Provides session-based authentication for admin users
    Why: Some admin features may still rely on session authentication
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = AdminModel.verify_admin_credentials(username, password)
        
        if admin:
            session['logged_in'] = True
            session['admin_user'] = username
            session['user_role'] = 'admin'
            return redirect(url_for('admin.new_page'))
        else:
            return render_template('admin_login.html', error="Invalid username or password")
    
    return render_template('admin_login.html')

@auth_bp.route('/admin')
def admin_page():
    """
    Admin page with session authentication check
    What this does: Protects admin routes using session authentication
    Why: Maintains compatibility with existing admin functionality
    """
    if not session.get('logged_in'):
        return redirect(url_for('auth.admin_login'))
    return render_template('admin_dashboard.html')

@auth_bp.route('/create-admin-secret', methods=['POST'])
def create_admin_secret():
    """
    TEMPORARY endpoint to create admin user
    DELETE THIS AFTER CREATING YOUR ADMIN!
    """
    # Add a secret key for security
    secret = request.get_json().get('secret')
    if secret != "YOUR_SECRET_KEY_HERE":  # Change this!
        return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    user_id = AuthModel.create_user_and_link(
        email=data.get('email'),
        password=data.get('password'),  # Will be hashed by the model
        role='admin',
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        phone=data.get('phone'),
        address=data.get('address'),
        shelter_id=None
    )
    
    if user_id:
        return jsonify({'message': 'Admin created', 'user_id': user_id}), 201
    return jsonify({'message': 'Failed'}), 500

@auth_bp.route('/logout')
def logout():
    """
    Logout route for session-based authentication
    What this does: Clears session data and redirects to login
    Why: Users need a way to securely log out
    """
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    What this does: Gives users a new access token when theirs expires
    Why: Users don't have to login again every hour
    """
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': new_access_token})

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me_endpoint():
    """
    Helper function to get current logged-in user
    """
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = AuthModel.get_user_by_id(current_user_id)
        
        if user:
            # Clean the user data
            user_clean = {}
            for key, value in user.items():
                if key in ('password_hash', 'password'):
                    continue
                elif hasattr(value, 'isoformat'):
                    user_clean[key] = value.isoformat()
                elif isinstance(value, bytes):
                    continue
                else:
                    user_clean[key] = value
            return user_clean
        return None
    except Exception as e:
        print(f"Get current user error: {e}")
        return None
@auth_bp.route('/test-roles', methods=['GET'])
@jwt_required()
def test_roles():
    """
    TEST ROUTE: Check what role the current user has
    What this does: Shows user info for testing
    Why: To verify the role system is working
    """
    try:
        current_user_id = get_jwt_identity()
        user = AuthModel.get_user_by_id(current_user_id)
        
        return jsonify({
            'message': f'Hello {user["first_name"]}!',
            'your_role': user['role'],
            'you_can_access': {
                'admin_features': user['role'] == 'admin',
                'shelter_features': user['role'] in ['admin', 'shelter_staff'],
                'adopter_features': user['role'] == 'adopter'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@auth_bp.route('/validate-token', methods=['POST'])
@jwt_required()
def validate_token():
    """
    Validate JWT token
    What this does: Checks if the current token is valid
    Why: Frontend can verify authentication status
    """
    try:
        current_user_id = get_jwt_identity()
        user = AuthModel.get_user_by_id(current_user_id)
        
        if user:
            return jsonify({
                'valid': True,
                'user_id': current_user_id,
                'role': user['role']
            }), 200
        else:
            return jsonify({'valid': False, 'message': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Token validation error: {str(e)}'}), 500