"""
Service de prévision des inondations
Contient les algorithmes de prévision découplés du reste de l'application
"""

from datetime import datetime, timedelta
import statistics
from typing import List, Dict, Any

class ForecastService:
    """Service pour générer des prévisions d'inondation avec différents algorithmes"""
    
    def __init__(self):
        self.current_algorithm = 'moving_average'
        self.algorithms = {
            'simple': 'Tendance Simple',
            'moving_average': 'Moyenne Mobile (7 jours)',
            'linear_regression': 'Régression Linéaire'
        }
    
    def get_available_algorithms(self) -> Dict[str, str]:
        """Retourne la liste des algorithmes disponibles"""
        return self.algorithms
    
    def get_current_algorithm(self) -> str:
        """Retourne l'algorithme actuellement sélectionné"""
        return self.current_algorithm
    
    def set_algorithm(self, algorithm_name: str) -> None:
        """Change l'algorithme de prévision"""
        if algorithm_name not in self.algorithms:
            raise ValueError(f"Algorithme '{algorithm_name}' non disponible. Algorithmes disponibles: {list(self.algorithms.keys())}")
        self.current_algorithm = algorithm_name
    
    def generate_forecast(self, historical_data: List[Dict], hours: int = 24, algorithm_name: str = None) -> Dict[str, Any]:
        """
        Génère des prévisions basées sur les données historiques
        
        Args:
            historical_data: Liste des observations historiques
            hours: Nombre d'heures de prévision
            algorithm_name: Nom de l'algorithme à utiliser (optionnel)
        
        Returns:
            Dictionnaire contenant les prévisions et métadonnées
        """
        if algorithm_name:
            self.set_algorithm(algorithm_name)
        
        if not historical_data:
            return {
                'success': False,
                'error': 'Aucune donnée historique fournie'
            }
        
        try:
            # Convertir et nettoyer les données
            clean_data = self._clean_historical_data(historical_data)
            
            if len(clean_data) < 2:
                return {
                    'success': False,
                    'error': 'Données historiques insuffisantes pour générer des prévisions'
                }
            
            # Générer les prévisions selon l'algorithme sélectionné
            if self.current_algorithm == 'simple':
                forecast_values = self._simple_trend_forecast(clean_data, hours)
            elif self.current_algorithm == 'moving_average':
                forecast_values = self._moving_average_forecast(clean_data, hours)
            elif self.current_algorithm == 'linear_regression':
                forecast_values = self._linear_regression_forecast(clean_data, hours)
            else:
                forecast_values = self._moving_average_forecast(clean_data, hours)
            
            # Calculer les valeurs min/max basées sur les variations historiques
            min_max_data = self._calculate_min_max_bounds(clean_data, forecast_values)
            
            # Générer les timestamps de prévision
            start_time = datetime.now()
            previsions = []
            
            for i, (value, min_val, max_val) in enumerate(zip(forecast_values, min_max_data['min'], min_max_data['max'])):
                forecast_time = start_time + timedelta(hours=i+1)
                previsions.append({
                    'date_prevision': forecast_time.isoformat(),
                    'valeur_prevue': round(value, 3),
                    'valeur_min': round(min_val, 3),
                    'valeur_max': round(max_val, 3),
                    'algorithme': self.algorithms[self.current_algorithm]
                })
            
            return {
                'success': True,
                'algorithme_utilise': self.algorithms[self.current_algorithm],
                'nombre_previsions': len(previsions),
                'periode_prevision': f"{hours} heures",
                'donnees_historiques_utilisees': len(clean_data),
                'previsions': previsions
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la génération des prévisions: {str(e)}'
            }
    
    def _clean_historical_data(self, historical_data: List[Dict]) -> List[float]:
        """Nettoie et convertit les données historiques en valeurs numériques"""
        clean_values = []
        
        for obs in historical_data:
            try:
                # Essayer différents champs possibles
                value = None
                if 'resultat_obs_elab' in obs and obs['resultat_obs_elab']:
                    value = float(obs['resultat_obs_elab'])
                elif 'resultat_obs' in obs and obs['resultat_obs']:
                    value = float(obs['resultat_obs'])
                elif 'valeur' in obs and obs['valeur']:
                    value = float(obs['valeur'])
                
                if value is not None and value > 0:
                    # Conversion L/s vers m³/s si nécessaire
                    if value > 1000:  # Probablement en L/s
                        value = value / 1000.0
                    clean_values.append(value)
                    
            except (ValueError, TypeError):
                continue
        
        return clean_values
    
    def _simple_trend_forecast(self, data: List[float], hours: int) -> List[float]:
        """Algorithme de prévision par tendance simple"""
        if len(data) < 2:
            return [data[-1]] * hours
        
        # Calculer la tendance sur les dernières valeurs
        recent_data = data[-7:] if len(data) >= 7 else data
        trend = (recent_data[-1] - recent_data[0]) / len(recent_data)
        
        forecast = []
        last_value = data[-1]
        
        for i in range(hours):
            next_value = last_value + (trend * (i + 1))
            forecast.append(max(0, next_value))  # Éviter les valeurs négatives
        
        return forecast
    
    def _moving_average_forecast(self, data: List[float], hours: int) -> List[float]:
        """Algorithme de prévision par moyenne mobile"""
        window_size = min(7, len(data))
        recent_data = data[-window_size:]
        avg_value = statistics.mean(recent_data)
        
        # Calculer la variance pour ajouter une légère variation
        if len(recent_data) > 1:
            variance = statistics.stdev(recent_data)
            trend_factor = (recent_data[-1] - avg_value) / variance if variance > 0 else 0
        else:
            trend_factor = 0
        
        forecast = []
        for i in range(hours):
            # Légère décroissance de la tendance au fil du temps
            decay_factor = 0.95 ** i
            predicted_value = avg_value + (trend_factor * variance * decay_factor)
            forecast.append(max(0, predicted_value))
        
        return forecast
    
    def _linear_regression_forecast(self, data: List[float], hours: int) -> List[float]:
        """Algorithme de prévision par régression linéaire simple"""
        n = len(data)
        if n < 2:
            return [data[-1]] * hours
        
        # Régression linéaire simple: y = ax + b
        x_values = list(range(n))
        y_values = data
        
        # Calcul des coefficients
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return [y_mean] * hours
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Générer les prévisions
        forecast = []
        for i in range(hours):
            x_future = n + i
            predicted_value = slope * x_future + intercept
            forecast.append(max(0, predicted_value))
        
        return forecast
    
    def _calculate_min_max_bounds(self, historical_data: List[float], forecast_values: List[float]) -> Dict[str, List[float]]:
        """Calcule les bornes min/max basées sur les variations historiques"""
        if len(historical_data) < 2:
            return {
                'min': [v * 0.8 for v in forecast_values],
                'max': [v * 1.2 for v in forecast_values]
            }
        
        # Calculer la variabilité historique
        recent_data = historical_data[-24:] if len(historical_data) >= 24 else historical_data
        
        if len(recent_data) > 1:
            std_dev = statistics.stdev(recent_data)
            mean_value = statistics.mean(recent_data)
            
            # Coefficient de variation
            cv = std_dev / mean_value if mean_value > 0 else 0.2
        else:
            cv = 0.2  # Valeur par défaut
        
        # Appliquer la variabilité aux prévisions
        min_values = []
        max_values = []
        
        for i, forecast_val in enumerate(forecast_values):
            # Augmenter l'incertitude avec le temps
            uncertainty_factor = 1 + (i * 0.05)  # 5% d'incertitude supplémentaire par heure
            
            variation = forecast_val * cv * uncertainty_factor
            min_val = max(0, forecast_val - variation)
            max_val = forecast_val + variation
            
            min_values.append(min_val)
            max_values.append(max_val)
        
        return {
            'min': min_values,
            'max': max_values
        }

