import { useState, useEffect } from 'react';
import { Card, Table, Tag } from 'antd';
import { api } from '../../services/api';

export default function Seats() {
  const [selections, setSelections] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchSelections = async () => {
      setLoading(true);
      try {
        const data: any[] = await api.get('/student/selections/history');
        setSelections(data);
      } catch (e) {
      } finally {
        setLoading(false);
      }
    };
    fetchSelections();
  }, []);

  const columns = [
    { title: '轮次', dataIndex: 'round_id', render: (_: any, r: any) => r.round?.name },
    { title: '学期', dataIndex: 'semester', render: (_: any, r: any) => r.round?.semester?.name },
    { title: '座位号', dataIndex: 'seat_code', render: (_: any, r: any) => r.seat?.seat_code },
    { title: '分配类型', dataIndex: 'assignment_type', render: (t: string) => <Tag color="blue">{t}</Tag> },
    { title: '选择时间', dataIndex: 'created_at', render: (t: string) => new Date(t).toLocaleString() },
  ];

  return (
    <Card title="历史座位记录">
      <Table 
        rowKey="id" 
        columns={columns} 
        dataSource={selections} 
        loading={loading}
      />
    </Card>
  );
}
