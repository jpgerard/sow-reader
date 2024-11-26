import React from 'react';
import { createRoot } from 'react-dom/client';
import RequirementsManagementUI from './RequirementsManagementUI';
import './index.css';

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <RequirementsManagementUI />
    </React.StrictMode>
  );
}
