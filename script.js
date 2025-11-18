let historyChart, predChart;
let latestAqiNow = 0;
let latestPred1 = 0;
let latestPred5 = 0;

/* ---------- Dummy Dataset ---------- */
const HIST = [
  {year: 2018, pm25:110, co2:405, no2:46},
  {year: 2019, pm25:120, co2:408, no2:49},
  {year: 2020, pm25:95,  co2:409, no2:39},
  {year: 2021, pm25:102, co2:410, no2:42},
  {year: 2022, pm25:108, co2:412, no2:45},
  {year: 2023, pm25:115, co2:414, no2:47},
  {year: 2024, pm25:118, co2:416, no2:50},
  {year: 2025, pm25:112, co2:417, no2:48},
];

/* ---------- AQI Calculation ---------- */
function calculateAQI(pm) {
  const bp = [
    {c_low:0,   c_high:12,   i_low:0,   i_high:50},
    {c_low:12.1,c_high:35.4, i_low:51,  i_high:100},
    {c_low:35.5,c_high:55.4, i_low:101, i_high:150},
    {c_low:55.5,c_high:150.4,i_low:151, i_high:200},
    {c_low:150.5,c_high:250.4,i_low:201,i_high:300},
    {c_low:250.5,c_high:500,  i_low:301,i_high:500}
  ];

  for (const b of bp) {
    if (pm >= b.c_low && pm <= b.c_high) {
      return Math.round(
        ((b.i_high - b.i_low) / (b.c_high - b.c_low)) * (pm - b.c_low) + b.i_low
      );
    }
  }
  return 500;
}

function aqiLabel(aqi) {
  if (aqi <= 50) return {text:"Good", color:"bg-success"};
  if (aqi <= 100) return {text:"Moderate", color:"bg-warning text-dark"};
  if (aqi <= 150) return {text:"Unhealthy-Sensitive", color:"bg-orange"};
  if (aqi <= 200) return {text:"Unhealthy", color:"bg-danger"};
  if (aqi <= 300) return {text:"Very Unhealthy", color:"bg-purple"};
  return {text:"Hazardous", color:"bg-dark"};
}

/* ---------- Generate Simulated Current Values ---------- */
function getCurrent() {
  const last = HIST[HIST.length - 1];
  return {
    pm25: last.pm25 + (Math.random() * 10 - 5),
    co2: last.co2 + (Math.random() * 6 - 3),
    no2: last.no2 + (Math.random() * 8 - 4),
  };
}

/* ---------- Prediction ---------- */
function predictAQI(nowPM, years) {
  const slope = (HIST[HIST.length-1].pm25 - HIST[0].pm25) / HIST.length;
  const futurePM = nowPM + slope * years + (Math.random() * 6 - 3);
  return calculateAQI(futurePM);
}

/* ---------- Charts ---------- */
function getTextColor() {
  return document.body.classList.contains("dark") ? "#e2e8f0" : "#1e293b";
}

function renderHistory() {
  const ctx = document.getElementById("historyChart");
  if (historyChart) historyChart.destroy();

  historyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: HIST.map(h => h.year),
      datasets: [
        {label:"PM2.5", data:HIST.map(h=>h.pm25), borderWidth:2},
        {label:"CO2", data:HIST.map(h=>h.co2), borderWidth:2},
        {label:"NO2", data:HIST.map(h=>h.no2), borderWidth:2},
      ]
    },
    options: {
      plugins: {
        legend: { labels: { color: getTextColor() } }
      },
      scales: {
        x: { ticks: { color: getTextColor() } },
        y: { ticks: { color: getTextColor() } }
      }
    }
  });
}

function renderPredChart(aqiNow, aqi1, aqi5) {
  const ctx = document.getElementById("predChart");
  if (predChart) predChart.destroy();

  predChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Now", "1 Year", "5 Years"],
      datasets: [
        {label:"AQI", data:[aqiNow, aqi1, aqi5], borderWidth:1}
      ]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          max: 500,
          ticks: { color: getTextColor() }
        },
        x: {
          ticks: { color: getTextColor() }
        }
      },
      plugins: {
        legend: { labels: { color: getTextColor() } }
      }
    }
  });
}

/* ---------- Heatmap ---------- */
function matplotlibColor(value) {
  const v = value / 100;
  const r = Math.floor(255 * v);
  const g = Math.floor(255 * Math.min(1, v * 1.5));
  const b = Math.floor(255 * (1 - v));
  return `rgb(${r},${g},${b})`;
}

function renderHeatmap() {
  const matrix = [
    [98, 92, 95],
    [89, 97, 91],
    [90, 88, 96]
  ];

  const container = document.getElementById("heatmap");
  container.innerHTML = "";

  matrix.forEach(row => {
    row.forEach(val => {
      const cell = document.createElement("div");
      cell.className = "heat-cell";
      cell.style.background = matplotlibColor(val);
      cell.textContent = val + "%";
      container.appendChild(cell);
    });
  });
}

/* ---------- Load Dashboard ---------- */
function loadDashboard() {
  const now = getCurrent();

  // Present Values
  document.getElementById("presentPm").textContent = now.pm25.toFixed(1);
  document.getElementById("presentCo2").textContent = now.co2.toFixed(1);
  document.getElementById("presentNo2").textContent = now.no2.toFixed(1);

  // Present AQI
  const aqiNow = calculateAQI(now.pm25);
  document.getElementById("presentAqi").textContent = aqiNow;

  latestAqiNow = aqiNow;

  const lbl = aqiLabel(aqiNow);
  const badge = document.getElementById("presentLabel");
  badge.textContent = lbl.text;
  badge.className = "badge " + lbl.color;

  // Last year
  const last = HIST[HIST.length - 2];
  document.getElementById("lastPm").textContent = last.pm25;
  document.getElementById("lastCo2").textContent = last.co2;
  document.getElementById("lastNo2").textContent = last.no2;

  // Predict AQI
  document.getElementById("predictBtn").onclick = () => {
    const pred1 = predictAQI(now.pm25, 1);
    const pred5 = predictAQI(now.pm25, 5);

    document.getElementById("pred1").textContent = pred1;
    document.getElementById("pred5").textContent = pred5;

    latestPred1 = pred1;
    latestPred5 = pred5;

    renderPredChart(aqiNow, pred1, pred5);
  };

  renderHistory();
  renderHeatmap();
}

/* ---------- Dark Mode Toggle ---------- */
document.getElementById("themeToggle").onclick = () => {
  document.body.classList.toggle("dark");

  const isDark = document.body.classList.contains("dark");
  document.getElementById("themeToggle").textContent = isDark
    ? "☀️ Light Mode"
    : "🌙 Dark Mode";

  if (historyChart) historyChart.destroy();
  if (predChart) predChart.destroy();

  renderHistory();
  renderPredChart(latestAqiNow, latestPred1, latestPred5);
};

loadDashboard();