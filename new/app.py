from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from config import Config

# Import your route blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.pet_routes import pet_bp
from routes.adopter_routes import adopter_bp
from routes.main_routes import main_bp
from routes.search_routes import search_bp
from routes.adoption_routes import adoption_bp
from routes.shelter_routes import shelter_bp

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize JWT with this app (MOVED INSIDE create_app)
    jwt = JWTManager(app)
    
    # JWT Error handlers (MOVED INSIDE create_app)
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token is required'}, 401
    
    # Debug route to see all available routes
    @app.route('/debug-routes', methods=['GET'])
    def debug_routes():
        """Debug route to see all registered routes"""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),  # Remove HEAD/OPTIONS for clarity
                'url': str(rule)
            })
        return jsonify({
            'total_routes': len(routes),
            'routes': sorted(routes, key=lambda x: x['url'])
        })
    
    # Debug route to check JWT configuration
    @app.route('/debug-config', methods=['GET'])
    def debug_config():
        """Debug route to check JWT configuration"""
        return jsonify({
            'JWT_SECRET_KEY_LENGTH': len(app.config.get('JWT_SECRET_KEY', '')),
            'JWT_SECRET_KEY_SET': bool(app.config.get('JWT_SECRET_KEY')),
            'JWT_ACCESS_TOKEN_EXPIRES': str(app.config.get('JWT_ACCESS_TOKEN_EXPIRES')),
            'SECRET_KEY_LENGTH': len(app.config.get('SECRET_KEY', '')),
            'DEBUG_MODE': app.debug
        })
    
    # Register blueprints (route groups)
    try:
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ auth_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering auth_bp: {e}")
    
    try:
        app.register_blueprint(admin_bp, url_prefix='/admin')
        print("✅ admin_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering admin_bp: {e}")
    
    try:
        app.register_blueprint(pet_bp, url_prefix='/pets')
        print("✅ pet_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering pet_bp: {e}")
    
    try:
        app.register_blueprint(adopter_bp, url_prefix='/adopter')
        print("✅ adopter_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering adopter_bp: {e}")
    
    try:
        app.register_blueprint(shelter_bp)
        print("✅ shelter_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering shelter_bp: {e}")
    
    try:
        app.register_blueprint(main_bp)
        print("✅ main_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering main_bp: {e}")
    
    try:
        app.register_blueprint(search_bp, url_prefix='/api')
        print("✅ search_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering search_bp: {e}")
    
    try:
        app.register_blueprint(adoption_bp, url_prefix='/api/adoptions')
        print("✅ adoption_bp registered successfully")
    except Exception as e:
        print(f"❌ Error registering adoption_bp: {e}")
        print("❌ Make sure routes/adoption_routes.py exists and has adoption_bp defined")

    print(f"\n🚀 Flask app created successfully!")
    print(f"📊 Total blueprints registered: 7")
    print(f"🔧 Debug routes available:")
    print(f"   - GET /debug-routes (see all routes)")
    print(f"   - GET /debug-config (see JWT config)")
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"\n🌟 Starting Flask development server...")
    print(f"🔗 Access your app at: http://localhost:5000")
    print(f"🐛 Debug routes:")
    print(f"   - http://localhost:5000/debug-routes")
    print(f"   - http://localhost:5000/debug-config")
    print(f"   - http://localhost:5000/auth/test-jwt")
    app.run(debug=True)