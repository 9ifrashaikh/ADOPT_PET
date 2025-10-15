import mysql.connector
from database.db_connection import connect_to_database

class ShelterModel:
    @staticmethod
    def get_all_shelters():
        """Fetch shelter data from the database"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM shelter"
        cursor.execute(query)
        shelters = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return shelters
    
    @staticmethod
    def get_shelter_by_user_id(user_id):
        """Get shelter managed by specific user"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM shelter WHERE manager_user_id = %s"
        cursor.execute(query, (user_id,))
        shelter = cursor.fetchone()
        
        cursor.close()
        mysql_connection.close()
        return shelter
    
    @staticmethod
    def get_shelter_by_id(shelter_id):
        """Get shelter by ID"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM shelter WHERE shelter_id = %s"
        cursor.execute(query, (shelter_id,))
        shelter = cursor.fetchone()
        
        cursor.close()
        mysql_connection.close()
        return shelter
    
    @staticmethod
    def shelter_has_manager(shelter_id):
        """
        Check if shelter already has a manager assigned
        Returns True if manager exists, False otherwise
        """
        try:
            conn = connect_to_database()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT manager_user_id 
                FROM shelter 
                WHERE shelter_id = %s AND manager_user_id IS NOT NULL
            ''', (shelter_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result is not None
        except Exception as e:
            print(f"Error checking shelter manager: {e}")
            return False
    
    @staticmethod
    def get_shelter_pets(shelter_id):
        """Get all pets in specific shelter"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM pets WHERE shelter_id = %s"
        cursor.execute(query, (shelter_id,))
        pets = cursor.fetchall()
        
        cursor.close()
        mysql_connection.close()
        return pets
    
    @staticmethod
    def get_shelter_statistics(shelter_id):
        """Get statistics for specific shelter"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            # Total pets in shelter
            cursor.execute("SELECT COUNT(*) as total_pets FROM pets WHERE shelter_id = %s", (shelter_id,))
            result = cursor.fetchone()
            total_pets = result[0] if result else 0
            
            # Adopted pets from shelter
            cursor.execute("SELECT COUNT(*) as adopted_pets FROM pets WHERE shelter_id = %s AND adoption_status = 'Adopted'", (shelter_id,))
            result = cursor.fetchone()
            adopted_pets = result[0] if result else 0
            
            # Available pets in shelter
            cursor.execute("SELECT COUNT(*) as available_pets FROM pets WHERE shelter_id = %s AND adoption_status = 'Not Adopted'", (shelter_id,))
            result = cursor.fetchone()
            available_pets = result[0] if result else 0
            
            # Pending applications for shelter pets
            cursor.execute("""
                SELECT COUNT(*) as pending_applications 
                FROM adoption_procedure ap 
                JOIN pets p ON ap.pet_id = p.pet_id 
                WHERE p.shelter_id = %s AND (ap.status IS NULL OR ap.status = 'pending')
            """, (shelter_id,))
            result = cursor.fetchone()
            pending_applications = result[0] if result else 0
            
            cursor.close()
            mysql_connection.close()
            
            return {
                'total_pets': total_pets,
                'adopted_pets': adopted_pets,
                'available_pets': available_pets,
                'pending_applications': pending_applications
            }
        except mysql.connector.Error as e:
            print(f"Error in get_shelter_statistics: {e}")
            import traceback
            traceback.print_exc()
            cursor.close()
            mysql_connection.close()
            return None
    
    @staticmethod
    def add_shelter(shelter_name, location, contact_person, contact_phone=None, email=None, manager_user_id=None):
        """Add new shelter"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            insert_query = """
            INSERT INTO shelter (shelter_name, location, contact_person, contact_phone, email, manager_user_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (shelter_name, location, contact_person, contact_phone, email, manager_user_id))
            mysql_connection.commit()
            shelter_id = cursor.lastrowid
            return shelter_id
        except mysql.connector.Error as e:
            print(f"Error adding shelter: {e}")
            mysql_connection.rollback()
            return None
        finally:
            cursor.close()
            mysql_connection.close()
    
    @staticmethod
    def update_shelter(shelter_id, shelter_name=None, location=None, contact_person=None, contact_phone=None, email=None):
        """Update shelter information"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            # Build dynamic update query
            update_fields = []
            values = []
            
            if shelter_name:
                update_fields.append("shelter_name = %s")
                values.append(shelter_name)
            if location:
                update_fields.append("location = %s")
                values.append(location)
            if contact_person:
                update_fields.append("contact_person = %s")
                values.append(contact_person)
            if contact_phone:
                update_fields.append("contact_phone = %s")
                values.append(contact_phone)
            if email:
                update_fields.append("email = %s")
                values.append(email)
            
            if update_fields:
                values.append(shelter_id)
                update_query = f"UPDATE shelter SET {', '.join(update_fields)} WHERE shelter_id = %s"
                cursor.execute(update_query, values)
                mysql_connection.commit()
                return True
            return False
        except mysql.connector.Error as e:
            print(f"Error updating shelter: {e}")
            mysql_connection.rollback()
            return False
        finally:
            cursor.close()
            mysql_connection.close()
    
    @staticmethod
    def can_user_manage_shelter(user_id, role, shelter_id):
        """Check if user can manage specific shelter"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        if role == 'admin':
            cursor.close()
            mysql_connection.close()
            return True
        elif role == 'shelter_staff':
            # Check if user manages this shelter
            query = "SELECT shelter_id FROM shelter WHERE shelter_id = %s AND manager_user_id = %s"
            cursor.execute(query, (shelter_id, user_id))
            result = cursor.fetchone()
            cursor.close()
            mysql_connection.close()
            return result is not None
        
        cursor.close()
        mysql_connection.close()
        return False
    
    @staticmethod
    def delete_shelter(shelter_id):
        """Delete shelter (admin only)"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            # First check if shelter has pets
            cursor.execute("SELECT COUNT(*) FROM pets WHERE shelter_id = %s", (shelter_id,))
            result = cursor.fetchone()
            pet_count = result[0] if result else 0
            
            if pet_count > 0:
                cursor.close()
                mysql_connection.close()
                return False, "Cannot delete shelter with existing pets"
            
            # Delete shelter
            delete_query = "DELETE FROM shelter WHERE shelter_id = %s"
            cursor.execute(delete_query, (shelter_id,))
            mysql_connection.commit()
            cursor.close()
            mysql_connection.close()
            return True, "Shelter deleted successfully"
        except mysql.connector.Error as e:
            print(f"Error deleting shelter: {e}")
            mysql_connection.rollback()
            cursor.close()
            mysql_connection.close()
            return False, f"Error deleting shelter: {str(e)}"