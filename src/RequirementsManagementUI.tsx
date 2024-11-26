import React, { useState } from 'react';
import { AIAnalysisPanel } from './components/AIAnalysisPanel';
import { AIRequirementInsights } from './types/AIAnalysis';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';

// Mock data for requirements and AI insights
const mockAIInsights: AIRequirementInsights = {
  qualityScore: {
    overallScore: 0.85,
    clarity: 0.78,
    completeness: 0.92,
    specificity: 0.80,
    testability: 0.75
  },
  gapAnalysis: {
    missingElements: [
      'Performance requirements',
      'Security constraints',
      'User authentication details'
    ],
    potentialRisks: [
      'Scalability limitations',
      'Potential integration challenges'
    ],
    recommendedActions: [
      'Define clear performance metrics',
      'Specify security protocols',
      'Elaborate on user access controls'
    ]
  },
  terminologyStandardization: [
    {
      originalTerm: 'system interaction',
      recommendedTerm: 'user interface engagement',
      confidence: 0.85
    },
    {
      originalTerm: 'data processing',
      recommendedTerm: 'information transformation',
      confidence: 0.72
    }
  ],
  relationshipDetection: [
    {
      relatedRequirements: ['User Authentication', 'Access Control'],
      relationshipStrength: 0.9,
      relationshipType: 'dependency'
    }
  ],
  testCaseSuggestions: [
    {
      testScenario: 'Validate user authentication workflow',
      testType: 'system',
      complexity: 'medium'
    },
    {
      testScenario: 'Performance load testing',
      testType: 'integration',
      complexity: 'high'
    }
  ],
  complianceChecks: [
    {
      standard: 'GDPR',
      status: 'partial',
      details: [
        'Data protection measures incomplete',
        'User consent mechanism needs refinement'
      ]
    },
    {
      standard: 'ISO 27001',
      status: 'compliant',
      details: ['Security framework adequately defined']
    }
  ],
  workflowPatterns: [
    {
      patternName: 'Requirements Refinement',
      frequency: 0.75,
      efficiency: 0.65,
      suggestedOptimizations: [
        'Implement iterative review process',
        'Add collaborative annotation features'
      ]
    }
  ],
  ambiguityDetection: {
    phrases: [
      'system should handle',
      'user might need',
      'potentially implement'
    ],
    suggestedReplacements: [
      'system must explicitly handle',
      'user requires',
      'definitively implement'
    ],
    ambiguityScore: 0.45
  },
  performanceMetrics: {
    processingTime: 0.25,
    confidenceLevel: 0.88
  }
};

// Mock requirements data with explicit type
interface Requirement {
  id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
}

const mockRequirements: Requirement[] = [
  {
    id: '1',
    title: 'User Authentication',
    description: 'Implement secure user login and registration process',
    priority: 'High',
    status: 'Draft'
  },
  {
    id: '2',
    title: 'Dashboard Functionality',
    description: 'Create a comprehensive user dashboard with key metrics',
    priority: 'Medium',
    status: 'In Progress'
  }
];

export const RequirementsManagementUI: React.FC = () => {
  const [requirementText, setRequirementText] = useState('');
  const [requirements, setRequirements] = useState<Requirement[]>(mockRequirements);
  const [showAIInsights, setShowAIInsights] = useState(false);
  const [activeTab, setActiveTab] = useState('requirements');

  const handleAddRequirement = () => {
    if (requirementText.trim()) {
      const newRequirement: Requirement = {
        id: (requirements.length + 1).toString(),
        title: requirementText.split('\n')[0],
        description: requirementText,
        priority: 'Medium',
        status: 'Draft'
      };
      setRequirements([...requirements, newRequirement]);
      setRequirementText('');
    }
  };

  const handleAnalyzeRequirement = () => {
    setShowAIInsights(true);
    setActiveTab('analysis');
  };

  const handleClearRequirement = () => {
    setRequirementText('');
    setShowAIInsights(false);
  };

  return (
    <div className="container mx-auto p-4">
      <Tabs defaultValue={activeTab}>
        <TabsList>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          <TabsTrigger value="analysis">AI Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="requirements">
          <div className="grid grid-cols-3 gap-4">
            <Card className="p-4 col-span-2">
              <h2 className="text-xl font-bold mb-4">Add New Requirement</h2>
              <Input 
                placeholder="Enter your requirement details"
                value={requirementText}
                onChange={(e) => setRequirementText(e.target.value)}
                className="mb-4 h-32"
              />
              <div className="flex space-x-2">
                <Button onClick={handleAddRequirement}>
                  Add Requirement
                </Button>
                <Button variant="outline" onClick={handleClearRequirement}>
                  Clear
                </Button>
                <Button onClick={handleAnalyzeRequirement}>
                  AI Analysis
                </Button>
              </div>
            </Card>

            <Card className="p-4">
              <h2 className="text-xl font-bold mb-4">Requirements List</h2>
              <div className="space-y-2">
                {requirements.map((req) => (
                  <div key={req.id} className="border p-2 rounded">
                    <div className="font-semibold">{req.title}</div>
                    <div className="text-sm text-gray-600">{req.description}</div>
                    <div className="flex justify-between text-xs mt-1">
                      <span>Priority: {req.priority}</span>
                      <span>Status: {req.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analysis">
          {showAIInsights && (
            <div className="grid grid-cols-1 gap-4">
              <AIAnalysisPanel insights={mockAIInsights} />
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RequirementsManagementUI;
