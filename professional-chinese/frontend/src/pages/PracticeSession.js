import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, Space, Row, Col, Spin, message } from 'antd';
import axios from 'axios';

const { Title, Text } = Typography;

const PracticeSession = () => {
  const [session, setSession] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSession = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get('http://localhost:8000/api/practice/daily-session', {
          timeout: 5000 // 5 second timeout
        });
        setSession(response.data);
      } catch (error) {
        console.error('Error fetching session:', error);
        setError('Failed to load practice session. Please try again.');
        message.error('Failed to load practice session');
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, []);

  const handleNext = async (proficiency) => {
    if (!session?.vocabulary_items[currentIndex]) return;

    try {
      await axios.post('http://localhost:8000/api/practice/update-progress', {
        vocabulary_id: session.vocabulary_items[currentIndex].id,
        proficiency_level: proficiency
      }, {
        timeout: 3000 // 3 second timeout
      });
      
      setShowAnswer(false);
      setCurrentIndex(prev => prev + 1);
    } catch (error) {
      console.error('Error updating progress:', error);
      message.error('Failed to update progress');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px' }}>Loading practice session...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Card style={{ maxWidth: 600, margin: '0 auto', marginTop: 50, textAlign: 'center' }}>
        <Title level={3}>Error</Title>
        <Text type="danger">{error}</Text>
        <Button type="primary" onClick={() => window.location.reload()} style={{ marginTop: '20px' }}>
          Try Again
        </Button>
      </Card>
    );
  }

  if (!session?.vocabulary_items?.length) {
    return (
      <Card style={{ maxWidth: 600, margin: '0 auto', marginTop: 50, textAlign: 'center' }}>
        <Title level={3}>No Practice Items Available</Title>
        <Text>All items have been reviewed for today!</Text>
        <Button type="primary" onClick={() => window.location.reload()} style={{ marginTop: '20px' }}>
          Check Again
        </Button>
      </Card>
    );
  }

  const currentWord = session.vocabulary_items[currentIndex];

  if (!currentWord) {
    return (
      <Card style={{ maxWidth: 600, margin: '0 auto', marginTop: 50, textAlign: 'center' }}>
        <Title level={3}>Practice Complete!</Title>
        <Text>Great job! You've completed your practice session.</Text>
        <Button type="primary" onClick={() => window.location.reload()} style={{ marginTop: '20px' }}>
          Start New Session
        </Button>
      </Card>
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
          <Title level={2}>{currentWord.chinese_simplified}</Title>
          <Text type="secondary">{currentWord.pinyin}</Text>
          
          {!showAnswer ? (
            <Button type="primary" onClick={() => setShowAnswer(true)}>
              Show Answer
            </Button>
          ) : (
            <>
              <div>
                <Title level={3}>{currentWord.english}</Title>
                {currentWord.chinese_traditional && (
                  <Text type="secondary">Traditional: {currentWord.chinese_traditional}</Text>
                )}
              </div>
              
              <Row gutter={[16, 16]} justify="center">
                <Col>
                  <Button onClick={() => handleNext(1)}>Still Learning</Button>
                </Col>
                <Col>
                  <Button type="primary" onClick={() => handleNext(2)}>Got It!</Button>
                </Col>
                <Col>
                  <Button type="primary" onClick={() => handleNext(3)}>Easy!</Button>
                </Col>
              </Row>
            </>
          )}
          
          <Text type="secondary">
            Word {currentIndex + 1} of {session.vocabulary_items.length}
          </Text>
        </Space>
      </Card>
    </div>
  );
};

export default PracticeSession;
