import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './App.css'

const API_BASE_URL = '/api/flood'

function App() {
  const [sites, setSites] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredSites, setFilteredSites] = useState([])
  const [historicalData, setHistoricalData] = useState([])
  const [realTimeData, setRealTimeData] = useState([])
  const [forecastData, setForecastData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [algorithms, setAlgorithms] = useState({})
  const [currentAlgorithm, setCurrentAlgorithm] = useState('')
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('moving_average')

  // Charger les algorithmes disponibles
  useEffect(() => {
    const fetchAlgorithms = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/algorithms`)
        const data = await response.json()
        if (data.success) {
          setAlgorithms(data.available_algorithms)
          setCurrentAlgorithm(data.current_algorithm)
        }
      } catch (error) {
        console.error('Erreur lors du chargement des algorithmes:', error)
      }
    }
    fetchAlgorithms()
  }, [])

  // Recherche de sites
  useEffect(() => {
    const searchSites = async () => {
      if (searchTerm.length < 2) {
        setFilteredSites([])
        return
      }

      setLoading(true)
      try {
        const response = await fetch(`${API_BASE_URL}/sites/search/${encodeURIComponent(searchTerm)}`)
        const data = await response.json()
        if (data.success) {
          setFilteredSites(data.sites)
        } else {
          setError(data.error)
        }
      } catch (error) {
        setError('Erreur lors de la recherche de sites')
        console.error('Erreur:', error)
      } finally {
        setLoading(false)
      }
    }

    const timeoutId = setTimeout(searchSites, 300) // Debounce
    return () => clearTimeout(timeoutId)
  }, [searchTerm])

  const handleSiteSelect = async (site) => {
    setSelectedSite(site)
    setError(null)
    setLoading(true)

    try {
      // Charger les données historiques
      const historicalResponse = await fetch(`${API_BASE_URL}/historical-data/${site.code_site}`)
      const historicalResult = await historicalResponse.json()
      
      if (historicalResult.success) {
        const processedHistorical = historicalResult.observations.map(obs => ({
          date: obs.date_obs_elab,
          debit: parseFloat(obs.resultat_obs_elab) || 0
        })).filter(item => item.debit > 0)
        setHistoricalData(processedHistorical)
      }

      // Charger les données temps réel
      const realTimeResponse = await fetch(`${API_BASE_URL}/real-time-data/${site.code_site}`)
      const realTimeResult = await realTimeResponse.json()
      
      if (realTimeResult.success) {
        setRealTimeData(realTimeResult.observations.slice(0, 3))
      }

      // Charger les prévisions avec l'algorithme sélectionné
      const forecastResponse = await fetch(`${API_BASE_URL}/forecast/${site.code_site}?algorithm=${selectedAlgorithm}`)
      const forecastResult = await forecastResponse.json()
      
      if (forecastResult.success) {
        const processedForecast = forecastResult.previsions.map(prev => ({
          date: prev.date_prevision,
          debit_prevu: prev.valeur_prevue,
          debit_min: prev.valeur_min || prev.valeur_prevue * 0.8,
          debit_max: prev.valeur_max || prev.valeur_prevue * 1.2
        }))
        setForecastData(processedForecast)
      }

    } catch (error) {
      setError('Erreur lors du chargement des données')
      console.error('Erreur:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAlgorithmChange = async (algorithmKey) => {
    setSelectedAlgorithm(algorithmKey)
    
    if (selectedSite) {
      setLoading(true)
      try {
        const forecastResponse = await fetch(`${API_BASE_URL}/forecast/${selectedSite.code_site}?algorithm=${algorithmKey}`)
        const forecastResult = await forecastResponse.json()
        
        if (forecastResult.success) {
          const processedForecast = forecastResult.previsions.map(prev => ({
            date: prev.date_prevision,
            debit_prevu: prev.valeur_prevue,
            debit_min: prev.valeur_min || prev.valeur_prevue * 0.8,
            debit_max: prev.valeur_max || prev.valeur_prevue * 1.2
          }))
          setForecastData(processedForecast)
        }
      } catch (error) {
        setError('Erreur lors du changement d\'algorithme')
        console.error('Erreur:', error)
      } finally {
        setLoading(false)
      }
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-2">
              <span className="text-blue-600">🌊</span>
              MVP Prévision des Inondations
            </h1>
            <p className="text-gray-600 mt-2">Alpes du Nord - Isère & Savoie</p>
            <p className="text-sm text-gray-500 mt-1">Pour les ingénieurs DREAL</p>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Sélection du site */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span className="text-blue-600">📍</span>
            Sélection du site hydrométrique
          </h2>
          <p className="text-gray-600 mb-4">
            Recherchez et sélectionnez un site pour visualiser les données historiques et les prévisions
          </p>
          
          <div className="space-y-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Rechercher par nom de site, commune ou code..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pl-10"
              />
              <span className="absolute left-3 top-3 text-gray-400">🔍</span>
            </div>

            {searchTerm && (
              <div className="text-sm text-gray-600">
                {loading ? 'Recherche en cours...' : `${filteredSites.length} site(s) trouvé(s) pour "${searchTerm}"`}
              </div>
            )}

            <select
              value={selectedSite?.code_site || ''}
              onChange={(e) => {
                const site = filteredSites.find(s => s.code_site === e.target.value)
                if (site) handleSiteSelect(site)
              }}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Sélectionnez un site hydrométrique...</option>
              {filteredSites.map((site) => (
                <option key={site.code_site} value={site.code_site}>
                  {site.libelle_site} - ({site.code_departement})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Informations du site sélectionné */}
        {selectedSite && (
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              {selectedSite.libelle_site}
            </h3>
            <div className="text-blue-700">
              <p><strong>Commune :</strong> {selectedSite.libelle_commune_site}, {selectedSite.libelle_departement}</p>
              <p><strong>Code site :</strong> {selectedSite.code_site}</p>
            </div>
          </div>
        )}

        {/* Configuration des prévisions */}
        {selectedSite && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-purple-600">⚙️</span>
              Configuration des prévisions
            </h2>
            <p className="text-gray-600 mb-4">
              Choisissez l'algorithme de prévision à utiliser
            </p>
            
            <div className="space-y-4">
              <select
                value={selectedAlgorithm}
                onChange={(e) => handleAlgorithmChange(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                {Object.entries(algorithms).map(([key, name]) => (
                  <option key={key} value={key}>{name}</option>
                ))}
              </select>
              
              <div className="text-sm text-gray-600">
                <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded">
                  Actuel: {algorithms[selectedAlgorithm] || selectedAlgorithm}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Données en temps réel */}
        {selectedSite && realTimeData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-green-600">📊</span>
              Données en temps réel
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {realTimeData.slice(0, 3).map((obs, index) => (
                <div key={index} className="bg-green-50 p-4 rounded-lg">
                  <div className="text-sm text-green-600 font-medium">
                    {obs.grandeur_hydro === 'H' ? 'Hauteur' : 'Débit'}
                  </div>
                  <div className="text-2xl font-bold text-green-800">
                    {parseFloat(obs.resultat_obs || 0).toFixed(3)}
                  </div>
                  <div className="text-sm text-green-600">
                    {obs.grandeur_hydro === 'H' ? 'mm' : 'm³/s'}
                  </div>
                  <div className="text-xs text-green-500 mt-1">
                    {formatDateTime(obs.date_obs)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Graphique des données historiques */}
        {selectedSite && historicalData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-purple-600">📈</span>
              Données historiques (30 derniers jours)
            </h2>
            <p className="text-gray-600 mb-4">Évolution du débit moyen journalier</p>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatDate}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis 
                    label={{ value: 'Débit (m³/s)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    labelFormatter={(value) => formatDate(value)}
                    formatter={(value) => [value.toFixed(3) + ' m³/s', 'Débit historique']}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="debit" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                    name="Débit historique"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Graphique des prévisions avec min/max */}
        {selectedSite && forecastData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-orange-600">🔮</span>
              Prévisions (24 prochaines heures)
            </h2>
            <p className="text-gray-600 mb-2">
              Prévision avec algorithme: {algorithms[selectedAlgorithm] || selectedAlgorithm}
            </p>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis 
                    label={{ value: 'Débit (m³/s)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    labelFormatter={(value) => formatDateTime(value)}
                    formatter={(value, name) => [
                      value.toFixed(3) + ' m³/s', 
                      name === 'debit_prevu' ? 'Débit prévu' : 
                      name === 'debit_min' ? 'Débit minimum' : 'Débit maximum'
                    ]}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="debit_max" 
                    stroke="#ff7300" 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    name="Débit maximum"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="debit_prevu" 
                    stroke="#ff7300" 
                    strokeWidth={3}
                    name="Débit prévu"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="debit_min" 
                    stroke="#ff7300" 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    name="Débit minimum"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            <div className="mt-4 p-3 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-800">
                <strong>Algorithme utilisé:</strong> {algorithms[selectedAlgorithm] || selectedAlgorithm}
              </p>
              <p className="text-xs text-orange-600 mt-1">
                Les courbes en pointillés montrent les valeurs minimales et maximales estimées basées sur les variations historiques des dernières 24h.
              </p>
              <p className="text-xs text-orange-600 mt-1">
                Vous pouvez changer d'algorithme dans la section "Configuration des prévisions" ci-dessus.
              </p>
            </div>
          </div>
        )}

        {/* Message d'aide */}
        {!selectedSite && (
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Recherchez et sélectionnez un site hydrométrique
            </h3>
            <p className="text-gray-600">
              Utilisez la barre de recherche pour trouver des sites comme "Isère", "Bastille", "Grignon", etc.
            </p>
          </div>
        )}

        {/* Erreurs */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">
              <strong>⚠️ Erreur de connexion lors de la recherche</strong>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-8">
            <div className="text-blue-600">Chargement des données...</div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-600">
          <p>MVP Prévision des Inondations - Données fournies par Hub'Eau et Météo-France</p>
          <p className="text-sm mt-1">Algorithmes de prévision configurables - Version corrigée (m³/s)</p>
        </div>
      </footer>
    </div>
  )
}

export default App

