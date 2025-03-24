import React from "react";
import { useNavigate } from "react-router-dom";

const ModelDetails = () => {
  const navigate = useNavigate();

  return (
    <div className="p-6 text-center bg-gray-100 rounded-lg shadow-lg max-w-lg mx-auto">
      <h2 className="text-3xl font-extrabold text-gray-800">Model Insights</h2>
      <p className="mt-3 text-gray-600">Here you will see details about the uploaded model.</p>
      
      <div className="mt-6 flex justify-center gap-6">
        <button 
          className="px-5 py-3 bg-blue-500 text-white rounded-lg shadow-md transition-transform transform hover:scale-105 hover:bg-blue-600"
          onClick={() => navigate("/lime")}
        >
          LIME
        </button>
        <button 
          className="px-5 py-3 bg-green-500 text-white rounded-lg shadow-md transition-transform transform hover:scale-105 hover:bg-green-600"
          onClick={() => navigate("/shap")}
        >
          SHAP
        </button>
        <button 
          className="px-5 py-3 bg-purple-500 text-white rounded-lg shadow-md transition-transform transform hover:scale-105 hover:bg-purple-600"
          onClick={() => navigate("/visualization")}
        >
          Visualization
        </button>
      </div>
    </div>
  );
};

export default ModelDetails;
