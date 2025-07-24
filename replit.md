# Free Fire Token Generator Service

## Project Overview
This is a Flask API service for Free Fire game-like bot functionality with multi-server support and encrypted communication. The service includes automatic token generation for multiple accounts across different regions (India and Pakistan).

## Current Features
- Free Fire game API service with like functionality
- Multi-server support for different regions (IND, PK, BD, BR, SG)
- Encrypted communication using protobuf and AES encryption
- Token management system for different regions

## Recent Changes
- 2025-01-24: Completed REAL JWT token generation system setup
  - Integrated real JWT token generation using complete protobuf + encryption process
  - Implemented scheduled real JWT token generation every 4 hours
  - System runs completely built-in without web dashboard interface
  - Successfully generating authentic JWT tokens for both India and Pakistan regions
  - Using exact same algorithm as provided working JWT generator
  - Tokens are automatically saved to tokens/ind.json and tokens/pk.json

## Project Architecture
- **Main Application**: Flask API in `main.py`
- **Core App**: Base Flask setup in `app/`
- **Token Management**: Region-specific token files in `tokens/`
- **Account Data**: Account credentials in `IND_ACC.json` and `PK_ACC.json`
- **Encryption**: AES encryption and protobuf handling
- **Database**: PostgreSQL with SQLAlchemy

## User Preferences
- Non-technical user requiring simple explanations
- Focus on functionality over technical details
- Prefers automatic solutions over manual interventions
- Wants everything built-in without web dashboard interface
- Prefers automatic background operation

## Account Structure
- **IND_ACC.json**: Contains India region accounts with guest UIDs and passwords
- **PK_ACC.json**: Contains Pakistan region accounts with guest UIDs and passwords
- Both files store encrypted guest account credentials for token generation

## Token Generation Requirements
- Generate REAL JWT tokens for all accounts in IND_ACC.json and PK_ACC.json
- Save India tokens to `tokens/ind.json`
- Save Pakistan tokens to `tokens/pk.json`
- Automatically regenerate every 4 hours
- Use complete JWT generation process with protobuf, AES encryption, and Garena API
- Generate authentic tokens using exact same algorithm as provided working source code

## Development Status
- ✅ Completed: Automatic REAL JWT token generation system fully integrated
- ✅ Completed: Scheduled real JWT token generation every 4 hours
- ✅ Completed: Built-in operation without web interface
- ✅ Completed: Authentic JWT tokens using protobuf + encryption process
- Current: System running automatically in background generating real JWT tokens
- Next: Monitor and maintain automatic operation