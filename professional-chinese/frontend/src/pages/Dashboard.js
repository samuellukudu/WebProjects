import React from 'react';
import { Card, Row, Col, Button, Typography } from 'antd';
import { BookOutlined, PlayCircleOutlined, LineChartOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

const Dashboard = () => {
  const navigate = useNavigate();

  const cards = [
    {
      title: 'Vocabulary',
      icon: <BookOutlined style={{ fontSize: '24px' }} />,
      description: 'Browse and learn professional Chinese vocabulary',
      route: '/vocabulary'
    },
    {
      title: 'Practice',
      icon: <PlayCircleOutlined style={{ fontSize: '24px' }} />,
      description: 'Start your daily practice session',
      route: '/practice'
    },
    {
      title: 'Progress',
      icon: <LineChartOutlined style={{ fontSize: '24px' }} />,
      description: 'Track your learning progress',
      route: '/progress'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Welcome to Professional Chinese</Title>
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        {cards.map((card, index) => (
          <Col xs={24} sm={12} md={8} key={index}>
            <Card
              hoverable
              style={{ height: '100%' }}
              onClick={() => navigate(card.route)}
            >
              <div style={{ textAlign: 'center' }}>
                {card.icon}
                <Title level={4} style={{ marginTop: '16px' }}>{card.title}</Title>
                <p>{card.description}</p>
                <Button type="primary" onClick={() => navigate(card.route)}>
                  Get Started
                </Button>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default Dashboard;
