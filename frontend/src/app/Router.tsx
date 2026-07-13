/* eslint-disable react-refresh/only-export-components -- routing config module,
   not a Fast Refresh component file; it declares lazy pages and exports `router`. */
/**
 * Router — Application routing with RBAC-protected routes.
 *
 * Dashboard pages are code-split with React.lazy so the initial bundle only
 * carries the login screen; each feature loads on demand behind a Suspense
 * fallback.
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
import { lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import type { UserRole } from '@/types';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardLayout } from '@/components/layout';
import { LoadingSpinner } from '@/components/ui';
import { LoginPage } from '@/features/auth/pages/LoginPage';

// Lazy-loaded feature pages (each becomes its own chunk).
const MapPage = lazy(() => import('@/features/map/pages/MapPage').then((m) => ({ default: m.MapPage })));
const AssessmentPage = lazy(() => import('@/features/assessment/pages/AssessmentPage').then((m) => ({ default: m.AssessmentPage })));
const ResultsPage = lazy(() => import('@/features/results/pages/ResultsPage').then((m) => ({ default: m.ResultsPage })));
const AnalysisPage = lazy(() => import('@/features/analysis/pages/AnalysisPage').then((m) => ({ default: m.AnalysisPage })));
const ExportPage = lazy(() => import('@/features/export/pages/ExportPage').then((m) => ({ default: m.ExportPage })));
const ShapefileImportPage = lazy(() => import('@/features/data/pages/ShapefileImportPage').then((m) => ({ default: m.ShapefileImportPage })));
const ScreeningPage = lazy(() => import('@/features/screening/pages/ScreeningPage').then((m) => ({ default: m.ScreeningPage })));
const UserManagementPage = lazy(() => import('@/features/admin/pages/UserManagementPage').then((m) => ({ default: m.UserManagementPage })));
const LayerConfigPage = lazy(() => import('@/features/admin/pages/LayerConfigPage').then((m) => ({ default: m.LayerConfigPage })));
const AuditLogPage = lazy(() => import('@/features/admin/pages/AuditLogPage').then((m) => ({ default: m.AuditLogPage })));
const SystemHealthPage = lazy(() => import('@/features/dev/pages/SystemHealthPage').then((m) => ({ default: m.SystemHealthPage })));
const ProcessingLogsPage = lazy(() => import('@/features/dev/pages/ProcessingLogsPage').then((m) => ({ default: m.ProcessingLogsPage })));
const DebugPage = lazy(() => import('@/features/dev/pages/DebugPage').then((m) => ({ default: m.DebugPage })));

/** Wraps a lazily-loaded element in a Suspense boundary with a spinner. */
function page(node: ReactNode): ReactNode {
  return (
    <Suspense
      fallback={
        <div className="flex h-full min-h-[50vh] items-center justify-center">
          <LoadingSpinner size="lg" label="Carregando..." />
        </div>
      }
    >
      {node}
    </Suspense>
  );
}

// Operational pages: any operational role.
const OPERATIONAL_ROLES: UserRole[] = ['operador', 'administrador', 'desenvolvedor'];
// Admin pages: administrator and developer.
const ADMIN_ROLES: UserRole[] = ['administrador', 'desenvolvedor'];
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
      { path: 'map', element: page(<MapPage />) },

      // MESA flow — analysis/assessment/results/export
      {
        path: 'analysis',
        element: <ProtectedRoute allowedRoles={OPERATIONAL_ROLES}>{page(<AnalysisPage />)}</ProtectedRoute>,
      },
      {
        path: 'assessment',
        element: <ProtectedRoute allowedRoles={OPERATIONAL_ROLES}>{page(<AssessmentPage />)}</ProtectedRoute>,
      },
      {
        path: 'results',
        element: <ProtectedRoute allowedRoles={OPERATIONAL_ROLES}>{page(<ResultsPage />)}</ProtectedRoute>,
      },
      {
        path: 'export',
        element: <ProtectedRoute allowedRoles={OPERATIONAL_ROLES}>{page(<ExportPage />)}</ProtectedRoute>,
      },
      {
        path: 'screening',
        element: <ProtectedRoute allowedRoles={OPERATIONAL_ROLES}>{page(<ScreeningPage />)}</ProtectedRoute>,
      },

      // Data — ingestion/import (HU-31)
      {
        path: 'data/shapefiles',
        element: <ProtectedRoute allowedRoles={OPERATIONAL_ROLES}>{page(<ShapefileImportPage />)}</ProtectedRoute>,
      },

      // Administration
      {
        path: 'admin/users',
        element: <ProtectedRoute allowedRoles={ADMIN_ROLES}>{page(<UserManagementPage />)}</ProtectedRoute>,
      },
      {
        path: 'admin/layers',
        element: <ProtectedRoute allowedRoles={ADMIN_ROLES}>{page(<LayerConfigPage />)}</ProtectedRoute>,
      },
      {
        path: 'admin/audit',
        element: <ProtectedRoute allowedRoles={ADMIN_ROLES}>{page(<AuditLogPage />)}</ProtectedRoute>,
      },

      // System technical operations
      {
        path: 'dev/health',
        element: <ProtectedRoute allowedRoles={DEV_ROLES}>{page(<SystemHealthPage />)}</ProtectedRoute>,
      },
      {
        path: 'dev/logs',
        element: <ProtectedRoute allowedRoles={DEV_ROLES}>{page(<ProcessingLogsPage />)}</ProtectedRoute>,
      },
      {
        path: 'dev/debug',
        element: <ProtectedRoute allowedRoles={DEV_ROLES}>{page(<DebugPage />)}</ProtectedRoute>,
      },
    ],
  },
  { path: '/', element: <Navigate to="/dashboard/map" replace /> },
  { path: '*', element: <Navigate to="/dashboard/map" replace /> },
]);
