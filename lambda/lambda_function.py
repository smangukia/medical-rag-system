import json
import boto3
import hashlib
import time
import requests
import os
import re
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

dynamodb = boto3.resource('dynamodb')
embeddings_table = dynamodb.Table('MedicalEmbeddings')
cache_table = dynamodb.Table('QueryCache')

cloudwatch = boto3.client('cloudwatch')

def create_response(status_code, body):
    """Create API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Cache-Control': 'no-cache' if status_code != 200 else 'max-age=300'
        },
        'body': json.dumps(body, cls=DecimalEncoder, ensure_ascii=False)
    }

def lambda_handler(event, context):
    """
    Enhanced Medical RAG System with Prioritized Groq Integration
    """
    
    try:
        if 'queryStringParameters' in event and event['queryStringParameters']:
            query = event['queryStringParameters'].get('q', '')
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            query = body.get('query', '')
        else:
            query = event.get('query', '')
        
        if not query or not query.strip():
            return create_response(400, {
                'error': 'Query parameter required',
                'message': 'Please provide a medical question using ?q=your_question'
            })
        
        query = query.strip()
        print(f"Processing medical query: {query}")
        
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        print(f"Generated query hash: {query_hash}")
        
        cached_result = check_cache(query_hash)
        if cached_result:
            print("Returning cached result")
            return create_response(200, {**cached_result, 'cached': True})
        
        print("No cached result found, proceeding with fresh search")

        search_results = enhanced_medical_rag_search(query, top_k=5)
        
        send_custom_metrics(search_results, query)
        
        response_data = {
            'query': query,
            'generated_response': search_results['generated_response'],
            'sources': search_results['sources'],
            'total_results': len(search_results['sources']),
            'method': 'enhanced_groq_rag',
            'search_strategy': search_results['strategy'],
            'response_type': search_results['response_type'],
            'llm_enhancement': search_results['llm_enhancement'],
            'debug_info': search_results['debug_info'],
            'cached': False,
            'timestamp': int(time.time())
        }

        print(f"About to attempt caching...")
        try:
            cache_success = cache_result(query_hash, query, response_data)
            print(f"Cache result returned: {cache_success}")
            if cache_success:
                print("Result cached successfully")
                response_data['debug_info']['cache_status'] = 'success'
            else:
                print("Caching failed - adding to debug info")
                response_data['debug_info']['cache_status'] = 'failed'
        except Exception as cache_error:
            print(f"Exception in cache_result call: {str(cache_error)}")
            response_data['debug_info']['cache_status'] = 'exception'
            response_data['debug_info']['cache_exception'] = str(cache_error)
        
        return create_response(200, response_data)
        
    except Exception as e:
        print(f"Lambda error: {str(e)}")
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })

def enhanced_medical_rag_search(query, top_k=8):
    """
    Enhanced medical RAG search with PRIORITIZED Groq natural language generation
    """
    
    print(f"Enhanced medical RAG search for: {query}")
    start_time = time.time()
    
    try:
        all_medical_data = load_all_database_content()
        
        if not all_medical_data:
            return create_no_content_response(query)
        
        print(f"Loaded {len(all_medical_data)} medical items from database")

        search_info = extract_smart_search_terms(query.lower())
        
        print(f"Search analysis:")
        print(f" Primary terms: {search_info['primary_terms']}")  
        print(f" Intent: {search_info['intent']}")
        
        scored_results = enhanced_python_scoring(all_medical_data, search_info)

        final_results = filter_and_rank_results(scored_results, search_info, top_k)
        
        print(f"Final results: {len(final_results)} relevant items found")

        if final_results:
            print("Attempting Groq-enhanced natural language generation...")

            groq_response = enhance_with_groq_comprehensive(query, final_results[:4], search_info)
            
            if groq_response:
                print("Using Groq-enhanced natural language response")
                final_response = groq_response
                llm_enhancement = "groq_comprehensive"
                strategy = "groq_natural_language"
            else:
                print("Groq enhancement failed, using structured RAG response")
                final_response = build_structured_medical_response(query, final_results, search_info)
                llm_enhancement = "rag_structured"
                strategy = "structured_medical_fallback"
            
            response_type = "medical_content_found"
        
        else:
            final_response = create_helpful_no_results_response(query, search_info)
            strategy = "no_relevant_medical_content"
            response_type = "helpful_guidance"
            llm_enhancement = "none"
        
        search_time = time.time() - start_time
        
        return {
            'generated_response': clean_response_for_frontend(final_response),
            'sources': final_results,
            'strategy': strategy,
            'response_type': response_type,
            'llm_enhancement': llm_enhancement,
            'debug_info': {
                'total_items_processed': len(all_medical_data),
                'relevant_results_found': len(final_results),
                'search_time': round(search_time, 2),
                'primary_terms': search_info['primary_terms'],
                'intent': search_info['intent'],
                'groq_attempted': GROQ_API_KEY is not None,
                'groq_api_available': bool(GROQ_API_KEY),
                'optimized_system': True
            },
            'search_time': search_time
        }
        
    except Exception as e:
        print(f"Enhanced medical RAG search error: {str(e)}")
        return create_error_response(query, str(e))

def enhance_with_groq_comprehensive(query, top_sources, search_info):
    """ENHANCED Groq integration for natural medical responses"""

    print(f"Groq API Key present: {bool(GROQ_API_KEY)}")
    print(f"Groq API Key length: {len(GROQ_API_KEY) if GROQ_API_KEY else 0}")
    
    if not GROQ_API_KEY:
        print("No Groq API key - using RAG only")
        return None
    
    try:
        print("Starting comprehensive Groq enhancement...")
        
        medical_context = ""
        for i, source in enumerate(top_sources[:4], 1):
            medical_context += f"\n--- Source {i}: {source['title']} ({source['section']}) ---\n"
            content = source['content'][:800] if len(source['content']) > 800 else source['content']
            medical_context += f"{content}\n"
        
        system_prompt = """You are a knowledgeable medical information assistant. Create a CONCISE, focused response (2-3 paragraphs maximum) about medical topics using the provided sources.

