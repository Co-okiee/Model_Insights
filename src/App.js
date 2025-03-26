import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { 
  FileText, 
  Layers, 
  Zap, 
  PieChart, 
  Moon, 
  Sun 
} from 'lucide-react';
import './App.css';
import FileUpload from './FileUpload';
import ModelDetails from './ModelDetails';
import LimePage from "./LimePage";
import ShapPage from "./ShapPage";
import VisualizationPage from "./VisualizationPage";

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    document.body.classList.toggle('dark-mode', newMode);
    document.body.classList.toggle('light-mode', !newMode);
  };

  // Apply initial mode on mount
  useEffect(() => {
    document.body.classList.add('light-mode');
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-center">
              Machine Learning Model Insights
            </h1>
            <button 
              onClick={toggleDarkMode} 
              className="mode-toggle p-2 rounded-full hover:bg-gray-100"
            >
              {isDarkMode ? <Sun size={24} /> : <Moon size={24} />}
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex justify-center space-x-4 mb-8">
            <NavLink 
              to="/" 
              className={({ isActive }) => 
                `nav-link flex items-center ${isActive ? 'active' : ''}`
              }
            >
              <FileText className="mr-2" size={20} /> Upload
            </NavLink>
            <NavLink 
              to="/model-details" 
              className={({ isActive }) => 
                `nav-link flex items-center ${isActive ? 'active' : ''}`
              }
            >
              <Layers className="mr-2" size={20} /> Model Details
            </NavLink>
            <NavLink 
              to="/lime" 
              className={({ isActive }) => 
                `nav-link flex items-center ${isActive ? 'active' : ''}`
              }
            >
              <Zap className="mr-2" size={20} /> LIME
            </NavLink>
            <NavLink 
              to="/shap" 
              className={({ isActive }) => 
                `nav-link flex items-center ${isActive ? 'active' : ''}`
              }
            >
              <PieChart className="mr-2" size={20} /> SHAP
            </NavLink>
          </nav>

          <Routes>
            <Route path="/" element={<FileUpload />} />
            <Route path="/model-details" element={<ModelDetails />} />
            <Route path="/lime" element={<LimePage />} />
            <Route path="/shap" element={<ShapPage />} />
            <Route path="/visualization" element={<VisualizationPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;