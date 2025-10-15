import mysql.connector
from database.db_connection import connect_to_database

class MedicalModel:
    @staticmethod
    def get_medical_records(pet_id):
        """Fetch medical records data from the database based on pet_id"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        query = "SELECT * FROM medical_records WHERE pet_id = %s"
        cursor.execute(query, (pet_id,))
        medical_records = cursor.fetchall()
        
        print("Retrieved medical records:", medical_records)  # Debug
        
        cursor.close()
        mysql_connection.close()
        return medical_records
    
    @staticmethod
    def update_medical_records(pet_id, date_of_visit, medicines_or_vaccinations, diagnosis, dr_name, dr_number):
        """Update medical records using stored procedure"""
        mysql_connection = connect_to_database()
        cursor = mysql_connection.cursor()
        
        try:
            print("Calling stored procedure with parameters:")
            print("Pet ID:", pet_id)
            print("Date of Visit:", date_of_visit)
            print("Medicines or Vaccinations:", medicines_or_vaccinations)
            print("Diagnosis:", diagnosis)
            print("Doctor's Name:", dr_name)
            print("Doctor's Number:", dr_number)
            
            update_medical_records_query = """
                CALL update_medical_records(%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(update_medical_records_query, (pet_id, date_of_visit, medicines_or_vaccinations, diagnosis, dr_name, dr_number))
            mysql_connection.commit()
            return True
        except mysql.connector.Error as e:
            print("Error:", e)
            mysql_connection.rollback()
            return False
        finally:
            cursor.close()
            mysql_connection.close()