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

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found. Ensure index.html contains <div id="root"></div>.');
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
