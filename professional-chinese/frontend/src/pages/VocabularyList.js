import React, { useState, useEffect } from 'react';
import { Table, Input, Select, Card, Space, message } from 'antd';
import { vocabularyAPI } from '../services/api';

const { Search } = Input;

const VocabularyList = () => {
  const [vocabulary, setVocabulary] = useState([]);
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const columns = [
    {
      title: 'Chinese',
      dataIndex: 'chinese_simplified',
      key: 'chinese_simplified',
      render: (text, record) => (
        <Space direction="vertical" size="small">
          <div style={{ fontSize: '18px' }}>{text}</div>
          <div style={{ color: '#666' }}>{record.pinyin}</div>
        </Space>
      ),
    },
    {
      title: 'Traditional',
      dataIndex: 'chinese_traditional',
      key: 'chinese_traditional',
    },
    {
      title: 'English',
      dataIndex: 'english',
      key: 'english',
    },
    {
      title: 'Category',
      dataIndex: 'context_category',
      key: 'context_category',
      filters: categories.map(cat => ({ text: cat, value: cat })),
      onFilter: (value, record) => record.context_category === value,
    },
    {
      title: 'Difficulty',
      dataIndex: 'difficulty_level',
      key: 'difficulty_level',
      sorter: (a, b) => a.difficulty_level - b.difficulty_level,
      render: (level) => '⭐'.repeat(level),
    },
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [vocabResponse, categoriesResponse] = await Promise.all([
          vocabularyAPI.getAll(),
          vocabularyAPI.getCategories()
        ]);
        setVocabulary(vocabResponse.data);
        setCategories(categoriesResponse.data);
      } catch (error) {
        console.error('Error fetching data:', error);
        message.error('Failed to load vocabulary data');
      }
      setLoading(false);
    };

    fetchData();
  }, []);

  const handleSearch = async (value) => {
    if (!value.trim()) {
      const response = await vocabularyAPI.getAll();
      setVocabulary(response.data);
      return;
    }
    
    setLoading(true);
    try {
      const response = await vocabularyAPI.search(value);
      setVocabulary(response.data);
    } catch (error) {
      console.error('Error searching:', error);
      message.error('Failed to search vocabulary');
    }
    setLoading(false);
  };

  const handleCategoryChange = async (value) => {
    setSelectedCategory(value);
    setLoading(true);
    try {
      const response = await vocabularyAPI.getAll({ category: value });
      setVocabulary(response.data);
    } catch (error) {
      console.error('Error filtering by category:', error);
      message.error('Failed to filter vocabulary');
    }
    setLoading(false);
  };

  return (
    <Card title="Vocabulary List" className="vocabulary-list">
      <Space style={{ marginBottom: 16 }} size="large">
        <Search
          placeholder="Search vocabulary..."
          allowClear
          enterButton
          style={{ width: 300 }}
          onSearch={handleSearch}
        />
        <Select
          style={{ width: 200 }}
          placeholder="Filter by category"
          allowClear
          onChange={handleCategoryChange}
          options={categories.map(cat => ({ label: cat, value: cat }))}
        />
      </Space>
      <Table
        columns={columns}
        dataSource={vocabulary}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};

export default VocabularyList;
