from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from models.auth_model import AuthModel
import traceback

def login_required(f):
    """
    Basic login requirement - any logged in user can access
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()  # Automatically checks cookies if configured
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Login required error: {e}")
            return jsonify({'message': 'Login required', 'error': str(e)}), 401
    return decorated_function

def admin_required(f):
    """
    Admin-only access decorator
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            print("=== ADMIN REQUIRED DEBUG ===")
            print("Authorization header:", request.headers.get('Authorization'))
            print("Cookies present:", list(request.cookies.keys()))
            print("authToken cookie:", request.cookies.get('authToken', 'NOT FOUND')[:30] if request.cookies.get('authToken') else 'NOT FOUND')
            
            verify_jwt_in_request()  # Checks both headers and cookies
            print("✅ JWT verification passed!")
            
            current_user_id = get_jwt_identity()
            print("JWT Identity:", current_user_id)
            
            # Get role from JWT claims first
            claims = get_jwt()
            user_role = claims.get('role')
            print("Role from JWT claims:", user_role)
            
            if user_role == 'admin':
                print("✅ Admin access granted (from JWT claims)!")
                return f(*args, **kwargs)
            
            # Fallback: check database
            user = AuthModel.get_user_by_id(current_user_id)
            print("User from DB:", user)
            
            if user and user['role'] == 'admin':
                print("✅ Admin access granted (from DB)!")
                return f(*args, **kwargs)
            else:
                print(f"❌ Access denied - role is: {user_role or user.get('role') if user else 'No user'}")
                return jsonify({'message': 'Admin access required'}), 403
                
        except Exception as e:
            print(f"❌ Admin required error: {e}")
            print("Full traceback:", traceback.format_exc())
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
    return decorated_function

def shelter_staff_required(f):
    """
    Shelter staff access decorator
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            print("=== SHELTER STAFF REQUIRED DEBUG ===")
            print("Authorization header:", request.headers.get('Authorization'))
            print("Cookies present:", list(request.cookies.keys()))
            
            verify_jwt_in_request()
            print("✅ JWT verification passed!")
            
            current_user_id = get_jwt_identity()
            print("JWT Identity:", current_user_id)
            
            # Get role from JWT claims first
            claims = get_jwt()
            user_role = claims.get('role')
            print("Role from JWT claims:", user_role)
            
            if user_role in ['shelter_staff', 'admin']:
                print("✅ Shelter staff access granted!")
                return f(*args, **kwargs)
            
            # Fallback: check database
            user = AuthModel.get_user_by_id(current_user_id)
            print("User from DB:", user)
            
            if user and user['role'] in ['shelter_staff', 'admin']:
                print("✅ Shelter staff access granted (from DB)!")
                return f(*args, **kwargs)
            else:
                print(f"❌ Access denied - role is: {user_role}")
                return jsonify({'message': 'Shelter staff access required'}), 403
                
        except Exception as e:
            print(f"❌ Shelter staff required error: {e}")
            print("Full traceback:", traceback.format_exc())
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
    return decorated_function

def adopter_required(f):
    """
    Adopter access decorator - WITH DETAILED DEBUGGING
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            print("=== ADOPTER REQUIRED DEBUG START ===")
            print("Authorization header:", request.headers.get('Authorization'))
            print("Cookies present:", list(request.cookies.keys()))
            
            verify_jwt_in_request()
            print("✅ JWT verification passed!")
            
            current_user_id = get_jwt_identity()
            print("JWT Identity (user_id):", current_user_id)
            
            # Get role from JWT claims first
            claims = get_jwt()
            user_role = claims.get('role')
            print("Role from JWT claims:", user_role)
            
            if user_role == 'adopter':
                print("✅ Access granted for adopter!")
                return f(*args, **kwargs)
            
            # Fallback: check database
            user = AuthModel.get_user_by_id(current_user_id)
            print("User from database:", user)
            
            if user and user['role'] == 'adopter':
                print("✅ Access granted for adopter (from DB)!")
                return f(*args, **kwargs)
            else:
                print(f"❌ Access denied - user role is: {user_role or user.get('role') if user else 'No user found'}")
                return jsonify({'message': 'Adopter access required'}), 403
                
        except Exception as e:
            print(f"❌ Adopter required error: {e}")
            print("Full traceback:", traceback.format_exc())
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
    return decorated_function

def role_required(allowed_roles):
    """
    Flexible role requirement decorator
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                
                # Get role from JWT claims first
                claims = get_jwt()
                user_role = claims.get('role')
                
                if user_role in allowed_roles:
                    return f(*args, **kwargs)
                
                # Fallback: check database
                current_user_id = get_jwt_identity()
                user = AuthModel.get_user_by_id(current_user_id)
                
                if user and user['role'] in allowed_roles:
                    return f(*args, **kwargs)
                else:
                    return jsonify({'message': f'Access denied. Required roles: {allowed_roles}'}), 403
            except Exception as e:
                return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
        return decorated_function
    return decorator

def get_current_user():
    """
    Helper function to get current logged-in user
    """
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        return AuthModel.get_user_by_id(current_user_id)
    except Exception as e:
        print(f"Get current user error: {e}")
        return None