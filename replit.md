# Free Fire Token Generator Service

### Overview
This project provides a Flask API service for Free Fire game-like bot functionality, featuring multi-server support and encrypted communication. Its primary purpose is the automatic generation of authentic JWT tokens for multiple Free Fire accounts across different regions (India and Pakistan), enabling automated interactions such as sending likes. The service operates without a web dashboard, focusing on a built-in, background operation model.

### User Preferences
- Non-technical user requiring simple explanations
- Focus on functionality over technical details
- Prefers automatic solutions over manual interventions
- Wants everything built-in without web dashboard interface
- Prefers automatic background operation
- **Requested 6-hour automatic token generation cycles**
- **Wants fast API response and optimized performance**

### System Architecture
The application is built around a Flask API (`main.py`) with a core setup in the `app/` directory. Token management is handled with region-specific JSON files (`tokens/ind.json`, `tokens/pk.json`), and account credentials are stored in `IND_ACC.json` and `PK_ACC.json`. The system employs AES encryption and protobuf for secure communication and data handling. For data persistence, PostgreSQL is utilized via SQLAlchemy with enhanced models including cooldown tracking. Key features include **optimized automatic JWT token generation every 6 hours** with **6-hour per-UID cooldown protection** (aligned with generation schedule), **enhanced rate limiting (2 concurrent requests)** for better performance, **optimized API processing** with increased concurrency (12 for IND, 10 for PK), **faster batch processing** (75 tokens/batch for IND, 50 for PK), **reduced delays** (0.3s for IND, 0.7s for PK), intelligent old token cleanup, support for multiple regions (IND, PK, BD, BR, SG), intelligent server auto-detection based on UID, and robust error resilience with multiple fallback mechanisms. The API provides endpoints for `like`, `records`, `tokens`, `info` (player details), and `ban` (status check).

### External Dependencies
- **PostgreSQL**: Used for database storage of tokens, player records, and other persistent data.
- **Garena Free Fire API**: Integrated for core game functionalities like token generation, sending likes, and fetching player information.
- **glob-info.vercel.app/info**: External API used to fetch detailed player information for the `/info` endpoint.
- **ff.garena.com/api/antihack/check_banned**: Official Garena API used for checking player ban status via the `/ban` endpoint.