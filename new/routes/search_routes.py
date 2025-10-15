# routes/search_routes.py
from flask import Blueprint, request, jsonify, render_template
from models.search_model import SearchModel
from models.auth_decorators import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
def search_pets():
    """
    Advanced pet search endpoint
    What this does: Searches pets with multiple filters
    Why: Users need powerful search capabilities
    
    Usage: /search?search_text=golden&category=dog&min_age=1&max_age=5
    """
    try:
        # Get all search parameters
        filters = {
            'search_text': request.args.get('search_text', '').strip(),
            'category': request.args.get('category', '').strip(),
            'species': request.args.get('species', '').strip(),
            'breed': request.args.get('breed', '').strip(),
            'min_age': request.args.get('min_age'),
            'max_age': request.args.get('max_age'),
            'gender': request.args.get('gender', '').strip(),
            'vaccinated': request.args.get('vaccinated', '').strip(),
            'location': request.args.get('location', '').strip(),
            'size': request.args.get('size', '').strip(),
            'sort_by': request.args.get('sort_by', 'name'),
            'sort_order': request.args.get('sort_order', 'ASC'),
            'limit': request.args.get('limit', 20),
            'offset': request.args.get('offset', 0)
        }
        
        # Remove empty filters
        filters = {k: v for k, v in filters.items() if v}
        
        # Perform search
        search_results = SearchModel.search_pets(filters)
        
        return jsonify({
            'success': True,
            'results': search_results,
            'filters_applied': filters
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Search error: {str(e)}'
        }), 500

@search_bp.route('/search/filters', methods=['GET'])
def get_filter_options():
    """
    Get available filter options
    What this does: Returns all possible filter values
    Why: Frontend needs to populate dropdowns
    """
    try:
        filters = SearchModel.get_search_filters()
        return jsonify({
            'success': True,
            'filters': filters
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting filters: {str(e)}'
        }), 500

@search_bp.route('/search/popular', methods=['GET'])
def get_popular_searches():
    """
    Get popular/trending searches
    What this does: Shows what people are searching for most
    Why: Helps users discover popular pets
    """
    try:
        popular = SearchModel.get_popular_searches()
        return jsonify({
            'success': True,
            'popular': popular
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting popular searches: {str(e)}'
        }), 500

@search_bp.route('/pets/advanced-search', methods=['GET'])
def advanced_search_page():
    """
    Advanced search page (HTML)
    What this does: Renders the advanced search form
    Why: Users need a UI to input search criteria
    """
    # Get filter options for dropdowns
    filters = SearchModel.get_search_filters()
    popular = SearchModel.get_popular_searches()
    
    return render_template('advanced_search.html', 
                         filters=filters, 
                         popular=popular)

@search_bp.route('/pets/search-results', methods=['GET'])
def search_results_page():
    """
    Search results page (HTML)
    What this does: Shows search results in a nice format
    Why: Users want to see results in a user-friendly way
    """
    # Get search parameters from URL
    search_params = dict(request.args)
    
    # Perform search
    results = SearchModel.search_pets(search_params)
    
    return render_template('search_results.html', 
                         results=results, 
                         search_params=search_params)