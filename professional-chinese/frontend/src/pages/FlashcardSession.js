import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Progress, Typography, message, Spin, Statistic } from 'antd';
import { practiceAPI } from '../services/api';
import { SoundOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const FlashcardSession = () => {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [stats, setStats] = useState(null);

  const loadStats = async () => {
    try {
      const response = await practiceAPI.getStats();
      if (response?.data) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
      // Don't show error message for stats loading failure
      // as it's not critical to the main functionality
    }
  };

  useEffect(() => {
    const initializeSession = async () => {
      setLoading(true);
      try {
        await loadSession();
        await loadStats();  // Load stats separately
      } catch (error) {
        console.error('Error initializing session:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeSession();
  }, []);

  const loadSession = async () => {
    setLoading(true);
    try {
      const response = await practiceAPI.getDailySession('flashcard');
      
      if (!response.data.vocabulary_items.length) {
        message.info('No more items available for review. Great job!');
        setSession(null);
        return;
      }
      
      setSession(response.data);
      setCurrentIndex(0);
      setShowAnswer(false);
      
      // Load stats
      const statsResponse = await practiceAPI.getStats();
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Error loading session:', error);
      message.error('Failed to load practice session. Please try again.');
    }
    setLoading(false);
  };

  const handleAnswer = async (isCorrect) => {
    if (!session?.vocabulary_items[currentIndex]) return;

    const vocab = session.vocabulary_items[currentIndex];
    try {
      await practiceAPI.updateProgress({
        vocabulary_id: vocab.id,
        proficiency_level: vocab.difficulty_level,
        is_correct: isCorrect
      });

      if (currentIndex < session.vocabulary_items.length - 1) {
        setCurrentIndex(prev => prev + 1);
        setShowAnswer(false);
      } else {
        message.success('Session completed!');
        await loadSession();
      }
    } catch (error) {
      console.error('Error updating progress:', error);
      message.error('Failed to update progress');
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: '20px' }}>Loading flashcards...</div>
      </div>
    );
  }

  if (!session || !session.vocabulary_items.length) {
    return (
      <Card>
        <Title level={4}>No flashcards available</Title>
        <Text>Please try again later.</Text>
      </Card>
    );
  }

  const currentVocab = session.vocabulary_items[currentIndex];
  const progress = ((currentIndex + 1) / session.vocabulary_items.length) * 100;

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '20px' }}>
      <Card title={
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text>Level {session.current_level}</Text>
            <Text>Streak: {stats?.streak || 0} days</Text>
          </div>
          <Progress percent={progress} showInfo={false} />
        </Space>
      }>
        <div style={{ minHeight: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          {!showAnswer ? (
            <>
              <Title level={2}>{currentVocab.chinese_simplified}</Title>
              {currentVocab.chinese_traditional && (
                <Text type="secondary">{currentVocab.chinese_traditional}</Text>
              )}
              <Text>{currentVocab.pinyin}</Text>
            </>
          ) : (
            <>
              <Title level={3}>{currentVocab.english}</Title>
              <Text>Context: {currentVocab.context_category}</Text>
              {currentVocab.usage_examples && Object.values(currentVocab.usage_examples)[0] && (
                <Card size="small" style={{ marginTop: 16, width: '100%' }}>
                  <Text>Example:</Text>
                  <div>{Object.values(currentVocab.usage_examples)[0].chinese}</div>
                  <div>{Object.values(currentVocab.usage_examples)[0].pinyin}</div>
                  <div>{Object.values(currentVocab.usage_examples)[0].english}</div>
                </Card>
              )}
            </>
          )}
        </div>

        <div style={{ marginTop: 20, display: 'flex', justifyContent: 'center', gap: 16 }}>
          {!showAnswer ? (
            <Button type="primary" onClick={() => setShowAnswer(true)}>
              Show Answer
            </Button>
          ) : (
            <Space>
              <Button 
                type="primary" 
                danger 
                icon={<CloseOutlined />}
                onClick={() => handleAnswer(false)}
              >
                Incorrect
              </Button>
              <Button 
                type="primary"
                style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                icon={<CheckOutlined />}
                onClick={() => handleAnswer(true)}
              >
                Correct
              </Button>
            </Space>
          )}
        </div>
      </Card>

      {stats && (
        <Card style={{ marginTop: 20 }}>
          <Space size="large" wrap>
            <Statistic
              title="Mastered"
              value={stats.mastered_items}
              suffix={`/ ${stats.total_items}`}
            />
            <Statistic
              title="Completion"
              value={parseFloat(stats.completion_rate.toFixed(1))}
              suffix="%"
            />
            <Statistic
              title="Current Level"
              value={stats.current_level}
              suffix={`/ 5`}
            />
          </Space>
        </Card>
      )}
    </div>
  );
};

export default FlashcardSession;
