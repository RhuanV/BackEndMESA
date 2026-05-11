/**
 * Application-wide constants for GeoAvia.
 *
 * Centralized configuration values that don't belong in environment variables.
 * Security note: No secrets or API keys should ever be placed here.
 */

/** Application metadata */
export const APP_NAME = 'GeoAvia';
export const APP_DESCRIPTION = 'Sistema de Prospecção de Sítios Aeroportuários — MESA-Auto';

/** Rate limiting for login attempts (client-side visual feedback) */
export const LOGIN_COOLDOWN_BASE_MS = 3000;
export const LOGIN_MAX_ATTEMPTS = 5;

/** Form validation limits */
export const USERNAME_MIN_LENGTH = 3;
export const USERNAME_MAX_LENGTH = 50;
export const PASSWORD_MIN_LENGTH = 6;
export const PASSWORD_MAX_LENGTH = 128;
export const SITE_NAME_MAX_LENGTH = 100;
export const DESCRIPTION_MAX_LENGTH = 500;

/** Map defaults */
export const DEFAULT_MAP_CENTER: [number, number] = [-14.235, -51.9253]; // Center of Brazil
export const DEFAULT_MAP_ZOOM = 4;
