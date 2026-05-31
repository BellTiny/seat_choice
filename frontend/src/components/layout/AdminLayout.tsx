import { Layout, Menu, Button, Dropdown } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { 
  DashboardOutlined, 
  ControlOutlined, 
  AppstoreOutlined, 
  TeamOutlined, 
  SettingOutlined, 
  SwapOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const menuItems = [
    { key: '/admin/dashboard', icon: <DashboardOutlined />, label: '数据仪表盘' },
    { key: '/admin/console', icon: <ControlOutlined />, label: '选座控制台' },
    { key: '/admin/seats', icon: <AppstoreOutlined />, label: '座位图管理' },
    { key: '/admin/students', icon: <TeamOutlined />, label: '学生管理' },
    { key: '/admin/audit/swap', icon: <SwapOutlined />, label: '换座审核' },
    { key: '/admin/audit/special', icon: <ExclamationCircleOutlined />, label: '特殊需求审批' },
    { key: '/admin/settings', icon: <SettingOutlined />, label: '系统设置' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenu = {
    items: [
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        onClick: handleLogout,
      },
    ],
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible theme="light">
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 16 }}>
          班级选座管理
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Button type="text" icon={<UserOutlined />}>
              {user?.full_name || '管理员'}
            </Button>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', borderRadius: 8, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
