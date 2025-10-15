from flask import Blueprint, render_template, request
from models.pet_model import PetModel
from models.medical_model import MedicalModel
from models.shelter_model import ShelterModel

pet_bp = Blueprint('pets', __name__)

@pet_bp.route('/our_pets')
def our_pets():
    """Display pets page with optional category filter"""
    category = request.args.get('category')
    
    if category:
        pets_data = PetModel.get_pets_by_category(category)
    else:
        pets_data = PetModel.get_all_pets()
    
    return render_template('OurPets.html', pets=pets_data, selected_category=category)

@pet_bp.route('/pet/<int:pet_id>')
def pet_info(pet_id):
    """Individual pet information page"""
    pet_data = PetModel.get_pet_info_from_view(pet_id)
    return render_template('pet_info.html', pet=pet_data)

@pet_bp.route('/medical_records/<int:pet_id>')
def medical_records(pet_id):
    """Medical records page for a pet"""
    medical_records_data = MedicalModel.get_medical_records(pet_id)
    return render_template('medical_records.html', pet_id=pet_id, medical_records=medical_records_data)

@pet_bp.route('/shelter')
def shelter():
    """Shelter information page"""
    shelters = ShelterModel.get_all_shelters()
    return render_template('shelter.html', shelters=shelters)

# Individual pet pages
@pet_bp.route('/Chanda')
def chanda():
    return render_template('chanda.html')

@pet_bp.route('/Anu')
def anu():
    return render_template('Anu.html')

@pet_bp.route('/Ganesha')
def ganesha():
    return render_template('Ganesha.html')

@pet_bp.route('/Gopi')
def gopi():
    return render_template('Gopi.html')

@pet_bp.route('/Gulab')
def gulab():
    return render_template('Gulab.html')
@pet_bp.route('/tara')
def tara():
    return render_template('tara.html')