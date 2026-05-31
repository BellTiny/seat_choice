import { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, message, Tag } from 'antd';
import { api } from '../../services/api';

export default function Swap() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const data: any[] = await api.get('/student/swaps');
      setRequests(data);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleApply = async (values: any) => {
    try {
      await api.post('/student/swaps', values);
      message.success('申请提交成功');
      setIsModalVisible(false);
      form.resetFields();
      fetchRequests();
    } catch (e) {}
  };

  const columns = [
    { title: '发起人', dataIndex: 'requester_id', render: (_: any, r: any) => r.requester?.full_name },
    { title: '目标对象', dataIndex: 'target_id', render: (_: any, r: any) => r.target?.full_name },
    { title: '理由', dataIndex: 'reason' },
    { title: '状态', dataIndex: 'status', render: (s: string) => {
      const colorMap: any = { pending_target: 'warning', pending_admin: 'processing', approved: 'success', rejected: 'error' };
      return <Tag color={colorMap[s]}>{s}</Tag>;
    }},
    { title: '审批意见', dataIndex: 'review_comment' },
    { title: '操作', render: (_: any, r: any) => {
      // If current user is the target and status is pending_target, they can respond
      // In a real app we'd check against current user ID
      return null;
    }}
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>换座申请</h2>
        <Button type="primary" onClick={() => setIsModalVisible(true)}>发起换座申请</Button>
      </div>

      <Card>
        <Table 
          rowKey="id" 
          columns={columns} 
          dataSource={requests} 
          loading={loading}
        />
      </Card>

      <Modal title="发起换座" open={isModalVisible} onCancel={() => setIsModalVisible(false)} onOk={() => form.submit()}>
        <Form form={form} layout="vertical" onFinish={handleApply}>
          <Form.Item name="target_student_id" label="目标学号" rules={[{ required: true }]}><Input placeholder="输入你想交换座位的同学学号" /></Form.Item>
          <Form.Item name="reason" label="申请理由" rules={[{ required: true }]}><Input.TextArea rows={4} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
