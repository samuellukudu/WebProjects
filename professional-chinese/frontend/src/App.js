import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import VocabularyList from './pages/VocabularyList';
import PracticeSession from './pages/PracticeSession';
import FlashcardSession from './pages/FlashcardSession';
import Progress from './pages/Progress';
import Login from './pages/Login';
import PersonalizedLearning from './pages/PersonalizedLearning';
import CurriculumBuilder from './pages/CurriculumBuilder';
import WeeklyLesson from './pages/WeeklyLesson';
import { Layout } from 'antd';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Navigation />
        <Layout style={{ marginLeft: 200 }}>
          <Content style={{ 
            padding: '24px',
            background: '#fff',
            minHeight: '100vh',
            overflow: 'auto'
          }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/vocabulary" element={<VocabularyList />} />
              <Route path="/practice" element={<PracticeSession />} />
              <Route path="/flashcards" element={<FlashcardSession />} />
              <Route path="/progress" element={<Progress />} />
              <Route path="/login" element={<Login />} />
              <Route path="/personalized" element={<PersonalizedLearning />} />
              <Route path="/curriculum" element={<CurriculumBuilder />} />
              <Route path="/curriculum/week/:lessonId" element={<WeeklyLesson />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
