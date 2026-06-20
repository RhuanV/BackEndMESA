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
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
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

      // Fluxo MESA — análise/avaliação/resultados/exportação
      {
        path: 'analysis',
        element: <ProtectedRoute allowedRoles={['coordenador', 'supervisor', 'operador']}><AnalysisPage /></ProtectedRoute>,
      },
      {
        path: 'assessment',
        element: <ProtectedRoute allowedRoles={['coordenador', 'gestor', 'operador']}><AssessmentPage /></ProtectedRoute>,
      },
      {
        path: 'results',
        element: <ProtectedRoute allowedRoles={['coordenador', 'gestor', 'supervisor', 'operador']}><ResultsPage /></ProtectedRoute>,
      },
      {
        path: 'export',
        element: <ProtectedRoute allowedRoles={['coordenador', 'gestor', 'supervisor', 'operador']}><ExportPage /></ProtectedRoute>,
      },
      {
        path: 'screening',
        element: <ProtectedRoute allowedRoles={['coordenador', 'gestor', 'operador']}><ScreeningPage /></ProtectedRoute>,
      },

      // Dados — ingestão/importação (HU-31)
      {
        path: 'data/shapefiles',
        element: <ProtectedRoute allowedRoles={['coordenador', 'gestor', 'supervisor', 'operador', 'administrador']}><ShapefileImportPage /></ProtectedRoute>,
      },

      // Administração
      {
        path: 'admin/users',
        element: <ProtectedRoute allowedRoles={['coordenador', 'gestor', 'supervisor']}><UserManagementPage /></ProtectedRoute>,
      },
      {
        path: 'admin/layers',
        element: <ProtectedRoute allowedRoles={['coordenador', 'administrador']}><LayerConfigPage /></ProtectedRoute>,
      },
      {
        path: 'admin/audit',
        element: <ProtectedRoute allowedRoles={['coordenador', 'administrador']}><AuditLogPage /></ProtectedRoute>,
      },

      // Operação técnica do sistema
      {
        path: 'dev/health',
        element: <ProtectedRoute allowedRoles={['administrador']}><ApiHealthPage /></ProtectedRoute>,
      },
      {
        path: 'dev/logs',
        element: <ProtectedRoute allowedRoles={['administrador']}><ProcessingLogsPage /></ProtectedRoute>,
      },
      {
        path: 'dev/debug',
        element: <ProtectedRoute allowedRoles={['administrador']}><DebugPage /></ProtectedRoute>,
      },
    ],
  },
  { path: '/', element: <Navigate to="/dashboard/map" replace /> },
  { path: '*', element: <Navigate to="/dashboard/map" replace /> },
]);
