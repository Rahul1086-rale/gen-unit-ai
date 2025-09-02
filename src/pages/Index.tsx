
import { useState } from "react";
import Header from "@/components/Header";
import FileUpload from "@/components/FileUpload";
import TestGeneration from "@/components/TestGeneration";

const Index = () => {
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [testResults, setTestResults] = useState<any>(null);

  const handleFilesChange = (files: any[]) => {
    setUploadedFiles(files);
    console.log('Files uploaded:', files);
  };

  const handleTestGenerated = (results: any) => {
    setTestResults(results);
    console.log('Test results:', results);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-6 py-8 space-y-8">
        <div className="text-center space-y-4 mb-12">
          <h2 className="text-4xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
            AI-Powered Unit Testing
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Upload your C/C++ source files and let our AI generate comprehensive unit tests 
            with GCC compilation and LCOV coverage reporting
          </p>
        </div>

        <div className="grid gap-8 max-w-4xl mx-auto">
          <FileUpload onFilesChange={handleFilesChange} />
          <TestGeneration 
            files={uploadedFiles}
            onTestGenerated={handleTestGenerated}
          />
        </div>

        {testResults && (
          <div className="max-w-4xl mx-auto mt-12 p-6 bg-success/10 border border-success/20 rounded-lg animate-fade-in">
            <h3 className="text-lg font-semibold text-success mb-2">
              Test Generation Complete!
            </h3>
            <p className="text-muted-foreground">
              Generated {testResults.testsGenerated} unit tests with {testResults.coverage}% coverage. 
              Execution completed in {testResults.executionTime}.
            </p>
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;
