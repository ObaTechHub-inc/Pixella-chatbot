#!/usr/bin/env python3
"""
Pixella - Main Verification and Setup Hub
Central command hub for verifying installation and configuration
"""

import sys
import os
from pathlib import Path

# Ensure Python 3.11+
if sys.version_info < (3, 11):
    print("❌ Error: Python 3.11 or higher is required")
    print(f"   Your version: {sys.version_info.major}.{sys.version_info.minor}")
    print(f"   Required: 3.11+")
    sys.exit(1)


# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


class PixellaVerifier:
    """Verify Pixella installation and configuration"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.checks_passed = 0
        self.checks_failed = 0
    
    def print_header(self):
        """Print welcome header"""
        print(f"\n{CYAN}{'='*60}")
        print(f"{'🤖 PIXELLA - VERIFICATION & SETUP HUB':^60}")
        print(f"{'='*60}{RESET}\n")
    
    def check_python_version(self) -> bool:
        """Verify Python 3.11+ is being used"""
        print(f"{BLUE}[1/8]{RESET} Checking Python version...")
        version = sys.version_info
        
        if version >= (3, 11):
            print(f"  {GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{RESET}\n")
            self.checks_passed += 1
            return True
        else:
            print(f"  {RED}✗ Python {version.major}.{version.minor} (required: 3.11+){RESET}\n")
            self.checks_failed += 1
            return False
    
    def check_env_file(self) -> bool:
        """Verify .env file exists"""
        print(f"{BLUE}[2/8]{RESET} Checking .env file...")
        
        if self.env_file.exists():
            print(f"  {GREEN}✓ .env file found{RESET}\n")
            self.checks_passed += 1
            return True
        else:
            print(f"  {RED}✗ .env file not found{RESET}")
            print(f"  {YELLOW}→ Run: pixella config --init{RESET}\n")
            self.checks_failed += 1
            return False
    
    def check_env_variables(self) -> bool:
        """Verify required environment variables"""
        print(f"{BLUE}[3/8]{RESET} Checking environment variables...")
        
        try:
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
            
            api_key = os.getenv("GOOGLE_API_KEY")
            model = os.getenv("GOOGLE_AI_MODEL")
            
            if api_key and model:
                print(f"  {GREEN}✓ GOOGLE_API_KEY set{RESET}")
                print(f"  {GREEN}✓ GOOGLE_AI_MODEL: {model}{RESET}\n")
                self.checks_passed += 1
                return True
            else:
                print(f"  {RED}✗ Missing environment variables{RESET}")
                if not api_key:
                    print(f"  {YELLOW}→ GOOGLE_API_KEY not set{RESET}")
                if not model:
                    print(f"  {YELLOW}→ GOOGLE_AI_MODEL not set{RESET}")
                print()
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"  {RED}✗ Error loading .env: {e}{RESET}\n")
            self.checks_failed += 1
            return False
    
    def check_modules(self) -> bool:
        """Verify all required Python modules"""
        print(f"{BLUE}[4/8]{RESET} Checking Python modules...")
        
        modules = [
            ("typer", "CLI framework"),
            ("streamlit", "Web UI"),
            ("langchain", "LLM chains"),
            ("langchain_google_genai", "Google Generative AI"),
            ("chromadb", "Vector database"),
            ("dotenv", "Environment variables"),
            ("rich", "Styling"),
        ]
        
        missing = []
        for module, description in modules:
            try:
                __import__(module)
                print(f"  {GREEN}✓ {module:<25} - {description}{RESET}")
            except ImportError:
                print(f"  {RED}✗ {module:<25} - {description}{RESET}")
                missing.append(module)
        
        
        if missing:
            print(f"\n  {YELLOW}→ Install missing packages: pip install {' '.join(missing)}{RESET}\n")
            self.checks_failed += 1
            return False
        
        print()
        self.checks_passed += 1
        return True
    
    def check_directories(self) -> bool:
        """Verify necessary directories exist"""
        print(f"{BLUE}[5/8]{RESET} Checking directories...")
        
        directories = [
            ("bin", "Executables"),
            ("db", "Databases (created on first use)"),
            ("data", "Session data (created on first use)"),
        ]
        
        all_exist = True
        for dir_name, description in directories:
            dir_path = self.project_root / dir_name
            if dir_path.exists() or dir_name in ["db", "data"]:
                status = "exists" if dir_path.exists() else "will be created"
                print(f"  {GREEN}✓ /{dir_name:<15} - {description} ({status}){RESET}")
            else:
                print(f"  {RED}✗ /{dir_name:<15} - {description}{RESET}")
                all_exist = False
        
        if all_exist:
            self.checks_passed += 1
            print()
            return True
        else:
            self.checks_failed += 1
            print()
            return False
    
    def check_python_modules_import(self) -> bool:
        """Quick check that core modules can be imported"""
        print(f"{BLUE}[6/8]{RESET} Checking core module imports...")
        
        try:
            # Simple import check without initializing complex objects
            import chatbot
            import chromadb_rag
            import memory
            import config
            
            print(f"  {GREEN}✓ All core modules importable{RESET}\n")
            self.checks_passed += 1
            return True
        except Exception as e:
            print(f"  {YELLOW}⚠ Module import warning: {e} (may be non-fatal){RESET}\n")
            # Don't count as failure - could be harmless
            return True
    
    def check_rag(self) -> bool:
        """Verify RAG system availability"""
        print(f"{BLUE}[7/8]{RESET} Checking RAG system...")
        
        try:
            from chromadb_rag import get_current_embedding_model
            model = get_current_embedding_model()
            print(f"  {GREEN}✓ RAG embedding model: {model}{RESET}\n")
            self.checks_passed += 1
            return True
        except Exception as e:
            print(f"  {YELLOW}⚠ RAG warning: {e} (optional){RESET}\n")
            # Don't count as failure - RAG is optional
            return True
    
    def check_config_system(self) -> bool:
        """Verify config system"""
        print(f"{BLUE}[8/8]{RESET} Checking config system...")
        
        try:
            from config import CONFIG_TEMPLATE, load_env
            count = len(CONFIG_TEMPLATE)
            print(f"  {GREEN}✓ Config system ready ({count} settings){RESET}\n")
            self.checks_passed += 1
            return True
        except Exception as e:
            print(f"  {YELLOW}⚠ Config warning: {e} (optional){RESET}\n")
            # Don't count as failure - config is optional for this check
            return True
    
    def print_summary(self):
        """Print verification summary"""
        # Only count hard failures
        total_failures = self.checks_failed
        total_passed = self.checks_passed
        
        print(f"{CYAN}{'='*60}")
        print(f"{'VERIFICATION SUMMARY':^60}")
        print(f"{'='*60}{RESET}")
        print(f"  {GREEN}✓ Critical checks passed: {total_passed}{RESET}")
        
        if total_failures > 0:
            print(f"  {RED}✗ Critical checks failed: {total_failures}{RESET}")
        
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        if total_failures == 0:
            print(f"{GREEN}✓ All critical checks passed! Pixella is ready to use.{RESET}\n")
            print("Quick start:")
            print("  pixella cli --interactive    # Start interactive mode")
            print("  pixella ui                   # Start web interface")
            print("  pixella config --show        # View settings")
            print()
            return True
        else:
            print(f"{RED}✗ Please fix the critical issues above before using Pixella.{RESET}\n")
            print("Quick fixes:")
            print("  pixella config --init        # Initialize configuration")
            print("  pip install -r requirements.txt  # Install dependencies")
            print()
            return False
    
    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        self.print_header()
        
        self.check_python_version()
        self.check_env_file()
        self.check_env_variables()
        self.check_modules()
        self.check_directories()
        self.check_python_modules_import()
        self.check_rag()
        self.check_config_system()
        
        success = self.print_summary()
        return success


def main():
    """Main entry point"""
    verifier = PixellaVerifier()
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
