import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuthStore } from '../../stores/useAuthStore';
import { api } from '../../services/api';

const { Title } = Typography;

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      const tokenRes: any = await api.post('/auth/login', {
        username: values.username,
        password: values.password
      });
      
      const userRes: any = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${tokenRes.access_token}` }
      });

      setAuth(tokenRes.access_token, userRes);
      message.success('登录成功');

      if (userRes.must_change_password) {
        navigate('/change-password');
      } else if (userRes.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/student/hall');
      }
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3}>德育学分座次选择系统</Title>
        </div>
        <Form name="login" onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入账号' }]}>
            <Input prefix={<UserOutlined />} placeholder="账号 (默认admin)" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码 (默认admin123456)" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
