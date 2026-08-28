// Food Freshness Monitoring System - Dynamic Dashboard JavaScript
// Handles real-time sensor input, ML predictions, and live updates

class DynamicFoodDashboard {
    constructor() {
        this.apiBase = 'http://localhost:5000/api';
        this.foodTypes = [];
        this.isAutoMode = false;
        this.autoUpdateInterval = null;
        this.sensorSimulator = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadFoodTypes();
        this.checkModelStatus();
        this.loadHistory();
        this.setupDynamicInputs();
    }

    setupEventListeners() {
        // Prediction form
        document.getElementById('predictionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.predictFreshness();
        });

        // Real-time input changes
        const inputs = ['foodType', 'temperature', 'humidity', 'gas'];
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.onInputChange());
                element.addEventListener('input', () => this.onInputChange());
            }
        });

        // Auto mode toggle
        const autoModeBtn = document.getElementById('autoModeBtn');
        if (autoModeBtn) {
            autoModeBtn.addEventListener('click', () => this.toggleAutoMode());
        }

        // Manual refresh
        document.getElementById('modelStatus').addEventListener('click', () => {
            this.checkModelStatus();
        });
    }

    setupDynamicInputs() {
        // Make sensor inputs editable and responsive
        const sensorInputs = document.querySelectorAll('.sensor-input');
        sensorInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.updateSensorDisplay(e.target.id, e.target.value);
                this.predictFreshness();
            });
        });
    }

    onInputChange() {
        // Debounce predictions to avoid too many API calls
        clearTimeout(this.predictionTimeout);
        this.predictionTimeout = setTimeout(() => {
            this.predictFreshness();
        }, 500);
    }

    async loadFoodTypes() {
        try {
            const response = await fetch(`${this.apiBase}/food-types`);
            const result = await response.json();
            
            if (result.success) {
                this.foodTypes = result.data.food_types;
                this.populateFoodTypeSelect();
            }
        } catch (error) {
            console.error('Error loading food types:', error);
        }
    }

    populateFoodTypeSelect() {
        const select = document.getElementById('foodType');
        select.innerHTML = '<option value="">Select food type...</option>';
        
        const categories = {
            'Fresh Produce': ['leafy_greens', 'fruits', 'vegetables', 'herbs'],
            'Packaged Foods': ['canned_goods', 'dry_goods', 'frozen_foods', 'snacks'],
            'Fast Foods': ['burgers', 'pizza', 'sandwiches', 'fried_items'],
            'Cooked Foods': ['prepared_meals', 'leftovers', 'restaurant_food', 'homemade'],
            'Other': ['dairy', 'meat', 'fish', 'cooked', 'packaged']
        };

        Object.entries(categories).forEach(([category, types]) => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = category;
            
            types.forEach(type => {
                if (this.foodTypes.includes(type)) {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = this.formatFoodTypeName(type);
                    optgroup.appendChild(option);
                }
            });
            
            select.appendChild(optgroup);
        });
    }

    formatFoodTypeName(type) {
        return type.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    async predictFreshness() {
        const foodType = document.getElementById('foodType').value;
        const temperature = document.getElementById('temperature').value;
        const humidity = document.getElementById('humidity').value;
        const gas = document.getElementById('gas').value;

        if (!foodType || !temperature || !humidity || !gas) {
            return;
        }

        this.showLoading(true);

        try {
            const data = {
                food_type: foodType,
                temperature: parseFloat(temperature),
                humidity: parseFloat(humidity),
                gas: parseFloat(gas)
            };

            const response = await fetch(`${this.apiBase}/predict/freshness`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success && result.data.success) {
                this.displayResults(result.data);
                this.updateSensorReadings(data);
                await this.loadHistory();
            } else {
                this.showError(result.data?.error || 'Prediction failed');
            }
        } catch (error) {
            console.error('Prediction error:', error);
            this.showError('Network error during prediction');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.style.display = 'block';

        // Update result cards with animation
        const statusEl = document.getElementById('predictedStatus');
        const confidenceEl = document.getElementById('confidence');
        const freshnessEl = document.getElementById('freshnessPercentage');
        const daysEl = document.getElementById('remainingDays');

        // Update status
        const status = data.predicted_status || 'unknown';
        statusEl.textContent = status;
        statusEl.className = `status-value status-${status}`;

        // Update confidence
        const confidence = data.confidence || 0;
        confidenceEl.textContent = `${(confidence * 100).toFixed(1)}%`;
        confidenceEl.className = `confidence-value confidence-${this.getConfidenceLevel(confidence)}`;

        // Update freshness percentage
        const freshness = data.freshness_percentage || 0;
        freshnessEl.textContent = `${freshness.toFixed(1)}%`;

        // Update remaining days
        const days = data.predicted_remaining_days || 0;
        daysEl.textContent = `${days.toFixed(1)} days`;

        // Update recommendations
        this.displayRecommendations(data.recommendations);

        // Animate results
        this.animateResults();
    }

    updateSensorReadings(data) {
        // Update display elements if they exist
        const tempDisplay = document.getElementById('tempDisplay');
        const humidityDisplay = document.getElementById('humidityDisplay');
        const gasDisplay = document.getElementById('gasDisplay');
        const foodTypeDisplay = document.getElementById('foodTypeDisplay');

        if (tempDisplay) tempDisplay.textContent = `${data.temperature} °C`;
        if (humidityDisplay) humidityDisplay.textContent = `${data.humidity} %`;
        if (gasDisplay) gasDisplay.textContent = `${data.gas} ppm`;
        if (foodTypeDisplay) foodTypeDisplay.textContent = this.formatFoodTypeName(data.food_type);
    }

    animateResults() {
        const cards = document.querySelectorAll('.result-card');
        cards.forEach((card, index) => {
            card.style.animation = 'none';
            card.offsetHeight; // Trigger reflow
            card.style.animation = `fadeIn 0.5s ease ${index * 0.1}s`;
        });
    }

    displayRecommendations(recommendations) {
        const container = document.getElementById('recommendationsList');
        container.innerHTML = '';

        if (recommendations && recommendations.recommendations && recommendations.recommendations.length > 0) {
            const list = document.createElement('ul');
            list.className = 'recommendations-list';
            
            recommendations.recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                list.appendChild(li);
            });
            
            container.appendChild(list);
        } else {
            container.innerHTML = '<p>No recommendations available</p>';
        }
    }

    getConfidenceLevel(confidence) {
        if (confidence >= 0.8) return 'high';
        if (confidence >= 0.6) return 'medium';
        return 'low';
    }

    async checkModelStatus() {
        const statusElement = document.getElementById('modelStatus');
        statusElement.className = 'model-status loading';
        statusElement.innerHTML = '<p>Checking model status...</p>';

        try {
            const response = await fetch(`${this.apiBase}/models/status`);
            const result = await response.json();
            
            if (result.success) {
                const status = result.data;
                const statusClass = status.is_loaded ? 'success' : 'error';
                
                statusElement.className = `model-status ${statusClass}`;
                statusElement.innerHTML = `
                    <div class="status-info">
                        <p><strong>Model Loaded:</strong> ${status.is_loaded ? 'Yes' : 'No'}</p>
                        <p><strong>Model File Available:</strong> ${status.model_available ? 'Yes' : 'No'}</p>
                        <p><strong>Fallback Available:</strong> ${status.fallback_available ? 'Yes' : 'No'}</p>
                    </div>
                `;
            }
        } catch (error) {
            statusElement.className = 'model-status error';
            statusElement.innerHTML = `<p>Error checking model status: ${error.message}</p>`;
        }
    }

    async loadHistory() {
        try {
            const response = await fetch(`${this.apiBase}/history`);
            const data = await response.json();
            
            if (Array.isArray(data)) {
                this.displayHistory(data);
                this.updateAnalytics(data);
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    displayHistory(history) {
        const tbody = document.getElementById('historyBody');
        if (!tbody) return;

        tbody.innerHTML = '';
        const recentHistory = history.slice(-10).reverse();
        
        recentHistory.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatFoodTypeName(record.food_type)}</td>
                <td>${record.temperature}°C</td>
                <td>${record.humidity}%</td>
                <td>${record.gas} ppm</td>
                <td><span class="status-${record.ml_predicted_status || 'unknown'}">${record.ml_predicted_status || 'N/A'}</span></td>
                <td>${record.ml_confidence ? (record.ml_confidence * 100).toFixed(1) + '%' : 'N/A'}</td>
                <td>${record.ml_predicted_days || 'N/A'}</td>
                <td>${new Date(record.timestamp).toLocaleString()}</td>
            `;
            tbody.appendChild(row);
        });

        if (recentHistory.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8">No prediction history available</td></tr>';
        }
    }

    updateAnalytics(history) {
        if (window.chartsManager && history.length > 0) {
            window.chartsManager.updateCharts(history);
        }
    }

    toggleAutoMode() {
        this.isAutoMode = !this.isAutoMode;
        const btn = document.getElementById('autoModeBtn');
        
        if (this.isAutoMode) {
            btn.textContent = 'Stop Auto Mode';
            btn.classList.add('active');
            this.startAutoSimulation();
        } else {
            btn.textContent = 'Start Auto Mode';
            btn.classList.remove('active');
            this.stopAutoSimulation();
        }
    }

    startAutoSimulation() {
        this.sensorSimulator = new SensorSimulator();
        
        this.autoUpdateInterval = setInterval(() => {
            const randomFoodType = this.foodTypes[Math.floor(Math.random() * this.foodTypes.length)];
            const sensorValues = this.sensorSimulator.getRandomValues(randomFoodType);
            
            // Update input fields
            document.getElementById('foodType').value = randomFoodType;
            document.getElementById('temperature').value = sensorValues.temperature;
            document.getElementById('humidity').value = sensorValues.humidity;
            document.getElementById('gas').value = sensorValues.gas;
            
            // Trigger prediction
            this.predictFreshness();
        }, 5000); // Every 5 seconds
    }

    stopAutoSimulation() {
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = null;
        }
    }

    updateSensorDisplay(sensorId, value) {
        const displayElement = document.getElementById(`${sensorId}Display`);
        if (displayElement) {
            const unit = sensorId === 'temperature' ? '°C' : sensorId === 'humidity' ? '%' : 'ppm';
            displayElement.textContent = `${value} ${unit}`;
        }
    }

    showLoading(show) {
        const modal = document.getElementById('loadingModal');
        if (modal) {
            modal.style.display = show ? 'flex' : 'none';
        }
    }

    showError(message) {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #e74c3c;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Sensor Simulator for Auto Mode
class SensorSimulator {
    constructor() {
        this.baseValues = {
            'leafy_greens': { temp: 4.0, humidity: 85.0, gas: 0.3 },
            'dairy': { temp: 5.0, humidity: 70.0, gas: 0.4 },
            'meat': { temp: 2.0, humidity: 80.0, gas: 0.8 },
            'fruits': { temp: 8.0, humidity: 75.0, gas: 0.5 },
            'vegetables': { temp: 6.0, humidity: 65.0, gas: 0.2 }
        };
    }

    getRandomValues(foodType) {
        const base = this.baseValues[foodType] || this.baseValues['leafy_greens'];
        
        return {
            temperature: Math.round((base.temp + (Math.random() - 0.5) * 4) * 10) / 10,
            humidity: Math.round(Math.max(0, Math.min(100, base.humidity + (Math.random() - 0.5) * 20)) * 10) / 10,
            gas: Math.round(Math.max(0, base.gas + (Math.random() - 0.5) * 0.5) * 100) / 100
        };
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    new DynamicFoodDashboard();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .sensor-input {
        transition: all 0.3s ease;
    }
    
    .sensor-input:focus {
        transform: scale(1.02);
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
    }
    
    .auto-mode-active {
        background: #27ae60 !important;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
`;
document.head.appendChild(style);
