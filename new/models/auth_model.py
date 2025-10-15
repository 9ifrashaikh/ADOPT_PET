import bcrypt
import mysql.connector  
from datetime import datetime
from database.db_connection import connect_to_database as get_db_connection
from config import Config

class AuthModel:
    @staticmethod
    def hash_password(password):
        """
        Hash a password using bcrypt
        What this does: Takes a plain text password and makes it unreadable
        Why: We never store plain text passwords in the database for security
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=Config.BCRYPT_LOG_ROUNDS))
    
    @staticmethod
    def verify_password(password, hashed_password):
        """
        Verify a password against its hash
        What this does: Checks if the entered password matches the stored hash
        Why: This is how we verify login without storing actual passwords
        """
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
    
    @staticmethod
    def create_user_and_link(email, password, role, first_name, last_name, phone=None, address=None, shelter_id=None, status='active'):
        """
        Create a new user account AND link to appropriate existing table
        What this does: Creates user account + adds to role-specific table
        Why: This connects the new auth system to your existing tables
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Hash the password before storing
            hashed_password = AuthModel.hash_password(password)
            
            # Insert new user into users table
            cursor.execute('''
                INSERT INTO users (email, password_hash, role, first_name, last_name, phone, address, created_at, is_active, shelter_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (email, hashed_password, role, first_name, last_name, phone, address, datetime.now(), True, shelter_id, status))
            
            user_id = cursor.lastrowid
            
            # SMART LINKING: Add to role-specific table based on role
            if role == 'adopter':
                # Link to existing adopters table
                cursor.execute('''
                    INSERT INTO adopters (user_id, adopter_name, mail, cont_no, address)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, f"{first_name} {last_name}", email, phone, address))
                
            elif role == 'shelter_staff':
                # Update shelter table to link this user as manager
                if shelter_id:
                    cursor.execute('''
                        UPDATE shelter SET manager_user_id = %s WHERE shelter_id = %s
                    ''', (user_id, shelter_id))
                
            # Admin doesn't need additional table entry
            
            conn.commit()
            conn.close()
            
            return user_id
        except mysql.connector.IntegrityError as e:
            print(f"Integrity error: {e}")
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """
        Find a user by their email address with role-specific data
        What this does: Gets user info + their specific role data
        Why: We need both auth info and role-specific details
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user from users table
            cursor.execute('''
                SELECT id, email, password_hash, role, first_name, last_name, 
                       phone, address, is_active, created_at, shelter_id
                FROM users WHERE email = %s AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            
            if user:
                # Get role-specific additional data
                if user['role'] == 'adopter':
                    cursor.execute('''
                        SELECT adoption_id, pet_id FROM adopters 
                        WHERE user_id = %s
                    ''', (user['id'],))
                    adopter_data = cursor.fetchone()
                    if adopter_data:
                        user['adopter_id'] = adopter_data['adoption_id']
                        user['adopted_pet_id'] = adopter_data.get('pet_id')
                
                elif user['role'] == 'shelter_staff' and user['shelter_id']:
                    cursor.execute('''
                        SELECT shelter_name, location, contact_person 
                        FROM shelter WHERE shelter_id = %s
                    ''', (user['shelter_id'],))
                    shelter_data = cursor.fetchone()
                    if shelter_data:
                        user['shelter_name'] = shelter_data['shelter_name']
                        user['shelter_location'] = shelter_data['location']
            
            conn.close()
            return user
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        Find a user by their ID with role-specific data
        What this does: Looks up a user by their unique ID number
        Why: JWT tokens contain user ID, so we need to look up user info
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT id, email, role, first_name, last_name, phone, address, 
                       is_active, created_at, shelter_id
                FROM users WHERE id = %s AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            
            if user:
                # Get role-specific data
                if user['role'] == 'adopter':
                    cursor.execute('''
                        SELECT adoption_id FROM adopters WHERE user_id = %s
                    ''', (user_id,))
                    adopter_data = cursor.fetchone()
                    if adopter_data:
                        user['adopter_id'] = adopter_data['adoption_id']
                
                elif user['role'] == 'shelter_staff' and user['shelter_id']:
                    cursor.execute('''
                        SELECT shelter_name FROM shelter WHERE shelter_id = %s
                    ''', (user['shelter_id'],))
                    shelter_data = cursor.fetchone()
                    if shelter_data:
                        user['shelter_name'] = shelter_data['shelter_name']
            
            conn.close()
            return user
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    def update_user_login(user_id):
        """
        Update last login time
        What this does: Records when a user last logged in
        Why: Useful for security monitoring and user activity tracking
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_login = %s WHERE id = %s
            ''', (datetime.now(), user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating user login: {e}")
            return False
    
    @staticmethod
    def get_user_pets(user_id, role):
        """
        Get pets based on user role
        What this does: Returns pets that the user can manage
        Why: Shelter staff only see their shelter's pets, adopters see available pets
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            if role == 'admin':
                # Admins see all pets
                cursor.execute('''
                    SELECT p.*, s.shelter_name 
                    FROM pets p
                    LEFT JOIN shelter s ON p.shelter_id = s.shelter_id
                ''')
            
            elif role == 'shelter_staff':
                # Shelter staff only see their shelter's pets
                user = AuthModel.get_user_by_id(user_id)
                if user and user['shelter_id']:
                    cursor.execute('''
                        SELECT p.*, s.shelter_name 
                        FROM pets p
                        LEFT JOIN shelter s ON p.shelter_id = s.shelter_id
                        WHERE p.shelter_id = %s
                    ''', (user['shelter_id'],))
            
            elif role == 'adopter':
                # Adopters see all available pets
                cursor.execute('''
                    SELECT p.*, s.shelter_name 
                    FROM pets p
                    LEFT JOIN shelter s ON p.shelter_id = s.shelter_id
                    WHERE p.adoption_status = 'notadopted'
                ''')
            
            pets = cursor.fetchall()
            conn.close()
            return pets
            
        except Exception as e:
            print(f"Error getting user pets: {e}")
            return []
    
    @staticmethod
    def get_users_by_status(status):
        """
        Get all users with a specific status
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM users WHERE status = %s ORDER BY created_at DESC"
        cursor.execute(query, (status,))
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return users
    
    @staticmethod
    def update_user_status(user_id, status):
        """
        Update user account status (pending, active, rejected)
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET status = %s
                WHERE id = %s
            """, (status, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating user status: {e}")
            raise e
        finally:
            conn.close()