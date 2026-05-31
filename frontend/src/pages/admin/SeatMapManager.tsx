import { useState, useEffect } from 'react';
import { Card, Button, Modal, Form, Input, InputNumber, message, Space, Select, Empty } from 'antd';
import { api } from '../../services/api';

export default function SeatMapManager() {
  const [layouts, setLayouts] = useState<any[]>([]);
  const [activeLayout, setActiveLayout] = useState<any>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [previewRotation, setPreviewRotation] = useState(0);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form] = Form.useForm();

  const fetchLayouts = async () => {
    setLoading(true);
    try {
      const data: any[] = await api.get('/admin/layouts');
      setLayouts(data);
      const active = data.find(l => l.is_active);
      if (active) {
        setActiveLayout(active);
      } else {
        setActiveLayout(null);
      }
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLayouts();
  }, []);

  const handleCreate = async (values: any) => {
    try {
      setCreating(true);
      const res: any = await api.post('/admin/layouts', values);
      message.success('创建成功');
      setLayouts((prev) => [res, ...prev.filter((item) => item.id !== res.id)]);
      setActiveLayout(res);
      setIsModalVisible(false);
      form.resetFields();
      await fetchLayouts();
    } catch (e) {}
    finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>座位图管理</h2>
        <Space>
          <Select 
            style={{ width: 200 }} 
            value={activeLayout?.id} 
            options={layouts.map(l => ({ label: l.name, value: l.id }))}
            onChange={async (val) => {
              await api.put(`/admin/layouts/${val}`, { is_active: true });
              fetchLayouts();
            }}
          />
          <Button onClick={() => setPreviewRotation(r => (r + 90) % 360)}>旋转预览方位</Button>
          <Button type="primary" onClick={() => setIsModalVisible(true)}>新建布局</Button>
        </Space>
      </div>

      {activeLayout ? (
        <Card 
          loading={loading}
          title={`当前布局: ${activeLayout.name} (${activeLayout.rows}x${activeLayout.cols})`}
          extra={<span style={{color: '#888'}}>提示：点击座位可将其标记为过道/隐藏</span>}
          style={{ overflow: 'hidden' }}
        >
          <div style={{ padding: 60, display: 'flex', justifyContent: 'center' }}>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: `repeat(${activeLayout.cols}, 1fr)`,
              gap: 8,
              transform: `rotate(${previewRotation}deg)`,
              transition: 'transform 0.5s ease',
              width: 'max-content'
            }}>
              {activeLayout.seats.map((seat: any) => (
                <div 
                  key={seat.id} 
                  onClick={async () => {
                    try {
                      const currentTags = Array.isArray(seat.tags) ? seat.tags : [];
                      const newTags = currentTags.includes('hidden') ? ['normal'] : ['hidden'];
                      await api.put(`/admin/seats/${seat.id}`, { tags: newTags });
                      fetchLayouts();
                    } catch (e) {}
                  }}
                  style={{
                    border: '1px solid #d9d9d9',
                    borderRadius: 4,
                    padding: 8,
                    textAlign: 'center',
                    cursor: 'pointer',
                    opacity: seat.tags?.includes('hidden') ? 0.2 : 1,
                    background: seat.status === 'locked' ? '#f5f5f5' : '#fff',
                    transform: `rotate(-${previewRotation}deg)`,
                    transition: 'transform 0.5s ease, opacity 0.3s ease',
                    minWidth: 50,
                    minHeight: 50,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center'
                  }}
                >
                  <div style={{ fontWeight: 'bold' }}>{seat.seat_code}</div>
                  <div style={{ fontSize: 12, color: '#888' }}>{seat.status}</div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      ) : (
        <Card loading={loading}>
          <Empty description="暂无配置好的座位图数据，请新建布局" />
        </Card>
      )}

      <Modal title="新建教室布局" open={isModalVisible} onCancel={() => setIsModalVisible(false)} onOk={() => form.submit()} confirmLoading={creating}>
        <Form form={form} layout="vertical" onFinish={handleCreate} initialValues={{ rows: 8, cols: 8 }}>
          <Form.Item name="name" label="布局名称" rules={[{ required: true }]}><Input placeholder="如：高一(1)班标准教室" /></Form.Item>
          <Form.Item name="rows" label="行数" rules={[{ required: true }]}><InputNumber min={1} max={30} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="cols" label="列数" rules={[{ required: true }]}><InputNumber min={1} max={30} style={{ width: '100%' }} /></Form.Item>
          <div style={{color: '#888', marginTop: 16}}>
            提示：创建完成后，你可以在布局图中点击特定座位将其设置为“过道”进行隐藏。
          </div>
        </Form>
      </Modal>
    </div>
  );
}
