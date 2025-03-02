import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Sidebar';
import FileManager from './components/FileManager';
import UserManager from './components/UserManager';
import Login from './components/Login';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sidebar />
        <Layout>
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/files/*" element={<FileManager />} />
              <Route path="/users" element={<UserManager />} />
              <Route path="/" element={<FileManager />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
};

export default App; 