import React from 'react';
import { AIRequirementInsights } from '../types/AIAnalysis';
import { Card } from './ui/card';
import { Button } from './ui/button';

interface AIAnalysisPanelProps {
  insights: AIRequirementInsights;
}

export const AIAnalysisPanel: React.FC<AIAnalysisPanelProps> = ({ insights }) => {
  return (
    <Card className="p-4 space-y-4 bg-white shadow-md rounded-lg">
      <div className="text-lg font-bold text-blue-600">AI Requirement Insights</div>
      
      <section className="mb-4">
        <h3 className="font-semibold text-gray-700 mb-2">Quality Score</h3>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(insights.qualityScore).map(([key, value]) => (
            <div key={key} className="bg-gray-100 p-2 rounded">
              <span className="text-sm text-gray-600 capitalize">{key}</span>
              <div className="text-md font-bold">{value.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-4">
        <h3 className="font-semibold text-gray-700 mb-2">Gap Analysis</h3>
        <div className="space-y-2">
          {insights.gapAnalysis.missingElements.map((element, index) => (
            <div key={index} className="bg-yellow-50 p-2 rounded">
              <span className="text-yellow-600">Missing: {element}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-4">
        <h3 className="font-semibold text-gray-700 mb-2">Terminology Standardization</h3>
        <div className="space-y-2">
          {insights.terminologyStandardization.map((term, index) => (
            <div key={index} className="bg-green-50 p-2 rounded flex justify-between items-center">
              <div>
                <span className="text-sm text-gray-600">Original: {term.originalTerm}</span>
                <div className="font-bold text-green-600">Recommended: {term.recommendedTerm}</div>
              </div>
              <span className="text-sm text-gray-500">Confidence: {term.confidence.toFixed(2)}%</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-4">
        <h3 className="font-semibold text-gray-700 mb-2">Test Case Suggestions</h3>
        <div className="space-y-2">
          {insights.testCaseSuggestions.map((suggestion, index) => (
            <div key={index} className="bg-blue-50 p-2 rounded">
              <div className="font-bold">{suggestion.testScenario}</div>
              <div className="text-sm text-gray-600">
                Type: {suggestion.testType} | Complexity: {suggestion.complexity}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-4">
        <h3 className="font-semibold text-gray-700 mb-2">Compliance Checks</h3>
        <div className="space-y-2">
          {insights.complianceChecks.map((check, index) => (
            <div key={index} className={`p-2 rounded ${
              check.status === 'compliant' ? 'bg-green-50 text-green-700' :
              check.status === 'partial' ? 'bg-yellow-50 text-yellow-700' :
              'bg-red-50 text-red-700'
            }`}>
              <div className="font-bold">{check.standard}</div>
              <div className="text-sm">Status: {check.status}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="flex justify-end space-x-2">
        <Button variant="outline">Detailed Report</Button>
        <Button>Apply Suggestions</Button>
      </div>
    </Card>
  );
};

// Export an empty object to make this a module
export {};
