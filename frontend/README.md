```markdown
# React Frontend - Medical RAG Interface

## Overview
Professional medical information interface built with React 18.2.

## Features
- Responsive design for all devices
- Natural language query input
- Real-time search with loading states
- Source attribution and medical disclaimers
- Sample query suggestions

## Deployment
1. Ensure API Gateway URL is updated in index.html
2. Test locally by opening index.html in browser
3. Deploy to AWS Amplify via ZIP upload

## Configuration
Update the API_BASE_URL constant with your API Gateway endpoint:
```javascript
const API_BASE_URL = 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';