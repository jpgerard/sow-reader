import React, { useState } from 'react';
import { Search, Plus, FileText, GitBranch, RefreshCw, Settings, ChevronDown, MessageSquare, Check, Brain, Zap, History, Users, Layout } from 'lucide-react';
import { Card, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';
import { AIAnalysisPanel } from './components/AIAnalysisPanel';
import { AIRequirementInsights } from './types/AIAnalysis';

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
      'Security constraints'
    ],
    potentialRisks: [
      'Scalability limitations',
      'Integration challenges'
    ],
    recommendedActions: [
      'Define performance metrics',
      'Specify security protocols'
    ]
  },
  terminologyStandardization: [
    {
      originalTerm: 'system interaction',
      recommendedTerm: 'user interface engagement',
      confidence: 0.85
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
      testScenario: 'Validate dimming response',
      testType: 'system',
      complexity: 'medium'
    }
  ],
  complianceChecks: [
    {
      standard: 'ISO 26262',
      status: 'partial',
      details: ['Safety requirements need enhancement']
    }
  ],
  workflowPatterns: [
    {
      patternName: 'Requirements Refinement',
      frequency: 0.75,
      efficiency: 0.65,
      suggestedOptimizations: [
        'Implement iterative review process'
      ]
    }
  ],
  ambiguityDetection: {
    phrases: ['should handle', 'might need'],
    suggestedReplacements: ['must handle', 'requires'],
    ambiguityScore: 0.45
  },
  performanceMetrics: {
    processingTime: 0.25,
    confidenceLevel: 0.88
  }
};

interface Requirement {
  id: string;
  title: string;
  description: string;
  status: string;
  type: string;
  priority: string;
}

const requirements: Requirement[] = [
  {
    id: 'REQ-001',
    title: 'Automatic Dimming Activation',
    description: 'The rearview mirror shall automatically dim in response to headlights from vehicles approaching from the rear during night-time driving or low-light conditions.',
    status: 'In Review',
    type: 'Functional',
    priority: 'High'
  },
  {
    id: 'REQ-002',
    title: 'Manual Override',
    description: 'The system shall allow the driver to manually control the dimming feature through a switch located on the mirror or within the vehicle\'s central control interface.',
    status: 'Approved',
    type: 'Functional',
    priority: 'Medium'
  }
];

