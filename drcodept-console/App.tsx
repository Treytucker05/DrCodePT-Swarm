import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import RunDetailsPage from './pages/RunDetails';
import EnvPage from './pages/Env';
import HandoffPage from './pages/Handoff';
import RunsList from './pages/RunsList';
import HelpPage from './pages/Help';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="runs" element={<RunsList />} />
          <Route path="runs/:id" element={<RunDetailsPage />} />
          <Route path="env" element={<EnvPage />} />
          <Route path="handoff" element={<HandoffPage />} />
          <Route path="help" element={<HelpPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;