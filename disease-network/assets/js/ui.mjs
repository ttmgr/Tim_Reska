import {
  firstStageId,
  getClusterMeta,
  getDisease,
  getInputConfig
} from "./data.mjs";
import {
  COST_LABEL,
  buildEvidencePayload,
  buildScenarioBundle,
  buildSourceCards,
  computeStageSuggestion,
  confidenceToLabel,
  deriveNetworkModel,
  deriveTimelineModel
} from "./model.mjs";

const d3 = globalThis.d3;
const Chart = globalThis.Chart;

export function createUI(context, store) {
  const dom = collectDom();
  const runtime = {
    charts: {},
    networkSimulation: null,
    lastSuggestion: null,
    sourcesRendered: false
  };

  initStaticControls(context, store, dom, runtime);
  render(store.getState());
  const unsubscribe = store.subscribe(render);

  return {
    destroy() {
      unsubscribe();
      Object.values(runtime.charts).forEach((chart) => chart?.destroy());
      runtime.networkSimulation?.stop?.();
    }
  };

  function render(state) {
    const baselineBundle = buildScenarioBundle(context, state.patient, [], {
      seed: state.simulationSeed,
      samples: 220
    });
    const interventionBundle = buildScenarioBundle(context, state.patient, state.activeInterventionIds, {
      seed: state.simulationSeed + 97,
      samples: 220
    });
    const activeBundle = state.activeScenario === "intervention" ? interventionBundle : baselineBundle;
    const stageSuggestion = computeStageSuggestion(context, state.patient);
    const timelineModel = deriveTimelineModel(context, activeBundle.patient);
    const networkModel = deriveNetworkModel(context, activeBundle.patient, state.network);

    runtime.lastSuggestion = stageSuggestion;

    syncControls(context, state, stageSuggestion, dom);
    renderSummary(store, state, baselineBundle, interventionBundle, activeBundle, dom);
    renderComparison(baselineBundle, interventionBundle, dom);
    renderDrivers(activeBundle, dom);
    renderTimeline(context, store, dom, timelineModel);
    renderNetwork(context, store, dom, runtime, networkModel, state.network.animate);
    renderTrajectory(context, dom, runtime, baselineBundle, interventionBundle);
    renderSources(context, dom, runtime);
    renderDrawer(context, state, dom);
  }
}

function collectDom() {
  return {
    heroNote: document.getElementById("hero-note"),
    patientForm: document.getElementById("patient-form"),
    diseaseFields: document.getElementById("disease-fields"),
    applySuggestedStage: document.getElementById("apply-suggested-stage"),
    stageInsight: document.getElementById("stage-insight"),
    interventionList: document.getElementById("intervention-list"),
    scenarioToggle: document.getElementById("scenario-toggle"),
    riskDrivers: document.getElementById("risk-drivers"),
    baselineSummary: document.getElementById("baseline-summary"),
    interventionSummary: document.getElementById("intervention-summary"),
    deltaSummary: document.getElementById("delta-summary"),
    confidenceBanner: document.getElementById("confidence-banner"),
    comparisonTable: document.getElementById("comparison-table"),
    comparisonExplainer: document.getElementById("comparison-explainer"),
    timelineMeta: document.getElementById("timeline-meta"),
    timelineLanes: document.getElementById("timeline-lanes"),
    networkSearch: document.getElementById("network-search"),
    networkCluster: document.getElementById("network-cluster"),
    networkModifiable: document.getElementById("network-modifiable"),
    networkFromCurrent: document.getElementById("network-from-current"),
    networkAnimate: document.getElementById("network-animate"),
    networkSvg: document.getElementById("network-svg"),
    networkLegend: document.getElementById("network-legend"),
    pathTrace: document.getElementById("path-trace"),
    rerunSimulation: document.getElementById("rerun-simulation"),
    survivalChart: document.getElementById("survival-chart"),
    incidenceChart: document.getElementById("incidence-chart"),
    trajectorySummary: document.getElementById("trajectory-summary"),
    sourcesList: document.getElementById("sources-list"),
    tooltip: document.getElementById("tooltip"),
    drawer: document.getElementById("evidence-drawer"),
    drawerBody: document.getElementById("drawer-body"),
    drawerKicker: document.getElementById("drawer-kicker"),
    drawerTitle: document.getElementById("drawer-title"),
    drawerScrim: document.getElementById("drawer-scrim"),
    closeDrawer: document.getElementById("close-drawer")
  };
}

