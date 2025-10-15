import mysql.connector
from database.db_connection import connect_to_database

class AdopterModel:
    
    @staticmethod
    def get_all_adopters():
        """Fetch all adopter data from the database"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM adopters"
        cursor.execute(query)
        adopter_data = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return adopter_data
    
    @staticmethod
    def get_adopter_applications(user_id):
        """Get adoption applications for specific adopter - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = """
        SELECT ap.*, p.name as pet_name, p.species, p.breed, p.image,
               a.adopter_name, a.mail, a.cont_no, a.address
        FROM adoption_procedure ap 
        JOIN pets p ON ap.pet_id = p.pet_id 
        JOIN adopters a ON ap.adopter_id = a.adoption_id 
        WHERE a.user_id = %s
        ORDER BY ap.adoption_date DESC
        """
        cursor.execute(query, (user_id,))
        applications = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return applications
    
    @staticmethod
    def get_adopter_by_user_id(user_id):
        """Get adopter record by user ID - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM adopters WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        adopter = cursor.fetchone()
        
        cursor.close()
        mysql_connection.close()
        return adopter
    
    @staticmethod
    def get_applications_by_shelter(shelter_id):
        """Get adoption applications for specific shelter - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = """
        SELECT ap.*, p.name as pet_name, p.species, p.breed,
               a.adopter_name, a.mail, a.cont_no, a.address
        FROM adoption_procedure ap 
        JOIN pets p ON ap.pet_id = p.pet_id 
        JOIN adopters a ON ap.adopter_id = a.adoption_id 
        WHERE p.shelter_id = %s
        ORDER BY ap.adoption_date DESC
        """
        cursor.execute(query, (shelter_id,))
        applications = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return applications
    
    @staticmethod
    def verify_adopter_credentials(name, email):
        """Verify adopter login credentials"""
        connection = connect_to_database()
        cursor = connection.cursor()
        
        query = "SELECT * FROM adopters WHERE adopter_name = %s AND mail = %s"
        cursor.execute(query, (name, email))
        adopter = cursor.fetchone()
        
        cursor.close()
        connection.close()
        return adopter
    
    @staticmethod
    def add_adopter(adopter_name, mail, phone, address, pet_id, user_id=None):
        """Add new adopter and create adoption procedure - UPDATED METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            # Insert form data into the adopters table
            adopter_query = "INSERT INTO adopters (adopter_name, mail, cont_no, address, pet_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(adopter_query, (adopter_name, mail, phone, address, pet_id, user_id))
            adopter_id = cursor.lastrowid
            
            # Insert data into the adoption_procedure table
            adoption_query = "INSERT INTO adoption_procedure (pet_id, adopter_id, adoption_date) VALUES (%s, %s, CURDATE())"
            cursor.execute(adoption_query, (pet_id, adopter_id))
            
            mysql_connection.commit()
            return adopter_id
        except mysql.connector.Error as e:
            print("Error:", e)
            mysql_connection.rollback()
            return None
        finally:
            cursor.close()
            mysql_connection.close()
    
    @staticmethod
    def update_application_status(application_id, status):
        """Update adoption application status - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            # Add status column if it doesn't exist (you might need to add this to your DB)
            update_query = "UPDATE adoption_procedure SET status = %s WHERE adoption_procedure_id = %s"
            cursor.execute(update_query, (status, application_id))
            mysql_connection.commit()
            return True
        except mysql.connector.Error as e:
            print("Error:", e)
            mysql_connection.rollback()
            return False
        finally:
            cursor.close()
            mysql_connection.close()
            # Add this method to models/adopter_model.py
def add_adopter_with_user_link(user_id, adopter_name, mail, phone, address, pet_id):
    # Link adopter record to authenticated user
    cursor.execute('''
        INSERT INTO adopters (user_id, adopter_name, mail, cont_no, address, pet_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (user_id, adopter_name, mail, phone, address, pet_id))
    
    @staticmethod
    def can_user_manage_application(user_id, role, application_id):
        """Check if user can manage specific application - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        if role == 'admin':
            cursor.close()
            mysql_connection.close()
            return True
        elif role == 'shelter_staff':
            # Check if application is for a pet in user's shelter
            query = """
            SELECT ap.adoption_procedure_id 
            FROM adoption_procedure ap 
            JOIN pets p ON ap.pet_id = p.pet_id 
            JOIN users u ON p.shelter_id = u.shelter_id 
            WHERE ap.adoption_procedure_id = %s AND u.id = %s
            """
            cursor.execute(query, (application_id, user_id))
            result = cursor.fetchone()
            cursor.close()
            mysql_connection.close()
            return result is not None
        elif role == 'adopter':
            # Check if this is the adopter's own application
            query = """
            SELECT ap.adoption_procedure_id 
            FROM adoption_procedure ap 
            JOIN adopters a ON ap.adopter_id = a.adoption_id 
            WHERE ap.adoption_procedure_id = %s AND a.user_id = %s
            """
            cursor.execute(query, (application_id, user_id))
            result = cursor.fetchone()
            cursor.close()
            mysql_connection.close()
            return result is not None
        
        cursor.close()
        mysql_connection.close()
        return False