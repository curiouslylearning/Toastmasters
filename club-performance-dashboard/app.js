const CSV_PATH = "../d95.csv";
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const state = {
  rows: [],
  tmYears: [],
  asOfByYear: new Map(),
  filters: {
    tmYear: "",
    asOf: "",
    division: "All",
    status: "All",
    search: "",
    hierarchyMetric: "score"
  },
  drill: {
    level: "district",
    division: null,
    area: null,
    clubNumber: null
  }
};

const els = {};

function toNumber(value) {
  if (value === null || value === undefined) {
    return 0;
  }
  const cleaned = String(value).trim();
  if (!cleaned) {
    return 0;
  }
  const number = Number(cleaned.replace(/,/g, ""));
  return Number.isFinite(number) ? number : 0;
}

function parseDate(value) {
  if (!value) {
    return null;
  }
  const parts = String(value).trim().split("/");
  if (parts.length !== 3) {
    return null;
  }
  const month = Number(parts[0]);
  const day = Number(parts[1]);
  const year = Number(parts[2]);
  if (!month || !day || !year) {
    return null;
  }
  const date = new Date(year, month - 1, day);
  return Number.isFinite(date.valueOf()) ? date : null;
}

function normalizeStatus(raw) {
  const value = (raw || "").trim();
  const lower = value.toLowerCase();
  if (!value) {
    return "Unknown";
  }
  if (lower.includes("inactive")) {
    return "Inactive";
  }
  if (lower.includes("ineligible")) {
    return "Ineligible";
  }
  if (lower.includes("suspended")) {
    return "Suspended";
  }
  if (lower.includes("active")) {
    return "Active";
  }
  return value;
}

function performanceScore(row) {
  const score =
    row.goalsMet * 11 +
    row.netGrowth * 1.6 +
    row.newMembers * 2.8 +
    row.officerRound1 * 4 +
    row.officerRound2 * 4 +
    row.duesOct * 2.5 +
    row.duesApr * 2.5 +
    row.officerListOnTime * 2.5 +
    row.activeMembers * 0.4;
  return Number(score.toFixed(1));
}

function normalizeRow(raw) {
  const tmYear = String(raw.TM_Year || "").trim();
  const asOf = String(raw.AsOf || "").trim();
  const monthNum = Number(raw.Month_Num || raw.AsOfMonth || 0);
  const division = String(raw.Division || "").trim();
  const area = String(raw.Area || "").trim();
  const clubNumber = String(raw["Club Number"] || raw["Club numeric"] || "").trim();

  if (!tmYear || !asOf || !division || !clubNumber) {
    return null;
  }

  const row = {
    district: String(raw.District || "").trim(),
    division,
    area,
    clubNumber,
    clubName: String(raw["Club Name"] || "").trim() || `Club ${clubNumber}`,
    clubStatus: normalizeStatus(raw["Club Status"]),
    csp: String(raw.CSP || "").trim(),
    memBase: toNumber(raw["Mem. Base"]),
    activeMembers: toNumber(raw["Active Members"]),
    netGrowth: toNumber(raw["Net Growth"]),
    goalsMet: toNumber(raw["Goals Met"]),
    level1: toNumber(raw["Level 1s"]),
    level2: toNumber(raw["Level 2s"]),
    level3: toNumber(raw["Level 3s"]),
    level4: toNumber(raw["Level 4s"]),
    level5: toNumber(raw["Level 5s"]),
    newMembers: toNumber(raw["New Members"]),
    addNewMembers: toNumber(raw["Add. New Members"]),
    officerRound1: toNumber(raw["Off. Trained Round 1"]),
    officerRound2: toNumber(raw["Off. Trained Round 2"]),
    duesOct: toNumber(raw["Mem. dues on time Oct"]),
    duesApr: toNumber(raw["Mem. dues on time Apr"]),
    officerListOnTime: toNumber(raw["Off. List On Time"]),
    tmYear,
    monthNum,
    monthName: MONTH_NAMES[Math.max(0, Math.min(11, monthNum - 1))] || String(raw.MonthOf || ""),
    asOf,
    asOfDate: parseDate(asOf),
    distinguishedStatus: String(raw["Club Distinguished Status"] || "").trim()
  };

  row.score = performanceScore(row);
  row.isAtRisk = row.activeMembers < 20 || row.netGrowth < -2 || row.goalsMet < 3;
  row.distinguishedProgress = Number(((row.goalsMet / 10) * 100).toFixed(1));

  return row;
}

