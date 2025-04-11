import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import './App.css';

import ProjectsPage from './pages/ProjectsPage';
import DocumentsPage from './pages/DocumentsPage';
import QueryPage from './pages/QueryPage';
import GraphPage from './pages/GraphPage';
import SettingsPage from './pages/SettingsPage';
import MCPPage from './pages/MCPPage';

const App: React.FC = () => {
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  }, []);

  return (
    <BrowserRouter>
      <div className="app-container">
        <nav className="top-navbar">
          <ul>
            <li><NavLink to="/" end>Projects</NavLink></li>
            <li><NavLink to="/documents">Documents</NavLink></li>
            <li><NavLink to="/query">Query</NavLink></li>
            <li><NavLink to="/graph">Graph</NavLink></li>
            <li><NavLink to="/settings">Settings</NavLink></li>
            <li><NavLink to="/mcp">MCP Tools</NavLink></li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ProjectsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/query" element={<QueryPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/mcp" element={<MCPPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
