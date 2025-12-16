import React, { useState, useEffect } from 'react';
import './App.css';

const DrCodePTDashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [studyPlan, setStudyPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [studyHistory, setStudyHistory] = useState([]);

  const API_URL = 'http://localhost:5000/api';

  useEffect(() => {
    fetchDashboard();
    fetchCourses();
    loadStudyHistory();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await fetch(`${API_URL}/dashboard`);
      const data = await response.json();
      if (data.success) setDashboard(data.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const fetchCourses = async () => {
    try {
      const response = await fetch(`${API_URL}/courses`);
      const data = await response.json();
      if (data.success) setCourses(data.courses);
    } catch (error) {
      console.error('Error:', error);
    }
  };
  const loadStudyHistory = () => {
    const saved = localStorage.getItem('studyHistory');
    if (saved) setStudyHistory(JSON.parse(saved));
  };

  const generateStudyPlan = async (course) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/study/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ course_id: course.id, topic: course.name })
      });
      const data = await response.json();
      if (data.success) {
        setStudyPlan(data.plan);
        setSelectedCourse(course);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeStudy = async () => {
    if (!selectedCourse) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/study/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ course_id: selectedCourse.id })
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ Study complete! 24 cards added to Anki.');
        fetchDashboard();
        setStudyPlan(null);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  if (!dashboard) {
    return <div className="loading"><div className="spinner"></div><p>Loading...</p></div>;
  }

  return (
    <div className="app">
      <header className="header">
        <div><h1>🎓 DrCodePT Phase 7</h1></div>
        <div className="header-stats">
          <div className="stat"><span>{dashboard.total_cards}</span> Cards</div>
          <div className="stat"><span>{dashboard.study_sessions}</span> Sessions</div>
        </div>
      </header>

      <nav className="tabs">
        <button className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>📊 Dashboard</button>
        <button className={`tab ${activeTab === 'study' ? 'active' : ''}`} onClick={() => setActiveTab('study')}>📚 Study</button>
        <button className={`tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>📈 History</button>
      </nav>

      <main className="main">
        {activeTab === 'dashboard' && (
          <div className="dashboard-tab">
            <h2>Your Courses</h2>
            <div className="courses-grid">
              {courses.map((course) => (
                <div key={course.id} className="course-card">
                  <h3>{course.name}</h3>
                  <div className="course-stats">
                    <div>📅 {course.due_dates} due dates</div>
                    <div>🎴 {course.anki_cards} cards</div>
                  </div>
                  <button className="btn-study" onClick={() => generateStudyPlan(course)} disabled={loading}>
                    {loading ? 'Planning...' : '▶️ Study Now'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'study' && (
          <div className="study-tab">
            {!studyPlan ? (
              <p>Select a course to create a study plan</p>
            ) : (
              <div className="study-plan">
                <h2>{studyPlan.course} Study Plan</h2>
                <div className="phases">
                  {studyPlan.phases.map((p, i) => (
                    <div key={i} className="phase">{p.phase} ({p.duration}m)</div>
                  ))}
                </div>
                <p>📝 {studyPlan.estimated_cards} cards | ⏱️ {studyPlan.total_time_minutes} min</p>
                <button className="btn-execute" onClick={executeStudy} disabled={loading}>
                  {loading ? '⏳ Running...' : '🚀 Execute Study'}
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="history-tab">
            <h2>Study History</h2>
            {studyHistory.length === 0 ? <p>No sessions yet</p> : <p>{studyHistory.length} sessions completed</p>}
          </div>
        )}
      </main>
    </div>
  );
};

export default DrCodePTDashboard;