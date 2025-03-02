import React from 'react';
import { Layout, Menu } from 'antd';
import { FileOutlined, UserOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/files',
      icon: <FileOutlined />,
      label: '文件管理',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/login',
      icon: <LoginOutlined />,
      label: '登录',
    },
  ];

  return (
    <Sider theme="light" breakpoint="lg" collapsible>
      <div style={{ height: 32, margin: 16, background: 'rgba(0, 0, 0, 0.2)' }} />
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  );
};

export default Sidebar; 