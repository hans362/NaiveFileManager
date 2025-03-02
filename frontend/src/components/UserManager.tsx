import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
} from 'antd';
import {
  UserOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import axios from 'axios';

interface User {
  username: string;
  base_dir: string;
}

const UserManager: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/user/list');
      if (response.data.status === 'success') {
        setUsers(response.data.data);
      }
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSubmit = async (values: any) => {
    try {
      const formData = new FormData();
      formData.append('username', values.username);
      formData.append('password', values.password || '');
      formData.append('base_dir', values.base_dir || '/');

      const url = editingUser
        ? '/api/user/update'
        : '/api/user/create';
      const method = editingUser ? 'patch' : 'put';

      const response = await axios({
        method,
        url,
        data: formData,
      });

      if (response.data.status === 'success') {
        message.success(editingUser ? '更新成功' : '创建成功');
        setModalVisible(false);
        form.resetFields();
        fetchUsers();
      } else {
        message.error(response.data.message || '操作失败');
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleDelete = async (username: string) => {
    try {
      const formData = new FormData();
      formData.append('username', username);
      const response = await axios.delete('/api/user/delete', { data: formData });
      if (response.data.status === 'success') {
        message.success('删除成功');
        fetchUsers();
      } else {
        message.error(response.data.message || '删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '基础目录',
      dataIndex: 'base_dir',
      key: 'base_dir',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: User) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingUser(record);
              form.setFieldsValue(record);
              setModalVisible(true);
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.username)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        style={{ marginBottom: 16 }}
        onClick={() => {
          setEditingUser(null);
          form.resetFields();
          setModalVisible(true);
        }}
      >
        添加用户
      </Button>

      <Table
        columns={columns}
        dataSource={users}
        loading={loading}
        rowKey="username"
      />

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password />
            </Form.Item>
          )}

          <Form.Item
            name="base_dir"
            label="基础目录"
            initialValue="/"
          >
            <Input />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit">
              {editingUser ? '更新' : '创建'}
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManager; 