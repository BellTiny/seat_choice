import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, message, Tag, Modal, Input } from 'antd';
import { api } from '../../services/api';

export default function AuditSwap() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reviewModal, setReviewModal] = useState<{visible: boolean, record: any, approve: boolean}>({visible: false, record: null, approve: true});
  const [comment, setComment] = useState('');

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const data: any[] = await api.get('/admin/swap-requests');
      setRequests(data);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleReview = async () => {
    try {
      await api.post(`/admin/swap-requests/${reviewModal.record.id}/review`, {
        approve: reviewModal.approve,
        review_comment: comment
      });
      message.success('审核成功');
      setReviewModal({visible: false, record: null, approve: true});
      setComment('');
      fetchRequests();
    } catch (e) {}
  };

  const columns = [
    { title: '轮次', dataIndex: 'round_id', render: (_: any, r: any) => r.round?.name },
    { title: '发起人', dataIndex: 'requester_id', render: (_: any, r: any) => r.requester?.full_name },
    { title: '目标对象', dataIndex: 'target_id', render: (_: any, r: any) => r.target?.full_name },
    { title: '理由', dataIndex: 'reason' },
    { title: '状态', dataIndex: 'status', render: (s: string) => {
      const colorMap: any = { pending_target: 'warning', pending_admin: 'processing', approved: 'success', rejected: 'error' };
      return <Tag color={colorMap[s]}>{s}</Tag>;
    }},
    { title: '操作', render: (_: any, r: any) => {
      if (r.status !== 'pending_admin') return null;
      return (
        <Space>
          <Button type="primary" size="small" onClick={() => setReviewModal({visible: true, record: r, approve: true})}>批准</Button>
          <Button danger size="small" onClick={() => setReviewModal({visible: true, record: r, approve: false})}>驳回</Button>
        </Space>
      );
    }}
  ];

  return (
    <Card title="换座审核">
      <Table 
        rowKey="id" 
        columns={columns} 
        dataSource={requests} 
        loading={loading}
        locale={{ emptyText: '暂无换座申请' }}
      />
      <Modal 
        title={reviewModal.approve ? "批准换座" : "驳回换座"}
        open={reviewModal.visible} 
        onCancel={() => setReviewModal({visible: false, record: null, approve: true})} 
        onOk={handleReview}
      >
        <div style={{ marginBottom: 8 }}>请输入审批意见：</div>
        <Input.TextArea rows={4} value={comment} onChange={e => setComment(e.target.value)} />
      </Modal>
    </Card>
  );
}
