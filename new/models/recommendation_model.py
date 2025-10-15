import mysql.connector
from database.db_connection import connect_to_database as get_db_connection

class RecommendationModel:
    @staticmethod
    def get_user_preferences(user_id):
        """
        Analyze user preferences from their application history
        What this does: Learns what types of pets user likes
        Why: AI recommendations based on user behavior
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user's application history to understand preferences
            cursor.execute('''
                SELECT p.species, p.breed, p.age, p.gender, p.category
                FROM adoption_applications aa
                JOIN pets p ON aa.pet_id = p.pet_id
                WHERE aa.user_id = %s AND aa.status IN ('pending', 'approved')
            ''', (user_id,))
            
            history = cursor.fetchall()
            conn.close()
            
            if not history:
                return None
            
            # Simple preference analysis
            preferences = {
                'species': {},
                'breeds': {},
                'age_ranges': {'young': 0, 'adult': 0, 'senior': 0},
                'genders': {}
            }
            
            for app in history:
                # Count species preferences
                species = app['species']
                preferences['species'][species] = preferences['species'].get(species, 0) + 1
                
                # Count breed preferences
                breed = app['breed']
                preferences['breeds'][breed] = preferences['breeds'].get(breed, 0) + 1
                
                # Age range preferences
                age = app['age']
                if age <= 2:
                    preferences['age_ranges']['young'] += 1
                elif age <= 7:
                    preferences['age_ranges']['adult'] += 1
                else:
                    preferences['age_ranges']['senior'] += 1
                
                # Gender preferences
                gender = app['gender']
                preferences['genders'][gender] = preferences['genders'].get(gender, 0) + 1
            
            return preferences
            
        except Exception as e:
            print(f"Error analyzing preferences: {e}")
            return None
    
    @staticmethod
    def get_recommended_pets(user_id, limit=10):
        """
        AI-powered pet recommendations
        What this does: Suggests pets based on user preferences and behavior
        Why: Personalized experience increases adoption chances
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user preferences
            preferences = RecommendationModel.get_user_preferences(user_id)
            
            if not preferences:
                # New user - show popular/recent pets
                cursor.execute('''
                    SELECT p.*, s.shelter_name, 
                           COUNT(aa.pet_id) as application_count
                    FROM pets p
                    LEFT JOIN shelter s ON p.shelter_id = s.shelter_id
                    LEFT JOIN adoption_applications aa ON p.pet_id = aa.pet_id
                    WHERE p.adoption_status = 'notadopted'
                    GROUP BY p.pet_id
                    ORDER BY application_count DESC, p.created_at DESC
                    LIMIT %s
                ''', (limit,))
                
                recommendations = cursor.fetchall()
                conn.close()
                
                return {
                    'type': 'popular',
                    'message': 'Popular pets that others are interested in',
                    'pets': recommendations
                }
            
            # Build recommendation query based on preferences
            query = '''
                SELECT p.*, s.shelter_name, 
                       (CASE 
            '''
            
            score_conditions = []
            params = []
            
            # Species scoring
            for species, count in preferences['species'].items():
                score_conditions.append(f"WHEN p.species = %s THEN {count * 10}")
                params.append(species)
            
            # Breed scoring
            for breed, count in preferences['breeds'].items():
                score_conditions.append(f"WHEN p.breed = %s THEN {count * 5}")
                params.append(breed)
            
            # Age range scoring
            if preferences['age_ranges']['young'] > 0:
                score_conditions.append(f"WHEN p.age <= 2 THEN {preferences['age_ranges']['young'] * 3}")
            if preferences['age_ranges']['adult'] > 0:
                score_conditions.append(f"WHEN p.age BETWEEN 3 AND 7 THEN {preferences['age_ranges']['adult'] * 3}")
            if preferences['age_ranges']['senior'] > 0:
                score_conditions.append(f"WHEN p.age > 7 THEN {preferences['age_ranges']['senior'] * 3}")
            
            query += ' + '.join(score_conditions) if score_conditions else '0'
            query += '''
                       ELSE 1 END) as recommendation_score
                FROM pets p
                LEFT JOIN shelter s ON p.shelter_id = s.shelter_id
                WHERE p.adoption_status = 'notadopted'
                  AND p.pet_id NOT IN (
                      SELECT pet_id FROM adoption_applications 
                      WHERE user_id = %s AND status IN ('pending', 'approved')
                  )
                ORDER BY recommendation_score DESC, p.created_at DESC
                LIMIT %s
            '''
            
            params.extend([user_id, limit])
            
            cursor.execute(query, params)
            recommendations = cursor.fetchall()
            conn.close()
            
            return {
                'type': 'personalized',
                'message': 'Recommended based on your preferences',
                'pets': recommendations,
                'preferences_used': preferences
            }
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return {'type': 'error', 'pets': [], 'message': str(e)}