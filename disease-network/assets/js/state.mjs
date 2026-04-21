export function createStore(initialState) {
  let state = structuredClone(initialState);
  const listeners = new Set();

  return {
    getState() {
      return structuredClone(state);
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    update(updater) {
      const draft = structuredClone(state);
      const nextState = updater(draft) || draft;
      state = nextState;
      listeners.forEach((listener) => listener(structuredClone(state)));
    }
  };
}
