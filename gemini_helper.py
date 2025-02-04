import google.generativeai as genai
from typing import List, Dict, Union
import base64
from PIL import Image
import io
import json
from config import GEMINI_API_KEY

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def preprocess_query(query: str) -> str:
    """
    Preprocesses user query to focus on financial analysis aspects.
    """
    try:
        # Initialize model for preprocessing
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        preprocess_prompt = """
        You are an expert in financial analysis query processing. Your job is to:
        
        1. Determine the core financial analysis request from the user's question
        2. Extract key elements like:
           - Stock symbols or company names
           - Time periods
           - Type of analysis requested (price analysis, trading volume, etc.)
           - Specific metrics mentioned
        
        Return only the essential part of the query that's relevant for financial analysis.
        If the query isn't finance-related, return the original query.
        
        Format the response as JSON with:
        {
            "processed_query": "refined question",
            "analysis_type": "price|volume|general|news",
            "entities": ["AAPL", "TSLA", etc],
            "time_period": "specified time or null"
        }
        
        USER QUERY: {query}
        """
        
        response = model.generate_content(preprocess_prompt.format(query=query))
        result = json.loads(response.text)
        return result
        
    except Exception as e:
        print(f"Preprocessing error: {str(e)}")
        return {"processed_query": query, "analysis_type": "general", "entities": [], "time_period": None}

def get_gemini_response(chunks: List[str], prompt: str, response_format: str = "text") -> Union[str, Dict]:
    """
    Enhanced Gemini response function with more detailed prompts.
    """
    try:
        # Preprocess the query
        processed = preprocess_query(prompt)
        
        # Initialize model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Combine chunks with reasonable length limit
        context = "\n\n".join(chunks)[:30000]
        
        # Enhanced format-specific prompts
        if response_format == "table":
            full_prompt = f"""
            You are a financial analysis expert. Analyze the following content and question:
            
            Context: {context}
            
            Query: {processed['processed_query']}
            Analysis Type: {processed['analysis_type']}
            Entities: {', '.join(processed['entities']) if processed['entities'] else 'None specified'}
            Time Period: {processed['time_period'] if processed['time_period'] else 'Not specified'}
            
            Instructions:
            1. Extract all relevant trading activities and financial data
            2. Format the response as a markdown table with these columns:
               - Date/Time
               - Trader/Entity
               - Action (Buy/Sell)
               - Stock/Asset
               - Price
               - Quantity (if available)
               - Reason/Notes
            3. Include a summary row if multiple trades are found
            4. Sort by date/time if available
            
            Use | for columns and include a header row.
            """
        elif response_format == "image":
            full_prompt = f"""
            Context: {context}
            
            Create a visual representation of the financial data:
            Query: {processed['processed_query']}
            Type: {processed['analysis_type']}
            
            Generate a detailed description for a chart or visualization that shows:
            1. Key trends and patterns
            2. Price movements or volume changes
            3. Important events or milestones
            4. Color scheme: Use green for positive, red for negative changes
            
            Include specific details about style, layout, and data representation.
            """
        else:
            full_prompt = f"""
            You are a financial analysis expert. Analyze this content:
            
            Context: {context}
            
            Query: {processed['processed_query']}
            Analysis Type: {processed['analysis_type']}
            Entities: {', '.join(processed['entities']) if processed['entities'] else 'None specified'}
            
            Provide a detailed analysis that includes:
            1. Key findings and insights
            2. Relevant trading activities
            3. Market impact and implications
            4. Supporting data points
            5. Any caveats or limitations
            
            Format the response clearly with sections and bullet points where appropriate.
            """
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        if response_format == "image":
            # For image generation, we need to parse the response and generate the image
            image_prompt = response.text
            image_model = genai.GenerativeModel('gemini-1.5-flash')
            image_response = image_model.generate_content([
                "Generate an image based on this description: " + image_prompt
            ])
            
            # Convert the generated image data to a format that can be displayed
            if hasattr(image_response, 'image') and image_response.image:
                # Convert image data to base64
                image_data = base64.b64encode(image_response.image).decode('utf-8')
                return {
                    'type': 'image',
                    'data': image_data,
                    'description': image_prompt
                }
            else:
                return {
                    'type': 'error',
                    'message': 'Image generation failed'
                }
        
        return response.text

    except Exception as e:
        return f"Error generating response: {str(e)}"

def format_table_response(text: str) -> str:
    """
    Ensures table response is properly formatted in Markdown with consistent spacing.
    """
    if not text:
        return "No trading activities found in the content."
        
    # Add title if not present
    if not text.startswith("#"):
        text = "### Stock Trading Activities\n\n" + text
        
    # Clean up the table formatting
    lines = text.split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        if '|' in line:
            if not in_table:
                in_table = True
            # Clean up cell spacing
            cells = [cell.strip() for cell in line.split('|')]
            table_lines.append('| ' + ' | '.join(cells[1:-1]) + ' |')
            
            # Add separator line if it's the header
            if len(table_lines) == 1:
                separator = '|' + '|'.join(['-' * (len(cell) + 2) for cell in cells[1:-1]]) + '|'
                table_lines.append(separator)
        else:
            if in_table:
                table_lines.append('')  # Add spacing after table
                in_table = False
            table_lines.append(line)
            
    return '\n'.join(table_lines)


def process_image_response(response: Dict) -> str:
    """
    Processes image response into markdown format
    """
    if response['type'] == 'image':
        return f"""
![Generated Image]({response['data']})

Description: {response['description']}
"""
    else:
        return f"Error: {response['message']}" 