# test_app.py - Create this file to test authentication
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt
from datetime import timedelta

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = 'your-test-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Initialize JWT
jwt = JWTManager(app)

# Test user storage (in memory for testing)
test_users = {}

@app.route('/test-register', methods=['POST'])
def test_register():
    """Simple test registration"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'adopter')
        
        if email in test_users:
            return jsonify({'message': 'User already exists'}), 409
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Store user
        test_users[email] = {
            'email': email,
            'password_hash': hashed_password,
            'role': role,
            'first_name': data.get('first_name', 'Test'),
            'last_name': data.get('last_name', 'User')
        }
        
        return jsonify({
            'message': 'User created successfully',
            'email': email,
            'role': role
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/test-login', methods=['POST'])
def test_login():
    """Simple test login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if email not in test_users:
            return jsonify({'message': 'User not found'}), 404
        
        user = test_users[email]
        
        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            # Create token
            access_token = create_access_token(identity=email)
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'role': user['role']
            }), 200
        else:
            return jsonify({'message': 'Invalid password'}), 401
            
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/test-protected', methods=['GET'])
@jwt_required()
def test_protected():
    """Test protected route"""
    current_user_email = get_jwt_identity()
    user = test_users.get(current_user_email)
    
    return jsonify({
        'message': 'Access granted!',
        'user': current_user_email,
        'role': user['role'] if user else 'unknown'
    }), 200

@app.route('/test', methods=['GET'])
def test_basic():
    """Basic test route"""
    return jsonify({'message': 'Flask is working!'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)