/**
 * GeoAvia — Application entry point.
 *
 * Imports the global stylesheet (Tailwind CSS + custom design tokens)
 * and renders the root App component with React StrictMode.
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@/styles/index.css';
import { App } from '@/app/App';
import { initTheme } from '@/features/theme/initTheme';

// Apply the persisted theme before the first render to avoid a flash of the
// wrong theme (the ThemeProvider then owns it from here on).
initTheme();

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found. Ensure index.html contains <div id="root"></div>.');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
