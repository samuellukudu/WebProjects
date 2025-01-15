import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress as AntProgress } from 'antd';
import { practiceAPI } from '../services/api';

const Progress = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await practiceAPI.getStats();
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
              title="Mastered Items"
              value={stats.mastered_items}
              suffix="words"
            />
          </Card>
        </Col>
        <Col xs={24}>
          <Card>
            <Statistic
              title="Completion Rate"
              value={stats.completion_rate}
              precision={1}
              suffix="%"
            />
            <AntProgress
              percent={stats.completion_rate}
              status="active"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Progress;
