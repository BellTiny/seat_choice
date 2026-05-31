import { Layout, Menu, Button, Dropdown } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { 
  AppstoreOutlined, 
  IdcardOutlined, 
  SwapOutlined, 
  MessageOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons';

const { Header, Content } = Layout;

export default function StudentLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const menuItems = [
    { key: '/student/hall', icon: <AppstoreOutlined />, label: '选座大厅' },
    { key: '/student/seats', icon: <IdcardOutlined />, label: '我的座位' },
    { key: '/student/swap', icon: <SwapOutlined />, label: '换座申请' },
    { key: '/student/messages', icon: <MessageOutlined />, label: '消息中心' },
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
      <Header style={{ background: '#fff', display: 'flex', alignItems: 'center', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
        <div style={{ fontWeight: 'bold', fontSize: 18, marginRight: 48, color: '#1677ff' }}>
          德育选座系统
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, borderBottom: 'none' }}
        />
        <div>
          <Dropdown menu={userMenu} placement="bottomRight">
            <Button type="text" icon={<UserOutlined />}>
              {user?.full_name || '学生'}
            </Button>
          </Dropdown>
        </div>
      </Header>
      <Content style={{ padding: '24px 50px', background: '#f5f5f5' }}>
        <div style={{ background: '#fff', padding: 24, minHeight: 'calc(100vh - 112px)', borderRadius: 8 }}>
          <Outlet />
        </div>
      </Content>
    </Layout>
  );
}
