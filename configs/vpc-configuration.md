# VPC Configuration Guide

## Network Architecture Overview
The Medical RAG System uses a secure VPC architecture with public/private subnet isolation.

## VPC Configuration

### 1. VPC Creation
- **Name**: medical-rag-vpc
- **CIDR Block**: 10.0.0.0/16
- **DNS Hostnames**: Enabled
- **DNS Resolution**: Enabled

### 2. Subnet Configuration

#### Public Subnet
- **Name**: medical-rag-public-subnet
- **CIDR Block**: 10.0.1.0/24
- **Availability Zone**: us-east-1a
- **Auto-assign Public IP**: Enabled

#### Private Subnet
- **Name**: medical-rag-private-subnet
- **CIDR Block**: 10.0.2.0/24
- **Availability Zone**: us-east-1a
- **Auto-assign Public IP**: Disabled

### 3. Internet Gateway
- **Name**: medical-rag-igw
- **Attachment**: Attached to medical-rag-vpc

### 4. NAT Gateway
- **Name**: medical-rag-nat
- **Subnet**: Public subnet (10.0.1.0/24)
- **Elastic IP**: Allocated and associated

### 5. Route Tables

#### Public Route Table
- **Name**: medical-rag-public-rt
- **Routes**:
  - 10.0.0.0/16 → Local
  - 0.0.0.0/0 → Internet Gateway
- **Associated Subnets**: Public subnet

#### Private Route Table
- **Name**: medical-rag-private-rt
- **Routes**:
  - 10.0.0.0/16 → Local
  - 0.0.0.0/0 → NAT Gateway
- **Associated Subnets**: Private subnet

### 6. Security Groups

#### Lambda Security Group
- **Name**: medical-rag-lambda-sg
- **Inbound Rules**: None
- **Outbound Rules**:
  - HTTPS (443) → 0.0.0.0/0
  - DynamoDB → AWS service endpoints
  - S3 → AWS service endpoints

#### Default VPC Security Group
- **Inbound Rules**: All traffic from same security group
- **Outbound Rules**: All traffic to 0.0.0.0/0

### 7. VPC Endpoints

#### SageMaker API VPC Endpoint
- **Service**: com.amazonaws.us-east-1.sagemaker.api
- **Type**: Interface
- **Subnets**: Private subnet
- **Security Groups**: Default VPC security group
- **Policy**: Full access

#### SageMaker Runtime VPC Endpoint
- **Service**: com.amazonaws.us-east-1.sagemaker.runtime
- **Type**: Interface
- **Subnets**: Private subnet
- **Security Groups**: Default VPC security group
- **Policy**: Full access

## Component Placement

### Public Subnet Components
- AWS Amplify (external reference)
- API Gateway (AWS managed)
- NAT Gateway
- Internet Gateway

### Private Subnet Components
- Lambda Function (medical-rag-query)
- SageMaker Notebook Instance
- VPC Endpoints (SageMaker API/Runtime)

## Network Traffic Flow

### Inbound Traffic
1. User → Internet → Internet Gateway
2. Internet Gateway → Public Subnet → API Gateway
3. API Gateway → Private Subnet → Lambda Function

### Outbound Traffic
1. Lambda Function → NAT Gateway (for external APIs)
2. Lambda Function → VPC Endpoints (for AWS services)
3. SageMaker → VPC Endpoints (for secure API access)

## Security Benefits
- **Isolation**: Backend components isolated in private subnet
- **Controlled Access**: No direct internet access to sensitive components
- **Secure Communication**: VPC endpoints for AWS service access
- **Network Segmentation**: Clear separation of public/private resources