const RequirementsManagementUI: React.FC = () => {
  const [selectedRequirement, setSelectedRequirement] = useState<Requirement | null>(null);
  const [showAIInsights, setShowAIInsights] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCollaborators] = useState([
    { id: 1, name: 'John Doe', status: 'active' },
    { id: 2, name: 'Jane Smith', status: 'reviewing' }
  ]);

  const handleAnalyzeRequirement = () => {
    setShowAIInsights(true);
  };

  const handleInputChange = (field: keyof Requirement, value: string) => {
    if (selectedRequirement) {
      setSelectedRequirement({
        ...selectedRequirement,
        [field]: value
      });
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Sidebar */}
      <div className="w-16 bg-gray-900 p-3 flex flex-col items-center space-y-4">
        <Button variant="ghost" className="w-10 h-10 p-2 text-gray-400 hover:text-white">
          <FileText className="w-6 h-6" />
        </Button>
        <Button variant="ghost" className="w-10 h-10 p-2 text-gray-400 hover:text-white">
          <GitBranch className="w-6 h-6" />
        </Button>
        <Button variant="ghost" className="w-10 h-10 p-2 text-gray-400 hover:text-white">
          <Brain className="w-6 h-6" />
        </Button>
        <div className="flex-grow" />
        <Button variant="ghost" className="w-10 h-10 p-2 text-gray-400 hover:text-white">
          <Settings className="w-6 h-6" />
        </Button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Project Navigator */}
        <div className="w-64 bg-white border-r">
          <div className="p-4">
            <Button className="w-full justify-between">
              MFAI Project
              <ChevronDown className="w-4 h-4" />
            </Button>
          </div>
          <div className="p-4 border-t relative">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search requirements..."
                className="pl-10 w-full"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="overflow-y-auto">
            {requirements.map(req => (
              <div
                key={req.id}
                className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${
                  selectedRequirement?.id === req.id ? 'bg-blue-50' : ''
                }`}
                onClick={() => setSelectedRequirement(req)}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{req.id}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    req.status === 'Approved' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {req.status}
                  </span>
                </div>
                <div className="text-sm mt-1 text-gray-600 truncate">
                  {req.title}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Toolbar */}
          <div className="h-16 border-b bg-white flex items-center px-4 justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                New Requirement
              </Button>
              <Button variant="outline">Import</Button>
              <Button variant="outline">Export</Button>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline" onClick={handleAnalyzeRequirement}>
                <Zap className="w-4 h-4 mr-2" />
                AI Analysis
              </Button>
              <Button className="bg-blue-600 text-white hover:bg-blue-700">
                <Check className="w-4 h-4 mr-2" />
                Approve
              </Button>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6 overflow-y-auto">
            {selectedRequirement ? (
              <Card>
                <CardContent className="p-6">
                  <Tabs defaultValue="details">
                    <TabsList>
                      <TabsTrigger value="details">Details</TabsTrigger>
                      <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
                      <TabsTrigger value="relationships">Relationships</TabsTrigger>
                      <TabsTrigger value="history">History</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="details" className="mt-4">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">ID</label>
                          <Input value={selectedRequirement.id} readOnly />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Title</label>
                          <Input 
                            value={selectedRequirement.title}
                            onChange={(e) => handleInputChange('title', e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Description</label>
                          <textarea 
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            rows={4}
                            value={selectedRequirement.description}
                            onChange={(e) => handleInputChange('description', e.target.value)}
                          />
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Type</label>
                            <Input 
                              value={selectedRequirement.type}
                              onChange={(e) => handleInputChange('type', e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Priority</label>
                            <Input 
                              value={selectedRequirement.priority}
                              onChange={(e) => handleInputChange('priority', e.target.value)}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Status</label>
                            <Input 
                              value={selectedRequirement.status}
                              onChange={(e) => handleInputChange('status', e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="ai-insights" className="mt-4">
                      <AIAnalysisPanel insights={mockAIInsights} />
                    </TabsContent>

                    <TabsContent value="relationships" className="mt-4">
                      <div className="text-gray-500">Relationship mapping coming soon...</div>
                    </TabsContent>

                    <TabsContent value="history" className="mt-4">
                      <div className="text-gray-500">History tracking coming soon...</div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <div className="text-center text-gray-500 mt-10">
                Select a requirement to view details
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar - AI Assistant & Collaboration */}
        <div className="w-80 bg-white border-l flex flex-col">
          {/* AI Assistant Section */}
          <div className="p-4 border-b">
            <h3 className="font-medium mb-4">AI Assistant</h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <Plus className="w-4 h-4 mr-2" />
                Generate Requirements
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <RefreshCw className="w-4 h-4 mr-2" />
                Augment Requirements
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Search className="w-4 h-4 mr-2" />
                Impact Analysis
              </Button>
            </div>
          </div>

          {/* Collaboration Section */}
          <div className="p-4 border-b">
            <h3 className="font-medium mb-4">Active Collaborators</h3>
            <div className="space-y-2">
              {activeCollaborators.map(user => (
                <div key={user.id} className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    user.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  <span>{user.name}</span>
                  <span className="text-xs text-gray-500">
                    {user.status === 'active' ? 'editing' : 'reviewing'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Template Management */}
          <div className="p-4 border-b">
            <h3 className="font-medium mb-4">Templates</h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <Layout className="w-4 h-4 mr-2" />
                Manage Templates
              </Button>
            </div>
          </div>

          {/* Activity History */}
          <div className="flex-1 p-4 overflow-y-auto">
            <h3 className="font-medium mb-4">Recent Activity</h3>
            <div className="space-y-2">
              <div className="text-sm text-gray-600">
                <History className="w-4 h-4 inline mr-2" />
                John updated REQ-001
                <div className="text-xs text-gray-500 ml-6">5 minutes ago</div>
              </div>
              <div className="text-sm text-gray-600">
                <MessageSquare className="w-4 h-4 inline mr-2" />
                Jane commented on REQ-002
                <div className="text-xs text-gray-500 ml-6">10 minutes ago</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RequirementsManagementUI;
