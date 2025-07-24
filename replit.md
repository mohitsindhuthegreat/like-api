# Free Fire Like Bot API

## Overview

This is a Free Fire Like Bot API service built with Flask that automates the process of sending likes to Free Fire players across multiple servers. The application uses Protocol Buffers for API communication, AES encryption for securing UIDs, and supports various Free Fire servers including IND, BR, US, SAC, NA, PK, MENA, and THAI.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Flask-based architecture with the following key design decisions:

### Backend Architecture
- **Framework**: Flask web framework chosen for its simplicity and lightweight nature
- **Language**: Python 3.x for rapid development and extensive library support
- **Structure**: Modular package structure separating concerns into distinct modules

### API Communication
- **Protocol**: Uses Protocol Buffers (protobuf) for efficient binary serialization when communicating with Free Fire's official APIs
- **Security**: Implements AES encryption in CBC mode for securing player UIDs before transmission
- **Authentication**: Token-based authentication system with server-specific JWT tokens

### Multi-Server Support
- **Server Routing**: Dynamic endpoint selection based on server names (IND, BR, US, etc.)
- **Token Management**: Server-specific token storage and retrieval system
- **Scalability**: Designed to handle multiple servers with different API endpoints

## Key Components

### Core Modules

1. **main.py**: Flask application entry point with route handlers
   - Handles HTTP requests and responses
   - Provides web interface for testing
   - Manages request validation and error handling

2. **app/encryption.py**: Security layer for UID protection
   - AES-256 encryption in CBC mode
   - Base64 encoding for safe transmission
   - Hardcoded keys (would normally be extracted from game client)

3. **app/protobuf_handler.py**: Protocol Buffer message management
   - Serializes/deserializes protobuf messages
   - Handles PlayerInfo and LikeRequest message types
   - Provides abstraction layer for protobuf operations

4. **app/request_handler.py**: HTTP client for Free Fire API communication
   - Synchronous and asynchronous request capabilities
   - Server-specific endpoint routing
   - Authentication header management

5. **app/utils.py**: Utility functions and configuration management
   - Token loading from JSON configuration
   - Server URL mapping
   - Logging and error handling utilities

### Frontend Components

6. **templates/index.html**: Web interface for API testing
   - Bootstrap-based dark theme UI
   - Form for submitting like requests
   - Real-time feedback and results display

7. **static/style.css**: Custom styling for enhanced user experience
   - Gradient buttons and hover effects
   - Responsive design elements
   - Consistent color scheme

### Configuration

8. **tokens/tokens.json**: Authentication token storage
   - Server-specific JWT tokens
   - Multiple tokens per server for load balancing
   - Structured JSON format for easy management

9. **proto/game_pb2.py**: Generated Protocol Buffer classes
   - PlayerInfo message definition
   - LikeRequest and LikeResponse structures
   - Auto-generated from .proto files

## Data Flow

1. **Request Initiation**: User submits UID and server name via web interface
2. **Token Loading**: System loads appropriate tokens for the specified server
3. **UID Encryption**: Player UID is encrypted using AES for security
4. **Player Info Retrieval**: Initial request to get player information
5. **Like Requests**: Multiple concurrent requests sent using different tokens
6. **Response Processing**: Results aggregated and returned to user

## External Dependencies

### Python Packages
- **Flask**: Web framework for HTTP handling
- **requests/aiohttp**: HTTP client libraries for API communication
- **protobuf**: Google Protocol Buffers for message serialization
- **pycryptodome**: AES encryption implementation
- **asyncio**: Asynchronous programming for concurrent requests

### Free Fire API Integration
- **Authentication**: JWT token-based authentication
- **Endpoints**: Server-specific API endpoints for different regions
- **Protocol**: Binary protobuf communication protocol
- **Rate Limiting**: Handled through multiple token rotation

### Frontend Dependencies
- **Bootstrap**: CSS framework for responsive UI
- **Font Awesome**: Icon library for enhanced UX
- **CDN Resources**: External CSS and JavaScript resources

## Deployment Strategy

### Development Environment
- **Local Development**: Flask development server with debug mode
- **Configuration**: Environment variables for secrets management
- **File Structure**: Modular organization for easy maintenance

### Production Considerations
- **WSGI Server**: Would require Gunicorn or similar for production
- **Security**: Environment-based secret key management
- **Scalability**: Stateless design allows for horizontal scaling
- **Monitoring**: Comprehensive logging system for debugging

### Security Measures
- **Encryption**: AES encryption for sensitive data
- **Token Management**: Secure token storage and rotation
- **Input Validation**: Server-side validation for all inputs
- **Error Handling**: Graceful error handling without exposing internals

The application is designed to be easily deployable on platforms like Replit, with minimal configuration required and a clean separation of concerns for maintainability.