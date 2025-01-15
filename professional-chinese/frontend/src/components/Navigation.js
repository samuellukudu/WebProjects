import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Layout } from 'antd';
import {
  HomeOutlined,
  BookOutlined,
  FormOutlined,
  LineChartOutlined,
  CreditCardOutlined,
  UserOutlined,
  AimOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

const Navigation = () => {
  const location = useLocation();

  const items = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">Dashboard</Link>,
    },
    {
      key: '/vocabulary',
      icon: <BookOutlined />,
      label: <Link to="/vocabulary">Vocabulary</Link>,
    },
    {
      key: '/practice',
      icon: <FormOutlined />,
      label: <Link to="/practice">Practice</Link>,
    },
    {
      key: '/flashcards',
      icon: <CreditCardOutlined />,
      label: <Link to="/flashcards">Flashcards</Link>,
    },
    {
      key: '/progress',
      icon: <LineChartOutlined />,
      label: <Link to="/progress">Progress</Link>,
    },
    {
      key: '/login',
      icon: <UserOutlined />,
      label: <Link to="/login">Login</Link>,
      style: { marginTop: 'auto' }
    },
    {
      key: '/personalized',
      icon: <AimOutlined />,
      label: <Link to="/personalized">Personal Path</Link>,
    },
    {
      key: '/curriculum',
      icon: <BookOutlined />,
      label: <Link to="/curriculum">Create Curriculum</Link>,
    }
  ];

  return (
    <Sider
      width={200}
      style={{
        background: '#fff',
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        boxShadow: '2px 0 8px rgba(0,0,0,0.15)'
      }}
    >
      <div 
        style={{ 
          height: 64, 
          margin: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#1890ff'
        }}
      >
        Professional Chinese
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ 
          height: 'calc(100vh - 96px)',
          borderRight: 0,
          display: 'flex',
          flexDirection: 'column'
        }}
        items={items}
      />
    </Sider>
  );
};

export default Navigation;