function initStaticControls(context, store, dom, runtime) {
  renderPatientInputs(context, store, dom);
  renderDiseaseFields(context, store, dom);
  renderInterventions(context, store, dom);
  renderScenarioToggle(store, dom);
  renderNetworkFilters(context, store, dom);

  dom.applySuggestedStage.addEventListener("click", () => {
    if (!runtime.lastSuggestion?.suggestedStage) return;
    store.update((draft) => {
      draft.patient.stage = runtime.lastSuggestion.suggestedStage.id;
      return draft;
    });
  });

  dom.rerunSimulation.addEventListener("click", () => {
    store.update((draft) => {
      draft.simulationSeed += 1;
      return draft;
    });
  });

  dom.closeDrawer.addEventListener("click", () => closeDrawer(store));
  dom.drawerScrim.addEventListener("click", () => closeDrawer(store));
}

function renderPatientInputs(context, store, dom) {
  const entries = Object.entries(context.meta.input_schema);
  dom.patientForm.innerHTML = entries
    .map(([key, config]) => {
      if (config.kind === "range") {
        return `
          <label class="field-block">
            <span class="field-top">
              <span>${config.label}</span>
              <strong id="value-${key}"></strong>
            </span>
            <input id="field-${key}" type="range" min="${config.min}" max="${config.max}" step="${config.step}" />
          </label>
        `;
      }
      if (config.kind === "segmented") {
        return `
          <div class="field-block">
            <span class="field-top">
              <span>${config.label}</span>
              <strong id="value-${key}"></strong>
            </span>
            <div id="field-${key}" class="segmented-group"></div>
          </div>
        `;
      }
      return `
        <label class="field-block">
          <span class="field-top">
            <span>${config.label}</span>
            <strong id="value-${key}"></strong>
          </span>
          <select id="field-${key}"></select>
        </label>
      `;
    })
    .join("");

  entries.forEach(([key, config]) => {
    const el = document.getElementById(`field-${key}`);
    if (config.kind === "range") {
      el.addEventListener("input", (event) => {
        const nextValue = Number(event.target.value);
        updatePatientField(store, key, nextValue);
      });
    } else if (config.kind === "segmented") {
      el.innerHTML = config.options
        .map((option) => `<button type="button" data-field="${key}" data-value="${option.value}">${option.label}</button>`)
        .join("");
      el.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-field]");
        if (!button) return;
        updatePatientField(store, key, button.dataset.value);
      });
    } else {
      el.innerHTML = config.options
        .map((option) => `<option value="${option.value}">${option.label}</option>`)
        .join("");
      el.addEventListener("change", (event) => {
        updatePatientField(store, key, event.target.value);
      });
    }
  });
}

function renderDiseaseFields(context, store, dom) {
  const diseaseOptions = context.diseases
    .map((disease) => `<option value="${disease.id}">${disease.label}</option>`)
    .join("");

  dom.diseaseFields.innerHTML = `
    <label class="field-block">
      <span class="field-top">
        <span>Primordiagnose</span>
        <strong id="value-primary_disease"></strong>
      </span>
      <select id="field-primary_disease">${diseaseOptions}</select>
    </label>
    <label class="field-block">
      <span class="field-top">
        <span>Stage</span>
        <strong id="value-stage"></strong>
      </span>
      <select id="field-stage"></select>
    </label>
  `;

  document.getElementById("field-primary_disease").addEventListener("change", (event) => {
    const diseaseId = event.target.value;
    store.update((draft) => {
      const disease = getDisease(context, diseaseId);
      draft.patient.primary_disease = diseaseId;
      draft.patient.stage = firstStageId(disease);
      draft.network.pinnedDiseaseId = null;
      return draft;
    });
  });

  document.getElementById("field-stage").addEventListener("change", (event) => {
    updatePatientField(store, "stage", event.target.value);
  });
}

function renderInterventions(context, store, dom) {
  dom.interventionList.innerHTML = context.meta.interventions
    .map((intervention) => `
      <label class="intervention-item">
        <input id="intervention-${intervention.id}" type="checkbox" />
        <span>
          <strong>${intervention.label}</strong>
          <small>${intervention.description}</small>
        </span>
      </label>
    `)
    .join("");

  context.meta.interventions.forEach((intervention) => {
    document
      .getElementById(`intervention-${intervention.id}`)
      .addEventListener("change", (event) => {
        store.update((draft) => {
          const set = new Set(draft.activeInterventionIds);
          if (event.target.checked) set.add(intervention.id);
          else set.delete(intervention.id);
          draft.activeInterventionIds = [...set];
          return draft;
        });
      });
  });
}

