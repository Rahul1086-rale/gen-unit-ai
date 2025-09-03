
import { useState } from "react";
import { Play, Loader2, CheckCircle, XCircle, FileText, Code, Download, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface TestGenerationProps {
  files: any[];
  onTestGenerated: (results: any) => void;
}

type TestStatus = 'idle' | 'generating' | 'parsing' | 'running' | 'completed' | 'failed';

const TestGeneration = ({ files, onTestGenerated }: TestGenerationProps) => {
  const [status, setStatus] = useState<TestStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [results, setResults] = useState<any>(null);

  const steps = [
    { id: 'generating', label: 'Generating Tests with Gemini AI', progress: 25 },
    { id: 'parsing', label: 'Parsing Response & Extracting Scripts', progress: 50 },
    { id: 'running', label: 'Compiling & Running Unit Tests', progress: 75 },
    { id: 'completed', label: 'Generating Coverage Report', progress: 100 }
  ];

  const generateTests = async () => {
    setStatus('generating');
    setProgress(0);
    
    try {
      // Simulate the workflow steps
      for (const step of steps) {
        setCurrentStep(step.label);
        setStatus(step.id as TestStatus);
        setProgress(step.progress);
        
        // Simulate API calls and processing time
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      // Mock results
      const mockResults = {
        testsGenerated: 12,
        testsPassed: 10,
        testsFailed: 2,
        coverage: 85.5,
        executionTime: '2.34s',
        failedTests: [
          { name: 'test_divide_by_zero', error: 'Assertion failed: Expected 0, got inf' },
          { name: 'test_null_pointer', error: 'Segmentation fault' }
        ],
        excelReport: 'unit_tests_report.xlsx',
        coverageReport: 'coverage_report.html'
      };

      setResults(mockResults);
      setStatus('completed');
      onTestGenerated(mockResults);
    } catch (error) {
      setStatus('failed');
      console.error('Test generation failed:', error);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'generating':
      case 'parsing':
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />;
      default:
        return null;
    }
  };

  const getStatusBadge = () => {
    const configs = {
      idle: { variant: 'secondary', text: 'Ready' },
      generating: { variant: 'default', text: 'Generating...' },
      parsing: { variant: 'default', text: 'Parsing...' },
      running: { variant: 'default', text: 'Running...' },
      completed: { variant: 'success', text: 'Completed' },
      failed: { variant: 'destructive', text: 'Failed' }
    };

    const config = configs[status] || configs.idle;
    return <Badge variant={config.variant as any}>{config.text}</Badge>;
  };

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Code className="h-5 w-5 text-primary" />
            <span>Unit Test Generation</span>
          </div>
          {getStatusBadge()}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {files.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Upload source files to begin test generation</p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              <div>
                <p className="font-medium">Files Ready: {files.length}</p>
                <p className="text-sm text-muted-foreground">
                  Source: {files.filter(f => f.type === 'source').length} | 
                  Headers: {files.filter(f => f.type === 'header').length}
                </p>
              </div>
              <Button 
                onClick={generateTests}
                disabled={status !== 'idle' && status !== 'completed' && status !== 'failed'}
                className="w-full gradient-primary"
                size="lg"
              >
                {(status !== 'idle' && status !== 'completed' && status !== 'failed') ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating Unit Tests...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Generate Unit Tests
                  </>
                )}
              </Button>
            </div>

            {status !== 'idle' && (
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  {getStatusIcon()}
                  <span className="text-sm font-medium">{currentStep}</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}

            {results && status === 'completed' && (
              <Tabs defaultValue="summary" className="mt-6">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="failures">Failures</TabsTrigger>
                  <TabsTrigger value="reports">Reports</TabsTrigger>
                </TabsList>
                
                <TabsContent value="summary" className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-2xl font-bold text-primary">{results.testsGenerated}</p>
                      <p className="text-sm text-muted-foreground">Tests Generated</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-2xl font-bold text-success">{results.testsPassed}</p>
                      <p className="text-sm text-muted-foreground">Tests Passed</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-2xl font-bold text-destructive">{results.testsFailed}</p>
                      <p className="text-sm text-muted-foreground">Tests Failed</p>
                    </div>
                    <div className="bg-card p-4 rounded-lg border">
                      <p className="text-2xl font-bold text-warning">{results.coverage}%</p>
                      <p className="text-sm text-muted-foreground">Coverage</p>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="failures">
                  {results.failedTests.length > 0 ? (
                    <div className="space-y-3">
                      {results.failedTests.map((test: any, index: number) => (
                        <div key={index} className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                          <h4 className="font-mono text-sm font-medium text-destructive mb-2">
                            {test.name}
                          </h4>
                          <p className="text-sm text-muted-foreground font-mono">
                            {test.error}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-success">
                      <CheckCircle className="h-12 w-12 mx-auto mb-4" />
                      <p>All tests passed successfully!</p>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="reports" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <Button variant="outline" className="justify-start">
                      <Eye className="h-4 w-4 mr-2" />
                      View Excel Report
                    </Button>
                    <Button variant="outline" className="justify-start">
                      <Download className="h-4 w-4 mr-2" />
                      Download Excel Report
                    </Button>
                    <Button variant="outline" className="justify-start">
                      <Eye className="h-4 w-4 mr-2" />
                      View Test Scripts
                    </Button>
                    <Button variant="outline" className="justify-start">
                      <Download className="h-4 w-4 mr-2" />
                      Download Test Scripts
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default TestGeneration;
