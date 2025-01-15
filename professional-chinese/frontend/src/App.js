import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import VocabularyList from './pages/VocabularyList';
import PracticeSession from './pages/PracticeSession';
import Progress from './pages/Progress';
import Login from './pages/Login';

const { Header, Content, Footer } = Layout;

function App() {
  return (
    <Router>
      <Layout className="layout" style={{ minHeight: '100vh' }}>
        <Header style={{ position: 'fixed', zIndex: 1, width: '100%', padding: 0 }}>
          <Navigation />
        </Header>
        <Content style={{ padding: '24px', marginTop: 64 }}>
          <div style={{ background: '#fff', padding: 24, minHeight: 380 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/vocabulary" element={<VocabularyList />} />
              <Route path="/practice" element={<PracticeSession />} />
              <Route path="/progress" element={<Progress />} />
              <Route path="/login" element={<Login />} />
            </Routes>
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          Professional Chinese ©{new Date().getFullYear()}
        </Footer>
      </Layout>
    </Router>
  );
}

export default App;
