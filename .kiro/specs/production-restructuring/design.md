# Design Document: Production-Ready Restructuring for NovaHR

## Overview

This design transforms the NovaHR HR Assistant from a working prototype with 12+ Python files in the root directory into a production-ready application with proper structure, error handling, configuration management, security, monitoring, and deployment capabilities. The restructuring maintains all existing functionality while introducing enterprise-grade patterns for scalability, maintainability, and operational excellence.

**Key Goals:**
- Zero breaking changes to agent behavior and LangGraph workflows
- Backward compatible with existing MySQL database schema
- Environment-based configuration (dev/staging/prod)
- Comprehensive error handling and structured logging
- Production security practices (secrets management, input validation)
- Docker containerization with health checks
- CI/CD pipeline integration
- Monitoring and observability hooks

## Architecture

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Interface]
        API[REST API - Future]
    end
    
    subgraph "Application Layer"
        Router[Main Router Agent<br/>LangGraph StateGraph]
        
        subgraph "Agent Layer"
            LA[Leave Agent]
            EA[Email Agent]
            QA[Query Agent]
            SA[Schedule Agent]
            GA[General Agent]
            EmA[Employee Agent]
        end
        
        subgraph "Core Services"
            MM[Memory Manager]
            CM[Config Manager]
            LM[Logger Manager]
            EM[Error Handler]
        end
    end
    
    subgraph "Data Layer"
        MySQL[(MySQL DB<br/>Employees/Leaves)]
        ChromaDB[(ChromaDB<br/>Policy Vectors)]
        Cache[Redis Cache<br/>Future]
    end
    
    subgraph "External Services"
        Groq[Groq LLM API]
        Gmail[Gmail SMTP]
        GCal[Google Calendar API]
    end
    
    subgraph "Infrastructure"
        Docker[Docker Container]
        Secrets[Secrets Manager]
        Monitor[Monitoring<br/>Prometheus/Grafana]
    end
    
    CLI --> Router
    API --> Router
    
    Router --> LA
    Router --> EA
    Router --> QA
    Router --> SA
    Router --> GA
    Router --> EmA
    
    LA --> MM
    EA --> MM
    QA --> MM
    SA --> MM
    GA --> MM
    
    LA --> CM
    EA --> CM
    QA --> CM
    
    LA --> LM
    EA --> LM
    QA --> LM
    
    LA --> EM
    EA --> EM
    QA --> EM
    
    LA --> MySQL
    QA --> MySQL
    QA --> ChromaDB
    
    LA --> Groq
    EA --> Groq
    QA --> Groq
    GA --> Groq
    SA --> Groq
    
    EA --> Gmail
    SA --> GCal
    
    Router -.-> Docker
    Docker -.-> Secrets
    Docker -.-> Monitor
```

### Data Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Router
    participant Agent
    participant Service
    participant DB
    participant External
    participant Logger
    participant Monitor
    
    User->>Router: User Input
    Router->>Logger: Log Request
    Router->>Monitor: Increment Request Counter
    
    Router->>Router: Detect Intent
    Router->>Agent: Route to Agent
    
    Agent->>Logger: Log Agent Start
    Agent->>Service: Load Config
    Agent->>Service: Get Memory
    
    Agent->>DB: Query Data
    DB-->>Agent: Return Data
    
    Agent->>External: API Call (with retry)
    External-->>Agent: Response
    
    Agent->>Service: Update Memory
    Agent->>Logger: Log Agent Complete
    Agent->>Monitor: Record Metrics
    
    Agent-->>Router: Return State
    Router-->>User: Response
    Router->>Logger: Log Response
