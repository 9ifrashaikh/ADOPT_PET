# models/search_model.py
import mysql.connector
from database.db_connection import connect_to_database as get_db_connection

class SearchModel:
    @staticmethod
    def search_pets(filters):
        """
        Advanced pet search with multiple filters
        What this does: Searches pets based on multiple criteria
        Why: Users want to find specific types of pets quickly
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Base query with JOINs for complete pet info
            base_query = '''
                SELECT DISTINCT p.*, s.shelter_name, s.location as shelter_location,
                       m.vaccinations, m.diagnosis, m.dr_name
                FROM pets p
                LEFT JOIN shelter s ON p.shelter_id = s.shelter_id
                LEFT JOIN medical_records m ON p.pet_id = m.pet_id
                WHERE p.adoption_status = 'notadopted'
            '''
            
            conditions = []
            params = []
            
            # TEXT SEARCH (breed, name, species)
            if filters.get('search_text'):
                search_text = f"%{filters['search_text']}%"
                conditions.append('''
                    (p.name LIKE %s OR p.breed LIKE %s OR p.species LIKE %s 
                     OR s.shelter_name LIKE %s)
                ''')
                params.extend([search_text, search_text, search_text, search_text])
            
            # CATEGORY FILTER
            if filters.get('category'):
                conditions.append('p.category = %s')
                params.append(filters['category'])
            
            # SPECIES FILTER
            if filters.get('species'):
                conditions.append('p.species = %s')
                params.append(filters['species'])
            
            # BREED FILTER
            if filters.get('breed'):
                conditions.append('p.breed LIKE %s')
                params.append(f"%{filters['breed']}%")
            
            # AGE RANGE FILTER
            if filters.get('min_age'):
                conditions.append('p.age >= %s')
                params.append(int(filters['min_age']))
            
            if filters.get('max_age'):
                conditions.append('p.age <= %s')
                params.append(int(filters['max_age']))
            
            # GENDER FILTER
            if filters.get('gender'):
                conditions.append('p.gender = %s')
                params.append(filters['gender'])
            
            # VACCINATION STATUS FILTER
            if filters.get('vaccinated'):
                if filters['vaccinated'].lower() == 'true':
                    conditions.append('m.vaccinations IS NOT NULL AND m.vaccinations != ""')
                else:
                    conditions.append('(m.vaccinations IS NULL OR m.vaccinations = "")')
            
            # SHELTER LOCATION FILTER
            if filters.get('location'):
                conditions.append('s.location LIKE %s')
                params.append(f"%{filters['location']}%")
            
            # SIZE FILTER (if you have size field)
            if filters.get('size'):
                conditions.append('p.size = %s')
                params.append(filters['size'])
            
            # Build final query
            if conditions:
                query = base_query + ' AND ' + ' AND '.join(conditions)
            else:
                query = base_query
            
            # SORTING
            sort_by = filters.get('sort_by', 'name')
            sort_order = filters.get('sort_order', 'ASC')
            
            valid_sort_fields = ['name', 'age', 'breed', 'species', 'created_at']
            if sort_by in valid_sort_fields:
                query += f' ORDER BY p.{sort_by} {sort_order}'
            
            # PAGINATION
            limit = min(int(filters.get('limit', 20)), 100)  # Max 100 results
            offset = int(filters.get('offset', 0))
            query += f' LIMIT {limit} OFFSET {offset}'
            
            print(f"Search Query: {query}")  # Debug
            print(f"Params: {params}")  # Debug
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Get total count for pagination
            count_query = base_query.replace('SELECT DISTINCT p.*, s.shelter_name, s.location as shelter_location, m.vaccinations, m.diagnosis, m.dr_name', 'SELECT COUNT(DISTINCT p.pet_id)')
            if conditions:
                count_query += ' AND ' + ' AND '.join(conditions)
            
            cursor.execute(count_query, params[:-2] if conditions else [])  # Remove LIMIT/OFFSET params
            total_count = cursor.fetchone()['COUNT(DISTINCT p.pet_id)']
            
            conn.close()
            
            return {
                'pets': results,
                'total_count': total_count,
                'current_page': offset // limit + 1,
                'total_pages': (total_count + limit - 1) // limit
            }
            
        except Exception as e:
            print(f"Search error: {e}")
            return {'pets': [], 'total_count': 0, 'current_page': 1, 'total_pages': 1}
    
    @staticmethod
    def get_search_filters():
        """
        Get available filter options from database
        What this does: Returns all unique values for filter dropdowns
        Why: Frontend needs to know what filter options are available
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            filters = {}
            
            # Get unique categories
            cursor.execute('SELECT DISTINCT category FROM pets WHERE category IS NOT NULL ORDER BY category')
            filters['categories'] = [row['category'] for row in cursor.fetchall()]
            
            # Get unique species
            cursor.execute('SELECT DISTINCT species FROM pets WHERE species IS NOT NULL ORDER BY species')
            filters['species'] = [row['species'] for row in cursor.fetchall()]
            
            # Get unique breeds
            cursor.execute('SELECT DISTINCT breed FROM pets WHERE breed IS NOT NULL ORDER BY breed LIMIT 50')
            filters['breeds'] = [row['breed'] for row in cursor.fetchall()]
            
            # Get shelter locations
            cursor.execute('SELECT DISTINCT location FROM shelter WHERE location IS NOT NULL ORDER BY location')
            filters['locations'] = [row['location'] for row in cursor.fetchall()]
            
            # Age range (get min/max)
            cursor.execute('SELECT MIN(age) as min_age, MAX(age) as max_age FROM pets')
            age_range = cursor.fetchone()
            filters['age_range'] = {
                'min': age_range['min_age'] or 0,
                'max': age_range['max_age'] or 15
            }
            
            conn.close()
            return filters
            
        except Exception as e:
            print(f"Error getting filters: {e}")
            return {}
    
    @staticmethod
    def get_popular_searches():
        """
        Get popular/trending searches
        What this does: Returns commonly searched breeds and categories
        Why: Helps users discover popular pets
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Most common breeds
            cursor.execute('''
                SELECT breed, COUNT(*) as count 
                FROM pets 
                WHERE adoption_status = 'notadopted' 
                GROUP BY breed 
                ORDER BY count DESC 
                LIMIT 8
            ''')
            popular_breeds = cursor.fetchall()
            
            # Most common categories
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM pets 
                WHERE adoption_status = 'notadopted' 
                GROUP BY category 
                ORDER BY count DESC
            ''')
            popular_categories = cursor.fetchall()
            
            conn.close()
            
            return {
                'popular_breeds': popular_breeds,
                'popular_categories': popular_categories
            }
            
        except Exception as e:
            print(f"Error getting popular searches: {e}")
            return {'popular_breeds': [], 'popular_categories': []}