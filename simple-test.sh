#!/bin/bash
# =============================================================================
# AWS SAM Learning Script - Wikipedia TOC API
# Learn serverless development with hands-on testing
# =============================================================================

set -e

AWS_REGION="us-east-1"
STACK_NAME="sam-sample-pytest"

# Colors for better learning experience
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

setup_environment() {
    echo "🛠️ Setting up development environment..."
    print_info "Checking required tools for serverless development"
    
    # Check required tools
    command -v python3 >/dev/null || { print_error "Python3 not found - install from python.org"; exit 1; }
    command -v aws >/dev/null || { print_error "AWS CLI not found - install from aws.amazon.com/cli"; exit 1; }
    command -v sam >/dev/null || { print_error "SAM CLI not found - install AWS SAM CLI"; exit 1; }
    
    print_info "Installing Python testing libraries..."
    # Install Python packages with educational feedback
    pip install pytest pytest-cov boto3 requests
    
    print_success "Environment setup complete - ready for serverless development!"
}

build_and_test() {
    echo "🏗️ Building application and running tests..."
    print_info "Learning: This step builds your serverless application and runs unit tests"
    
    # Check for template
    [ -f "template.yaml" ] || [ -f "template.yml" ] || { print_error "SAM template not found - this defines your AWS resources"; exit 1; }
    
    # Build with educational feedback
    print_info "Running 'sam build' - this packages your Lambda function and dependencies"
    sam build || { print_error "SAM build failed - check your template.yaml and requirements.txt"; exit 1; }
    
    # Set environment variables for integration tests that need them
    export AWS_SAM_STACK_NAME="$STACK_NAME"
    export AWS_DEFAULT_REGION="$AWS_REGION"
    
    # Run unit tests if they exist
    if [ -d "tests" ]; then
        print_info "Running unit tests - these test individual functions without AWS"
        if pytest tests/unit/ -v 2>/dev/null; then
            print_success "Unit tests passed!"
        else
            print_warning "Unit tests had issues, but continuing..."
        fi
        
        print_info "Skipping integration tests (they need deployed API) - will run after deployment"
    else
        print_warning "No tests directory found - consider adding tests for better code quality"
    fi
    
    print_success "Build and test complete!"
}

local_test() {
    echo "🏠 Running local test..."
    print_info "Learning: This tests your Lambda function locally using Docker"
    
    [ -d ".aws-sam/build" ] || { print_error "No build found. Run build step first"; exit 1; }
    
    # Check Docker
    if ! command -v docker >/dev/null || ! docker info >/dev/null 2>&1; then
        print_warning "Docker not available - install Docker Desktop to test locally"
        return 0
    fi
    
    # Create test event if not exists
    mkdir -p events
    if [ ! -f "events/event.json" ]; then
        print_info "Creating test event with Wikipedia URL parameter"
        cat > events/event.json << 'EOF'
{
  "httpMethod": "GET",
  "path": "/",
  "queryStringParameters": {"url": "https://ja.wikipedia.org/wiki/Amazon_Web_Services"},
  "headers": {"Accept": "application/json"},
  "body": null
}
EOF
    fi
    
    # Find function name from template
    FUNCTION_NAME=$(grep -E "^\s*[A-Za-z][A-Za-z0-9]*Function:" .aws-sam/build/template.yaml | head -1 | sed 's/://g' | sed 's/^[[:space:]]*//' || echo "WikipediaTocFunction")
    
    print_info "Testing function '$FUNCTION_NAME' locally with sample Wikipedia URL"
    if sam local invoke "$FUNCTION_NAME" --event events/event.json; then
        print_success "Local test successful - your function works!"
    else
        print_warning "Local test had issues - check the output above for details"
    fi
    
    print_success "Local test complete!"
}

