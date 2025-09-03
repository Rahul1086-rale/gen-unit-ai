
import { FileCode2, Zap } from "lucide-react";

const Header = () => {
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className="relative">
              <FileCode2 className="h-8 w-8 text-primary" />
              <Zap className="h-4 w-4 text-warning absolute -top-1 -right-1" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                RT UnitTestGen
              </h1>
              <p className="text-xs text-muted-foreground">
                AI-Powered Unit Testing with GCC Integration
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
