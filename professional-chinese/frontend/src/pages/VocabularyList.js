import React, { useState, useEffect } from 'react';
import { Table, Input, Select, Card, Space } from 'antd';
import axios from 'axios';

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
          axios.get('http://localhost:8000/vocabulary/'),
          axios.get('http://localhost:8000/vocabulary/categories')
        ]);
        setVocabulary(vocabResponse.data);
        setCategories(categoriesResponse.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
      setLoading(false);
    };

    fetchData();
  }, []);

  const handleSearch = async (value) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/vocabulary/search?query=${value}`);
      setVocabulary(response.data);
    } catch (error) {
      console.error('Error searching:', error);
    }
    setLoading(false);
  };

  return (
    <Card title="Vocabulary List">
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
          onChange={setSelectedCategory}
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