function renderScenarioToggle(store, dom) {
  dom.scenarioToggle.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-scenario]");
    if (!button) return;
    store.update((draft) => {
      draft.activeScenario = button.dataset.scenario;
      return draft;
    });
  });
}

function renderNetworkFilters(context, store, dom) {
  dom.networkCluster.innerHTML = `
    <option value="all">Alle Cluster</option>
    ${Object.entries(context.meta.clusters)
      .map(([clusterId, cluster]) => `<option value="${clusterId}">${cluster.label}</option>`)
      .join("")}
  `;

  dom.networkSearch.addEventListener("input", (event) => {
    store.update((draft) => {
      draft.network.search = event.target.value;
      return draft;
    });
  });
  dom.networkCluster.addEventListener("change", (event) => {
    store.update((draft) => {
      draft.network.cluster = event.target.value;
      return draft;
    });
  });
  dom.networkModifiable.addEventListener("change", (event) => {
    store.update((draft) => {
      draft.network.modifiableOnly = event.target.checked;
      return draft;
    });
  });
  dom.networkFromCurrent.addEventListener("change", (event) => {
    store.update((draft) => {
      draft.network.fromCurrentStageOnly = event.target.checked;
      return draft;
    });
  });
  dom.networkAnimate.addEventListener("change", (event) => {
    store.update((draft) => {
      draft.network.animate = event.target.checked;
      return draft;
    });
  });
}

function syncControls(context, state, stageSuggestion, dom) {
  Object.entries(context.meta.input_schema).forEach(([key, config]) => {
    const value = state.patient[key];
    const valueEl = document.getElementById(`value-${key}`);
    const field = document.getElementById(`field-${key}`);
    if (config.kind === "range") {
      field.value = value;
      valueEl.textContent = config.unit ? `${Number(value).toFixed(config.step < 1 ? 1 : 0)} ${config.unit}` : `${value}`;
    } else if (config.kind === "segmented") {
      [...field.querySelectorAll("button")].forEach((button) => {
        button.setAttribute("aria-pressed", button.dataset.value === value ? "true" : "false");
      });
      const selected = config.options.find((option) => option.value === value);
      valueEl.textContent = selected?.label || "";
    } else {
      field.value = value;
      const selected = config.options.find((option) => option.value === value);
      valueEl.textContent = selected?.label || "";
    }
  });

  const diseaseSelect = document.getElementById("field-primary_disease");
  diseaseSelect.value = state.patient.primary_disease;
  const currentDisease = getDisease(context, state.patient.primary_disease);
  const stageSelect = document.getElementById("field-stage");
  stageSelect.innerHTML = currentDisease.stages
    .map((stage) => `<option value="${stage.id}">${stage.label}</option>`)
    .join("");
  stageSelect.value = state.patient.stage;
  document.getElementById("value-primary_disease").textContent = currentDisease.short_label;
  document.getElementById("value-stage").textContent = getDisease(context, state.patient.primary_disease).stages.find((stage) => stage.id === state.patient.stage)?.label || "";

  context.meta.interventions.forEach((intervention) => {
    document.getElementById(`intervention-${intervention.id}`).checked = state.activeInterventionIds.includes(intervention.id);
  });

  [...dom.scenarioToggle.querySelectorAll("button[data-scenario]")].forEach((button) => {
    button.setAttribute("aria-pressed", button.dataset.scenario === state.activeScenario ? "true" : "false");
  });

  dom.networkSearch.value = state.network.search;
  dom.networkCluster.value = state.network.cluster;
  dom.networkModifiable.checked = state.network.modifiableOnly;
  dom.networkFromCurrent.checked = state.network.fromCurrentStageOnly;
  dom.networkAnimate.checked = state.network.animate;

  const deltaDirection = stageSuggestion.currentStage?.id === stageSuggestion.suggestedStage?.id
    ? "in-line"
    : "drift";
  dom.stageInsight.className = `insight-card ${deltaDirection}`;
  dom.stageInsight.innerHTML = `
    <strong>Biomarker-Check</strong>
    <p>
      Empfohlene Stage aus den aktuellen Eingaben: <span>${stageSuggestion.suggestedStage.label}</span>.
      ${stageSuggestion.currentStage?.id === stageSuggestion.suggestedStage?.id ? "Die manuell gewaehlte Stage passt bereits gut." : "Die aktuelle Stage weicht davon ab und kann uebernommen werden."}
    </p>
    <div class="mini-chip-row">
      ${stageSuggestion.reasons
        .map((reason) => `<span class="mini-chip ${reason.hit ? "match" : "muted"}">${reason.label}: ${reason.patientValue}</span>`)
        .join("")}
    </div>
  `;
}

