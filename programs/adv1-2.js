const API_URL = "https://airoco.necolico.jp/data-api/day-csv";
const DAY_SECONDS = 24 * 60 * 60;
const ENV_URL = "./.env";

const SENSOR_CONFIGS = [
  { name: "Ｒ３ーB１Ｆ_ＥＨ", color: "#006e90" },
  { name: "Ｒ３ー３Ｆ_ＥＨ", color: "#f18f01" },
  { name: "Ｒ３ー４Ｆ_ＥＨ", color: "#8f2d56" },
];

const statusElement = document.getElementById("status");
const latestCardsElement = document.getElementById("latest-cards");

async function fetchSensorData() {
  const env = await loadEnv();
  const subscriptionKey = env.SUBSCRIPTION_KEY;
  const idHashKey = env.ID_HASH_KEY;

  if (!subscriptionKey || !idHashKey) {
    throw new Error(".env に SUBSCRIPTION_KEY または ID_HASH_KEY がありません");
  }

  const currentTime = Math.floor(Date.now() / 1000);
  const startDate = currentTime - DAY_SECONDS;
  const url = `${API_URL}?id=${idHashKey}&subscription-key=${subscriptionKey}&startDate=${startDate}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  const rawText = (await response.text()).replace(/^\uFEFF/, "");
  return parseCsv(rawText);
}

async function loadEnv() {
  const response = await fetch(ENV_URL);

  if (!response.ok) {
    throw new Error(`.env の読み込みに失敗しました: ${response.status}`);
  }

  const rawText = await response.text();
  return parseEnv(rawText);
}

function parseEnv(rawText) {
  return rawText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .reduce((env, line) => {
      const separatorIndex = line.indexOf("=");
      const key = line.slice(0, separatorIndex).trim();
      const value = line.slice(separatorIndex + 1).trim().replace(/^["']|["']$/g, "");
      env[key] = value;
      return env;
    }, {});
}

function parseCsv(rawText) {
  return rawText
    .trim()
    .split(/\r?\n/)
    .map((line) => line.split(","))
    .filter((columns) => columns.length >= 7)
    .map((columns) => ({
      dateTime: columns[0],
      sensorName: columns[1],
      sensorNumber: columns[2],
      co2: Number(columns[3]),
      temperature: Number(columns[4]),
      humidity: Number(columns[5]),
      timestamp: Number(columns[6]),
    }));
}

function buildDatasets(rows) {
  return SENSOR_CONFIGS.map((sensor) => {
    const sensorRows = rows
      .filter((row) => row.sensorName === sensor.name)
      .sort((a, b) => a.timestamp - b.timestamp);

    return {
      ...sensor,
      rows: sensorRows,
      latest: sensorRows[sensorRows.length - 1] ?? null,
      co2Data: sensorRows.map((row) => ({ x: row.timestamp * 1000, y: row.co2 })),
      temperatureData: sensorRows.map((row) => ({ x: row.timestamp * 1000, y: row.temperature })),
      humidityData: sensorRows.map((row) => ({ x: row.timestamp * 1000, y: row.humidity })),
    };
  });
}

function renderLatestCards(datasets) {
  latestCardsElement.innerHTML = datasets
    .map((dataset) => {
      if (!dataset.latest) {
        return `
          <article class="card">
            <div class="sensor-name">${dataset.name}</div>
            <p>過去 24 時間のデータが見つかりませんでした。</p>
          </article>
        `;
      }

      return `
        <article class="card">
          <div class="sensor-name">${dataset.name}</div>
          <p>最新取得時刻: ${dataset.latest.dateTime}</p>
          <div class="latest-grid">
            <div class="metric">
              <div class="metric-label">CO2</div>
              <div class="metric-value">${dataset.latest.co2.toFixed(1)} ppm</div>
            </div>
            <div class="metric">
              <div class="metric-label">Temperature</div>
              <div class="metric-value">${dataset.latest.temperature.toFixed(1)} °C</div>
            </div>
            <div class="metric">
              <div class="metric-label">Humidity</div>
              <div class="metric-value">${dataset.latest.humidity.toFixed(1)} %</div>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function formatTimeLabel(value) {
  const date = new Date(value);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${month}/${day} ${hour}:${minute}`;
}

function buildChart(canvasId, datasets, key) {
  const canvas = document.getElementById(canvasId);
  return new Chart(canvas, {
    type: "scatter",
    data: {
      datasets: datasets.map((dataset) => ({
        label: dataset.name,
        data: dataset[key],
        showLine: true,
        pointRadius: 0,
        borderWidth: 2,
        borderColor: dataset.color,
        backgroundColor: dataset.color,
        tension: 0.2,
      })),
    },
    options: {
      maintainAspectRatio: false,
      interaction: {
        mode: "nearest",
        intersect: false,
      },
      plugins: {
        legend: {
          position: "bottom",
        },
        tooltip: {
          callbacks: {
            title(items) {
              return formatTimeLabel(items[0].parsed.x);
            },
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          title: {
            display: true,
            text: "Date",
          },
          ticks: {
            callback(value) {
              return formatTimeLabel(value);
            },
            maxTicksLimit: 8,
          },
        },
        y: {
          beginAtZero: false,
        },
      },
    },
  });
}

async function main() {
  try {
    const rows = await fetchSensorData();
    const datasets = buildDatasets(rows);

    renderLatestCards(datasets);
    buildChart("co2-chart", datasets, "co2Data");
    buildChart("temperature-chart", datasets, "temperatureData");
    buildChart("humidity-chart", datasets, "humidityData");

    statusElement.textContent = "取得完了: 過去 24 時間分のデータを表示しています。";
  } catch (error) {
    console.error(error);
    statusElement.textContent = `データ取得に失敗しました: ${error.message}`;
  }
}

main();
