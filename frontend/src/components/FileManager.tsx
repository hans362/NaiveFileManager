import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Breadcrumb,
  Upload,
  InputNumber,
  Select,
} from 'antd';
import {
  FolderOutlined,
  FileOutlined,
  UploadOutlined,
  DeleteOutlined,
  EditOutlined,
  SwapOutlined,
  LockOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

interface FileItem {
  name: string;
  size: number;
  type: 'dir' | 'file';
  target: string | null;
  gid: number;
  uid: number;
  last_modified: number;
  path: string; // 移除可选标记，使其成为必需属性
}

interface SystemUser {
  name: string;
  uid: number;
}

interface SystemGroup {
  name: string;
  gid: number;
}

interface SystemInfo {
  users: SystemUser[];
  groups: SystemGroup[];
}

const FileManager: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [moveModalVisible, setMoveModalVisible] = useState(false);
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [editingFile, setEditingFile] = useState<FileItem | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({ users: [], groups: [] });
  const [pagination, setPagination] = useState({ 
    current: 1, 
    pageSize: 10,  // 改回每页10条
    total: 0,
    showSizeChanger: false,  // 不显示分页大小选择器
  });
  const [form] = Form.useForm();
  const [moveForm] = Form.useForm();
  const [permissionForm] = Form.useForm();
  const [targetPath, setTargetPath] = useState<string | null>(null);

  const fetchSystemInfo = async () => {
    try {
      const [usersResponse, groupsResponse] = await Promise.all([
        axios.get('/api/system/user/list'),
        axios.get('/api/system/group/list')
      ]);
      if (usersResponse.data.status === 'success' && groupsResponse.data.status === 'success') {
        setSystemInfo({
          users: usersResponse.data.data,
          groups: groupsResponse.data.data
        });
      }
    } catch (error) {
      message.error('获取系统信息失败');
    }
  };

  const fetchFiles = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/file/list', {
        params: {
          path: currentPath,
          page: pagination.current,
          per_page: pagination.pageSize
        }
      });
      if (response.data.status === 'success') {
        setFiles(response.data.data.items);
        setPagination(prev => ({ 
          ...prev, 
          total: response.data.data.total
        }));
      }
    } catch (error) {
      message.error('获取文件列表失败');
    } finally {
      setLoading(false);
    }
  }, [currentPath, pagination.current, pagination.pageSize]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  const handleTableChange = (pagination: any) => {
    setPagination(pagination);
  };

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleDelete = async (path: string) => {
    try {
      const formData = new FormData();
      formData.append('path', path);
      const response = await axios.delete('/api/file/delete', { data: formData });
      if (response.data.status === 'success') {
        message.success('删除成功');
        fetchFiles();
      } else {
        message.error(response.data.message || '删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleEdit = async (values: { content: string }) => {
    if (!editingFile) return;
    try {
      const formData = new FormData();
      formData.append('path', editingFile.path);
      formData.append('content', values.content);
      const response = await axios.patch('/api/file/write', formData);
      if (response.data.status === 'success') {
        message.success('保存成功');
        setEditModalVisible(false);
        fetchFiles();
      } else {
        message.error(response.data.message || '保存失败');
      }
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleMove = async () => {
    if (!editingFile?.path || !targetPath) return;
    
    const formData = new FormData();
    formData.append('source', editingFile.path);
    formData.append('target', targetPath);

    try {
      await axios.post('/api/move', formData);
      message.success('移动成功');
      setMoveModalVisible(false);
      setTargetPath(null);
      moveForm.resetFields();
      fetchFiles();
    } catch (error) {
      message.error('移动失败');
    }
  };

  const handlePermissionChange = async (values: { mode: number; owner: number; group: number }) => {
    if (!editingFile?.path) return;
    
    const formData = new FormData();
    formData.append('path', editingFile.path);
    formData.append('mode', values.mode.toString());
    formData.append('owner', values.owner.toString());
    formData.append('group', values.group.toString());

    try {
      await axios.post('/api/chmod', formData);
      message.success('权限修改成功');
      setPermissionModalVisible(false);
      fetchFiles();
    } catch (error) {
      message.error('修改权限失败');
    }
  };

  const loadFileContent = async (file: FileItem) => {
    try {
      const response = await axios.get(`/api/file/read?path=${file.path}`);
      if (response.data.status === 'success') {
        form.setFieldsValue({ content: response.data.data });
        setEditingFile(file);
        setEditModalVisible(true);
      } else {
        message.error(response.data.message || '读取文件失败');
      }
    } catch (error) {
      message.error('读取文件失败');
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: FileItem) => (
        <Space>
          {record.type === 'dir' ? <FolderOutlined /> : <FileOutlined />}
          <span
            style={{ cursor: 'pointer' }}
            onClick={() => record.type === 'dir' && handleNavigate(`${currentPath}${currentPath.endsWith('/') ? '' : '/'}${record.name}`)}
          >
            {text}
            {record.target && <span style={{ color: '#999' }}> → {record.target}</span>}
          </span>
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => `${(size / 1024).toFixed(2)} KB`,
    },
    {
      title: '修改时间',
      dataIndex: 'last_modified',
      key: 'last_modified',
      render: (time: number) => dayjs(time * 1000).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '所有者',
      dataIndex: 'uid',
      key: 'uid',
      render: (uid: number) => {
        const user = systemInfo.users.find(u => u.uid === uid);
        return user ? user.name : uid;
      },
    },
    {
      title: '用户组',
      dataIndex: 'gid',
      key: 'gid',
      render: (gid: number) => {
        const group = systemInfo.groups.find(g => g.gid === gid);
        return group ? group.name : gid;
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: FileItem) => {
        const filePath = `${currentPath}${currentPath.endsWith('/') ? '' : '/'}${record.name}`;
        return (
          <Space size="middle">
            <Button
              type="link"
              icon={<SwapOutlined />}
              onClick={() => {
                setEditingFile({ ...record, path: filePath });
                setMoveModalVisible(true);
              }}
            >
              移动
            </Button>
            <Button
              type="link"
              icon={<LockOutlined />}
              onClick={() => {
                setEditingFile({ ...record, path: filePath });
                permissionForm.setFieldsValue({
                  mode: 0o644,
                  owner: record.uid,
                  group: record.gid,
                });
                setPermissionModalVisible(true);
              }}
            >
              权限
            </Button>
            {record.type === 'file' && (
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => loadFileContent({ ...record, path: filePath })}
              >
                编辑
              </Button>
            )}
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(filePath)}
            >
              删除
            </Button>
          </Space>
        );
      },
    },
  ];

  const pathParts = currentPath.split('/').filter(Boolean);

  const breadcrumbStyle = {
    cursor: 'pointer',
    color: '#1890ff',
    '&:hover': {
      color: '#40a9ff',
    },
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: 'calc(100vh - 48px)', // 减去内容区域的padding
    }}>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <span onClick={() => handleNavigate('/')} style={breadcrumbStyle}>
            根目录
          </span>
        </Breadcrumb.Item>
        {pathParts.map((part, index) => (
          <Breadcrumb.Item key={index}>
            <span
              onClick={() => handleNavigate(`/${pathParts.slice(0, index + 1).join('/')}`)}
              style={breadcrumbStyle}
            >
              {part}
            </span>
          </Breadcrumb.Item>
        ))}
      </Breadcrumb>

      <div style={{ flex: 1 }}>
        <Table
          columns={columns}
          dataSource={files}
          loading={loading}
          rowKey="path"
          pagination={{
            ...pagination,
            size: 'small',
            showTotal: (total) => `共 ${total} 项`,
            position: ['bottomCenter']
          }}
          onChange={handleTableChange}
        />
      </div>

      <Modal
        title="编辑文件"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleEdit}>
          <Form.Item name="content" rules={[{ required: true }]}>
            <Input.TextArea rows={10} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="移动文件"
        open={moveModalVisible}
        onCancel={() => {
          setMoveModalVisible(false);
          setTargetPath(null);
          moveForm.resetFields();
        }}
        footer={null}
      >
        <Form form={moveForm} onFinish={handleMove}>
          <Form.Item
            name="destination"
            label="目标路径"
            rules={[{ required: true, message: '请输入目标路径' }]}
          >
            <Input 
              placeholder="请输入目标路径，例如: /new/path"
              onChange={(e) => setTargetPath(e.target.value)}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              移动
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="修改权限"
        open={permissionModalVisible}
        onCancel={() => setPermissionModalVisible(false)}
        footer={null}
      >
        <Form form={permissionForm} onFinish={handlePermissionChange}>
          <Form.Item
            name="mode"
            label="权限模式"
            rules={[{ required: true, message: '请输入权限模式' }]}
          >
            <InputNumber min={0} max={777} />
          </Form.Item>
          <Form.Item
            name="owner"
            label="所有者"
            rules={[{ required: true, message: '请选择所有者' }]}
          >
            <Select>
              {systemInfo.users.map(user => (
                <Select.Option key={user.uid} value={user.uid}>
                  {user.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="group"
            label="用户组"
            rules={[{ required: true, message: '请选择用户组' }]}
          >
            <Select>
              {systemInfo.groups.map(group => (
                <Select.Option key={group.gid} value={group.gid}>
                  {group.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              修改
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FileManager; 