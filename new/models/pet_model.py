import mysql.connector
from database.db_connection import connect_to_database

class PetModel:
    @staticmethod
    def get_all_pets():
        """Fetch all pets data from the database"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM pets"
        cursor.execute(query)
        pets = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return pets
    
    @staticmethod
    def get_pets_by_user_role(user_id, role):
        """Get pets filtered by user role - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        if role == 'admin':
            query = "SELECT * FROM pets"
            cursor.execute(query)
        elif role == 'shelter_staff':
            # Get user's shelter_id first
            cursor.execute("SELECT shelter_id FROM users WHERE id = %s", (user_id,))
            user_shelter = cursor.fetchone()
            if user_shelter:
                query = "SELECT * FROM pets WHERE shelter_id = %s"
                cursor.execute(query, (user_shelter[0],))
            else:
                cursor.close()
                mysql_connection.close()
                return []
        elif role == 'adopter':
            query = "SELECT * FROM pets WHERE adoption_status = 'Not Adopted'"
            cursor.execute(query)
        else:
            cursor.close()
            mysql_connection.close()
            return []
        
        pets = cursor.fetchall()
        cursor.close()
        mysql_connection.close()
        return pets
    
    @staticmethod
    def get_pet_by_id(pet_id):
        """Fetch specific pet by ID"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM pets WHERE pet_id = %s"
        cursor.execute(query, (pet_id,))
        pets = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return pets
    
    @staticmethod
    def can_user_manage_pet(user_id, role, pet_id):
        """Check if user can manage specific pet - NEW METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        if role == 'admin':
            cursor.close()
            mysql_connection.close()
            return True
        elif role == 'shelter_staff':
            # Check if pet belongs to user's shelter
            query = """
            SELECT p.pet_id 
            FROM pets p 
            JOIN users u ON p.shelter_id = u.shelter_id 
            WHERE p.pet_id = %s AND u.id = %s
            """
            cursor.execute(query, (pet_id, user_id))
            result = cursor.fetchone()
            cursor.close()
            mysql_connection.close()
            return result is not None
        
        cursor.close()
        mysql_connection.close()
        return False
    
    @staticmethod
    def get_pets_by_category(category):
        """Fetch pets data filtered by category"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM pets WHERE category = %s"
        cursor.execute(query, (category,))
        pets = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return pets
    
    @staticmethod
    def get_pet_info_from_view(pet_id):
        """Fetch pet data from view"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM pet_info_view WHERE pet_id = %s"
        cursor.execute(query, (pet_id,))
        pet_data = cursor.fetchone()
        
        cursor.close()
        mysql_connection.close()
        return pet_data
    
    @staticmethod
    def add_pet(category, name, species, gender, age, breed, image, shelter_id=None, created_by=None):
        """Add new pet to database with user tracking - UPDATED METHOD"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            insert_query = "INSERT INTO pets (category, name, species, gender, age, breed, image, shelter_id, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (category, name, species, gender, age, breed, image, shelter_id, created_by))
            mysql_connection.commit()
            pet_id = cursor.lastrowid
            return pet_id
        except mysql.connector.Error as e:
            print("Error:", e)
            mysql_connection.rollback()
            return None
        finally:
            cursor.close()
            mysql_connection.close()
    
    @staticmethod
    def delete_pet(pet_id):
        """Delete pet and associated medical records"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            # Delete medical records first
            delete_medical_query = "DELETE FROM medical_records WHERE pet_id = %s"
            cursor.execute(delete_medical_query, (pet_id,))
            mysql_connection.commit()
            
            # Then delete the pet
            delete_query = "DELETE FROM pets WHERE pet_id = %s"
            cursor.execute(delete_query, (pet_id,))
            mysql_connection.commit()
            return True
        except mysql.connector.Error as e:
            print("Error:", e)
            mysql_connection.rollback()
            return False
        finally:
            cursor.close()
            mysql_connection.close()
    
    @staticmethod
    def update_adoption_status(pet_id, status='Adopted'):
        """Update pet adoption status"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            update_query = "UPDATE pets SET adoption_status = %s WHERE pet_id = %s"
            cursor.execute(update_query, (status, pet_id))
            mysql_connection.commit()
            return True
        except mysql.connector.Error as e:
            print("Error:", e)
            mysql_connection.rollback()
            return False
        finally:
            cursor.close()
            mysql_connection.close()
    
    @staticmethod
    def get_not_adopted_pets():
        """Get pets that are not adopted"""
        connection = connect_to_database()
        cursor = connection.cursor()
        
        try:
            query = """
            SELECT p.pet_id, p.name AS pet_name, p.species, p.gender
            FROM pets p
            LEFT JOIN adoption_procedure ap ON p.pet_id = ap.pet_id
            WHERE p.adoption_status = 'Not Adopted' AND ap.pet_id IS NULL
            """
            cursor.execute(query)
            not_adopted_pets = cursor.fetchall()
            return not_adopted_pets
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def get_adopted_pets():
        """Get adopted pets from view"""
        connection = connect_to_database()
        cursor = connection.cursor()
        
        cursor.execute("SELECT * FROM adopted_pets_view")
        adopted_pets = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return adopted_pets