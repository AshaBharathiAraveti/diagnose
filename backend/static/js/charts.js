const HISTORY_API = "http://127.0.0.1:5000/api/history";

let tempChart, humidityChart, gasChart, freshnessChart;

async function loadCharts() {
    const response = await fetch(HISTORY_API);
    const data = await response.json();

    const labels = data.map(item => item.timestamp);
    const temperatures = data.map(item => item.temperature);
    const humidity = data.map(item => item.humidity);
    const gas = data.map(item => item.gas);
    const freshness = data.map(item => item.freshness_percent);

    if (tempChart) tempChart.destroy();
    if (humidityChart) humidityChart.destroy();
    if (gasChart) gasChart.destroy();
    if (freshnessChart) freshnessChart.destroy();

    tempChart = createChart("tempChart", "Temperature (°C)", labels, temperatures);
    humidityChart = createChart("humidityChart", "Humidity (%)", labels, humidity);
    gasChart = createChart("gasChart", "Gas (ppm)", labels, gas);
    freshnessChart = createChart("freshnessChart", "Freshness (%)", labels, freshness);
}

function createChart(canvasId, label, labels, data) {
    return new Chart(document.getElementById(canvasId), {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderWidth: 2,
                fill: false
            }]
        }
    });
}

loadCharts();
setInterval(loadCharts, 10000);