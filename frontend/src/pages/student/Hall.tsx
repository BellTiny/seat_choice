import { useState, useEffect } from 'react';
import { Card, Button, message, Tag, Modal, Empty } from 'antd';
import { api } from '../../services/api';

export default function Hall() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rotation, setRotation] = useState(0);

  const fetchStatus = async () => {
    try {
      const data: any = await api.get('/student/selection/status');
      setStatus(data);
      // Initialize rotation from server default if not yet set manually
      setRotation(prev => {
        if (prev === 0 && data.default_orientation !== undefined) {
          return data.default_orientation;
        }
        return prev;
      });
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleSelectSeat = (seat: any) => {
    if (!status?.can_select) return;
    if (seat.status !== 'available') {
      message.warning('该座位不可选');
      return;
    }
    
    Modal.confirm({
      title: '确认选座',
      content: `确定选择座位 ${seat.seat_code} 吗？`,
      onOk: async () => {
        try {
          await api.post('/student/selection/choose', { seat_ids: [seat.id] });
          message.success('选座成功！');
          fetchStatus();
        } catch (e) {}
      }
    });
  };

  if (loading && !status) {
    return (
      <Card>
        <Empty description="暂无进行中的选座数据" />
      </Card>
    );
  }

  if (!status || !status.round_id || !Array.isArray(status.seats)) {
    return (
      <Card>
        <Empty description="暂无进行中的选座数据" />
      </Card>
    );
  }

  const { site_open, can_select, queue_status, queue_rank, seats } = status;
  const maxCol = seats.length ? Math.max(...seats.map((s: any) => s.col_index)) + 1 : 1;

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3>选座状态</h3>
            <div>您的排队位置: <strong>{queue_rank || '未知'}</strong></div>
            <div>当前状态: <Tag color={can_select ? 'success' : 'default'}>{can_select ? '请选座！' : (queue_status || '等待中')}</Tag></div>
          </div>
          <div>
            {!site_open && <Tag color="error">选座网站当前未开放</Tag>}
          </div>
        </div>
      </Card>

      <Card 
        title="教室座位图"
        extra={<Button onClick={() => setRotation(r => (r + 90) % 360)}>旋转调整方位</Button>}
        style={{ overflow: 'hidden' }}
      >
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center' }}><div style={{ width: 16, height: 16, background: '#f5f5f5', border: '1px solid #d9d9d9', marginRight: 8 }} /> 可选</div>
          <div style={{ display: 'flex', alignItems: 'center' }}><div style={{ width: 16, height: 16, background: '#ffccc7', border: '1px solid #ff4d4f', marginRight: 8 }} /> 已选</div>
          <div style={{ display: 'flex', alignItems: 'center' }}><div style={{ width: 16, height: 16, background: '#d9d9d9', border: '1px solid #8c8c8c', marginRight: 8 }} /> 锁定</div>
        </div>
        
        <div style={{ padding: 60, display: 'flex', justifyContent: 'center' }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: `repeat(${maxCol}, 1fr)`,
            gap: 8,
            transform: `rotate(${rotation}deg)`,
            transition: 'transform 0.5s ease',
            width: 'max-content'
          }}>
            {seats.map((seat: any) => {
              let bg = '#f5f5f5';
              let border = '1px solid #d9d9d9';
              if (seat.status === 'selected') {
                bg = '#ffccc7';
                border = '1px solid #ff4d4f';
              } else if (seat.status === 'locked') {
                bg = '#d9d9d9';
                border = '1px solid #8c8c8c';
              }

              return (
                <div 
                  key={seat.id} 
                  onClick={() => handleSelectSeat(seat)}
                  style={{
                    border,
                    background: bg,
                    borderRadius: 4,
                    padding: '12px 8px',
                    textAlign: 'center',
                    cursor: (can_select && seat.status === 'available') ? 'pointer' : 'not-allowed',
                    opacity: seat.tags?.includes('hidden') ? 0 : (seat.status === 'available' ? 1 : 0.8),
                    visibility: seat.tags?.includes('hidden') ? 'hidden' : 'visible',
                    transform: `rotate(-${rotation}deg)`,
                    transition: 'transform 0.5s ease, opacity 0.3s ease',
                    minWidth: 50,
                    minHeight: 50,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center'
                  }}
                >
                  <div style={{ fontWeight: 'bold' }}>{seat.seat_code}</div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>
    </div>
  );
}
