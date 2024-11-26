import React, { useState } from 'react';
import { Search, Plus, FileText, GitBranch, RefreshCw, Settings, ChevronDown, MessageSquare, Check } from 'lucide-react';
import { Card, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';

// Define the type for a requirement
interface Requirement {
  id: string;
  title: string;
  description: string;
  status: string;
  type: string;
  priority: string;
}

const RequirementsManagementUI: React.FC = () => {
  const [selectedRequirement, setSelectedRequirement] = useState<Requirement | null>(null);
  
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

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Sidebar */}
      <div className="w-16 bg-gray-900 p-3 flex flex-col items-center space-y-4">
        <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white">
          <FileText size={24} />
        </Button>
        <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white">
          <GitBranch size={24} />
        </Button>
        <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white">
          <RefreshCw size={24} />
        </Button>
        <div className="flex-grow" />
        <Button variant="ghost" size="icon" className="text-gray-400 hover:text-white">
          <Settings size={24} />
        </Button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Project Navigator */}
        <div className="w-64 bg-white border-r">
          <div className="p-4">
            <Button className="w-full justify-between">
              MFAI Project
              <ChevronDown size={16} />
            </Button>
          </div>
          <div className="p-4 border-t">
            <Input
              placeholder="Search requirements..."
              className="w-full"
              prefix={<Search className="text-gray-400" size={16} />}
            />
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
                <Plus size={16} className="mr-2" />
                New Requirement
              </Button>
              <Button variant="outline">Import</Button>
              <Button variant="outline">Export</Button>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline">
                <MessageSquare size={16} className="mr-2" />
                Review
              </Button>
              <Button className="bg-blue-600">
                <Check size={16} className="mr-2" />
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
                      <TabsTrigger value="relationships">Relationships</TabsTrigger>
                      <TabsTrigger value="history">History</TabsTrigger>
                      <TabsTrigger value="comments">Comments</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="details" className="mt-4">
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">ID</label>
                          <Input value={selectedRequirement.id} readOnly />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Title</label>
                          <Input value={selectedRequirement.title} />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Description</label>
                          <textarea 
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            rows={4}
                            value={selectedRequirement.description}
                          />
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Type</label>
                            <Input value={selectedRequirement.type} />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Priority</label>
                            <Input value={selectedRequirement.priority} />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700">Status</label>
                            <Input value={selectedRequirement.status} />
                          </div>
                        </div>
                      </div>
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

        {/* AI Assistant Panel */}
        <div className="w-80 bg-white border-l">
          <div className="p-4 border-b">
            <h3 className="font-medium">AI Assistant</h3>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <Plus size={16} className="mr-2" />
                Generate Requirements
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <RefreshCw size={16} className="mr-2" />
                Augment Requirements
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Search size={16} className="mr-2" />
                Impact Analysis
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RequirementsManagementUI;
