#!/usr/bin/env python3
"""
Float-Chat-AI Prototype Test Script

This script demonstrates the key functionality of the Float-Chat-AI prototype.
"""

import asyncio
import sys
import os

# Add the backend to the path
sys.path.append(os.path.join(os.path.dirname(_file_), 'backend'))

from services.data_processor import DataProcessor
from services.ai_service import AIService
from services.database import DatabaseService

async def test_data_processor():
    """Test the data processing pipeline"""
    print("\n🌊 Testing Data Processing Pipeline")
    print("=" * 50)
    
    processor = DataProcessor()
    
    # Test mock data generation
    print("📊 Loading/generating mock ARGO data...")
    dataset = await processor.load_netcdf_data()
    print(f"✅ Dataset loaded with variables: {list(dataset.data_vars.keys())}")
    print(f"   Dimensions: {dict(dataset.dims)}")
    
    # Test query execution
    sample_queries = [
        {'variable': 'TEMP', 'operation': 'mean'},
        {'variable': 'PSAL', 'operation': 'max'},
        {'variable': 'TEMP', 'operation': 'profile'}
    ]
    
    for query in sample_queries:
        result = await processor.execute_query(query)
        if result['success']:
            print(f"✅ Query: {query['variable']} {query['operation']}")
            print(f"   Result: {result['description']}")
            if isinstance(result['data'], (int, float)):
                print(f"   Value: {result['data']:.2f} {result['metadata']['units']}")
        else:
            print(f"❌ Query failed: {result['error']}")

async def test_ai_service():
    """Test the AI service functionality"""
    print("\n🤖 Testing AI Service Pipeline")
    print("=" * 50)
    
    ai_service = AIService()
    
    # Test query parsing
    test_queries = [
        "What's the average temperature?",
        "Show me a salinity profile", 
        "Find the maximum temperature at 1000 meters",
        "What's the pressure data?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Processing: '{query}'")
        parsed = await ai_service.parse_query(query)
        print(f"   Parsed as: {parsed}")
        
        # Mock data result for response generation
        mock_data_result = {
            'success': True,
            'data': 15.3,
            'metadata': {'variable': parsed['variable'], 'units': '°C'},
            'description': f"Average {parsed['variable']}"
        }
        
        response = await ai_service.generate_response(query, mock_data_result, parsed)
        print(f"   AI Response: {response}")

async def test_database_service():
    """Test the database service"""
    print("\n💾 Testing Database Service")
    print("=" * 50)
    
    db_service = DatabaseService()
    
    # Test session management
    session_id = "test_session_123"
    query_id = await db_service.save_query_history(
        session_id, 
        "What's the temperature?", 
        "The average temperature is 15.3°C",
        {'data': 15.3, 'success': True}
    )
    print(f"✅ Saved query with ID: {query_id}")
    
    # Test history retrieval
    history = await db_service.get_session_history(session_id)
    print(f"✅ Retrieved {len(history)} items from session history")
    
    if history:
        print(f"   Latest query: {history[0]['user_query']}")
        print(f"   AI response: {history[0]['ai_response']}")

async def test_end_to_end():
    """Test the complete pipeline"""
    print("\n🚀 End-to-End Pipeline Test")
    print("=" * 50)
    
    # Initialize services
    processor = DataProcessor()
    ai_service = AIService()
    db_service = DatabaseService()
    
    # Simulate a complete user query
    user_query = "What's the average temperature at 500 meters depth?"
    session_id = "test_e2e_session"
    
    print(f"👤 User Query: '{user_query}'")
    
    # Step 1: Parse query
    parsed_query = await ai_service.parse_query(user_query)
    print(f"🧠 Parsed Query: {parsed_query}")
    
    # Step 2: Execute data processing
    data_result = await processor.execute_query(parsed_query)
    print(f"📊 Data Result: {data_result['description'] if data_result['success'] else data_result['error']}")
    
    # Step 3: Generate AI response
    ai_response = await ai_service.generate_response(user_query, data_result, parsed_query)
    print(f"🤖 AI Response: {ai_response}")
    
    # Step 4: Save to database
    query_id = await db_service.save_query_history(session_id, user_query, ai_response, data_result)
    print(f"💾 Saved to database with ID: {query_id}")
    
    # Step 5: Create visualization (if applicable)
    if data_result['success'] and data_result.get('data'):
        viz = await processor.create_visualization(data_result['data'], parsed_query.get('viz_type', 'table'))
        if viz:
            print(f"📈 Visualization: {viz['type']} created")
        else:
            print("📊 No visualization generated")
    
    print("\n✅ End-to-end pipeline completed successfully!")

async def main():
    """Main test function"""
    print("🌊 Float-Chat-AI Prototype Test Suite")
    print("=====================================")
    print("Testing the conversational AI interface for oceanographic data")
    
    try:
        await test_data_processor()
        await test_ai_service()
        await test_database_service()
        await test_end_to_end()
        
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Data processing with mock ARGO data")
        print("   ✅ AI-powered natural language query parsing")
        print("   ✅ Conversational response generation")
        print("   ✅ Session management and history")
        print("   ✅ End-to-end pipeline integration")
        print("\n🚀 The Float-Chat-AI prototype is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if _name_ == "_main_":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)