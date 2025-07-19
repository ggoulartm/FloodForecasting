from flask import Blueprint, jsonify, request
import requests
from datetime import datetime, timedelta
import sys
import os

# Ajouter le chemin du service
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.forecast_service import ForecastService

flood_data_bp = Blueprint('flood_data', __name__)

# Configuration de l'API Hub'Eau
HUBEAU_BASE_URL = "https://hubeau.eaufrance.fr/api/v2/hydrometrie"

# Instance du service de prévision
forecast_service = ForecastService()

@flood_data_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de santé de l'API"""
    return jsonify({
        'success': True,
        'message': 'API de prévision des inondations opérationnelle',
        'timestamp': datetime.now().isoformat(),
        'algorithme_actuel': forecast_service.get_current_algorithm()
    })

@flood_data_bp.route('/sites', methods=['GET'])
def get_sites():
    """Récupère la liste des sites hydrométriques pour l'Isère et la Savoie avec recherche"""
    try:
        # Paramètres de recherche
        search_term = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        # Paramètres pour l'API Hub'Eau
        params = {
            'code_departement': ['38', '73'],  # Isère et Savoie
            'format': 'json',
            'size': 500  # Récupérer plus de sites pour permettre la recherche
        }
        
        # Appel à l'API Hub'Eau
        response = requests.get(f"{HUBEAU_BASE_URL}/referentiel/sites", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        sites = data.get('data', [])
        
        # Filtrage par terme de recherche si fourni
        if search_term:
            search_lower = search_term.lower()
            filtered_sites = []
            for site in sites:
                # Recherche dans le nom du site, la commune, et le code
                if (search_lower in site.get('libelle_site', '').lower() or
                    search_lower in site.get('libelle_commune_site', '').lower() or
                    search_lower in site.get('code_site', '').lower()):
                    filtered_sites.append(site)
            sites = filtered_sites
        
        # Limiter le nombre de résultats
        sites = sites[:limit]
        
        return jsonify({
            'success': True,
            'count': len(sites),
            'total_available': data.get('count', 0),
            'search_term': search_term,
            'sites': sites
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération des sites: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }), 500

@flood_data_bp.route('/sites/search/<search_term>', methods=['GET'])
def search_sites(search_term):
    """Endpoint dédié à la recherche de sites"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Recherche dans tous les départements si nécessaire
        all_departments = request.args.get('all_departments', 'false').lower() == 'true'
        
        params = {
            'format': 'json',
            'size': 500
        }
        
        if not all_departments:
            params['code_departement'] = ['38', '73']
        
        # Appel à l'API Hub'Eau
        response = requests.get(f"{HUBEAU_BASE_URL}/referentiel/sites", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        sites = data.get('data', [])
        
        # Filtrage par terme de recherche
        search_lower = search_term.lower()
        filtered_sites = []
        for site in sites:
            # Recherche étendue avec vérification des valeurs None
            site_name = site.get('libelle_site') or ''
            commune_name = site.get('libelle_commune_site') or ''
            site_code = site.get('code_site') or ''
            cours_eau = site.get('libelle_cours_eau') or ''
            
            if (search_lower in site_name.lower() or
                search_lower in commune_name.lower() or
                search_lower in site_code.lower() or
                search_lower in cours_eau.lower()):
                filtered_sites.append(site)
        
        # Trier par pertinence (sites avec le terme dans le nom en premier)
        def relevance_score(site):
            score = 0
            site_name = (site.get('libelle_site') or '').lower()
            cours_eau = (site.get('libelle_cours_eau') or '').lower()
            commune = (site.get('libelle_commune_site') or '').lower()
            
            if search_lower in site_name:
                if site_name.startswith(search_lower):
                    score += 100
                else:
                    score += 50
            if search_lower in cours_eau:
                score += 25
            if search_lower in commune:
                score += 10
            return score
        
        filtered_sites.sort(key=relevance_score, reverse=True)
        filtered_sites = filtered_sites[:limit]
        
        return jsonify({
            'success': True,
            'count': len(filtered_sites),
            'search_term': search_term,
            'sites': filtered_sites
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la recherche: {str(e)}'
        }), 500

@flood_data_bp.route('/historical-data/<code_site>', methods=['GET'])
def get_historical_data(code_site):
    """Récupère les données historiques pour un site donné"""
    try:
        # Calculer la date de début (30 jours avant aujourd'hui)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Paramètres pour l'API Hub'Eau
        params = {
            'code_entite': code_site,
            'grandeur_hydro': 'QmJ',  # Débit moyen journalier
            'date_debut_obs_elab': start_date.strftime('%Y-%m-%d'),
            'date_fin_obs_elab': end_date.strftime('%Y-%m-%d'),
            'format': 'json',
            'size': 100
        }
        
        # Appel à l'API Hub'Eau
        response = requests.get(f"{HUBEAU_BASE_URL}/obs_elab", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        observations = data.get('data', [])
        
        # Convertir les données historiques en m³/s
        for obs in observations:
            if 'resultat_obs_elab' in obs and obs['resultat_obs_elab']:
                try:
                    value_ls = float(obs['resultat_obs_elab'])
                    obs['resultat_obs_elab'] = round(value_ls / 1000.0, 3)  # Conversion L/s vers m³/s
                    obs['unite'] = 'm³/s'
                except (ValueError, TypeError):
                    pass
        
        return jsonify({
            'success': True,
            'count': len(observations),
            'observations': observations,
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération des données historiques: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }), 500

@flood_data_bp.route('/real-time-data/<code_site>', methods=['GET'])
def get_real_time_data(code_site):
    """Récupère les données en temps réel pour un site donné"""
    try:
        # Calculer la date de début (dernières 24 heures)
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        
        # Paramètres pour l'API Hub'Eau
        params = {
            'code_entite': code_site,
            'date_debut_obs': start_date.strftime('%Y-%m-%d'),
            'date_fin_obs': end_date.strftime('%Y-%m-%d'),
            'format': 'json',
            'size': 50
        }
        
        # Appel à l'API Hub'Eau
        response = requests.get(f"{HUBEAU_BASE_URL}/observations_tr", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        observations = data.get('data', [])
        
        # Convertir les données temps réel en m³/s
        for obs in observations:
            if 'resultat_obs' in obs and obs['resultat_obs']:
                try:
                    value_ls = float(obs['resultat_obs'])
                    obs['resultat_obs'] = round(value_ls / 1000.0, 3)  # Conversion L/s vers m³/s
                    obs['unite'] = 'm³/s'
                except (ValueError, TypeError):
                    pass
        
        return jsonify({
            'success': True,
            'count': len(observations),
            'observations': observations
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération des données temps réel: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }), 500

@flood_data_bp.route('/forecast/<code_site>', methods=['GET'])
def get_forecast(code_site):
    """Génère des prévisions pour un site donné avec algorithme configurable"""
    try:
        # Paramètres de la requête
        algorithm_name = request.args.get('algorithm', 'simple')
        hours = int(request.args.get('hours', 24))
        
        # Récupérer les données historiques pour la prévision
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            'code_entite': code_site,
            'grandeur_hydro': 'QmJ',
            'date_debut_obs_elab': start_date.strftime('%Y-%m-%d'),
            'date_fin_obs_elab': end_date.strftime('%Y-%m-%d'),
            'format': 'json',
            'size': 100
        }
        
        response = requests.get(f"{HUBEAU_BASE_URL}/obs_elab", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        historical_data = data.get('data', [])
        
        if not historical_data:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée historique disponible pour ce site'
            }), 404
        
        # Générer les prévisions avec le service découplé
        forecast_result = forecast_service.generate_forecast(
            historical_data, 
            hours=hours, 
            algorithm_name=algorithm_name
        )
        
        return jsonify(forecast_result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Paramètre invalide: {str(e)}'
        }), 400
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération des données: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la génération des prévisions: {str(e)}'
        }), 500

@flood_data_bp.route('/algorithms', methods=['GET'])
def get_algorithms():
    """Retourne la liste des algorithmes de prévision disponibles"""
    try:
        algorithms = forecast_service.get_available_algorithms()
        current = forecast_service.get_current_algorithm()
        
        return jsonify({
            'success': True,
            'current_algorithm': current,
            'available_algorithms': algorithms
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }), 500

@flood_data_bp.route('/algorithms/<algorithm_name>', methods=['POST'])
def set_algorithm(algorithm_name):
    """Change l'algorithme de prévision par défaut"""
    try:
        forecast_service.set_algorithm(algorithm_name)
        
        return jsonify({
            'success': True,
            'message': f'Algorithme changé vers: {forecast_service.get_current_algorithm()}',
            'current_algorithm': forecast_service.get_current_algorithm()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }), 500

