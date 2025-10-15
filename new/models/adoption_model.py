import mysql.connector
from datetime import datetime
from database.db_connection import connect_to_database as get_db_connection

class AdoptionModel:
    @staticmethod
    def create_adoption_application(user_id, pet_id, application_data):
        """
        Create new adoption application with status tracking
        What this does: Creates a formal adoption application
        Why: We need proper application workflow, not instant adoption
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO adoption_applications 
                (user_id, pet_id, applicant_name, email, phone, address, 
                 reason_for_adoption, experience_with_pets, living_situation,
                 status, application_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id, pet_id,
                application_data['applicant_name'],
                application_data['email'],
                application_data['phone'],
                application_data['address'],
                application_data.get('reason_for_adoption', ''),
                application_data.get('experience_with_pets', ''),
                application_data.get('living_situation', ''),
                'pending',  # Initial status
                datetime.now(),
                datetime.now()
            ))
            
            application_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            
            return application_id
            
        except Exception as e:
            print(f"Error creating application: {e}")
            return None
    
    @staticmethod
    def get_application_by_id(application_id):
        """
        Get specific application by ID (ADDED - WAS MISSING)
        What this does: Gets single application for notifications
        Why: We need this for sending status notifications
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = '''
                SELECT aa.*, p.name as pet_name, p.species, p.breed, p.age,
                       u.first_name, u.last_name, u.email, u.phone,
                       s.shelter_name
                FROM adoption_applications aa
                JOIN pets p ON aa.pet_id = p.pet_id
                JOIN users u ON aa.user_id = u.id
                JOIN shelter s ON p.shelter_id = s.shelter_id
                WHERE aa.application_id = %s
            '''
            
            cursor.execute(query, (application_id,))
            application = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return application
            
        except Exception as e:
            print(f"Error getting application by ID: {e}")
            return None
    
    @staticmethod
    def get_applications_by_status(status=None, shelter_id=None):
        """
        Get applications filtered by status and shelter
        What this does: Gets applications for shelter staff to review
        Why: Shelter staff need to see pending applications
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = '''
                SELECT aa.*, p.name as pet_name, p.species, p.breed, p.age,
                       u.first_name, u.last_name, s.shelter_name,
                       aa.application_id, aa.status, aa.application_date
                FROM adoption_applications aa
                JOIN pets p ON aa.pet_id = p.pet_id
                JOIN users u ON aa.user_id = u.id
                JOIN shelter s ON p.shelter_id = s.shelter_id
            '''
            
            conditions = []
            params = []
            
            if status:
                conditions.append('aa.status = %s')
                params.append(status)
            
            if shelter_id:
                conditions.append('p.shelter_id = %s')
                params.append(shelter_id)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY aa.application_date DESC'
            
            cursor.execute(query, params)
            applications = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return applications
            
        except Exception as e:
            print(f"Error getting applications: {e}")
            return []
    
    @staticmethod
    def update_application_status(application_id, new_status, reviewer_id, review_notes=None):
        """
        Update application status with reviewer tracking
        What this does: Shelter staff approve/reject applications
        Why: We need application workflow management
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # FIXED: Use correct column name 'application_id' not 'id'
            cursor.execute('''
                UPDATE adoption_applications 
                SET status = %s, reviewed_by = %s, review_notes = %s, 
                    reviewed_at = %s, updated_at = %s
                WHERE application_id = %s
            ''', (new_status, reviewer_id, review_notes, datetime.now(), datetime.now(), application_id))
            
            # If approved, update pet status to adopted
            if new_status == 'approved':
                cursor.execute('''
                    SELECT pet_id FROM adoption_applications WHERE application_id = %s
                ''', (application_id,))
                result = cursor.fetchone()
                if result:
                    pet_id = result[0]
                    
                    cursor.execute('''
                        UPDATE pets SET adoption_status = 'adopted' WHERE pet_id = %s
                    ''', (pet_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating application: {e}")
            return False
    
    @staticmethod
    def get_user_applications(user_id):
        """
        Get all applications by a specific user
        What this does: Shows adopter their application history
        Why: Users want to track their adoption applications
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT aa.*, p.name as pet_name, p.species, p.breed, p.image,
                       s.shelter_name, s.contact_person as shelter_contact,
                       aa.application_id, aa.status, aa.application_date
                FROM adoption_applications aa
                JOIN pets p ON aa.pet_id = p.pet_id
                JOIN shelter s ON p.shelter_id = s.shelter_id
                WHERE aa.user_id = %s
                ORDER BY aa.application_date DESC
            ''', (user_id,))
            
            applications = cursor.fetchall()
            cursor.close()
            conn.close()
            return applications
            
        except Exception as e:
            print(f"Error getting user applications: {e}")
            return []
    
    @staticmethod
    def get_adoption_statistics():
        """
        Get adoption statistics for analytics
        What this does: Provides adoption metrics
        Why: Shelters need adoption performance data
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get counts by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM adoption_applications
                GROUP BY status
            ''')
            status_counts = cursor.fetchall()
            
            # Get recent adoptions
            cursor.execute('''
                SELECT COUNT(*) as recent_adoptions
                FROM adoption_applications
                WHERE status = 'approved' 
                AND reviewed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ''')
            recent_adoptions = cursor.fetchone()['recent_adoptions']
            
            cursor.close()
            conn.close()
            
            return {
                'status_breakdown': status_counts,
                'recent_adoptions_30_days': recent_adoptions
            }
            
        except Exception as e:
            print(f"Error getting adoption statistics: {e}")
            return {}