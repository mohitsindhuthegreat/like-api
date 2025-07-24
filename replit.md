# Free Fire Token Generator Service

## Project Overview
This is a Flask API service for Free Fire game-like bot functionality with multi-server support and encrypted communication. The service includes automatic token generation for multiple accounts across different regions (India and Pakistan).

## Current Features
- Free Fire game API service with like functionality
- Multi-server support for different regions (IND, PK, BD, BR, SG)
- Encrypted communication using protobuf and AES encryption
- Token management system for different regions

## Recent Changes
- 2025-01-24: Setting up automatic token generation system
  - Analyzing provided token generation source code
  - Planning integration with existing account files (IND_ACC.json, PK_ACC.json)
  - Will implement scheduled token generation every 4 hours

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

## Account Structure
- **IND_ACC.json**: Contains India region accounts with guest UIDs and passwords
- **PK_ACC.json**: Contains Pakistan region accounts with guest UIDs and passwords
- Both files store encrypted guest account credentials for token generation

## Token Generation Requirements
- Generate tokens for all accounts in IND_ACC.json and PK_ACC.json
- Save India tokens to `ind.json`
- Save Pakistan tokens to `pk.json`
- Automatically regenerate every 4 hours
- Use the provided token generation algorithm from attached source code

## Development Status
- Current: Integrating token generation system
- Next: Implement scheduled automatic token generation
- Future: Web interface for monitoring token generation status