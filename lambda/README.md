# Lambda Function Deployment

## Overview
The `medical-rag-query` Lambda function serves as the core RAG engine for medical information retrieval.

## Configuration
- **Runtime**: Python 3.9
- **Memory**: 512MB
- **Timeout**: 45 seconds
- **VPC**: Enable VPC access (private subnet)

## Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key_here