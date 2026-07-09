/**
 * Router — Application routing with RBAC-protected routes.
 *
 * Route structure (3-role model):
 * - /login                    → Public
 * - /dashboard/*              → Protected (authenticated)
 *   - /dashboard/map          → all roles
 *   - /dashboard/analysis     → operador, administrador, desenvolvedor
 *   - /dashboard/assessment   → operador, administrador, desenvolvedor
 *   - /dashboard/results      → operador, administrador, desenvolvedor
 *   - /dashboard/export       → operador, administrador, desenvolvedor
 *   - /dashboard/screening    → operador, administrador, desenvolvedor
 *   - /dashboard/data/*       → operador, administrador, desenvolvedor
 *   - /dashboard/admin/*      → administrador, desenvolvedor
 *   - /dashboard/dev/*        → desenvolvedor
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import type { UserRole } from '@/types';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardLayout } from '@/components/layout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { MapPage } from '@/features/map/pages/MapPage';
import { AssessmentPage } from '@/features/assessment/pages/AssessmentPage';
import { ResultsPage } from '@/features/results/pages/ResultsPage';
import { AnalysisPage } from '@/features/analysis/pages/AnalysisPage';
import { ExportPage } from '@/features/export/pages/ExportPage';
import { ShapefileImportPage } from '@/features/data/pages/ShapefileImportPage';
import { ScreeningPage } from '@/features/screening/pages/ScreeningPage';
import { UserManagementPage } from '@/features/admin/pages/UserManagementPage';
import { LayerConfigPage } from '@/features/admin/pages/LayerConfigPage';
import { AuditLogPage } from '@/features/admin/pages/AuditLogPage';
import { ApiHealthPage } from '@/features/dev/pages/ApiHealthPage';
import { ProcessingLogsPage } from '@/features/dev/pages/ProcessingLogsPage';
import { DebugPage } from '@/features/dev/pages/DebugPage';

// Operational pages: any operational role.
const ANALYSIS_ROLES: UserRole[] = ['operador', 'administrador', 'desenvolvedor'];
const ASSESSMENT_ROLES: UserRole[] = ['operador', 'administrador', 'desenvolvedor'];
const RESULTS_ROLES: UserRole[] = ['operador', 'administrador', 'desenvolvedor'];
const SCREENING_ROLES: UserRole[] = ['operador', 'administrador', 'desenvolvedor'];
const DATA_IMPORT_ROLES: UserRole[] = ['operador', 'administrador', 'desenvolvedor'];
// Admin pages: administrator and developer.
const USER_ADMIN_ROLES: UserRole[] = ['administrador', 'desenvolvedor'];
const LAYER_ADMIN_ROLES: UserRole[] = ['administrador', 'desenvolvedor'];
// Developer tools: developer only.
const DEV_ROLES: UserRole[] = ['desenvolvedor'];

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard/map" replace /> },
      { path: 'map', element: <MapPage /> },

      // MESA flow — analysis/assessment/results/export
      {
        path: 'analysis',
        element: <ProtectedRoute allowedRoles={ANALYSIS_ROLES}><AnalysisPage /></ProtectedRoute>,
      },
      {
        path: 'assessment',
        element: <ProtectedRoute allowedRoles={ASSESSMENT_ROLES}><AssessmentPage /></ProtectedRoute>,
      },
      {
        path: 'results',
        element: <ProtectedRoute allowedRoles={RESULTS_ROLES}><ResultsPage /></ProtectedRoute>,
      },
      {
        path: 'export',
        element: <ProtectedRoute allowedRoles={RESULTS_ROLES}><ExportPage /></ProtectedRoute>,
      },
      {
        path: 'screening',
        element: <ProtectedRoute allowedRoles={SCREENING_ROLES}><ScreeningPage /></ProtectedRoute>,
      },

      // Data — ingestion/import (HU-31)
      {
        path: 'data/shapefiles',
        element: <ProtectedRoute allowedRoles={DATA_IMPORT_ROLES}><ShapefileImportPage /></ProtectedRoute>,
      },

      // Administration
      {
        path: 'admin/users',
        element: <ProtectedRoute allowedRoles={USER_ADMIN_ROLES}><UserManagementPage /></ProtectedRoute>,
      },
      {
        path: 'admin/layers',
        element: <ProtectedRoute allowedRoles={LAYER_ADMIN_ROLES}><LayerConfigPage /></ProtectedRoute>,
      },
      {
        path: 'admin/audit',
        element: <ProtectedRoute allowedRoles={LAYER_ADMIN_ROLES}><AuditLogPage /></ProtectedRoute>,
      },

      // System technical operations
      {
        path: 'dev/health',
        element: <ProtectedRoute allowedRoles={DEV_ROLES}><ApiHealthPage /></ProtectedRoute>,
      },
      {
        path: 'dev/logs',
        element: <ProtectedRoute allowedRoles={DEV_ROLES}><ProcessingLogsPage /></ProtectedRoute>,
      },
      {
        path: 'dev/debug',
        element: <ProtectedRoute allowedRoles={DEV_ROLES}><DebugPage /></ProtectedRoute>,
      },
    ],
  },
  { path: '/', element: <Navigate to="/dashboard/map" replace /> },
  { path: '*', element: <Navigate to="/dashboard/map" replace /> },
]);
