import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu } from 'antd';
import { 
  HomeOutlined, 
  BookOutlined, 
  PlayCircleOutlined, 
  LineChartOutlined,
  UserOutlined 
} from '@ant-design/icons';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const items = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Dashboard'
    },
    {
      key: '/vocabulary',
      icon: <BookOutlined />,
      label: 'Vocabulary'
    },
    {
      key: '/practice',
      icon: <PlayCircleOutlined />,
      label: 'Practice'
    },
    {
      key: '/progress',
      icon: <LineChartOutlined />,
      label: 'Progress'
    },
    {
      key: '/login',
      icon: <UserOutlined />,
      label: 'Login',
      style: { marginLeft: 'auto' }
    }
  ];

  return (
    <Menu
      theme="dark"
      mode="horizontal"
      selectedKeys={[location.pathname]}
      items={items}
      onClick={({ key }) => navigate(key)}
    />
  );
};

export default Navigation;
