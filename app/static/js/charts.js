window.SecondBrain = (function () {
  function isDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function pick(light, dark) {
    return isDark() ? dark : light;
  }

  const gridline = () => pick("#e1e0d9", "#2c2c2a");
  const muted = () => "#898781";
  const surface = () => pick("#fcfcfb", "#1a1a19");

  function toNumeric(v) {
    return typeof v === "boolean" ? (v ? 1 : 0) : v;
  }

  function sparkline(canvasId, series, colorLight, colorDark) {
    const el = document.getElementById(canvasId);
    if (!el || !series.length) return;
    const color = pick(colorLight, colorDark);
    new Chart(el, {
      type: "line",
      data: {
        labels: series.map((p) => p.date),
        datasets: [
          {
            data: series.map((p) => toNumeric(p.value)),
            borderColor: color,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.25,
            fill: false,
          },
        ],
      },
      options: {
        responsive: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false } },
      },
    });
  }

  function lineChart(canvasId, series, colorLight, colorDark, isBoolean) {
    const el = document.getElementById(canvasId);
    if (!el || !series.length) return;
    const color = pick(colorLight, colorDark);
    new Chart(el, {
      type: "line",
      data: {
        labels: series.map((p) => p.date),
        datasets: [
          {
            data: series.map((p) => toNumeric(p.value)),
            borderColor: color,
            backgroundColor: color + "1a",
            borderWidth: 2,
            pointRadius: 3,
            pointBackgroundColor: color,
            pointBorderColor: surface(),
            pointBorderWidth: 2,
            tension: 0.25,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: muted(), maxTicksLimit: 6 } },
          y: {
            grid: { color: gridline(), drawTicks: false },
            ticks: isBoolean
              ? { color: muted(), stepSize: 1, callback: (v) => (v === 1 ? "Yes" : v === 0 ? "No" : "") }
              : { color: muted() },
          },
        },
      },
    });
  }

  function comparisonBar(canvasId, labels, lastMonth, thisMonth, colorLight, colorDark) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const color = pick(colorLight, colorDark);
    new Chart(el, {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Last month", data: lastMonth, backgroundColor: color + "40", borderRadius: 4, maxBarThickness: 24 },
          { label: "This month", data: thisMonth, backgroundColor: color, borderRadius: 4, maxBarThickness: 24 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true, labels: { color: muted() } } },
        scales: {
          x: { grid: { display: false }, ticks: { color: muted() } },
          y: { grid: { color: gridline(), drawTicks: false }, ticks: { color: muted() } },
        },
      },
    });
  }

  return { sparkline, lineChart, comparisonBar };
})();
