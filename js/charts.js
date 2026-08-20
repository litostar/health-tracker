/* ===== Chart.js 折线图封装 ===== */
let trendChart = null;

function renderTrend(rows) {
  const ctx = document.getElementById("trendChart").getContext("2d");
  const labels = rows.map(d => d.date.slice(5));          // 只显示 MM-DD
  const intake = rows.map(d => d.intake);
  const tdee = rows.map(d => d.tdee);

  if (trendChart) trendChart.destroy();                   // 切换 7/30 天时先销毁旧图
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "摄入 kcal", data: intake, borderColor: "#e74c3c",
          backgroundColor: "rgba(231,76,60,.12)", fill: true, tension: 0.3, pointRadius: 2 },
        { label: "TDEE kcal", data: tdee, borderColor: "#3498db",
          backgroundColor: "rgba(52,152,219,.12)", fill: true, tension: 0.3, pointRadius: 2 },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "top" } },
      scales: { y: { beginAtZero: true } },
    },
  });
}
