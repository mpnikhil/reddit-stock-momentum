import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import StockDetail from './pages/StockDetail';
import Search from './pages/Search';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:symbol" element={<StockDetail key={window.location.pathname} />} />
          <Route path="/search" element={<Search />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;