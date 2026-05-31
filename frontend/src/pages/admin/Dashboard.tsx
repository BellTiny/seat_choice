import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { UserOutlined, TeamOutlined, DesktopOutlined } from '@ant-design/icons';
import { api } from '../../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    activeRound: '暂无',
    totalStudents: 0,
    selectedCount: 0,
    unselectedCount: 0,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const sems: any[] = await api.get('/admin/semesters');
        const activeSem = sems.find((s) => s.is_active);
        let roundName = '暂无活跃轮次';
        let selected = 0;
        let unselected = 0;

        if (activeSem) {
          const rounds: any[] = await api.get(`/admin/semesters/${activeSem.id}/rounds`);
          const activeRound = rounds.find((r) => r.status !== 'finished');
          if (activeRound) {
            roundName = activeRound.name;
            const queue: any[] = await api.get(`/admin/rounds/${activeRound.id}/queue`);
            selected = queue.filter(q => q.status === 'completed' || q.status === 'locked').length;
            unselected = queue.filter(q => q.status === 'pending' || q.status === 'current' || q.status === 'skipped').length;
          }
        }

        const students: any[] = await api.get('/admin/students');

        setStats({
          activeRound: roundName,
          totalStudents: students.length,
          selectedCount: selected,
          unselectedCount: unselected,
        });
      } catch (e) {}
    };
    fetchStats();
  }, []);

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>数据仪表盘</h2>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic title="当前轮次" value={stats.activeRound} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="系统学生总数" value={stats.totalStudents} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="本轮已选座人数" value={stats.selectedCount} prefix={<DesktopOutlined />} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="本轮待选座人数" value={stats.unselectedCount} prefix={<UserOutlined />} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
