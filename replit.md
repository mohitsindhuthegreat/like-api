# Replit.md

## Overview

This is a Flask-based web service that automates "liking" profiles in the Free Fire mobile game across different regional servers. The application uses Protocol Buffers for data serialization, AES encryption for message security, and makes asynchronous HTTP requests to game servers to simulate multiple users liking a target profile.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Updates (July 24, 2025)

### Credentials Integration Status
- Successfully integrated PK server guest account credentials from user's files
- Updated IND server tokens from provided credentials.json file
- Created new authentication system supporting both JWT tokens and guest credentials
- Added comprehensive API endpoints: /like, /api/servers, /api/status
- Built professional web interface with real-time testing capabilities

### Current Implementation Status
- **API Structure**: Fully functional with proper error handling and demo mode
- **Authentication**: Guest account credentials format requires Free Fire API authentication to generate valid JWT tokens
- **Server Support**: All servers (IND, BR, US, SAC, NA, PK, MENA, THAI) configured with proper routing
- **Demo Mode**: Working demonstration of expected functionality when tokens are valid

### Technical Notes
- Guest account credentials (UID + password) need conversion to JWT tokens via Free Fire authentication API
- Current JWT tokens from IND server may be expired (returning 401/503 errors)
- System architecture supports both authentication methods seamlessly
- All code components (encryption, protobuf, request handling) are working correctly

## System Architecture

The application follows a modular Flask architecture with the following key components:

### Backend Framework
- **Flask**: Simple web framework handling HTTP requests
- **Problem addressed**: Need for a lightweight web service to handle profile liking requests
- **Rationale**: Flask provides simplicity and ease of deployment on Vercel

### Request Processing
- **Synchronous Flask routes** with **asynchronous internal processing**
- **Problem addressed**: Need to handle multiple concurrent requests to game servers efficiently
- **Solution**: Uses asyncio for concurrent HTTP requests while maintaining simple Flask interface

### Data Serialization
- **Protocol Buffers (protobuf)**: Binary serialization format
- **Problem addressed**: Need to communicate with game servers using their expected data format
- **Rationale**: Game servers expect protobuf-encoded messages for authentication and requests

## Key Components

### 1. Main Application (`main.py`)
- Single endpoint `/like` that accepts UID and server_name parameters
- Orchestrates the entire liking process
- Handles before/after like count comparison

### 2. Encryption Module (`app/encryption.py`)
- **AES-256-CBC encryption** with hardcoded key and IV
- Encrypts protobuf messages before sending to game servers
- **Security consideration**: Uses static encryption keys (potential security risk)

### 3. Protocol Buffer Handler (`app/protobuf_handler.py`)
- Creates protobuf messages for different operations:
  - Like requests (`like_pb2`)
  - UID generation (`uid_generator_pb2`) 
  - Response parsing (`like_count_pb2`)

### 4. Request Handler (`app/request_handler.py`)
- **Asynchronous HTTP client** using aiohttp
- Sends 100 concurrent requests using token rotation
- **Problem addressed**: Need to simulate multiple users liking a profile quickly
- **Solution**: Concurrent requests with different authentication tokens

### 5. Utilities (`app/utils.py`)
- Token loading based on server regions
- **Regional mapping**:
  - IND: India server
  - BR/US/SAC/NA: Americas servers  
  - Others: Bangladesh/default servers

## Data Flow

1. **Request Reception**: Flask receives GET request with UID and server_name
2. **Initial State Check**: Retrieves current like count for the target profile
3. **Token Loading**: Loads appropriate authentication tokens for the server region
4. **Parallel Liking**: Sends 100 concurrent like requests using different tokens
5. **Final State Check**: Retrieves updated like count
6. **Response**: Returns before/after like counts

## External Dependencies

### Game Server Integration
- **Multiple regional endpoints**:
  - India: `client.ind.freefiremobile.com`
  - Americas: `client.us.freefiremobile.com` 
  - Others: `clientbp.ggblueshark.com`

### Authentication System
- **JWT tokens** stored in JSON files per region
- **Token rotation**: Cycles through available tokens for load distribution
- **Problem addressed**: Need to authenticate as different users
- **Solution**: Pre-generated authentication tokens for each region

### Protocol Requirements
- **Custom headers**: Mimics Android Dalvik user agent
- **Game version**: Targets "OB49" release version
- **Unity engine**: Specifies Unity 2018.4.11f1 compatibility

## Deployment Strategy

### Vercel Deployment
- **Serverless function** deployment using `@vercel/python`
- **Configuration**: Single route catching all requests and directing to main.py
- **Rationale**: Cost-effective serverless deployment with automatic scaling

### Dependencies Management
- **Requirements**: Flask with async support, HTTP clients (requests/aiohttp), cryptography, protobuf
- **Problem addressed**: Need for both sync and async HTTP capabilities
- **Solution**: Hybrid approach using both requests and aiohttp libraries

### File Structure
- **Token storage**: Separate JSON files for each regional server
- **Protobuf definitions**: Compiled Python modules from .proto files
- **Modular organization**: Separated concerns into logical modules

## Security Considerations

### Encryption
- **Static AES keys**: Hardcoded encryption key and IV (security risk)
- **Protocol compliance**: Matches expected game server encryption

### Authentication
- **Token management**: Stores authentication tokens in plaintext JSON
- **Regional isolation**: Tokens are region-specific to prevent cross-server issues

### Rate Limiting
- **Concurrent requests**: Limited to 100 simultaneous requests
- **Token rotation**: Distributes load across multiple authentication tokens