INSTRUCTIONS:
1. Write a brief, clear explanation of the medical topic
2. Include the most important information from the sources
3. Keep it under 3 paragraphs
4. Focus on key facts rather than comprehensive details

IMPORTANT: Base everything on the provided medical sources but present it as a natural, flowing explanation."""

        user_prompt = f"""Medical Query: "{query}"

Available Medical Information:
{medical_context}

Please provide a comprehensive, natural response about "{query}" using the medical information above. Make it conversational and well-organized, explaining the medical concepts clearly while including specific details from the sources. Focus on being helpful and educational."""

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,  
            "max_tokens": 800,  
            "top_p": 0.8
        }
        
        print("Sending comprehensive request to Groq...")
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=35)
        
        if response.status_code == 200:
            result = response.json()
            enhanced_response = result['choices'][0]['message']['content'].strip()

            print(f"Groq response length: {len(enhanced_response) if enhanced_response else 0}")
            print(f"Groq response preview: {enhanced_response[:200] if enhanced_response else 'EMPTY'}...")
            
            if enhanced_response and len(enhanced_response) > 300:
                print(f"Groq comprehensive enhancement successful ({len(enhanced_response)} chars)")
 
                enhanced_response += f"\n\n**Medical Sources Referenced:**\n"
                for i, source in enumerate(top_sources[:4], 1):
                    enhanced_response += f"• {source['title']} - {source['section']} (Relevance Score: {source['score']})\n"
                
                enhanced_response += f"\n**Medical Disclaimer:** This information is based on verified medical database sources and is for educational purposes only. Always consult healthcare professionals for personalized medical advice, diagnosis, and treatment decisions."
                
                return enhanced_response
            else:
                print(f"Groq response too short ({len(enhanced_response) if enhanced_response else 0} chars)")
                return None
        else:
            print(f"Groq API failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Groq comprehensive enhancement error: {str(e)}")
        return None

def build_structured_medical_response(query, results, search_info):
    """Build structured medical response as fallback"""
    
    if not results:
        return f"No specific medical information found for '{query}'."
    
    intent = search_info['intent']
    
    headers = {
        'treatment': f"**Medical Treatment Information: {query.title()}**",
        'symptoms': f"**Medical Symptoms Information: {query.title()}**", 
        'causes': f"**Medical Causes Information: {query.title()}**",
        'prevention': f"**Medical Prevention Information: {query.title()}**",
        'diagnosis': f"**Medical Diagnostic Information: {query.title()}**",
        'general': f"**Medical Information: {query.title()}**"
    }
    
    response_parts = [headers.get(intent, headers['general'])]
    response_parts.append(f"\n\n**Based on Medical Database ({len(results)} relevant sources found):**\n")
    
    for i, result in enumerate(results[:5], 1):
        response_parts.append(f"\n**{i}. {result['title']} - {result['section'].title()}**")
        response_parts.append(f"*(Relevance Score: {result['score']})*")
        
        content = result['content']
        if len(content) > 1000:
            content = content[:1000] + "..."
        
        response_parts.append(f"\n{content}")
        
        if i < len(results[:5]):
            response_parts.append("\n" + "─" * 60)
    
    response_parts.append("\n\n**Important Medical Information:**")
    response_parts.append("This information is from verified medical database sources for educational purposes. Always consult healthcare professionals for personalized medical advice, diagnosis, and treatment recommendations.")
    
    return ''.join(response_parts)

def load_all_database_content():
    """Load ALL content from database efficiently"""
    
    all_items = []
    
    try:
        print("Loading all database content...")
        
        response = embeddings_table.scan(
            ProjectionExpression='chunk_id, title, #section, content, #url',
            ExpressionAttributeNames={
                '#url': 'url',
                '#section': 'section'
            }
        )
        
        all_items.extend(response.get('Items', []))
        
        while 'LastEvaluatedKey' in response:
            response = embeddings_table.scan(
                ProjectionExpression='chunk_id, title, #section, content, #url',
                ExpressionAttributeNames={
                    '#url': 'url',
                    '#section': 'section'
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_items.extend(response.get('Items', []))
            
            if len(all_items) > 6000: 
                break
        
        print(f"Loaded {len(all_items)} total medical items")
        return all_items
        
    except Exception as e:
        print(f"Error loading database content: {str(e)}")
        return []

def extract_smart_search_terms(query_lower):
    """Smart extraction of medical search terms"""
    
    intent_patterns = {
        'treatment': ['treatment', 'treat', 'therapy', 'medicine', 'medication', 'manage', 'cure', 'help', 'remedy', 'options', 'drugs'],
        'symptoms': ['symptom', 'symptoms', 'signs', 'what are', 'how does', 'feel like', 'experience', 'manifestation'],
        'causes': ['cause', 'causes', 'why', 'reason', 'from', 'due to', 'triggers', 'etiology'],
        'prevention': ['prevent', 'prevention', 'avoid', 'reduce risk', 'stop', 'protect', 'lifestyle'],
        'diagnosis': ['diagnose', 'diagnosis', 'test', 'detect', 'identify', 'check', 'screen', 'examination']
    }
    
    detected_intent = 'general'
    intent_confidence = 0
    
    for intent, patterns in intent_patterns.items():
        matches = sum(1 for pattern in patterns if pattern in query_lower)
        if matches > intent_confidence:
            detected_intent = intent
            intent_confidence = matches
    
    words = query_lower.split()
    stop_words = {
        'what', 'how', 'why', 'when', 'where', 'who', 'which', 'that', 
        'this', 'these', 'those', 'and', 'or', 'but', 'with', 'for', 
        'from', 'about', 'into', 'through', 'during', 'are', 'is', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'the', 'a', 'an', 'some', 'any', 'all', 'most', 'many', 'few'
    }
    
    primary_terms = []
    secondary_terms = []
    
    for word in words:
        if len(word) > 2 and word not in stop_words:
            if len(word) >= 4:
                primary_terms.append(word)
            else:
                secondary_terms.append(word)
    
    return {
        'primary_terms': primary_terms,
        'secondary_terms': secondary_terms,
        'intent': detected_intent,
        'intent_confidence': intent_confidence,
        'all_terms': primary_terms + secondary_terms,
        'original_query': query_lower
    }

def enhanced_python_scoring(all_items, search_info):
    """Enhanced Python-based relevance scoring"""
    
    scored_items = []
    primary_terms = search_info['primary_terms']
    intent = search_info['intent']
    
    for item in all_items:
        try:
            title = item.get('title', '').lower()
            section = item.get('section', '').lower()
            content = item.get('content', '').lower()
            
            score = 0
            matched_terms = []

            for term in primary_terms:
                term_score = 0
        
                if term in title:
                    if term in ['migraine', 'headache', 'diabetes', 'cancer', 'heart', 'asthma', 'stroke']:
                        term_score += 200 
                    else:
                        term_score += 100
                    matched_terms.append(f"title:{term}")

                if term in section:
                    term_score += 60
                    matched_terms.append(f"section:{term}")
                
                if intent != 'general' and term in primary_terms:
                    intent_section_map = {
                        'treatment': 'treatment',
                        'symptoms': 'symptoms', 
                        'causes': 'causes',
                        'prevention': 'prevention',
                        'diagnosis': 'diagnosis'
                    }
                    
                    if intent in intent_section_map and intent_section_map[intent] in section:
                        if term in ['migraine', 'stroke', 'diabetes', 'asthma', 'cancer', 'heart']:
                            term_score += 300 
                        else:
                            term_score += 150
                
                content_count = content.count(term)
                if content_count > 0:
                    content_score = min(content_count * 15, 75)
                    term_score += content_score
                    if content_count >= 2:
                        matched_terms.append(f"content:{term}({content_count}x)")
                
                score += term_score
            
            intent_bonus = 0
            if intent != 'general':
                intent_keywords = {
                    'treatment': ['treatment', 'therapy', 'management', 'medication', 'drug'],
                    'symptoms': ['symptom', 'sign', 'manifestation', 'presentation'],
                    'causes': ['cause', 'etiology', 'factor', 'trigger'],
                    'prevention': ['prevention', 'prevent', 'avoid', 'lifestyle'],
                    'diagnosis': ['diagnosis', 'test', 'examination', 'screening']
                }
                
                if intent in intent_keywords:
                    for keyword in intent_keywords[intent]:
                        if keyword in section:
                            has_medical_condition = any(med_term in title for med_term in primary_terms 
                                                      if med_term in ['migraine', 'headache', 'diabetes', 'cancer', 'heart', 'asthma'])
                            if has_medical_condition:
                                intent_bonus += 120
                            else:
                                intent_bonus += 80
                            break
                        elif keyword in content:
                            intent_bonus += 30
                            break
            
            score += intent_bonus
            
            content_length = len(content.strip())
            if 100 <= content_length <= 2000:
                score += 25
            elif content_length > 2000:
                score += 15
            
            if score > 0 and (matched_terms or intent_bonus > 0):
                scored_items.append({
                    'item': item,
                    'score': score,
                    'matched_terms': matched_terms,
                    'intent_bonus': intent_bonus,
                    'content_length': content_length
                })
        
        except Exception as e:
            continue
    
    scored_items.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Enhanced scoring results:")
    for i, item in enumerate(scored_items[:5], 1):
        print(f"   {i}. Score: {item['score']:3d} | {item['item'].get('title', '')[:40]}...")
    
    return scored_items

def filter_and_rank_results(scored_items, search_info, top_k):
    """Filter and rank results for final output"""
    
    min_score = 50 if len(search_info['primary_terms']) > 1 else 30
    
    filtered_items = [item for item in scored_items if item['score'] >= min_score]
    
    final_results = []
    for item_data in filtered_items[:top_k]:
        item = item_data['item']
        final_results.append({
            'score': item_data['score'],
            'title': item.get('title', ''),
            'section': item.get('section', ''),
            'content': clean_medical_text(item.get('content', '')),
            'url': item.get('url', ''),
            'chunk_id': item.get('chunk_id', ''),
            'matched_terms': item_data['matched_terms'],
            'relevance_type': determine_relevance_type(search_info, item)
        })
    
    return final_results

def determine_relevance_type(search_info, item):
    """Determine relevance type"""
    title = item.get('title', '').lower()
    section = item.get('section', '').lower()
    
    for term in search_info['primary_terms']:
        if term in title:
            return f"exact_{search_info['intent']}_match" if search_info['intent'] != 'general' else "exact_match"
    
    return "content_relevance"

def clean_medical_text(text):
    """Clean medical text for display"""
    if not text:
        return ""
    
    text = text.replace('\\u2022', '•')
    text = text.replace('\\n', ' ')
    text = text.replace('\\u00c2', '')
    text = text.replace('\\u00a0', ' ')
    text = re.sub(r' +', ' ', text)
    return text.strip()

def clean_response_for_frontend(response_text):
    """Clean response for frontend display"""
    if not response_text:
        return ""
    
    cleaned = response_text.replace('\\u2022', '•')
    cleaned = cleaned.replace('\\u00c2', '')
    cleaned = cleaned.replace('\\u00a0', ' ')
    cleaned = cleaned.replace('\\n', '\n')
    cleaned = cleaned.replace('\\t', '\t')
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()

def create_no_content_response(query):
    """Create response when no content is available"""
    return {
        'generated_response': f"Unable to load medical database content for '{query}'. Please check database connectivity.",
        'sources': [],
        'strategy': 'no_database_content',
        'response_type': 'system_error',
        'llm_enhancement': 'none',
        'debug_info': {'database_load_failed': True},
        'search_time': 0
    }

def create_helpful_no_results_response(query, search_info):
    """Create helpful response when no relevant results found"""
    
    return f"""**Medical Information Request: {query.title()}**

