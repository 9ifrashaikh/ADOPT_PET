from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Home page redirect"""
    return render_template('landing.html')

@main_bp.route('/index')
def landing():
    """Main landing page"""
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/history')
def history():
    """History page"""
    return render_template('history.html')

@main_bp.route('/team')
def team():
    """Team page"""
    return render_template('team.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')