```markdown
# SageMaker Notebook - Medical Data Processing

## Overview
This notebook processes MedlinePlus medical articles and generates embeddings for the RAG system.

## Instance Configuration
- **Instance Type**: ml.t3.medium
- **VPC**: Enable VPC access (private subnet)
- **Storage**: 20GB EBS volume

## Processing Pipeline
1. **Data Loading**: Load 4,203 MedlinePlus articles from S3
2. **Text Processing**: Clean and chunk medical content
3. **Embedding Generation**: Use sentence-transformers/all-MiniLM-L6-v2
4. **Database Population**: Store 6,084 records in DynamoDB

## Dependencies
```python
!pip install sentence-transformers boto3 pandas numpy