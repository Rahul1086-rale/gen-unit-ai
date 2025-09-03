
import { useState } from "react";
import { Play, Loader2, CheckCircle, XCircle, FileText, Code, Download, Eye, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

interface TestGenerationProps {
  files: any[];
  onTestGenerated: (results: any) => void;
}

type TestStatus = 'idle' | 'generating' | 'parsing' | 'completed' | 'failed';

const TestGeneration = ({ files, onTestGenerated }: TestGenerationProps) => {
  const [status, setStatus] = useState<TestStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [results, setResults] = useState<any>(null);
  const [excelData, setExcelData] = useState<any>(null);
  const [testScripts, setTestScripts] = useState<any>(null);

  const steps = [
    { id: 'generating', label: 'Generating Tests with Gemini AI', progress: 50 },
    { id: 'parsing', label: 'Test Generation Complete', progress: 100 }
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

      // Set completion status
      setResults({ generated: true });
      setStatus('completed');
      onTestGenerated({ generated: true });
    } catch (error) {
      setStatus('failed');
      console.error('Test generation failed:', error);
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'generating':
      case 'parsing':
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
              <div className="mt-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <Eye className="h-4 w-4 mr-2" />
                        View Excel Report
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
                      <DialogHeader>
                        <DialogTitle>Excel Test Report</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="border rounded-lg p-4 bg-muted/50">
                          <h4 className="font-semibold mb-3">Test Cases Summary</h4>
                          <div className="grid grid-cols-5 gap-2 text-sm font-medium border-b pb-2">
                            <div>Test ID</div>
                            <div>Function Name</div>
                            <div>Description</div>
                            <div>Expected Result</div>
                            <div>Status</div>
                          </div>
                          <div className="space-y-2 mt-2">
                            {excelData?.map((row: any, index: number) => (
                              <div key={index} className="grid grid-cols-5 gap-2 text-sm py-2 border-b">
                                <div className="font-mono">TC_{String(index + 1).padStart(3, '0')}</div>
                                <div className="font-mono">{row.function_name || 'N/A'}</div>
                                <div className="text-muted-foreground">{row.description || 'N/A'}</div>
                                <div className="text-muted-foreground">{row.expected_result || 'N/A'}</div>
                                <div><Badge variant="secondary">Pending</Badge></div>
                              </div>
                            )) || (
                              <div className="text-center py-4 text-muted-foreground">
                                Excel data will be loaded here after generation
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <Eye className="h-4 w-4 mr-2" />
                        View Test Scripts
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
                      <DialogHeader>
                        <DialogTitle>Generated Test Scripts</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        {testScripts ? (
                          <>
                            <div className="space-y-3">
                              <div>
                                <h4 className="font-semibold mb-2">Test Runner (test_runner.c)</h4>
                                <div className="bg-muted p-4 rounded-lg">
                                  <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                                    {testScripts.test_runner_script || 'No test runner script available'}
                                  </pre>
                                </div>
                              </div>
                              
                              <div>
                                <h4 className="font-semibold mb-2">Makefile</h4>
                                <div className="bg-muted p-4 rounded-lg">
                                  <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                                    {testScripts.makefile_content || 'No makefile available'}
                                  </pre>
                                </div>
                              </div>

                              <div>
                                <h4 className="font-semibold mb-2">Test Cases</h4>
                                <div className="space-y-3">
                                  {testScripts.test_cases?.map((testCase: any, index: number) => (
                                    <div key={index} className="bg-muted p-4 rounded-lg">
                                      <h5 className="font-medium mb-2">{testCase.function_name}</h5>
                                      <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                                        {testCase.test_code}
                                      </pre>
                                    </div>
                                  )) || (
                                    <div className="text-center py-4 text-muted-foreground">
                                      No test cases available
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </>
                        ) : (
                          <div className="text-center py-8 text-muted-foreground">
                            <Code className="h-12 w-12 mx-auto mb-4 opacity-50" />
                            <p>Test scripts will be loaded here after generation</p>
                          </div>
                        )}
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default TestGeneration;
