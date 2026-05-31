import { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Switch, Button, message, Card, Select } from 'antd';
import { api } from '../../services/api';

export default function Settings() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await api.get('/admin/settings');
        form.setFieldsValue(data);
      } catch (e) {}
    };
    fetchSettings();
  }, [form]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await api.put('/admin/settings', values);
      message.success('设置保存成功');
    } catch (e) {} finally {
      setLoading(false);
    }
  };

  return (
    <Card title="系统设置">
      <Form form={form} layout="vertical" onFinish={onFinish} style={{ maxWidth: 600 }}>
        <Form.Item name="max_swap_count" label="每轮最大换座次数"><InputNumber min={0} /></Form.Item>
        <Form.Item name="swap_reason_required" label="换座必须填写理由" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="team_enabled" label="允许组队选座" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="team_max_carry" label="组队最大携带人数"><InputNumber min={1} /></Form.Item>
        <Form.Item name="team_adjacent_required" label="组队必须相邻" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="special_request_open" label="开放特殊需求申请" valuePropName="checked"><Switch /></Form.Item>
        <Form.Item name="default_orientation" label="学生端默认座位图方位">
          <Select options={[
            { label: '讲台在上方 (0°)', value: 0 },
            { label: '讲台在右侧 (90°)', value: 90 },
            { label: '讲台在下方 (180°)', value: 180 },
            { label: '讲台在左侧 (270°)', value: 270 },
          ]} />
        </Form.Item>
        <Form.Item name="webhook_url" label="Webhook URL"><Input /></Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>保存设置</Button>
        </Form.Item>
      </Form>
    </Card>
  );
}