I searched my medical database but couldn't find specific information matching "{query}".

**For Accurate Medical Information:**
• Consult healthcare professionals for personalized advice
• Visit trusted medical resources like MedlinePlus.gov
• Speak with your doctor about specific medical concerns
• Consider consulting medical specialists for specialized conditions

**Database Search:** Processed medical articles but found no relevant matches for your specific query."""

def create_error_response(query, error_msg):
    """Create error response"""
    return {
        'generated_response': f"I encountered an error while searching for medical information about '{query}'. Please try again or consult healthcare professionals.",
        'sources': [],
        'strategy': 'error',
        'response_type': 'error',
        'llm_enhancement': 'none',
        'debug_info': {'error': error_msg},
        'search_time': 0
    }

def check_cache(query_hash):
    """Check query cache with debugging"""
    try:
        print(f"Checking cache for hash: {query_hash}")
        cached_response = cache_table.get_item(Key={'query_hash': query_hash})
        if 'Item' in cached_response:
            print(f"Cache HIT found")
            cached_data = cached_response['Item']['response']
            if 'generated_response' in cached_data:
                cached_data['generated_response'] = clean_response_for_frontend(cached_data['generated_response'])
            return cached_data
        else:
            print(f"Cache MISS - no item found")
    except Exception as e:
        print(f"Cache check FAILED: {str(e)}")
    return None

def cache_result(query_hash, query, response_data):
    """Cache query result with bulletproof debugging and float conversion"""
    print(f"ENTERING cache_result function")
    
    try:
        print(f"Attempting to cache result for hash: {query_hash}")
        
        def convert_floats_to_decimals(obj):
            """Recursively convert floats to Decimals for DynamoDB"""
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimals(item) for item in obj]
            else:
                return obj
        
        converted_response_data = convert_floats_to_decimals(response_data)
        print(f"Float conversion completed")
        
        cache_item = {
            'query_hash': query_hash,
            'query': query,
            'response': converted_response_data,
            'timestamp': int(time.time()),
            'ttl': int(time.time()) + 1800  # 30 minutes
        }
        
        print(f"Cache item prepared")

        print(f"Calling put_item...")
        cache_table.put_item(Item=cache_item)
        
        print(f"Cache WRITE successful for hash: {query_hash}")
        return True
        
    except Exception as e:
        print(f"Cache write FAILED: {str(e)}")
        return False

def send_custom_metrics(search_results, query):
    """Send custom metrics to CloudWatch"""
    try:
        namespace = 'MedicalRAG/System'
        timestamp = time.time()

        metrics = []

        if 'search_time' in search_results:
            metrics.append({
                'MetricName': 'SearchLatency',
                'Value': search_results['search_time'],
                'Unit': 'Seconds',
                'Timestamp': timestamp
            })
        
        if 'sources' in search_results:
            metrics.append({
                'MetricName': 'ResultsFound',
                'Value': len(search_results['sources']),
                'Unit': 'Count',
                'Timestamp': timestamp
            })
            
            if search_results['sources']:
                avg_score = sum(source.get('score', 0) for source in search_results['sources']) / len(search_results['sources'])
                metrics.append({
                    'MetricName': 'AverageRelevanceScore',
                    'Value': avg_score,
                    'Unit': 'None',
                    'Timestamp': timestamp
                })

        debug_info = search_results.get('debug_info', {})
        if 'intent' in debug_info:
            intent = debug_info['intent']
            metrics.append({
                'MetricName': 'QueryByIntent',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp,
                'Dimensions': [
                    {
                        'Name': 'Intent',
                        'Value': intent.title()
                    }
                ]
            })

        if search_results.get('response_type') == 'medical_content_found':
            metrics.append({
                'MetricName': 'SuccessfulQueries',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        
        if 'llm_enhancement' in search_results:
            enhancement = search_results['llm_enhancement']
            metrics.append({
                'MetricName': 'LLMEnhancement',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp,
                'Dimensions': [
                    {
                        'Name': 'EnhancementType',
                        'Value': enhancement
                    }
                ]
            })
        
        if 'total_items_processed' in debug_info:
            metrics.append({
                'MetricName': 'ItemsProcessed',
                'Value': debug_info['total_items_processed'],
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        
        for i in range(0, len(metrics), 20):
            batch = metrics[i:i+20]
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=batch
            )
            print(f"Sent {len(batch)} custom metrics to CloudWatch")
            
    except Exception as e:
        print(f"Failed to send custom metrics: {str(e)}")

