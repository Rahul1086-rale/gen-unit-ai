
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

  const API_BASE_URL = 'http://localhost:8000';

  const uploadFiles = async (files: any[]) => {
    const formData = new FormData();
    
    for (const file of files) {
      formData.append('files', file);
    }
    
    const response = await fetch(`${API_BASE_URL}/upload_files`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return response.json();
  };

  const generateTestsAPI = async (fileData: any[]) => {
    const response = await fetch(`${API_BASE_URL}/generate_tests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ files: fileData }),
    });
    
    if (!response.ok) {
      throw new Error(`Test generation failed: ${response.statusText}`);
    }
    
    return response.json();
  };

  const generateTests = async () => {
    if (!files || files.length === 0) {
      console.error('No files available for processing');
      return;
    }

    setStatus('generating');
    setProgress(0);
    setCurrentStep('Uploading files...');
    
    try {
      // Step 1: Upload files and read content
      setProgress(25);
      const fileData = files.map(file => ({
        filename: file.name,
        content: file.content || '',
        size: file.size
      }));

      // Step 2: Generate tests with Gemini AI
      setCurrentStep('Generating Tests with Gemini AI');
      setProgress(50);
      
      const response = await generateTestsAPI(fileData);
      
      if (response.status === 'success' && response.data) {
        // Step 3: Parse response
        setCurrentStep('Test Generation Complete');
        setStatus('parsing');
        setProgress(100);
        
        const testData = response.data;
        setResults(testData);
        setExcelData(testData.test_cases || []);
        setTestScripts({
          test_runner_script: testData.test_runner_script || '',
          makefile_content: testData.makefile_content || '',
          test_cases: testData.test_cases || []
        });
        
        setStatus('completed');
        onTestGenerated(testData);
      } else {
        throw new Error(response.message || 'Failed to generate tests');
      }
    } catch (error) {
      setStatus('failed');
      setCurrentStep('Generation failed');
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <Eye className="h-4 w-4 mr-2" />
                        View Excel Report
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-6xl max-h-[80vh] overflow-auto">
                      <DialogHeader>
                        <DialogTitle>Excel Test Report</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="border rounded-lg p-4 bg-muted/50">
                          <h4 className="font-semibold mb-3">Test Cases Summary</h4>
                          <div className="overflow-x-auto">
                            <table className="w-full min-w-[600px]">
                              <thead>
                                <tr className="text-sm font-medium border-b">
                                  <th className="text-left p-2 w-20">Test ID</th>
                                  <th className="text-left p-2 w-32">Function Name</th>
                                  <th className="text-left p-2 flex-1">Description</th>
                                  <th className="text-left p-2 flex-1">Expected Result</th>
                                  <th className="text-left p-2 w-20">Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {excelData?.map((row: any, index: number) => (
                                  <tr key={index} className="text-sm border-b">
                                    <td className="p-2 font-mono">TC_{String(index + 1).padStart(3, '0')}</td>
                                    <td className="p-2 font-mono">{row.function_name || 'N/A'}</td>
                                    <td className="p-2 text-muted-foreground">{row.description || 'N/A'}</td>
                                    <td className="p-2 text-muted-foreground">{row.expected_result || 'N/A'}</td>
                                    <td className="p-2"><Badge variant="secondary">Pending</Badge></td>
                                  </tr>
                                )) || (
                                  <tr>
                                    <td colSpan={5} className="text-center py-4 text-muted-foreground">
                                      Excel data will be loaded here after generation
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
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
                    <DialogContent className="max-w-6xl max-h-[80vh] overflow-auto">
                      <DialogHeader>
                        <DialogTitle>Generated Test Scripts</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        {testScripts ? (
                          <>
                            <div className="space-y-3">
                              <div>
                                <h4 className="font-semibold mb-2">Test Runner (test_runner.c)</h4>
                                <div className="bg-muted p-4 rounded-lg overflow-x-auto">
                                  <pre className="text-xs whitespace-pre-wrap break-words">
                                    {testScripts.test_runner_script || 'No test runner script available'}
                                  </pre>
                                </div>
                              </div>
                              
                              <div>
                                <h4 className="font-semibold mb-2">Makefile</h4>
                                <div className="bg-muted p-4 rounded-lg overflow-x-auto">
                                  <pre className="text-xs whitespace-pre-wrap break-words">
                                    {testScripts.makefile_content || 'No makefile available'}
                                  </pre>
                                </div>
                              </div>

                              <div>
                                <h4 className="font-semibold mb-2">Test Cases</h4>
                                <div className="space-y-3">
                                  {testScripts.test_cases?.map((testCase: any, index: number) => (
                                    <div key={index} className="bg-muted p-4 rounded-lg overflow-x-auto">
                                      <h5 className="font-medium mb-2">{testCase.function_name}</h5>
                                      <pre className="text-xs whitespace-pre-wrap break-words">
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

                  {results.csv_content && (
                    <Button 
                      variant="outline" 
                      className="justify-start"
                      onClick={() => {
                        const blob = new Blob([results.csv_content], { type: 'text/csv' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'test_cases.csv';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download CSV
                    </Button>
                  )}

                  {testScripts?.test_runner_script && (
                    <Button 
                      variant="outline" 
                      className="justify-start"
                      onClick={() => {
                        const blob = new Blob([testScripts.test_runner_script], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'test_runner.c';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download Test Runner
                    </Button>
                  )}

                  {testScripts?.makefile_content && (
                    <Button 
                      variant="outline" 
                      className="justify-start"
                      onClick={() => {
                        const blob = new Blob([testScripts.makefile_content], { type: 'text/plain' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'Makefile';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download Makefile
                    </Button>
                  )}
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
