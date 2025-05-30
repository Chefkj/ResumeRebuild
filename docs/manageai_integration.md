# ManageAI Resume API Integration for Resume Rebuilder

This document provides information about how the Resume Rebuilder application handles the lifecycle of the ManageAI Resume API server.

## Server Lifecycle Management

The Resume Rebuilder application now automatically manages the lifecycle of the ManageAI Resume API server:

1. When the application starts, it automatically starts the ManageAI Resume API server.
2. When the application is closed, it automatically stops the server.
3. If the server becomes unresponsive during operation, it will be automatically restarted.
4. The application will fall back to the local server if the ManageAI API server cannot be started.

## Implementation Details

Server management is handled by the following components:

- **ManageAIAPIManager**: A class that manages the lifecycle of the ManageAI Resume API server. It provides methods to start, stop, restart, and check the status of the server.
- **ResumeAPIIntegration**: A unified interface for interacting with different backends (ManageAI Resume API, local server, or direct LLM Studio connection).
- **Settings**: A centralized location for application settings and preferences, including which API backend to use.

## Manual Server Management

You can also manually manage the ManageAI Resume API server using the `manage_api_server.py` script:

```bash
# Start the server
./manage_api_server.py start

# Check server status
./manage_api_server.py status

# Restart the server
./manage_api_server.py restart

# Stop the server
./manage_api_server.py stop
```

## Configuration

The application is configured to use the following default settings:
- Server: `http://localhost:8080`
- API Key: Environment variable `RESUME_API_KEY` or default test key

You can change these settings in the application's settings panel or by setting environment variables.

## Testing the Integration

The `demo_with_managerai.sh` script demonstrates how to use the ManageAI Resume API integration:

```bash
./demo_with_managerai.sh
```

This will:
1. Check if the ManageAI Resume API server is running
2. Start the server if it's not running
3. Run a demo that shows how to use the ManageAI Resume API

To clean up after the demo:

```bash
./demo_with_managerai.sh --cleanup
```

This will stop the ManageAI Resume API server.

## Enhancing the Integration

If you want to enhance the integration, here are some areas to consider:

1. **Error Handling**: Add more robust error handling for different types of server failures
2. **Fallback Mechanism**: Implement a smarter fallback mechanism that tries different backends
3. **UI Integration**: Add a UI to switch between different backends
4. **Health Monitoring**: Enhance health monitoring to detect and recover from more types of failures
5. **Multiple Server Support**: Support connecting to multiple ManageAI Resume API servers
