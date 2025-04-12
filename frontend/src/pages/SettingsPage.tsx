import React, { useEffect, useState } from 'react';
import ClearCacheButton from '../components/ClearCacheButton';

const SettingsPage: React.FC = () => {
  const [status, setStatus] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/health/');
      if (res.ok) {
        const data = await res.json();
        setStatus(data.status);
      } else {
        setStatus('unreachable');
      }
    } catch (e) {
      console.error(e);
      setStatus('error');
    }
  };

  useEffect(() => {
    fetchStatus();
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
      setDarkMode(true);
    }
  }, []);

  const toggleTheme = () => {
    if (darkMode) {
      document.body.classList.remove('dark-theme');
      localStorage.setItem('theme', 'light');
      setDarkMode(false);
    } else {
      document.body.classList.add('dark-theme');
      localStorage.setItem('theme', 'dark');
      setDarkMode(true);
    }
  };

  return (
    <div>
      <h1>Settings</h1>
      <p>Server status: {status ? status : 'loading...'}</p>
      <ClearCacheButton />
      <div style={{ marginTop: '1rem' }}>
        <button onClick={toggleTheme}>
          Switch to {darkMode ? 'Light' : 'Dark'} Theme
        </button>
      </div>
      <p>Additional server status and settings will be added here.</p>
    </div>
  );
};

export default SettingsPage;
