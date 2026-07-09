/**
 * Router — Application routing with RBAC-protected routes.
 *
 * Route structure (Sprint 3 — 5 perfis MESA-A):
 * - /login                    → Public
 * - /dashboard/*              → Protected (authenticated)
 *   - /dashboard/map          → todos
 *   - /dashboard/analysis     → coordenador, supervisor, operador
 *   - /dashboard/assessment   → coordenador, gestor, operador
 *   - /dashboard/results      → coordenador, gestor, supervisor, operador
 *   - /dashboard/export       → coordenador, gestor, supervisor, operador
 *   - /dashboard/admin/users  → coordenador, gestor, supervisor
 *   - /dashboard/admin/layers → coordenador, administrador
 *   - /dashboard/admin/audit  → coordenador, administrador
 *   - /dashboard/dev/*        → administrador
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

const ANALYSIS_ROLES: UserRole[] = ['coordenador', 'supervisor', 'operador', 'desenvolvedor'];
const ASSESSMENT_ROLES: UserRole[] = ['coordenador', 'gestor', 'operador', 'desenvolvedor'];
const RESULTS_ROLES: UserRole[] = ['coordenador', 'gestor', 'supervisor', 'operador', 'desenvolvedor'];
const SCREENING_ROLES: UserRole[] = ['coordenador', 'gestor', 'operador'];
const DATA_IMPORT_ROLES: UserRole[] = ['coordenador', 'gestor', 'supervisor', 'operador', 'administrador'];
const USER_ADMIN_ROLES: UserRole[] = ['coordenador', 'gestor', 'supervisor', 'desenvolvedor'];
const LAYER_ADMIN_ROLES: UserRole[] = ['coordenador', 'administrador', 'desenvolvedor'];
const DEV_ROLES: UserRole[] = ['administrador', 'desenvolvedor'];

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