function renderSummary(store, state, baselineBundle, interventionBundle, activeBundle, dom) {
  const delta = interventionBundle.summary.mortality10 - baselineBundle.summary.mortality10;
  dom.heroNote.textContent = `Educational simulation: ${activeBundle.disease.label} wird derzeit im ${state.activeScenario === "intervention" ? "Interventions" : "Baseline"}-Szenario fuer Timeline und Netzwerk verwendet.`;
  dom.confidenceBanner.innerHTML = `
    <span class="badge badge-${activeBundle.signal.key}">Signal: ${activeBundle.signal.label}</span>
    <span class="badge badge-neutral">Evidenz: ${confidenceToLabel(activeBundle.confidence)}</span>
    <span class="badge badge-neutral">Unsicherheit: ${(activeBundle.summary.mortality10Interval[0] * 100).toFixed(1)} - ${(activeBundle.summary.mortality10Interval[1] * 100).toFixed(1)}%</span>
  `;

  dom.baselineSummary.innerHTML = scenarioCardHtml("Baseline", baselineBundle);
  dom.interventionSummary.innerHTML = scenarioCardHtml("Intervention", interventionBundle);
  dom.deltaSummary.innerHTML = `
    <p class="eyebrow">Nettoeffekt</p>
    <h3>${delta <= 0 ? "Potentiell risikosenkend" : "Keine Entlastung sichtbar"}</h3>
    <div class="metric metric-delta ${delta <= 0 ? "good" : "bad"}">${Math.abs(delta * 100).toFixed(1)} Prozentpunkte</div>
    <p class="summary-copy">
      ${delta <= 0
        ? `Das aktive Interventionsbuendel senkt die modellierte 10-Jahres-Mortalitaet relativ zur Baseline.`
        : `Das gewaehlte Interventionsbuendel liefert im aktuellen Profil noch keine erkennbare Entlastung.`}
    </p>
    <div class="mini-chip-row">
      <span class="mini-chip">${state.activeInterventionIds.length} Interventionen aktiv</span>
      <span class="mini-chip">Top-Risiko: ${baselineBundle.summary.topFutureDisease?.label || "keine dominante Folgediagnose"}</span>
      <span class="mini-chip">Top-Entlastung: ${interventionBundle.riskDrivers.find((entry) => entry.kind === "intervention")?.label || "keine stage-spezifische Entlastung"}</span>
    </div>
  `;

  [dom.baselineSummary, dom.interventionSummary, dom.deltaSummary].forEach((container) => {
    container.querySelectorAll("[data-drawer-type]").forEach((button) => {
      button.addEventListener("click", () => {
        openDrawer(store, {
          type: button.dataset.drawerType,
          id: button.dataset.drawerId,
          diseaseId: button.dataset.diseaseId
        });
      });
    });
  });
}

function scenarioCardHtml(label, bundle) {
  return `
    <p class="eyebrow">${label}</p>
    <h3>${bundle.disease.short_label} · ${bundle.stage.label}</h3>
    <div class="metric-row">
      <div>
        <span class="metric-label">10-J-Mortalitaet</span>
        <div class="metric">${(bundle.summary.mortality10 * 100).toFixed(1)}%</div>
      </div>
      <div>
        <span class="metric-label">Median Survival</span>
        <div class="metric">${bundle.summary.medianSurvival} J</div>
      </div>
    </div>
    <div class="mini-chip-row">
      <span class="mini-chip ${bundle.signal.key}">${bundle.signal.label}</span>
      <span class="mini-chip">Evidenz ${confidenceToLabel(bundle.confidence)}</span>
      <span class="mini-chip">Band ${(bundle.summary.mortality10Interval[0] * 100).toFixed(1)}-${(bundle.summary.mortality10Interval[1] * 100).toFixed(1)}%</span>
    </div>
    <p class="summary-copy">${bundle.narrative.driver}</p>
    <button type="button" class="drawer-launch" data-drawer-type="stage" data-drawer-id="${bundle.stage.id}" data-disease-id="${bundle.disease.id}">
      Evidenz zu dieser Stage
    </button>
  `;
}

