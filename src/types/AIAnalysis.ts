export {};  // Make this a module

export interface RequirementQualityScore {
  overallScore: number;
  clarity: number;
  completeness: number;
  specificity: number;
  testability: number;
}

export interface GapAnalysis {
  missingElements: string[];
  potentialRisks: string[];
  recommendedActions: string[];
}

export interface TerminologyStandardization {
  originalTerm: string;
  recommendedTerm: string;
  confidence: number;
}

export interface RelationshipDetection {
  relatedRequirements: string[];
  relationshipStrength: number;
  relationshipType: 'dependency' | 'conflict' | 'enhancement' | 'prerequisite';
}

export interface TestCaseSuggestion {
  testScenario: string;
  testType: 'unit' | 'integration' | 'system' | 'acceptance';
  complexity: 'low' | 'medium' | 'high';
}

export interface ComplianceCheck {
  standard: string;
  status: 'compliant' | 'partial' | 'non-compliant';
  details: string[];
}

export interface WorkflowPattern {
  patternName: string;
  frequency: number;
  efficiency: number;
  suggestedOptimizations: string[];
}

export interface AmbiguityDetection {
  phrases: string[];
  suggestedReplacements: string[];
  ambiguityScore: number;
}

export interface AIRequirementInsights {
  qualityScore: RequirementQualityScore;
  gapAnalysis: GapAnalysis;
  terminologyStandardization: TerminologyStandardization[];
  relationshipDetection: RelationshipDetection[];
  testCaseSuggestions: TestCaseSuggestion[];
  complianceChecks: ComplianceCheck[];
  workflowPatterns: WorkflowPattern[];
  ambiguityDetection: AmbiguityDetection;
  performanceMetrics: {
    processingTime: number;
    confidenceLevel: number;
  };
}
