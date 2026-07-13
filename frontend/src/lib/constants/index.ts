/**
 * Application-wide constants for GeoAvia.
 *
 * Centralized configuration values that don't belong in environment variables.
 * Security note: No secrets or API keys should ever be placed here.
 */

/** Application metadata */
export const APP_NAME = 'GeoAvia';
export const APP_DESCRIPTION = 'Sistema de Prospecção de Sítios Aeroportuários';

/** Rate limiting for login attempts (client-side visual feedback) */
export const LOGIN_COOLDOWN_BASE_MS = 3000;
export const LOGIN_MAX_ATTEMPTS = 5;

/** Form validation limits */
export const USERNAME_MIN_LENGTH = 3;
export const USERNAME_MAX_LENGTH = 50;
/** Minimum length for NEW passwords (creation/change/reset). Login is not
 * revalidated against the policy, so legacy accounts keep working. */
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_MAX_LENGTH = 128;
/** Length of admin-issued recovery codes (see backend CODE_LENGTH). */
export const RECOVERY_CODE_LENGTH = 20;
export const SITE_NAME_MAX_LENGTH = 100;
export const DESCRIPTION_MAX_LENGTH = 500;

/** Map defaults */
export const DEFAULT_MAP_CENTER: [number, number] = [-14.235, -51.9253]; // Center of Brazil
export const DEFAULT_MAP_ZOOM = 4;