function renderComparison(baselineBundle, interventionBundle, dom) {
  dom.comparisonTable.innerHTML = `
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Parameter</th>
          <th>Baseline</th>
          <th>Intervention</th>
        </tr>
      </thead>
      <tbody>
        ${interventionBundle.comparisonRows
          .map((row) => `
            <tr class="${row.changed ? "changed" : ""}">
              <td>${row.label}</td>
              <td>${row.baseline}</td>
              <td>${row.intervention}</td>
            </tr>
          `)
          .join("")}
      </tbody>
    </table>
  `;

  dom.comparisonExplainer.innerHTML = `
    <p>${baselineBundle.narrative.intro}</p>
    <p>${interventionBundle.narrative.intro}</p>
    <p>${interventionBundle.narrative.future}</p>
  `;
}

function renderDrivers(activeBundle, dom) {
  dom.riskDrivers.innerHTML = `
    <div class="driver-list-head">
      <p class="eyebrow">Top Hazard-Beitraege</p>
      <h3>${activeBundle.disease.short_label}</h3>
    </div>
    ${activeBundle.riskDrivers
      .slice(0, 5)
      .map((driver) => `
        <div class="driver-row ${driver.logHazard < 0 ? "supportive" : ""}">
          <div>
            <strong>${driver.label}</strong>
            <small>${driver.valueLabel}</small>
          </div>
          <span>${driver.logHazard < 0 ? "entlastend" : "verstaerkend"}</span>
        </div>
      `)
      .join("")}
  `;
}

function renderTimeline(context, store, dom, timelineModel) {
  dom.timelineMeta.textContent = `Patient: ca. seit ${timelineModel.elapsedYears.toFixed(1)} Jahren im Verlauf der Primordiagnose · angenommener Beginn mit ${timelineModel.onsetAge.toFixed(0)} J.`;

  dom.timelineLanes.innerHTML = timelineModel.lanes
    .map((lane) => `
      <div class="timeline-lane ${lane.role}">
        <div class="lane-info">
          <button type="button" class="lane-disease" data-drawer-type="disease" data-drawer-id="${lane.disease.id}">
            ${lane.disease.label}
          </button>
          <span>${lane.relationLabel}</span>
        </div>
        <div class="lane-track">
          ${lane.stages
            .map((stage) => `
              <button
                type="button"
                class="stage-chip ${lane.currentStageId === stage.id ? "current" : ""}"
                style="flex:${Math.max(1.2, Number(stage.years_in_stage_median || 1))}"
                data-drawer-type="stage"
                data-drawer-id="${stage.id}"
                data-disease-id="${lane.disease.id}"
              >
                <span>${stage.label}</span>
                <strong>HR ${stage.mortality_hr.toFixed(2)}</strong>
              </button>
            `)
            .join("")}
        </div>
      </div>
    `)
    .join("");

  dom.timelineLanes.querySelectorAll("[data-drawer-type]").forEach((button) => {
    button.addEventListener("click", () => {
      openDrawer(store, {
        type: button.dataset.drawerType,
        id: button.dataset.drawerId,
        diseaseId: button.dataset.diseaseId
      });
    });
    button.addEventListener("mouseenter", (event) => showTooltip(dom.tooltip, event, button.textContent.trim()));
    button.addEventListener("mouseleave", () => hideTooltip(dom.tooltip));
    button.addEventListener("mousemove", (event) => moveTooltip(dom.tooltip, event));
  });
}

