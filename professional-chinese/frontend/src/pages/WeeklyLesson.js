import React, { useState, useEffect } from 'react';
import { Card, Steps, Button, Typography, Space, message } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { practiceAPI } from '../services/api';

const { Title, Text } = Typography;
const { Step } = Steps;

const WeeklyLesson = () => {
  const { lessonId } = useParams();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [lessonData, setLessonData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLessonData();
  }, [lessonId]);

  const loadLessonData = async () => {
    try {
      const response = await practiceAPI.getWeeklyLesson(lessonId);
      setLessonData(response.data);
    } catch (error) {
      console.error('Error loading lesson:', error);
      message.error('Failed to load lesson');
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    if (!lessonData) return null;

    const sections = [
      {
        title: 'Vocabulary',
        content: (
          <Space direction="vertical" style={{ width: '100%' }}>
            {lessonData.vocabulary_items.map((item, index) => (
              <Card key={index} size="small">
                <Space direction="vertical">
                  <Text strong>{item.chinese_simplified}</Text>
                  <Text type="secondary">{item.pinyin}</Text>
                  <Text>{item.english}</Text>
                </Space>
              </Card>
            ))}
          </Space>
        )
      },
      {
        title: 'Grammar',
        content: (
          <Space direction="vertical" style={{ width: '100%' }}>
            {lessonData.grammar_points.map((point, index) => (
              <Card key={index} size="small">
                <Text>{point}</Text>
              </Card>
            ))}
          </Space>
        )
      },
      {
        title: 'Practice',
        content: (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button type="primary" onClick={() => navigate('/practice')}>
              Start Practice Session
            </Button>
          </Space>
        )
      }
    ];

    return sections[currentStep]?.content;
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px' }}>
      <Title level={2}>{lessonData?.focus}</Title>
      
      <Steps current={currentStep} onChange={setCurrentStep} style={{ marginBottom: 24 }}>
        <Step title="Vocabulary" description="Learn new words" />
        <Step title="Grammar" description="Study grammar points" />
        <Step title="Practice" description="Test your knowledge" />
      </Steps>

      <Card loading={loading}>
        {renderContent()}
      </Card>

      <div style={{ marginTop: 24, textAlign: 'right' }}>
        {currentStep > 0 && (
          <Button style={{ marginRight: 8 }} onClick={() => setCurrentStep(current => current - 1)}>
            Previous
          </Button>
        )}
        {currentStep < 2 && (
          <Button type="primary" onClick={() => setCurrentStep(current => current + 1)}>
            Next
          </Button>
        )}
      </div>
    </div>
  );
};

export default WeeklyLesson; 