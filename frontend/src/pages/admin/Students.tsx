import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, message, Space, Upload } from 'antd';
import { UploadOutlined, PlusOutlined } from '@ant-design/icons';
import { api } from '../../services/api';

export default function Students() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [credentialModalOpen, setCredentialModalOpen] = useState(false);
  const [createdCredentials, setCreatedCredentials] = useState<any[]>([]);
  const [form] = Form.useForm();

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const data: any[] = await api.get('/admin/students');
      setStudents(data);
    } catch (e) {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, []);

  const handleAdd = async (values: any) => {
    try {
      await api.post('/admin/students', { ...values, role: 'student', password: '123456', must_change_password: true });
      message.success('添加成功，学生首次登录时将被强制修改密码');
      setIsModalVisible(false);
      form.resetFields();
      fetchStudents();
    } catch (e) {}
  };

  const showCreatedCredentials = (credentials: any[]) => {
    if (!Array.isArray(credentials) || credentials.length === 0) {
      return;
    }
    setCreatedCredentials(credentials);
    setCredentialModalOpen(true);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id' },
    { title: '学号', dataIndex: 'student_id' },
    { title: '登录名', dataIndex: 'username' },
    { title: '姓名', dataIndex: 'full_name' },
    { title: '德育学分', dataIndex: 'moral_score' },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>学生管理</h2>
        <Space>
          <Upload
            accept=".xlsx, .xls"
            showUploadList={false}
            customRequest={async (options) => {
              const formData = new FormData();
              formData.append('file', options.file as Blob);
              try {
                const res: any = await api.post('/admin/score-import-excel', formData);
                message.success(`导入成功: 更新/新增 ${res.updated_count} 条`);
                showCreatedCredentials(res.created_students || []);
                fetchStudents();
              } catch (e) {}
            }}
          >
            <Button icon={<UploadOutlined />}>导入学生/学分 (Excel)</Button>
          </Upload>
          <Upload
            accept=".json"
            showUploadList={false}
            customRequest={async (options) => {
              const formData = new FormData();
              formData.append('file', options.file as Blob);
              try {
                const res: any = await api.post('/admin/students/import-scores', formData);
                message.success(`导入成功: 更新 ${res.updated_count} 条`);
                fetchStudents();
              } catch (e) {}
            }}
          >
            <Button icon={<UploadOutlined />}>导入学分 (JSON)</Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>添加学生</Button>
        </Space>
      </div>
      <Table rowKey="id" columns={columns} dataSource={students} loading={loading} />

      <Modal title="添加学生" open={isModalVisible} onCancel={() => setIsModalVisible(false)} onOk={() => form.submit()}>
        <Form form={form} onFinish={handleAdd} layout="vertical">
          <Form.Item name="username" label="登录名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="full_name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="student_id" label="学号"><Input /></Form.Item>
          <Form.Item name="moral_score" label="德育学分" initialValue={0}><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新建学生临时账号信息"
        open={credentialModalOpen}
        footer={null}
        onCancel={() => setCredentialModalOpen(false)}
        width={720}
      >
        <p style={{ marginBottom: 16 }}>请通过安全渠道把以下临时密码发给学生，学生首次登录后必须修改密码。</p>
        <Table
          rowKey="student_id"
          pagination={false}
          dataSource={createdCredentials}
          columns={[
            { title: '学号', dataIndex: 'student_id' },
            { title: '登录名', dataIndex: 'username' },
            { title: '临时密码', dataIndex: 'temporary_password' },
          ]}
        />
      </Modal>
    </div>
  );
}