function renderNetwork(context, store, dom, runtime, networkModel, animate) {
  runtime.networkSimulation?.stop?.();
  dom.networkSvg.innerHTML = "";

  const width = dom.networkSvg.clientWidth || 900;
  const height = 560;
  dom.networkSvg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const svg = d3.select(dom.networkSvg);
  const root = svg.append("g");

  const nodes = networkModel.nodes.map((node) => ({ ...node }));
  const links = networkModel.edges.map((edge) => ({ ...edge }));

  const clusterColor = (clusterKey) => getClusterMeta(context, clusterKey)?.color || "#94a3b8";

  const link = root
    .append("g")
    .attr("class", "network-links")
    .selectAll("path")
    .data(links)
    .join("path")
    .attr("class", (edge) => `network-edge relevance-${edge.relevance} ${edge.onPinnedPath ? "path-active" : ""} ${animate && edge.relevance === 2 ? "edge-flow" : ""}`)
    .attr("stroke-width", (edge) => 1.5 + edge.annual_incidence_prob * 30)
    .attr("marker-end", "url(#arrow-head)")
    .on("mouseenter", (event, edge) => {
      const source = getDisease(context, edge.source);
      const target = getDisease(context, edge.target);
      showTooltip(dom.tooltip, event, `${source.short_label} -> ${target.short_label} · ${(edge.annual_incidence_prob * 100).toFixed(1)}% p.a.`);
    })
    .on("mousemove", (event) => moveTooltip(dom.tooltip, event))
    .on("mouseleave", () => hideTooltip(dom.tooltip))
    .on("click", (_, edge) => {
      openDrawer(store, { type: "edge", id: edge.id });
    });

  const node = root
    .append("g")
    .attr("class", "network-nodes")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", "network-node")
    .on("mouseenter", (event, datum) => {
      showTooltip(dom.tooltip, event, `${datum.label} · Praevalenz ${(datum.prevalence * 100).toFixed(1)}%`);
    })
    .on("mousemove", (event) => moveTooltip(dom.tooltip, event))
    .on("mouseleave", () => hideTooltip(dom.tooltip))
    .on("click", (_, datum) => {
      store.update((draft) => {
        draft.network.pinnedDiseaseId = datum.id === draft.network.pinnedDiseaseId ? null : datum.id;
        draft.ui.drawer = { type: "disease", id: datum.id };
        return draft;
      });
    });

  node
    .append("circle")
    .attr("r", (datum) => 18 + Math.sqrt(datum.prevalence) * 55)
    .attr("fill", (datum) => clusterColor(datum.cluster))
    .attr("stroke-width", (datum) => (datum.isPrimary || datum.isPinned ? 4 : 1.5))
    .attr("stroke", (datum) => (datum.isPrimary || datum.isPinned ? "#f8fafc" : "rgba(248,250,252,0.35)"));

  node
    .append("text")
    .attr("y", 4)
    .text((datum) => datum.shortLabel);

  svg
    .append("defs")
    .append("marker")
    .attr("id", "arrow-head")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 16)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#cbd5e1");

  runtime.networkSimulation = d3
    .forceSimulation(nodes)
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("charge", d3.forceManyBody().strength(-340))
    .force("collide", d3.forceCollide().radius((datum) => 28 + Math.sqrt(datum.prevalence) * 55))
    .force("link", d3.forceLink(links).id((datum) => datum.id).distance(145).strength(0.45))
    .on("tick", () => {
      link.attr("d", (edge) => {
        const dx = edge.target.x - edge.source.x;
        const dy = edge.target.y - edge.source.y;
        const dr = Math.max(80, Math.sqrt(dx * dx + dy * dy) * (edge.bidirectional ? 1.35 : 1.9));
        return `M${edge.source.x},${edge.source.y}A${dr},${dr} 0 0,1 ${edge.target.x},${edge.target.y}`;
      });
      node.attr("transform", (datum) => `translate(${datum.x},${datum.y})`);
    });

  dom.networkLegend.innerHTML = `
    <p class="eyebrow">Legende</p>
    ${Object.entries(context.meta.clusters)
      .map(
        ([clusterId, cluster]) => `
          <div class="legend-row">
            <span class="legend-dot" style="background:${cluster.color}"></span>
            <span>${cluster.label}</span>
          </div>
        `
      )
      .join("")}
    <div class="legend-row"><span class="legend-line current"></span><span>Ab aktueller Stage</span></div>
    <div class="legend-row"><span class="legend-line future"></span><span>Primaer spaetere Stage</span></div>
    <div class="legend-row"><span class="legend-line muted"></span><span>Kontextpfad</span></div>
  `;

  dom.pathTrace.innerHTML = `
    <p class="eyebrow">Pfadtrace</p>
    ${
      networkModel.pathTrace.length > 1
        ? `<div class="path-pill-row">${networkModel.pathTrace
            .map((diseaseId) => `<span class="path-pill">${getDisease(context, diseaseId).short_label}</span>`)
            .join("")}</div>`
        : `<p class="muted-copy">Knoten anklicken, um einen gerichteten Pfad ab der Primordiagnose zu markieren.</p>`
    }
  `;
}

