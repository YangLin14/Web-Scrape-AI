"""
HTML Template for Federal Contract Analysis Reports

This file contains the HTML template that will be used by the Gemini AI model
to format its analysis of federal contracts. The template provides a consistent
structure and styling for all generated reports.
"""

def get_html_template():
    """
    Returns the HTML template for federal contract analysis reports.
    
    This template includes placeholders that will be replaced with actual data:
    - {{CONTRACT_ID}} - The contract ID
    - {{COMPANY_NAME}} - The company name
    - {{CONTRACT_AMOUNT}} - The formatted contract amount
    - {{AWARD_DATE}} - The contract award date
    - {{AGENCY_NAME}} - The awarding agency
    - {{CONTRACT_DESCRIPTION}} - The contract description
    - {{PRICE_CHANGE_PCT}} - The stock price percentage change
    - {{VOLUME_CHANGE_PCT}} - The trading volume percentage change
    - {{PRICE_CHANGE_CLASS}} - CSS class for price change (positive/negative/neutral)
    - {{VOLUME_CHANGE_CLASS}} - CSS class for volume change (positive/negative/neutral)
    - {{MARKET_IMPACT_ANALYSIS}} - The market impact analysis text
    - {{SECTOR_TRENDS}} - The sector trends analysis
    - {{PREDICTIVE_INDICATORS}} - The predictive indicators analysis
    - {{ACTIONABLE_INSIGHTS}} - The actionable trading insights
    - {{TRADING_OPPORTUNITIES}} - The trading opportunities list
    - {{RISK_FACTORS}} - The risk factors list
    - {{AI_RECOMMENDATION}} - The AI-generated recommendation
    - {{GENERATION_DATE}} - The date and time the analysis was generated
    
    Returns:
        str: HTML template with placeholders
    """
    
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Federal Contract Analysis: {{CONTRACT_ID}} - {{COMPANY_NAME}}</title>
  <style>
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
      background-color: #f8f9fa;
      margin: 0;
      padding: 0;
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    
    .header {
      background-color: #0056b3;
      color: white;
      padding: 20px;
      border-radius: 5px 5px 0 0;
      margin-bottom: 20px;
    }
    
    .header h1 {
      margin: 0;
      font-size: 24px;
    }
    
    .header h2 {
      margin: 5px 0 0;
      font-size: 18px;
      font-weight: normal;
      opacity: 0.9;
    }
    
    .card {
      background-color: white;
      border-radius: 5px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      margin-bottom: 20px;
      overflow: hidden;
    }
    
    .card-header {
      background-color: #f8f9fa;
      padding: 15px 20px;
      border-bottom: 1px solid rgba(0,0,0,0.125);
      font-weight: bold;
      color: #0056b3;
    }
    
    .card-body {
      padding: 20px;
    }
    
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    
    @media (max-width: 768px) {
      .grid-2 {
        grid-template-columns: 1fr;
      }
    }
    
    .positive {
      color: #28a745;
    }
    
    .negative {
      color: #dc3545;
    }
    
    .neutral {
      color: #6c757d;
    }
    
    .metric-box {
      background-color: #f8f9fa;
      padding: 15px;
      border-radius: 5px;
      text-align: center;
    }
    
    .metric-value {
      font-size: 24px;
      font-weight: bold;
      margin: 10px 0;
    }
    
    .metric-label {
      color: #6c757d;
      font-size: 14px;
    }
    
    .chart-placeholder {
      background-color: #f8f9fa;
      height: 300px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 5px;
      color: #6c757d;
      font-style: italic;
    }
    
    .section-title {
      color: #0056b3;
      border-bottom: 2px solid #f8f9fa;
      padding-bottom: 10px;
      margin-bottom: 15px;
    }
    
    ul {
      padding-left: 20px;
    }
    
    li {
      margin-bottom: 10px;
    }
    
    .insight-box {
      border-left: 4px solid #0056b3;
      padding: 15px;
      background-color: rgba(0, 86, 179, 0.1);
      margin: 20px 0;
      border-radius: 0 5px 5px 0;
    }
    
    .footer {
      text-align: center;
      margin-top: 30px;
      padding: 20px;
      color: #6c757d;
      font-size: 14px;
    }
    
    .opportunity-box {
      border: 1px solid #28a745;
      background-color: rgba(40, 167, 69, 0.1);
      border-radius: 5px;
      padding: 15px;
    }
    
    .risk-box {
      border: 1px solid #dc3545;
      background-color: rgba(220, 53, 69, 0.1);
      border-radius: 5px;
      padding: 15px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Federal Contract Analysis</h1>
      <h2>{{CONTRACT_ID}} - {{COMPANY_NAME}}</h2>
    </div>
    
    <!-- Contract Summary -->
    <div class="card">
      <div class="card-header">Contract Summary</div>
      <div class="card-body">
        <div class="grid-2">
          <div>
            <p><strong>Company:</strong> {{COMPANY_NAME}}</p>
            <p><strong>Contract Amount:</strong> {{CONTRACT_AMOUNT}}</p>
            <p><strong>Award Date:</strong> {{AWARD_DATE}}</p>
          </div>
          <div>
            <p><strong>Awarding Agency:</strong> {{AGENCY_NAME}}</p>
            <p><strong>Description:</strong> {{CONTRACT_DESCRIPTION}}</p>
          </div>
        </div>
        
        <div class="grid-2" style="margin-top: 20px;">
          <div class="metric-box">
            <div class="metric-label">Stock Price Impact</div>
            <div class="metric-value {{PRICE_CHANGE_CLASS}}">{{PRICE_CHANGE_PCT}}%</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Trading Volume Impact</div>
            <div class="metric-value {{VOLUME_CHANGE_CLASS}}">{{VOLUME_CHANGE_PCT}}%</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Charts Section -->
    <div class="grid-2">
      <div class="card">
        <div class="card-header">Stock Price Trend</div>
        <div class="card-body">
          <div class="chart-placeholder">
            Stock price chart visualization
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">Trading Volume</div>
        <div class="card-body">
          <div class="chart-placeholder">
            Trading volume chart visualization
          </div>
        </div>
      </div>
    </div>
    
    <!-- Market Impact Analysis -->
    <div class="card">
      <div class="card-header">Market Impact Analysis</div>
      <div class="card-body">
        <p>{{MARKET_IMPACT_ANALYSIS}}</p>
        
        <h3 class="section-title">Sector Trends</h3>
        <ul>
          {{SECTOR_TRENDS}}
        </ul>
        
        <h3 class="section-title">Predictive Indicators</h3>
        <p>{{PREDICTIVE_INDICATORS}}</p>
      </div>
    </div>
    
    <!-- Trading Insights -->
    <div class="card">
      <div class="card-header">Trading Insights</div>
      <div class="card-body">
        <h3 class="section-title">Actionable Trading Strategies</h3>
        <ul>
          {{ACTIONABLE_INSIGHTS}}
        </ul>
        
        <div class="grid-2" style="margin-top: 20px;">
          <div class="opportunity-box">
            <h3 style="color: #28a745; margin-top: 0;">Trading Opportunities</h3>
            <ul>
              {{TRADING_OPPORTUNITIES}}
            </ul>
          </div>
          
          <div class="risk-box">
            <h3 style="color: #dc3545; margin-top: 0;">Risk Factors</h3>
            <ul>
              {{RISK_FACTORS}}
            </ul>
          </div>
        </div>
      </div>
    </div>
    
    <!-- AI Recommendation -->
    <div class="card">
      <div class="card-header">AI-Generated Recommendation</div>
      <div class="card-body">
        <div class="insight-box">
          <p>{{AI_RECOMMENDATION}}</p>
        </div>
      </div>
    </div>
    
    <div class="footer">
      <p>This analysis was generated using AI and should not be considered financial advice. Always conduct your own research before making investment decisions.</p>
      <p>Generated on {{GENERATION_DATE}}</p>
    </div>
  </div>
</body>
</html>
"""

def get_ai_prompt_template():
    """
    Returns the prompt template for the AI to generate analysis that fits the HTML format.
    
    This function provides a structured prompt that instructs the AI on how to format
    its analysis to match the HTML template structure.
    
    Returns:
        str: Prompt template with placeholders
    """
    
    return """
Analyze this federal contract and its market impact. Be concise and direct in your analysis:

Contract Details:
- ID: {{CONTRACT_ID}}
- Company: {{COMPANY_NAME}}
- Amount: {{CONTRACT_AMOUNT}}
- Award Date: {{AWARD_DATE}}
- Description: {{CONTRACT_DESCRIPTION}}
- Awarding Agency: {{AGENCY_NAME}}

Market Impact Metrics:
- Price Change: {{PRICE_CHANGE_PCT}}%
- Volume Change: {{VOLUME_CHANGE_PCT}}%
- Pre-Award Average Price: ${{PRE_PRICE_AVG}}
- Post-Award Average Price: ${{POST_PRICE_AVG}}
- Pre-Award Average Volume: {{PRE_VOLUME_AVG}} shares
- Post-Award Average Volume: {{POST_VOLUME_AVG}} shares

Please provide a focused analysis with the following sections:

1. Market Impact Analysis
Provide 1-2 concise paragraphs analyzing how this contract affected the company's stock price and trading volume.

2. Sector Trends
Provide 3 bullet points about trends in the defense/aerospace sector related to this contract.

3. Predictive Indicators
Provide 1 paragraph about indicators that could predict future stock movement based on this contract.

4. Actionable Trading Insights
Provide 3 bullet points with specific trading strategies related to this contract.

5. Trading Opportunities
Provide 3 bullet points about specific opportunities this contract creates.

6. Risk Factors
Provide 3 bullet points about potential risks investors should be aware of.

7. AI-Generated Recommendation
Provide a concise 1-paragraph recommendation summarizing whether this contract represents a positive signal for the company's stock.

Format your response as plain text that can be inserted into the corresponding sections of an HTML template. Do not include HTML tags or markdown formatting.
""" 