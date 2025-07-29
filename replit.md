# Medical AI Assistant

## Overview

The Medical AI Assistant is a sophisticated FastAPI-based application that analyzes prescriptions for allergy conflicts and drug cross-reactivity. It combines traditional database-driven allergy checking with AI-powered analysis using LangGraph workflows and the Groq API for fast LLM inference. The system helps healthcare providers identify potential adverse reactions before prescribing medications.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modern web architecture with clear separation of concerns:

### Backend Architecture
- **FastAPI Framework**: RESTful API server providing endpoints for prescription analysis
- **SQLAlchemy ORM**: Database abstraction layer with declarative models
- **LangGraph Workflow**: State-based AI agent for complex medical reasoning
- **Modular Design**: Separate modules for database operations, AI analysis, and allergy checking

### Frontend Architecture
- **Static Web Interface**: Bootstrap-based responsive UI served via FastAPI static files
- **Vanilla JavaScript**: Client-side logic for form handling and API communication
- **Real-time Analysis**: Asynchronous prescription checking with visual feedback

### AI Integration
- **Groq API Client**: Fast LLM inference using Llama-3.1-70b-versatile model
- **Multi-step Analysis**: Structured workflow for comprehensive medical evaluation
- **Cross-reactivity Detection**: Advanced pattern recognition for drug interactions

## Key Components

### Database Layer (`models.py`, `database.py`)
- **Patient Management**: Stores patient demographics and medical history
- **Drug Catalog**: Comprehensive medication database with ingredients and classifications
- **Allergy Tracking**: Patient-specific allergy records with severity levels
- **Cross-reactivity Mapping**: Relationships between allergens and drug families

### AI Agent (`ai_agent.py`)
- **LangGraph Workflow**: Multi-node state machine for medical analysis
- **Progressive Analysis**: Step-by-step evaluation from direct allergies to complex interactions
- **Structured Output**: Consistent JSON responses with confidence levels and recommendations

### Allergy Checker (`allergy_checker.py`)
- **Direct Matching**: Database-driven exact allergy conflict detection
- **Rule-based Logic**: Traditional pharmaceutical cross-reactivity rules
- **Integration Point**: Bridges database queries with AI analysis

### API Layer (`main.py`)
- **RESTful Endpoints**: Standardized API for prescription analysis
- **Request Validation**: Pydantic schemas ensure data integrity
- **Error Handling**: Graceful failure modes with detailed error messages

## Data Flow

1. **Input Processing**: Patient name and medication list received via API
2. **Patient Lookup**: Database query to retrieve patient allergies and history
3. **Direct Allergy Check**: Traditional database matching for known allergens
4. **AI Analysis Workflow**:
   - Initialize analysis state
   - Analyze direct allergies
   - Evaluate cross-reactivity patterns
   - Generate recommendations
   - Finalize structured output
5. **Response Compilation**: Combine database results with AI insights
6. **Frontend Display**: Visual presentation of safety assessment and recommendations

## External Dependencies

### AI Services
- **Groq API**: Primary LLM provider for medical reasoning (Llama-3.1-70b-versatile)
- **LangChain/LangGraph**: Workflow orchestration and prompt management

### Database
- **SQLAlchemy**: ORM and database abstraction
- **SQLite**: Default development database (configurable for PostgreSQL)

### Web Framework
- **FastAPI**: Modern async web framework
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and serialization

### Frontend Libraries
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icon library for enhanced UX

## Deployment Strategy

### Development Environment
- **SQLite Database**: Local file-based storage for rapid development
- **Environment Variables**: Configurable API keys and database URLs
- **Sample Data**: Automated population of test data for demonstration

### Production Considerations
- **PostgreSQL Support**: Environment-based database URL configuration
- **API Key Management**: Secure handling of Groq API credentials
- **Connection Pooling**: Database connection optimization for high load
- **Static File Serving**: Efficient frontend asset delivery

### Configuration Management
- **Environment Variables**: 
  - `DATABASE_URL`: Database connection string
  - `GROQ_API_KEY`: AI service authentication
- **Flexible Database Support**: Automatic PostgreSQL URL format handling
- **Development Defaults**: Sensible fallbacks for local development

The system is designed for easy deployment on cloud platforms with minimal configuration changes, supporting both development and production environments through environment variable configuration.