function renderTrajectory(context, dom, runtime, baselineBundle, interventionBundle) {
  const labels = baselineBundle.simulation.labels;
  const survivalDatasets = [
    datasetBand("Baseline Band oben", baselineBundle.simulation.survivalHigh, "rgba(59,130,246,0.10)", "+1"),
    datasetBand("Baseline Band unten", baselineBundle.simulation.survivalLow, "rgba(59,130,246,0.10)"),
    datasetLine("Baseline", baselineBundle.simulation.survival, "#60a5fa"),
    datasetBand("Intervention Band oben", interventionBundle.simulation.survivalHigh, "rgba(20,184,166,0.10)", "+1"),
    datasetBand("Intervention Band unten", interventionBundle.simulation.survivalLow, "rgba(20,184,166,0.10)"),
    datasetLine("Intervention", interventionBundle.simulation.survival, "#2dd4bf")
  ];

  runtime.charts.survival?.destroy();
  runtime.charts.survival = new Chart(dom.survivalChart, {
    type: "line",
    data: { labels, datasets: survivalDatasets },
    options: sharedChartOptions({
      yTick: (value) => `${Math.round(value * 100)}%`
    })
  });

  const incidenceRows = pickIncidenceRows(context, baselineBundle, interventionBundle);
  runtime.charts.incidence?.destroy();
  runtime.charts.incidence = new Chart(dom.incidenceChart, {
    type: "bar",
    data: {
      labels: incidenceRows.map((row) => row.label),
      datasets: [
        {
          label: "Baseline",
          data: incidenceRows.map((row) => row.baseline * 100),
          backgroundColor: "rgba(96,165,250,0.75)",
          borderRadius: 8
        },
        {
          label: "Intervention",
          data: incidenceRows.map((row) => row.intervention * 100),
          backgroundColor: "rgba(45,212,191,0.75)",
          borderRadius: 8
        }
      ]
    },
    options: {
      ...sharedChartOptions({ yTick: (value) => `${value}%` }),
      plugins: {
        legend: {
          labels: { color: "#cbd5e1", font: { family: "Manrope", size: 11 } }
        }
      }
    }
  });

  dom.trajectorySummary.innerHTML = `
    <div class="trajectory-table">
      <div class="trajectory-row">
        <span>Baseline aktive Diagnosen @ J10</span>
        <strong>${baselineBundle.simulation.activeCount10.toFixed(1)}</strong>
      </div>
      <div class="trajectory-row">
        <span>Intervention aktive Diagnosen @ J10</span>
        <strong>${interventionBundle.simulation.activeCount10.toFixed(1)}</strong>
      </div>
      <div class="trajectory-row">
        <span>Baseline Kostenklasse @ J10</span>
        <strong>${COST_LABEL[Math.round(baselineBundle.simulation.costAt10)]}</strong>
      </div>
      <div class="trajectory-row">
        <span>Intervention Kostenklasse @ J10</span>
        <strong>${COST_LABEL[Math.round(interventionBundle.simulation.costAt10)]}</strong>
      </div>
      <div class="trajectory-row">
        <span>Top Folgediagnose Baseline</span>
        <strong>${baselineBundle.summary.topFutureDisease?.label || "keine"}</strong>
      </div>
      <div class="trajectory-row">
        <span>Top Folgediagnose Intervention</span>
        <strong>${interventionBundle.summary.topFutureDisease?.label || "keine"}</strong>
      </div>
    </div>
  `;
}

function pickIncidenceRows(context, baselineBundle, interventionBundle) {
  const ids = new Set();
  baselineBundle.simulation.topFutureDiseases.slice(0, 5).forEach((row) => ids.add(row.id));
  interventionBundle.simulation.topFutureDiseases.slice(0, 5).forEach((row) => ids.add(row.id));

  return [...ids]
    .map((id) => {
      const disease = getDisease(context, id);
      const baseline = baselineBundle.simulation.topFutureDiseases.find((row) => row.id === id)?.probability10 || 0;
      const intervention = interventionBundle.simulation.topFutureDiseases.find((row) => row.id === id)?.probability10 || 0;
      return { id, label: disease.short_label, baseline, intervention };
    })
    .sort((left, right) => Math.max(right.baseline, right.intervention) - Math.max(left.baseline, left.intervention))
    .slice(0, 5);
}

function datasetBand(label, data, backgroundColor, fill = false) {
  return {
    label,
    data,
    pointRadius: 0,
    borderWidth: 0,
    borderColor: "transparent",
    backgroundColor,
    fill,
    tension: 0.25
  };
}

function datasetLine(label, data, borderColor) {
  return {
    label,
    data,
    pointRadius: 0,
    borderWidth: 2.4,
    borderColor,
    backgroundColor: borderColor,
    fill: false,
    tension: 0.25
  };
}

