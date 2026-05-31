import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, message, Tag, Popconfirm } from 'antd';
import { api } from '../../services/api';

export default function Console() {
  const [rounds, setRounds] = useState<any[]>([]);
  const [currentRound, setCurrentRound] = useState<any>(null);
  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const semRes: any[] = await api.get('/admin/semesters');
      const activeSem = semRes.find((s) => s.is_active);
      setCurrentRound(null);
      setQueue([]);
      if (activeSem) {
        const roundRes: any[] = await api.get(`/admin/semesters/${activeSem.id}/rounds`);
        setRounds(roundRes);
        const activeRound = roundRes.find((r) => r.status !== 'finished');
        if (activeRound) {
          setCurrentRound(activeRound);
          const queueRes: any[] = await api.get(`/admin/rounds/${activeRound.id}/queue`);
          setQueue(queueRes);
        }
      }
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAction = async (action: string) => {
    if (!currentRound) return;
    try {
      await api.post(`/admin/rounds/${currentRound.id}/${action}`);
      message.success('操作成功');
      fetchData();
    } catch (e) {}
  };

  const columns = [
    { title: '排名', dataIndex: 'rank_order' },
    { title: '学号', dataIndex: 'student_code' },
    { title: '姓名', dataIndex: 'student_name' },
    { title: '状态', dataIndex: 'status', render: (s: string) => {
      const colorMap: any = { pending: 'default', current: 'processing', completed: 'success', skipped: 'warning', locked: 'error' };
      return <Tag color={colorMap[s]}>{s}</Tag>;
    }},
    { title: '阶段', dataIndex: 'phase' },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>选座控制台</h2>
        {currentRound && (
          <Space>
            <Tag color={currentRound.site_open ? 'success' : 'default'}>
              站点状态: {currentRound.site_open ? '开放' : '关闭'}
            </Tag>
            <Tag color="blue">阶段: {currentRound.selection_phase}</Tag>
            {currentRound.site_open ? (
              <Button danger onClick={() => handleAction('close-site')}>关闭系统选座入口</Button>
            ) : (
              <Button type="primary" onClick={() => handleAction('open-site')}>开放系统选座入口</Button>
            )}
            <Button type="primary" onClick={() => handleAction('prepare')} disabled={currentRound.status !== 'not_started'}>
              准备排名
            </Button>
            <Popconfirm title="确定推进到下一批？" onConfirm={() => handleAction('next')}>
              <Button type="primary" disabled={currentRound.status === 'finished'}>下一位</Button>
            </Popconfirm>
            <Popconfirm title="确定跳过当前学生？" onConfirm={() => handleAction('skip')}>
              <Button danger disabled={currentRound.status === 'finished'}>跳过</Button>
            </Popconfirm>
            <Popconfirm title="开启补选？" onConfirm={() => handleAction('start-makeup')}>
              <Button disabled={currentRound.status === 'finished' || currentRound.selection_phase === 'makeup'}>开启补选</Button>
            </Popconfirm>
            <Popconfirm title="结束本轮？" onConfirm={() => handleAction('finish')}>
              <Button danger disabled={currentRound.status === 'finished'}>结束轮次</Button>
            </Popconfirm>
          </Space>
        )}
      </div>

      <Card title={currentRound ? `当前轮次: ${currentRound.name}` : '暂无活跃轮次'}>
        <Table 
          rowKey="id" 
          columns={columns} 
          dataSource={queue} 
          loading={loading}
          pagination={{ pageSize: 50 }}
          rowClassName={(record) => record.status === 'current' ? 'current-row' : ''}
        />
      </Card>
      <style>{`
        .current-row { background-color: #e6f4ff; }
      `}</style>
    </div>
  );
}