deploy_and_test() {
    echo "☁️ Deploying to AWS and running integration tests..."
    print_info "Learning: This deploys your app to real AWS and tests the complete system"
    
    [ -d ".aws-sam/build" ] || { print_error "No build found. Run build step first"; exit 1; }
    
    # Check AWS credentials
    aws sts get-caller-identity --region $AWS_REGION >/dev/null || { print_error "AWS credentials not configured - run 'aws configure'"; exit 1; }
    
    # Deploy with educational feedback
    print_info "Deploying to AWS CloudFormation stack: $STACK_NAME"
    if [ -f "samconfig.toml" ]; then
        print_info "Using saved configuration from samconfig.toml"
        sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
    else
        print_info "First time deployment - you'll be asked some questions"
        sam deploy --guided --stack-name $STACK_NAME --region $AWS_REGION
    fi
    
    # Get API URL with better error handling
    print_info "Getting API Gateway URL from CloudFormation outputs..."
    API_URL=""
    
    # Try different output keys that might contain the API URL
    for output_key in "WikipediaTocApi" "ApiGatewayApi" "HelloWorldApi" "Api"; do
        API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" --output text 2>/dev/null || echo "")
        if [ -n "$API_URL" ] && [ "$API_URL" != "None" ]; then
            print_success "Found API endpoint: $API_URL (from $output_key)"
            break
        fi
    done
    
    if [ -n "$API_URL" ] && [ "$API_URL" != "None" ]; then
        print_info "Testing deployed API with Wikipedia URL..."
        echo "🌐 API Test URL: ${API_URL}?url=https://ja.wikipedia.org/wiki/Amazon_Web_Services"
        
        if curl -s "$API_URL?url=https://ja.wikipedia.org/wiki/Amazon_Web_Services" | python -m json.tool; then
            print_success "API test successful - your Wikipedia TOC API is working!"
        else
            print_warning "API test had issues - check if the URL is correct"
        fi
        
        # Run integration tests with proper environment setup
        export API_URL="$API_URL"
        export AWS_SAM_STACK_NAME="$STACK_NAME"
        
        if [ -d "tests/integration" ]; then
            print_info "Running integration tests against deployed API..."
            if pytest tests/integration/ -v --tb=short; then
                print_success "Integration tests passed!"
            else
                print_warning "Some integration tests failed - check the details above"
            fi
        fi
        
        echo ""
        print_success "🎉 Deployment complete! Your Wikipedia TOC API is live at:"
        echo "📡 $API_URL"
        echo "💡 Try it: ${API_URL}?url=https://ja.wikipedia.org/wiki/Python"
    else
        print_warning "Could not get API URL - check CloudFormation stack outputs"
        print_info "Available outputs:"
        aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --query 'Stacks[0].Outputs[*].{Key:OutputKey,Value:OutputValue}' --output table 2>/dev/null || echo "No outputs found"
    fi
    
    print_success "Deploy and test complete!"
}

show_help() {
    echo "🎓 AWS SAM Learning Script - Wikipedia TOC API"
    echo ""
    echo "📚 What you'll learn:"
    echo "  • How to build serverless applications with AWS SAM"
    echo "  • Testing strategies: unit tests, local tests, integration tests"
    echo "  • AWS deployment and CloudFormation basics"
    echo "  • API Gateway and Lambda integration"
    echo ""
    echo "🚀 Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup   - Install tools and dependencies"
    echo "  build   - Build application and run unit tests"
    echo "  local   - Test Lambda function locally with Docker"
    echo "  deploy  - Deploy to AWS and run integration tests"
    echo "  all     - Run all steps in order (recommended for learning)"
    echo "  help    - Show this help"
    echo ""
    echo "💡 Tip: Start with 'all' to see the complete development workflow!"
}

main() {
    case ${1:-all} in
        setup)   setup_environment ;;
        build)   build_and_test ;;
        local)   local_test ;;
        deploy)  deploy_and_test ;;
        all)     
            echo "🎓 Starting complete AWS SAM learning workflow..."
            print_info "You'll learn: setup → build → local test → deploy → integration test"
            echo ""
            setup_environment && build_and_test && local_test && deploy_and_test 
            if [ $? -eq 0 ]; then
                echo ""
                print_success "🎉 Congratulations! You've completed the full serverless development cycle!"
                print_info "Next steps: Modify the code and run again to see the changes"
            fi
            ;;
        help)    show_help ;;
        *)       print_error "Unknown command: $1"; show_help; exit 1 ;;
    esac
}

main "$@"