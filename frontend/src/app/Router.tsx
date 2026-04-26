/**
 * Router — Application routing with RBAC-protected routes.
 *
 * Route structure:
 * - /login                    → Public
 * - /dashboard/*              → Protected (authenticated)
 *   - /dashboard/map          → All roles
 *   - /dashboard/analysis     → analyst
 *   - /dashboard/assessment   → analyst
 *   - /dashboard/results      → analyst, admin
 *   - /dashboard/export       → analyst
 *   - /dashboard/admin/*      → admin only
 *   - /dashboard/dev/*        → dev only
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { MapPage } from '@/features/map/pages/MapPage';
import { AssessmentPage } from '@/features/assessment/pages/AssessmentPage';
import { ResultsPage } from '@/features/results/pages/ResultsPage';
import { AnalysisPage } from '@/features/analysis/pages/AnalysisPage';
import { ExportPage } from '@/features/export/pages/ExportPage';
import { UserManagementPage } from '@/features/admin/pages/UserManagementPage';
import { LayerConfigPage } from '@/features/admin/pages/LayerConfigPage';
import { AuditLogPage } from '@/features/admin/pages/AuditLogPage';
import { ApiHealthPage } from '@/features/dev/pages/ApiHealthPage';
import { ProcessingLogsPage } from '@/features/dev/pages/ProcessingLogsPage';
import { DebugPage } from '@/features/dev/pages/DebugPage';

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

      // Analyst routes
      {
        path: 'analysis',
        element: <ProtectedRoute allowedRoles={['analyst']}><AnalysisPage /></ProtectedRoute>,
      },
      {
        path: 'assessment',
        element: <ProtectedRoute allowedRoles={['analyst']}><AssessmentPage /></ProtectedRoute>,
      },
      {
        path: 'results',
        element: <ProtectedRoute allowedRoles={['analyst', 'admin']}><ResultsPage /></ProtectedRoute>,
      },
      {
        path: 'export',
        element: <ProtectedRoute allowedRoles={['analyst']}><ExportPage /></ProtectedRoute>,
      },

      // Admin routes
      {
        path: 'admin/users',
        element: <ProtectedRoute allowedRoles={['admin']}><UserManagementPage /></ProtectedRoute>,
      },
      {
        path: 'admin/layers',
        element: <ProtectedRoute allowedRoles={['admin']}><LayerConfigPage /></ProtectedRoute>,
      },
      {
        path: 'admin/audit',
        element: <ProtectedRoute allowedRoles={['admin']}><AuditLogPage /></ProtectedRoute>,
      },

      // Dev routes
      {
        path: 'dev/health',
        element: <ProtectedRoute allowedRoles={['dev']}><ApiHealthPage /></ProtectedRoute>,
      },
      {
        path: 'dev/logs',
        element: <ProtectedRoute allowedRoles={['dev']}><ProcessingLogsPage /></ProtectedRoute>,
      },
      {
        path: 'dev/debug',
        element: <ProtectedRoute allowedRoles={['dev']}><DebugPage /></ProtectedRoute>,
      },
    ],
  },
  { path: '/', element: <Navigate to="/dashboard/map" replace /> },
  { path: '*', element: <Navigate to="/dashboard/map" replace /> },
]);
