import React from 'react';
import { AIRequirementInsights } from '../types/AIAnalysis';
import { Card } from './ui/card';
import { Brain, Zap, History, Lightbulb, BarChart } from 'lucide-react';

interface AIAnalysisPanelProps {
  insights: AIRequirementInsights;
}

export const AIAnalysisPanel: React.FC<AIAnalysisPanelProps> = ({ insights }) => {
  const features = [
    {
      title: 'Intelligent Analysis',
      icon: <Brain className="w-6 h-6 text-blue-500" />,
      items: [
        'Real-time requirement quality scoring',
        'Gap detection and analysis',
        'Context-aware suggestions based on current work',
        'Terminology standardization recommendations'
      ]
    },
    {
      title: 'Smart Suggestions',
      icon: <Zap className="w-6 h-6 text-yellow-500" />,
      items: [
        'Proactive recommendations for improvements',
        'Relationship detection between requirements',
        'Automatic test case generation suggestions',
        'Industry standard compliance checks'
      ]
    },
    {
      title: 'Learning Patterns',
      icon: <History className="w-6 h-6 text-purple-500" />,
      items: [
        'Team pattern recognition',
        'Workflow optimization suggestions',
        'Historical analysis of similar requirements',
        'Common review patterns'
      ]
    },
    {
      title: 'Context-Aware Features',
      icon: <Lightbulb className="w-6 h-6 text-green-500" />,
      items: [
        'Real-time analysis of requirement text',
        'Ambiguity detection',
        'Automatic relationship suggestions',
        'Performance metric recommendations'
      ]
    },
    {
      title: 'AI Insights',
      icon: <BarChart className="w-6 h-6 text-red-500" />,
      items: [
        'Quality scoring with detailed breakdowns',
        'Gap analysis',
        'Impact assessment',
        'Relationship mapping'
      ]
    }
  ];

  return (
    <div className="space-y-6">
      <div className="text-2xl font-bold text-gray-900 mb-8">
        AI Capability Overview
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, index) => (
          <Card key={index} className="p-6">
            <div className="flex items-center space-x-3 mb-4">
              {feature.icon}
              <h3 className="text-lg font-semibold text-gray-900">
                {feature.title}
              </h3>
            </div>
            <ul className="space-y-2">
              {feature.items.map((item, itemIndex) => (
                <li key={itemIndex} className="flex items-start space-x-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2" />
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>

      <Card className="p-6 mt-6">
        <div className="text-lg font-semibold mb-4">Current Analysis Results</div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium text-gray-500">Quality Score</div>
            <div className="text-2xl font-bold text-blue-600">
              {(insights.qualityScore.overallScore * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-gray-500">Confidence Level</div>
            <div className="text-2xl font-bold text-green-600">
              {(insights.performanceMetrics.confidenceLevel * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        <div className="mt-6">
          <div className="text-sm font-medium text-gray-500 mb-2">Key Findings</div>
          <ul className="space-y-2">
            {insights.gapAnalysis.recommendedActions.map((action, index) => (
              <li key={index} className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 mt-2" />
                <span className="text-gray-700">{action}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-6">
          <div className="text-sm font-medium text-gray-500 mb-2">Suggested Improvements</div>
          <ul className="space-y-2">
            {insights.terminologyStandardization.map((term, index) => (
              <li key={index} className="flex items-start space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-2" />
                <span className="text-gray-700">
                  Replace "{term.originalTerm}" with "{term.recommendedTerm}"
                </span>
              </li>
            ))}
          </ul>
        </div>
      </Card>
    </div>
  );
};