function sharedChartOptions({ yTick }) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 320 },
    plugins: {
      legend: {
        labels: { color: "#cbd5e1", font: { family: "Manrope", size: 11 } },
        filter: (legendItem) => !legendItem.text.includes("Band")
      }
    },
    scales: {
      x: {
        ticks: { color: "#94a3b8", font: { family: "IBM Plex Mono", size: 10 } },
        grid: { color: "rgba(148,163,184,0.14)" }
      },
      y: {
        ticks: {
          color: "#94a3b8",
          font: { family: "IBM Plex Mono", size: 10 },
          callback: yTick
        },
        grid: { color: "rgba(148,163,184,0.14)" }
      }
    }
  };
}

function renderSources(context, dom, runtime) {
  if (runtime.sourcesRendered) return;
  dom.sourcesList.innerHTML = buildSourceCards(context)
    .map(
      (citation) => `
        <article class="source-card">
          <div>
            <p class="eyebrow">${citation.evidence_type}</p>
            <h3>${citation.title}</h3>
            <p>${citation.publisher} · ${citation.year}</p>
          </div>
          <div class="source-meta">
            <span>${citation.diseaseCount} direkte Diagnose-Referenzen</span>
            <a href="${citation.url}" target="_blank" rel="noreferrer">Quelle oeffnen</a>
          </div>
        </article>
      `
    )
    .join("");
  runtime.sourcesRendered = true;
}

function renderDrawer(context, state, dom) {
  if (!state.ui.drawer) {
    dom.drawer.setAttribute("aria-hidden", "true");
    dom.drawer.classList.remove("open");
    dom.drawerScrim.hidden = true;
    return;
  }

  const payload = buildEvidencePayload(context, state.ui.drawer);
  if (!payload) return;

  dom.drawerKicker.textContent = payload.kicker;
  dom.drawerTitle.textContent = payload.title;
  dom.drawerBody.innerHTML = `
    <div class="drawer-copy">
      <p class="drawer-subtitle">${payload.subtitle || ""}</p>
      <p>${payload.summary}</p>
      <div class="mini-chip-row">
        <span class="mini-chip">Evidenz ${confidenceToLabel(payload.confidence)}</span>
      </div>
    </div>
    <div class="drawer-section">
      <h3>Kernaussagen</h3>
      <ul class="drawer-list">
        ${payload.bullets.map((bullet) => `<li>${bullet}</li>`).join("")}
      </ul>
    </div>
    <div class="drawer-section">
      <h3>Biomarker und Trigger</h3>
      <div class="drawer-rule-list">
        ${(payload.rules || [])
          .map((rule) => `<div class="rule-card"><strong>${rule.label}</strong><span>${rule.note || ""}</span></div>`)
          .join("")}
      </div>
    </div>
    ${
      payload.interventions?.length
        ? `
          <div class="drawer-section">
            <h3>Relevante Interventionen</h3>
            <div class="drawer-rule-list">
              ${payload.interventions
                .map((entry) => `<div class="rule-card"><strong>${entry.label}</strong><span>${entry.note}</span></div>`)
                .join("")}
            </div>
          </div>
        `
        : ""
    }
    <div class="drawer-section">
      <h3>Zitierte Quellen</h3>
      <div class="drawer-source-list">
        ${payload.citations
          .map(
            (citation) => `
              <a href="${citation.url}" target="_blank" rel="noreferrer" class="drawer-source">
                <strong>${citation.title}</strong>
                <span>${citation.publisher} · ${citation.year} · ${citation.evidence_type}</span>
              </a>
            `
          )
          .join("")}
      </div>
    </div>
  `;

  dom.drawer.setAttribute("aria-hidden", "false");
  dom.drawer.classList.add("open");
  dom.drawerScrim.hidden = false;
}

function openDrawer(store, descriptor) {
  store.update((draft) => {
    draft.ui.drawer = descriptor;
    return draft;
  });
}

function closeDrawer(store) {
  store.update((draft) => {
    draft.ui.drawer = null;
    return draft;
  });
}

function updatePatientField(store, key, value) {
  store.update((draft) => {
    draft.patient[key] = value;
    return draft;
  });
}

function showTooltip(tooltip, event, content) {
  tooltip.textContent = content;
  tooltip.setAttribute("aria-hidden", "false");
  tooltip.classList.add("visible");
  moveTooltip(tooltip, event);
}

function moveTooltip(tooltip, event) {
  tooltip.style.left = `${event.clientX + 14}px`;
  tooltip.style.top = `${event.clientY + 14}px`;
}

function hideTooltip(tooltip) {
  tooltip.classList.remove("visible");
  tooltip.setAttribute("aria-hidden", "true");
}
