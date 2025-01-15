import React, { useState } from 'react';
import { Card, Input, Button, Typography, message, Spin } from 'antd';
import { practiceAPI } from '../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const PersonalizedLearning = () => {
  const [loading, setLoading] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [currentLesson, setCurrentLesson] = useState(null);

  const handleSubmitGoal = async () => {
    if (!prompt.trim()) {
      message.warning('Please enter your learning goal');
      return;
    }

    setLoading(true);
    try {
      await practiceAPI.createLearningGoal({ prompt });
      message.success('Learning goal created! Generating your personalized lessons...');
      await loadNextLesson();
    } catch (error) {
      console.error('Error creating learning goal:', error);
      message.error('Failed to create learning goal');
    }
    setLoading(false);
  };

  const loadNextLesson = async () => {
    try {
      const response = await practiceAPI.getNextLesson();
      setCurrentLesson(response.data);
    } catch (error) {
      console.error('Error loading lesson:', error);
      message.error('Failed to load next lesson');
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px' }}>
      <Title level={2}>Personalized Learning Path</Title>
      
      <Card style={{ marginBottom: 24 }}>
        <Title level={4}>What would you like to learn?</Title>
        <Text type="secondary">
          Describe your learning goals, context, or specific areas you want to focus on.
          For example: "I want to learn Chinese for business meetings and email communication"
        </Text>
        <TextArea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your learning goal..."
          style={{ marginTop: 16, marginBottom: 16 }}
        />
        <Button 
          type="primary" 
          onClick={handleSubmitGoal}
          loading={loading}
        >
          Create Learning Path
        </Button>
      </Card>

      {currentLesson && (
        <Card title="Your Personalized Lesson">
          <Text>Focus: {currentLesson.focus_category}</Text>
          <Text>Difficulty Level: {currentLesson.difficulty_level}</Text>
          
          {currentLesson.vocabulary.map((vocab, index) => (
            <Card key={vocab.id} style={{ marginTop: 16 }}>
              <div style={{ fontSize: '18px' }}>{vocab.chinese_simplified}</div>
              <div>{vocab.pinyin}</div>
              <div>{vocab.english}</div>
            </Card>
          ))}
          
          <Button 
            type="primary" 
            style={{ marginTop: 16 }}
            onClick={loadNextLesson}
          >
            Next Lesson
          </Button>
        </Card>
      )}
    </div>
  );
};

export default PersonalizedLearning; 