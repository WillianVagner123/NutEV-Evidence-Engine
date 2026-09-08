import * as library from './saved-library.js';

// Compatibility alias only. The actual legacy/pilot routing lives in saved-library.js,
// which is the module already consumed by search-library-ui.js and saved-library-ui.js.
window.NutEVSavedLibrary=library;
window.NutEVEvidenceLibrary=library;
