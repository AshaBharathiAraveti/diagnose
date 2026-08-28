// Backend API URL
const API_URL = "http://127.0.0.1:5000/api/latest";

// Fetch latest data from backend
async function fetchLatestData() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        if (!data || Object.keys(data).length === 0) {
            console.log("No data available");
            return;
        }

        // Update UI values
        document.getElementById("foodType").innerText = data.food_type || "--";
        document.getElementById("temperature").innerText = `${data.temperature} °C`;
        document.getElementById("humidity").innerText = `${data.humidity} %`;
        document.getElementById("gas").innerText = `${data.gas} ppm`;

        document.getElementById("status").innerText = data.spoiled || "--";
        document.getElementById("remainingDays").innerText = `${data.remaining_days} days`;
        document.getElementById("freshness").innerText = `${data.freshness_percent} %`;

        // 🔔 Alert banner logic (MUST be inside try)
        const banner = document.getElementById("alertBanner");

        if (data.spoiled === "Spoiled") {
            banner.className = "alert danger";
            banner.innerText = "⚠️ Food is Spoiled!";
        } 
        else if (data.remaining_days <= 1) {
            banner.className = "alert warning";
            banner.innerText = "⚠️ Food may spoil soon!";
        } 
        else {
            banner.className = "alert success";
            banner.innerText = "✅ Food is Fresh";
        }

        // 🟥🟩 Status card color coding
        const statusCard = document.querySelector(".status");

        if (data.spoiled === "Spoiled") {
            statusCard.style.borderLeft = "6px solid red";
        } else {
            statusCard.style.borderLeft = "6px solid green";
        }

    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// Initial call
fetchLatestData();

// Refresh every 5 seconds
setInterval(fetchLatestData, 5000);