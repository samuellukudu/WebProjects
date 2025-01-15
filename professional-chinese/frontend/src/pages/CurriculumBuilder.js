import React, { useState } from 'react';
import { Card, Form, Input, Button, Select, Steps, message, Typography, Row, Col } from 'antd';
import { practiceAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import mockCurriculumData from '../mockData/curriculumData';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Step } = Steps;

const CurriculumBuilder = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [curriculum, setCurriculum] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      if (process.env.REACT_APP_USE_MOCK_DATA === 'true') {
        setCurriculum(mockCurriculumData);
        setCurrentStep(1);
        message.success('Curriculum created successfully!');
        setLoading(false);
        return;
      }

      const response = await practiceAPI.createCurriculum({
        context: values.context,
        proficiency: values.proficiency,
        focus_areas: values.focus_areas,
        time_commitment: values.time_commitment
      });
      
      console.log('Raw curriculum response:', response.data);
      
      if (!response.data || !response.data.curriculum) {
        throw new Error('Invalid response format');
      }

      const curriculumData = response.data.curriculum;
      
      if (!curriculumData.weekly_plan || !Array.isArray(curriculumData.weekly_plan)) {
        throw new Error('Invalid curriculum structure');
      }
      
      setCurriculum({ curriculum: curriculumData });
      setCurrentStep(1);
      message.success('Curriculum created successfully!');
    } catch (error) {
      console.error('API error:', error);
      message.error(error.response?.data?.detail || 'Failed to create curriculum');
    } finally {
      setLoading(false);
    }
  };

  const renderCurriculum = (curriculumData) => {
    try {
      const plan = typeof curriculumData === 'string' ? JSON.parse(curriculumData) : curriculumData;
      
      if (!plan.weekly_plan || !Array.isArray(plan.weekly_plan)) {
        throw new Error('Invalid curriculum structure');
      }

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <Card>
            <Title level={4}>Learning Objectives</Title>
            <ul>
              {plan.learning_objectives?.map((objective, index) => (
                <li key={index}>{objective}</li>
              ))}
            </ul>
            <Text>Estimated Duration: {plan.estimated_duration}</Text>
          </Card>

          {plan.weekly_plan.map((week, weekIndex) => (
            <Card
              key={weekIndex}
              hoverable
              title={`Week ${week.week}: ${week.focus}`}
              extra={
                <Button type="primary" onClick={() => handleStartWeek(week)}>
                  Start Learning
                </Button>
              }
            >
              <div style={{ marginBottom: '16px' }}>
                <Title level={5}>Activities</Title>
                <ul>
                  {week.activities?.map((activity, idx) => (
                    <li key={idx}>{activity}</li>
                  ))}
                </ul>
              </div>

              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card size="small" title="Vocabulary Focus">
                    <ul>
                      {week.vocabulary_focus?.map((vocab, idx) => (
                        <li key={idx}>{vocab}</li>
                      ))}
                    </ul>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small" title="Grammar Points">
                    <ul>
                      {week.grammar_points?.map((point, idx) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  </Card>
                </Col>
              </Row>
            </Card>
          ))}
        </div>
      );
    } catch (error) {
      console.error('Error rendering curriculum:', error);
      return <Text type="danger">Error displaying curriculum. Please try again.</Text>;
    }
  };

  const handleStartWeek = async (weekData) => {
    try {
      const response = await practiceAPI.startWeeklyLesson({
        focus: weekData.focus,
        vocabulary_focus: weekData.vocabulary_focus,
        grammar_points: weekData.grammar_points
      });
      
      navigate(`/curriculum/week/${response.data.lesson_id}`);
    } catch (error) {
      console.error('Error starting week:', error);
      message.error('Failed to start weekly lesson');
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={2}>Create Your Learning Curriculum</Title>
      
      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        <Step title="Define Goals" description="Set your learning objectives" />
        <Step title="Review Plan" description="Review your curriculum" />
      </Steps>

      {currentStep === 0 && (
        <Card>
          <Form layout="vertical" onFinish={handleSubmit}>
            <Form.Item
              label="What do you want to learn Chinese for?"
              name="context"
              rules={[{ required: true }]}
            >
              <TextArea 
                rows={4}
                placeholder="E.g., I need to communicate with Chinese colleagues in business meetings and email correspondence"
              />
            </Form.Item>

            <Form.Item
              label="Current Proficiency Level"
              name="proficiency"
              rules={[{ required: true }]}
            >
              <Select>
                <Select.Option value="beginner">Beginner</Select.Option>
                <Select.Option value="intermediate">Intermediate</Select.Option>
                <Select.Option value="advanced">Advanced</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="Focus Areas"
              name="focus_areas"
              rules={[{ required: true }]}
            >
              <Select mode="multiple">
                <Select.Option value="business">Business Communication</Select.Option>
                <Select.Option value="email">Email Writing</Select.Option>
                <Select.Option value="meetings">Meetings</Select.Option>
                <Select.Option value="technical">Technical Discussion</Select.Option>
                <Select.Option value="casual">Casual Conversation</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="Time Commitment (hours per week)"
              name="time_commitment"
              rules={[{ required: true }]}
            >
              <Select>
                <Select.Option value={1}>1 hour</Select.Option>
                <Select.Option value={3}>3 hours</Select.Option>
                <Select.Option value={5}>5 hours</Select.Option>
                <Select.Option value={10}>10+ hours</Select.Option>
              </Select>
            </Form.Item>

            <Button type="primary" htmlType="submit" loading={loading}>
              Generate Curriculum
            </Button>
          </Form>
        </Card>
      )}

      {currentStep === 1 && curriculum && (
        <Card>
          <Title level={3}>Your Personalized Curriculum</Title>
          {renderCurriculum(curriculum.curriculum)}
        </Card>
      )}
    </div>
  );
};

export default CurriculumBuilder; 