function formatNumber(value, digits = 0) {
  return Number(value || 0).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  });
}

function formatDelta(value, digits = 1) {
  const n = Number(value || 0);
  const fixed = formatNumber(Math.abs(n), digits);
  return `${n >= 0 ? "+" : "-"}${fixed}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#39;");
}

function setStatus(text) {
  els.datasetStatus.textContent = text;
}

function clearDrill() {
  state.drill.level = "district";
  state.drill.division = null;
  state.drill.area = null;
  state.drill.clubNumber = null;
}

function buildMeta() {
  const tmYearSet = new Set();
  const asOfMap = new Map();
  const statusSet = new Set(["All"]);

  for (const row of state.rows) {
    tmYearSet.add(row.tmYear);
    statusSet.add(row.clubStatus);
    if (!asOfMap.has(row.tmYear)) {
      asOfMap.set(row.tmYear, new Map());
    }
    if (row.asOfDate) {
      asOfMap.get(row.tmYear).set(row.asOf, row.asOfDate);
    }
  }

  state.tmYears = Array.from(tmYearSet).sort((a, b) => {
    const aYear = Number(a.split("-")[0]);
    const bYear = Number(b.split("-")[0]);
    return aYear - bYear;
  });

  state.asOfByYear = asOfMap;
  state.statuses = Array.from(statusSet).sort((a, b) => {
    if (a === "All") {
      return -1;
    }
    if (b === "All") {
      return 1;
    }
    return a.localeCompare(b);
  });
}

function populateControls() {
  const latestYear = state.tmYears[state.tmYears.length - 1];
  state.filters.tmYear = latestYear;

  els.tmYearSelect.innerHTML = state.tmYears
    .map((year) => `<option value="${escapeHtml(year)}">${escapeHtml(year)}</option>`)
    .join("");
  els.tmYearSelect.value = latestYear;

  populateAsOfOptions();
  populateDivisionOptions();
  populateStatusOptions();
  els.hierarchyMetricSelect.value = state.filters.hierarchyMetric;
}

function populateStatusOptions() {
  els.statusSelect.innerHTML = state.statuses
    .map((status) => `<option value="${escapeHtml(status)}">${escapeHtml(status)}</option>`)
    .join("");
  state.filters.status = "All";
  els.statusSelect.value = "All";
}

function populateAsOfOptions() {
  const year = state.filters.tmYear;
  const asOfMap = state.asOfByYear.get(year);
  const items = asOfMap ? Array.from(asOfMap.entries()) : [];
  items.sort((a, b) => a[1] - b[1]);

  els.asOfSelect.innerHTML = items
    .map(([asOf]) => `<option value="${escapeHtml(asOf)}">${escapeHtml(asOf)}</option>`)
    .join("");

  const latestAsOf = items.length ? items[items.length - 1][0] : "";
  state.filters.asOf = latestAsOf;
  els.asOfSelect.value = latestAsOf;
}

function populateDivisionOptions() {
  const year = state.filters.tmYear;
  const asOf = state.filters.asOf;
  const divisions = Array.from(
    new Set(
      state.rows
        .filter((row) => row.tmYear === year && row.asOf === asOf)
        .map((row) => row.division)
    )
  ).sort((a, b) => a.localeCompare(b));

  els.divisionSelect.innerHTML = [`<option value="All">All</option>`]
    .concat(divisions.map((division) => `<option value="${escapeHtml(division)}">${escapeHtml(division)}</option>`))
    .join("");
  state.filters.division = "All";
  els.divisionSelect.value = "All";
}

function bindEvents() {
  els.tmYearSelect.addEventListener("change", () => {
    state.filters.tmYear = els.tmYearSelect.value;
    clearDrill();
    populateAsOfOptions();
    populateDivisionOptions();
    render();
  });

  els.asOfSelect.addEventListener("change", () => {
    state.filters.asOf = els.asOfSelect.value;
    clearDrill();
    populateDivisionOptions();
    render();
  });

  els.divisionSelect.addEventListener("change", () => {
    state.filters.division = els.divisionSelect.value;
    if (state.drill.division && state.filters.division !== "All" && state.filters.division !== state.drill.division) {
      clearDrill();
    }
    render();
  });

  els.statusSelect.addEventListener("change", () => {
    state.filters.status = els.statusSelect.value;
    render();
  });

  els.hierarchyMetricSelect.addEventListener("change", () => {
    state.filters.hierarchyMetric = els.hierarchyMetricSelect.value;
    render();
  });

  els.clubSearchInput.addEventListener("input", () => {
    state.filters.search = els.clubSearchInput.value.trim().toLowerCase();
    render();
  });

  els.resetDrillBtn.addEventListener("click", () => {
    clearDrill();
    render();
  });
}

function rowMatchesFilters(row) {
  if (row.tmYear !== state.filters.tmYear || row.asOf !== state.filters.asOf) {
    return false;
  }
  if (state.filters.division !== "All" && row.division !== state.filters.division) {
    return false;
  }
  if (state.filters.status !== "All" && row.clubStatus !== state.filters.status) {
    return false;
  }
  if (state.filters.search && !row.clubName.toLowerCase().includes(state.filters.search)) {
    return false;
  }
  return true;
}

function applyDrillScope(rows, includeClub) {
  const drill = state.drill;
  if (drill.level === "district") {
    return rows;
  }
  if (drill.level === "division") {
    return rows.filter((row) => row.division === drill.division);
  }
  if (drill.level === "area") {
    return rows.filter((row) => row.division === drill.division && row.area === drill.area);
  }
  if (!includeClub) {
    return rows.filter((row) => row.division === drill.division && row.area === drill.area);
  }
  return rows.filter((row) => row.clubNumber === drill.clubNumber);
}

function getScopeLabel() {
  if (state.drill.level === "district") {
    return "District 95";
  }
  if (state.drill.level === "division") {
    return `Division ${state.drill.division}`;
  }
  if (state.drill.level === "area") {
    return `Division ${state.drill.division} / Area ${state.drill.area}`;
  }
  const club = state.rows.find((row) => row.clubNumber === state.drill.clubNumber);
  return club ? club.clubName : "Selected Club";
}

function renderKpis(scopeRows, totalRows) {
  const clubs = scopeRows.length;
  const activeClubs = scopeRows.filter((row) => row.clubStatus === "Active").length;
  const avgGoals = clubs ? scopeRows.reduce((sum, row) => sum + row.goalsMet, 0) / clubs : 0;
  const totalGrowth = scopeRows.reduce((sum, row) => sum + row.netGrowth, 0);
  const avgScore = clubs ? scopeRows.reduce((sum, row) => sum + row.score, 0) / clubs : 0;
  const atRisk = scopeRows.filter((row) => row.isAtRisk).length;

  const cards = [
    { label: "Clubs In Scope", value: formatNumber(clubs), context: `of ${formatNumber(totalRows)} after filters` },
    { label: "Active Clubs", value: formatNumber(activeClubs), context: clubs ? `${formatNumber((activeClubs / clubs) * 100, 1)}%` : "0%" },
    { label: "Avg Goals Met", value: formatNumber(avgGoals, 2), context: "Distinguished target is 5+" },
    { label: "Net Growth", value: formatDelta(totalGrowth, 0), context: "Total members vs base" },
    { label: "Avg Performance Score", value: formatNumber(avgScore, 1), context: `${formatNumber(atRisk)} clubs marked at risk` }
  ];

  els.kpiGrid.innerHTML = cards
    .map((card) => `
      <article class="kpi">
        <div class="label">${card.label}</div>
        <div class="value">${card.value}</div>
        <div class="context">${card.context}</div>
      </article>
    `)
    .join("");
}

function renderBreadcrumbs() {
  const crumbs = [{ key: "district", label: "District 95" }];
  if (state.drill.division) {
    crumbs.push({ key: "division", label: `Division ${state.drill.division}` });
  }
  if (state.drill.area) {
    crumbs.push({ key: "area", label: `Area ${state.drill.area}` });
  }
  if (state.drill.clubNumber) {
    const club = state.rows.find((row) => row.clubNumber === state.drill.clubNumber);
    if (club) {
      crumbs.push({ key: "club", label: club.clubName });
    }
  }

  els.breadcrumbs.innerHTML = crumbs
    .map((crumb, index) => `<button class="crumb ${index === crumbs.length - 1 ? "is-active" : ""}" data-index="${index}">${escapeHtml(crumb.label)}</button>`)
    .join("");

  Array.from(els.breadcrumbs.querySelectorAll(".crumb")).forEach((button) => {
    button.addEventListener("click", () => {
      const idx = Number(button.dataset.index);
      if (idx === 0) {
        clearDrill();
      } else if (idx === 1) {
        state.drill.level = "division";
        state.drill.area = null;
        state.drill.clubNumber = null;
      } else if (idx === 2) {
        state.drill.level = "area";
        state.drill.clubNumber = null;
      }
      render();
    });
  });
}

function groupRows(rows, keySelector, labelSelector) {
  const map = new Map();
  for (const row of rows) {
    const key = keySelector(row);
    if (!map.has(key)) {
      map.set(key, {
        key,
        label: labelSelector(row),
        clubs: 0,
        goals: 0,
        growth: 0,
        active: 0,
        score: 0,
        division: row.division,
        area: row.area,
        clubNumber: row.clubNumber
      });
    }
    const bucket = map.get(key);
    bucket.clubs += 1;
    bucket.goals += row.goalsMet;
    bucket.growth += row.netGrowth;
    bucket.active += row.activeMembers;
    bucket.score += row.score;
  }
  return Array.from(map.values()).map((bucket) => ({
    ...bucket,
    avgScore: bucket.clubs ? bucket.score / bucket.clubs : 0
  }));
}

function renderHierarchyChart(rows) {
  let grouped;
  let levelTitle;
  if (state.drill.level === "district") {
    grouped = groupRows(rows, (row) => row.division, (row) => `Division ${row.division}`);
    levelTitle = "Click a division to drill down";
  } else if (state.drill.level === "division") {
    grouped = groupRows(rows, (row) => row.area, (row) => `Area ${row.area}`);
    levelTitle = "Click an area to drill down";
  } else {
    grouped = groupRows(rows, (row) => row.clubNumber, (row) => row.clubName);
    levelTitle = "Click a club for detailed profile";
  }

  grouped.sort((a, b) => b.avgScore - a.avgScore);
  const top = grouped.slice(0, 24);

  const metricConfig = {
    score: {
      label: "Average Score",
      value: (item) => Number(item.avgScore.toFixed(2))
    },
    goals: {
      label: "Total Goals Met",
      value: (item) => Number(item.goals.toFixed(1))
    },
    growth: {
      label: "Total Net Growth",
      value: (item) => Number(item.growth.toFixed(1))
    },
    active: {
      label: "Total Active Members",
      value: (item) => Number(item.active.toFixed(1))
    }
  };
  const metricKey = state.filters.hierarchyMetric;
  const metric = metricConfig[metricKey] || metricConfig.score;

  const x = top.map((item) => item.label);
  const y = top.map((item) => metric.value(item));
  const growth = top.map((item) => item.growth);
  const customdata = top.map((item) => [item.division, item.area, item.clubNumber]);

  const yMin = Math.min(...y);
  const yMax = Math.max(...y);
  const normalize = (value) => {
    if (yMax === yMin) {
      return 0.6;
    }
    return (value - yMin) / (yMax - yMin);
  };
  const colors = metricKey === "growth"
    ? growth.map((g) => (g >= 0 ? "rgba(42, 157, 111, 0.78)" : "rgba(207, 62, 76, 0.76)"))
    : y.map((value) => {
      const t = normalize(value);
      const alpha = 0.48 + t * 0.4;
      return `rgba(14, 139, 143, ${alpha.toFixed(2)})`;
    });
  const trace = {
    type: "bar",
    x,
    y,
    customdata,
    marker: {
      color: colors,
      line: {
        width: top.map((item) => (state.drill.clubNumber === item.clubNumber ? 2.4 : 0)),
        color: "rgba(31, 44, 44, 0.85)"
      }
    },
    hovertemplate: `<b>%{x}</b><br>${metric.label}: %{y:.1f}<extra></extra>`
  };

  const layout = {
    margin: { t: 8, r: 8, b: 52, l: 42 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: { tickangle: -20, automargin: true },
    yaxis: { title: metric.label, zeroline: false },
    font: { family: "Manrope, sans-serif", size: 12, color: "#1f2c2c" }
  };

  Plotly.react(els.hierarchyChart, [trace], layout, { displayModeBar: false, responsive: true });
  els.hierarchySubtitle.textContent = `${levelTitle} | Scope: ${getScopeLabel()}`;

  if (els.hierarchyChart.removeAllListeners) {
    els.hierarchyChart.removeAllListeners("plotly_click");
  }
  els.hierarchyChart.on("plotly_click", (event) => {
    const point = event.points[0];
    const [division, area, clubNumber] = point.customdata;
    if (state.drill.level === "district") {
      state.drill.level = "division";
      state.drill.division = division;
      state.drill.area = null;
      state.drill.clubNumber = null;
    } else if (state.drill.level === "division") {
      state.drill.level = "area";
      state.drill.area = area;
      state.drill.clubNumber = null;
    } else {
      state.drill.level = "club";
      state.drill.clubNumber = clubNumber;
      state.drill.division = division;
      state.drill.area = area;
    }
    render();
  });
}

function getTrendRows() {
  const yearRows = state.rows.filter((row) => row.tmYear === state.filters.tmYear);
  const filtered = yearRows.filter((row) => {
    if (state.filters.division !== "All" && row.division !== state.filters.division) {
      return false;
    }
    if (state.filters.status !== "All" && row.clubStatus !== state.filters.status) {
      return false;
    }
    if (state.filters.search && !row.clubName.toLowerCase().includes(state.filters.search)) {
      return false;
    }
    return true;
  });
  return applyDrillScope(filtered, true);
}

function aggregateTrend(rows) {
  const map = new Map();
  for (const row of rows) {
    const month = row.monthNum;
    if (!month) {
      continue;
    }
    if (!map.has(month)) {
      map.set(month, {
        month,
        clubs: 0,
        goals: 0,
        active: 0,
        growth: 0
      });
    }
    const bucket = map.get(month);
    bucket.clubs += 1;
    bucket.goals += row.goalsMet;
    bucket.active += row.activeMembers;
    bucket.growth += row.netGrowth;
  }
  return Array.from(map.values())
    .sort((a, b) => a.month - b.month)
    .map((bucket) => ({
      ...bucket,
      avgGoals: bucket.clubs ? bucket.goals / bucket.clubs : 0,
      avgActive: bucket.clubs ? bucket.active / bucket.clubs : 0
    }));
}

function renderTrendChart(trendRows) {
  const series = aggregateTrend(trendRows);
  const x = series.map((row) => MONTH_NAMES[row.month - 1] || `M${row.month}`);
  const goals = series.map((row) => Number(row.avgGoals.toFixed(2)));
  const active = series.map((row) => Number(row.avgActive.toFixed(2)));
  const growth = series.map((row) => Number(row.growth.toFixed(1)));

  const traces = [
    {
      x,
      y: goals,
      type: "scatter",
      mode: "lines+markers",
      name: "Avg Goals Met",
      line: { color: "#db5f28", width: 3 },
      marker: { size: 7 }
    },
    {
      x,
      y: active,
      type: "scatter",
      mode: "lines+markers",
      name: "Avg Active Members",
      line: { color: "#0e8b8f", width: 2.5 },
      marker: { size: 6 }
    },
    {
      x,
      y: growth,
      type: "bar",
      name: "Total Net Growth",
      opacity: 0.42,
      marker: { color: "#2a9d6f" },
      yaxis: "y2"
    }
  ];

  const layout = {
    margin: { t: 8, r: 48, b: 38, l: 42 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    yaxis: { title: "Averages", zeroline: false },
    yaxis2: {
      title: "Net Growth",
      overlaying: "y",
      side: "right",
      showgrid: false
    },
    legend: { orientation: "h", y: 1.12, x: 0 },
    font: { family: "Manrope, sans-serif", size: 12, color: "#1f2c2c" }
  };

  Plotly.react(els.trendChart, traces, layout, { displayModeBar: false, responsive: true });
  els.trendSubtitle.textContent = `${getScopeLabel()} across ${state.filters.tmYear}`;
}

function renderScatterChart(rows) {
  const scopeRows = rows.slice(0, 1600);
  const x = scopeRows.map((row) => row.activeMembers);
  const y = scopeRows.map((row) => row.goalsMet);
  const colors = scopeRows.map((row) => row.netGrowth);
  const sizes = scopeRows.map((row) => Math.max(8, row.newMembers * 2 + 7));
  const text = scopeRows.map((row) => `${row.clubName}<br>Div ${row.division} / Area ${row.area}`);
  const customdata = scopeRows.map((row) => [row.clubNumber, row.division, row.area]);

  const avgX = x.length ? x.reduce((sum, n) => sum + n, 0) / x.length : 0;
  const avgY = y.length ? y.reduce((sum, n) => sum + n, 0) / y.length : 0;

  const trace = {
    x,
    y,
    type: "scattergl",
    mode: "markers",
    text,
    customdata,
    marker: {
      color: colors,
      colorscale: [
        [0, "#cf3e4c"],
        [0.5, "#f2b24f"],
        [1, "#2a9d6f"]
      ],
      cmin: -12,
      cmax: 12,
      size: sizes,
      opacity: 0.82,
      line: { width: 0.8, color: "rgba(31,44,44,0.35)" }
    },
    hovertemplate: "%{text}<br>Active: %{x}<br>Goals: %{y}<br>Net Growth: %{marker.color}<extra></extra>"
  };

  const layout = {
    margin: { t: 12, r: 8, b: 44, l: 48 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: { title: "Active Members" },
    yaxis: { title: "Goals Met" },
    shapes: [
      {
        type: "line",
        x0: avgX,
        x1: avgX,
        y0: Math.min(...y, 0),
        y1: Math.max(...y, 10),
        line: { color: "rgba(31, 44, 44, 0.28)", dash: "dot" }
      },
      {
        type: "line",
        x0: Math.min(...x, 0),
        x1: Math.max(...x, 40),
        y0: avgY,
        y1: avgY,
        line: { color: "rgba(31, 44, 44, 0.28)", dash: "dot" }
      }
    ],
    font: { family: "Manrope, sans-serif", size: 12, color: "#1f2c2c" }
  };

  Plotly.react(els.scatterChart, [trace], layout, { displayModeBar: false, responsive: true });
  if (els.scatterChart.removeAllListeners) {
    els.scatterChart.removeAllListeners("plotly_click");
  }
  els.scatterChart.on("plotly_click", (event) => {
    const [clubNumber, division, area] = event.points[0].customdata;
    state.drill.level = "club";
    state.drill.clubNumber = clubNumber;
    state.drill.division = division;
    state.drill.area = area;
    render();
  });
}

function renderTable(rows) {
  const sorted = [...rows].sort((a, b) => b.score - a.score);
  const bodyRows = sorted.slice(0, 120);
  const tbody = els.clubTableBody;
  tbody.innerHTML = bodyRows
    .map((row, index) => `
      <tr data-club="${escapeHtml(row.clubNumber)}" data-division="${escapeHtml(row.division)}" data-area="${escapeHtml(row.area)}">
        <td>${index + 1}</td>
        <td>
          ${escapeHtml(row.clubName)}
          <span class="badge ${row.isAtRisk ? "warn" : "good"}">${row.isAtRisk ? "At Risk" : "Healthy"}</span>
        </td>
        <td>${escapeHtml(row.division)}-${escapeHtml(row.area)}</td>
        <td>${formatNumber(row.goalsMet)}</td>
        <td>${formatDelta(row.netGrowth, 0)}</td>
        <td>${formatNumber(row.activeMembers)}</td>
        <td>${formatNumber(row.score, 1)}</td>
      </tr>
    `)
    .join("");

  Array.from(tbody.querySelectorAll("tr")).forEach((tr) => {
    tr.addEventListener("click", () => {
      state.drill.level = "club";
      state.drill.clubNumber = tr.dataset.club;
      state.drill.division = tr.dataset.division;
      state.drill.area = tr.dataset.area;
      render();
    });
  });
}

function renderDetails(scopeRows, peerRows, trendRows) {
  const list = [];
  const selected = scopeRows[0];
  const scopeLabel = getScopeLabel();

  if (state.drill.level === "club" && selected) {
    list.push({
      title: "Club Snapshot",
      text: `${selected.clubName} has ${formatNumber(selected.activeMembers)} active members, ${formatNumber(selected.goalsMet)} goals met, and ${formatDelta(selected.netGrowth, 0)} net growth at ${state.filters.asOf}.`
    });
    list.push({
      title: "Distinguished Progress",
      text: `${formatNumber(selected.distinguishedProgress, 1)}% of the 10-goal track completed. New members: ${formatNumber(selected.newMembers)}. CSP: ${selected.csp || "n/a"}.`
    });
    list.push({
      title: "Operational Compliance",
      text: `Officer training R1/R2: ${formatNumber(selected.officerRound1)}/${formatNumber(selected.officerRound2)}. Dues on-time Oct/Apr: ${formatNumber(selected.duesOct)}/${formatNumber(selected.duesApr)}.`
    });
  } else {
    const clubs = scopeRows.length;
    const avgActive = clubs ? scopeRows.reduce((sum, row) => sum + row.activeMembers, 0) / clubs : 0;
    const avgGoals = clubs ? scopeRows.reduce((sum, row) => sum + row.goalsMet, 0) / clubs : 0;
    const growth = scopeRows.reduce((sum, row) => sum + row.netGrowth, 0);
    list.push({
      title: "Scope Summary",
      text: `${scopeLabel} includes ${formatNumber(clubs)} clubs. Average active members: ${formatNumber(avgActive, 1)}. Average goals met: ${formatNumber(avgGoals, 2)}.`
    });

    const best = [...peerRows].sort((a, b) => b.score - a.score)[0];
    const weakest = [...peerRows].sort((a, b) => a.score - b.score)[0];
    if (best && weakest) {
      list.push({
        title: "Range of Performance",
        text: `Highest score: ${best.clubName} (${formatNumber(best.score, 1)}). Lowest score: ${weakest.clubName} (${formatNumber(weakest.score, 1)}).`
      });
    }

    const latestTrend = aggregateTrend(trendRows);
    if (latestTrend.length >= 2) {
      const prev = latestTrend[latestTrend.length - 2];
      const current = latestTrend[latestTrend.length - 1];
      list.push({
        title: "Latest Momentum",
        text: `${MONTH_NAMES[current.month - 1]} vs ${MONTH_NAMES[prev.month - 1]}: goals ${formatDelta(current.avgGoals - prev.avgGoals, 2)}, active members ${formatDelta(current.avgActive - prev.avgActive, 2)}, growth ${formatDelta(current.growth - prev.growth, 0)}.`
      });
    }
  }

  els.detailsSubtitle.textContent = `${scopeLabel} at ${state.filters.asOf}`;
  els.detailsPanel.innerHTML = list
    .map((item) => `<article class="details-item"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.text)}</p></article>`)
    .join("");
}

function renderInsights(rows, trendRows) {
  const items = [];
  const byDivision = groupRows(rows, (row) => row.division, (row) => row.division).sort((a, b) => b.avgScore - a.avgScore);
  if (byDivision.length) {
    const best = byDivision[0];
    items.push({
      title: "Top Division",
      text: `Division ${best.label} leads this slice with average score ${formatNumber(best.avgScore, 1)} across ${formatNumber(best.clubs)} clubs.`
    });
  }

  const atRiskCount = rows.filter((row) => row.isAtRisk).length;
  const highMomentum = rows
    .filter((row) => row.netGrowth >= 3 && row.goalsMet >= 5)
    .sort((a, b) => b.netGrowth - a.netGrowth)
    .slice(0, 1)[0];
  if (highMomentum) {
    items.push({
      title: "Momentum Club",
      text: `${highMomentum.clubName} (Div ${highMomentum.division}-${highMomentum.area}) shows strong momentum with ${formatDelta(highMomentum.netGrowth, 0)} growth and ${formatNumber(highMomentum.goalsMet)} goals.`
    });
  }

  items.push({
    title: "Risk Watch",
    text: `${formatNumber(atRiskCount)} of ${formatNumber(rows.length)} clubs are flagged at risk (low membership, negative growth, or low goals).`
  });

  const trend = aggregateTrend(trendRows);
  if (trend.length >= 2) {
    const first = trend[0];
    const latest = trend[trend.length - 1];
    items.push({
      title: "Season Direction",
      text: `From ${MONTH_NAMES[first.month - 1]} to ${MONTH_NAMES[latest.month - 1]}, average goals moved ${formatDelta(latest.avgGoals - first.avgGoals, 2)} and total net growth moved ${formatDelta(latest.growth - first.growth, 0)}.`
    });
  }

  els.insightPanel.innerHTML = items
    .slice(0, 4)
    .map((item) => `<article class="insight-item"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.text)}</p></article>`)
    .join("");
}

function renderEmptyState() {
  els.kpiGrid.innerHTML = `<div class="loading">No data found for this filter combination.</div>`;
  els.hierarchySubtitle.textContent = "";
  els.trendSubtitle.textContent = "";
  els.detailsSubtitle.textContent = "";
  els.detailsPanel.innerHTML = `<div class="loading">Adjust filters to view details.</div>`;
  els.insightPanel.innerHTML = `<div class="loading">Insights appear once data is available.</div>`;
  els.clubTableBody.innerHTML = "";
  Plotly.purge(els.hierarchyChart);
  Plotly.purge(els.trendChart);
  Plotly.purge(els.scatterChart);
}

function render() {
  const snapshotAll = state.rows.filter((row) => rowMatchesFilters(row));
  const scopeRows = applyDrillScope(snapshotAll, true);
  const peerRows = applyDrillScope(snapshotAll, false);
  const trendRows = getTrendRows();

  setStatus(`Loaded ${formatNumber(state.rows.length)} rows | ${state.filters.tmYear} | as of ${state.filters.asOf}`);
  renderBreadcrumbs();

  if (!scopeRows.length || !peerRows.length) {
    renderEmptyState();
    return;
  }

  renderKpis(scopeRows, snapshotAll.length);
  renderHierarchyChart(peerRows);
  renderTrendChart(trendRows);
  renderScatterChart(peerRows);
  renderTable(peerRows);
  renderDetails(scopeRows, peerRows, trendRows);
  renderInsights(peerRows, trendRows);
}

function initElements() {
  els.datasetStatus = document.getElementById("datasetStatus");
  els.tmYearSelect = document.getElementById("tmYearSelect");
  els.asOfSelect = document.getElementById("asOfSelect");
  els.divisionSelect = document.getElementById("divisionSelect");
  els.statusSelect = document.getElementById("statusSelect");
  els.hierarchyMetricSelect = document.getElementById("hierarchyMetricSelect");
  els.clubSearchInput = document.getElementById("clubSearchInput");
  els.resetDrillBtn = document.getElementById("resetDrillBtn");
  els.kpiGrid = document.getElementById("kpiGrid");
  els.breadcrumbs = document.getElementById("breadcrumbs");
  els.hierarchySubtitle = document.getElementById("hierarchySubtitle");
  els.trendSubtitle = document.getElementById("trendSubtitle");
  els.detailsSubtitle = document.getElementById("detailsSubtitle");
  els.hierarchyChart = document.getElementById("hierarchyChart");
  els.trendChart = document.getElementById("trendChart");
  els.scatterChart = document.getElementById("scatterChart");
  els.detailsPanel = document.getElementById("detailsPanel");
  els.insightPanel = document.getElementById("insightPanel");
  els.clubTableBody = document.querySelector("#clubTable tbody");
}

function decodeCsvBuffer(buffer) {
  const bytes = new Uint8Array(buffer);
  let text = new TextDecoder("utf-8").decode(bytes);

  // UTF-16LE CSV files decoded as UTF-8 contain null-byte interleaving.
  if (text.includes("\u0000")) {
    text = text.replace(/^\uFFFD\uFFFD/, "").replace(/\u0000/g, "");
  }

  return text.replace(/^\uFEFF/, "");
}

function toObjectRows(parsedRows) {
  if (!Array.isArray(parsedRows) || parsedRows.length < 2) {
    return [];
  }

  const header = parsedRows[0].map((name) => String(name || "").trim());
  const rows = parsedRows.slice(1);
  const objects = [];

  for (const row of rows) {
    const record = {};
    for (let i = 0; i < header.length; i += 1) {
      record[header[i]] = row[i] ?? "";
    }
    objects.push(record);
  }

  return objects;
}

async function loadData() {
  setStatus("Loading d95.csv...");
  try {
    const response = await fetch(CSV_PATH, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const csvText = decodeCsvBuffer(await response.arrayBuffer());
    const parsed = Papa.parse(csvText, {
      header: false,
      skipEmptyLines: true,
      worker: false
    });
    const objectRows = toObjectRows(parsed.data);
    const normalized = objectRows.map(normalizeRow).filter(Boolean);

    if (!normalized.length) {
      const parseError = parsed.errors && parsed.errors.length ? parsed.errors[0].message : "No valid rows after normalization.";
      throw new Error(parseError);
    }

    state.rows = normalized;
    buildMeta();
    populateControls();
    bindEvents();
    render();
  } catch (error) {
    setStatus(`Failed to load CSV: ${error.message}`);
    els.kpiGrid.innerHTML = `<div class="loading">Unable to parse dataset.</div>`;
  }
}

function boot() {
  initElements();
  if (!window.Papa) {
    setStatus("PapaParse failed to load. Check internet access or use a local script copy.");
    return;
  }
  if (!window.Plotly) {
    setStatus("Plotly failed to load. Check internet access or use a local script copy.");
    return;
  }
  loadData();
}

boot();
