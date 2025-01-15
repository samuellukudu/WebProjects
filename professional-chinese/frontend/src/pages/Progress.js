import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress as AntProgress } from 'antd';
import axios from 'axios';

const Progress = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/practice/progress-stats');
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
  }, []);

  if (!stats) {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Total Vocabulary Items"
              value={stats.total_items}
              suffix="words"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Reviewed Items"
              value={stats.reviewed_items}
              suffix="words"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Review Progress"
              value={stats.total_items ? Math.round((stats.reviewed_items / stats.total_items) * 100) : 0}
              suffix="%"
            />
            <AntProgress
              percent={stats.total_items ? Math.round((stats.reviewed_items / stats.total_items) * 100) : 0}
              status="active"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Progress;
