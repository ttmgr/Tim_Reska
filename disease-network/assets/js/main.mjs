import { getDefaultPatient, loadDiseaseData } from "./data.mjs";
import { createStore } from "./state.mjs";
import { createUI } from "./ui.mjs";

async function boot() {
  const context = await loadDiseaseData();
  const store = createStore({
    patient: getDefaultPatient(context),
    activeInterventionIds: ["bp_control", "glucose_control", "lipid_therapy"],
    activeScenario: "baseline",
    simulationSeed: 11,
    network: {
      search: "",
      cluster: "all",
      modifiableOnly: false,
      fromCurrentStageOnly: true,
      animate: true,
      pinnedDiseaseId: null
    },
    ui: {
      drawer: null
    }
  });

  createUI(context, store);
}

boot().catch((error) => {
  console.error(error);
  const fallback = document.createElement("div");
  fallback.className = "fatal-error";
  fallback.innerHTML = `
    <h1>Disease Network konnte nicht initialisiert werden</h1>
    <p>${error.message}</p>
    <p>Bitte die App ueber einen lokalen HTTP-Server starten, damit diseases.json geladen werden kann.</p>
  `;
  document.body.appendChild(fallback);
});
