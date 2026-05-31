import { Button, Card, Form, Input, Typography, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/useAuthStore';

const { Title, Paragraph } = Typography;

const getHomePath = (role: 'student' | 'admin') => (role === 'admin' ? '/admin/dashboard' : '/student/hall');

interface ChangePasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

const PASSWORD_MIN_LENGTH = 8;
const PASSWORD_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;

export default function ChangePassword() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();
  const [form] = Form.useForm<ChangePasswordForm>();

  const onFinish = async (values: ChangePasswordForm) => {
    try {
      setLoading(true);
      const response = await api.post('/auth/change-password', {
        current_password: values.current_password,
        new_password: values.new_password,
      });
      
      if (response && response.role) {
        setUser(response);
        message.success('密码修改成功');
        navigate(getHomePath(response.role));
      } else {
        message.success('密码修改成功');
        navigate(getHomePath(user?.role || 'student'));
      }
    } catch (e) {
      console.error('Password change failed:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 460, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3}>首次登录修改密码</Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {user?.full_name ? `${user.full_name}，请先修改初始密码后再继续使用系统。` : '请先修改初始密码后再继续使用系统。'}
          </Paragraph>
        </div>
        <Form form={form} name="change-password" onFinish={onFinish} size="large" layout="vertical">
          <Form.Item name="current_password" label="当前密码" rules={[{ required: true, message: '请输入当前密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="请输入当前密码" />
          </Form.Item>
          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: PASSWORD_MIN_LENGTH, message: `新密码至少 ${PASSWORD_MIN_LENGTH} 位` },
              { pattern: PASSWORD_PATTERN, message: '密码必须包含大小写字母和数字' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || value !== getFieldValue('current_password')) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('新密码不能与当前密码相同'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入新密码" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            label="确认新密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请再次输入新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的新密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请再次输入新密码" />
          </Form.Item>
          <Paragraph type="secondary" style={{ fontSize: 12, marginTop: -8, marginBottom: 16 }}>
            密码要求：至少 {PASSWORD_MIN_LENGTH} 位，包含大小写字母和数字
          </Paragraph>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block loading={loading}>
              保存新密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
