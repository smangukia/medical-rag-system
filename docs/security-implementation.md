# Security Implementation Guide

## Multi-Layer Security Architecture

The Medical Information RAG System implements comprehensive security measures across all architectural layers following AWS Well-Architected Framework principles.

## 1. Network Security

### VPC Isolation
- **Private VPC**: Dedicated virtual private cloud (medical-rag-vpc)
- **Subnet Segmentation**: Public/private subnet separation
- **Network ACLs**: Default subnet-level traffic filtering
- **Security Groups**: Instance-level firewall rules

### Traffic Control
- **Inbound Restrictions**: Only necessary ports (HTTPS:443) exposed
- **Outbound Filtering**: Restricted to required external services
- **VPC Endpoints**: Secure AWS service communication without internet
- **NAT Gateway**: Controlled outbound internet access for private resources

## 2. Identity and Access Management (IAM)

### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/MedicalEmbeddings",
        "arn:aws:dynamodb:us-east-1:*:table/QueryCache",
        "arn:aws:dynamodb:us-east-1:*:table/DocumentMetadata"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNetworkInterface",
        "ec2:DeleteNetworkInterface",
        "ec2:DescribeNetworkInterfaces"
      ],
      "Resource": "*"
    }
  ]
}