import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuthStore } from './stores/useAuthStore';

import Login from './pages/auth/Login';
import ChangePassword from './pages/auth/ChangePassword';
import StudentLayout from './components/layout/StudentLayout';
import AdminLayout from './components/layout/AdminLayout';

import Hall from './pages/student/Hall';
import Seats from './pages/student/Seats';
import Swap from './pages/student/Swap';
import Messages from './pages/student/Messages';

import Dashboard from './pages/admin/Dashboard';
import Console from './pages/admin/Console';
import SeatMapManager from './pages/admin/SeatMapManager';
import Students from './pages/admin/Students';
import Settings from './pages/admin/Settings';
import AuditSwap from './pages/admin/AuditSwap';
import AuditSpecial from './pages/admin/AuditSpecial';

const ProtectedRoute = ({ children, role }: { children: React.ReactNode; role: 'student' | 'admin' }) => {
  const { token, user } = useAuthStore();
  if (!token || !user) return <Navigate to="/login" replace />;
  if (user.must_change_password) {
    return <Navigate to="/change-password" replace />;
  }
  if (user.role !== role) {
    return <Navigate to={user.role === 'admin' ? '/admin/dashboard' : '/student/hall'} replace />;
  }
  return <>{children}</>;
};

const ChangePasswordRoute = () => {
  const { token, user } = useAuthStore();
  if (!token || !user) return <Navigate to="/login" replace />;
  if (!user.must_change_password) {
    return <Navigate to={user.role === 'admin' ? '/admin/dashboard' : '/student/hall'} replace />;
  }
  return <ChangePassword />;
};

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#1677ff' } }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/change-password" element={<ChangePasswordRoute />} />
          
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Student Routes */}
          <Route path="/student" element={<ProtectedRoute role="student"><StudentLayout /></ProtectedRoute>}>
            <Route path="hall" element={<Hall />} />
            <Route path="seats" element={<Seats />} />
            <Route path="swap" element={<Swap />} />
            <Route path="messages" element={<Messages />} />
            <Route index element={<Navigate to="/student/hall" replace />} />
          </Route>

          {/* Admin Routes */}
          <Route path="/admin" element={<ProtectedRoute role="admin"><AdminLayout /></ProtectedRoute>}>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="console" element={<Console />} />
            <Route path="seats" element={<SeatMapManager />} />
            <Route path="students" element={<Students />} />
            <Route path="settings" element={<Settings />} />
            <Route path="audit/swap" element={<AuditSwap />} />
            <Route path="audit/special" element={<AuditSpecial />} />
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
