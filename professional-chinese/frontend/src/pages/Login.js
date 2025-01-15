import React from 'react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

const Login = () => {
  return (
    <Card style={{ maxWidth: 400, margin: '0 auto', marginTop: 50 }}>
      <Title level={3}>Login functionality disabled</Title>
      <p>Authentication has been temporarily disabled for development purposes.</p>
    </Card>
  );
};

export default Login;
