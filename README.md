# Ethos Webhooks - Voice AI Integration

**Production URL:** `https://ethos-webhooks-production.up.railway.app`

FastAPI service that provides webhook endpoints for ElevenLabs Conversational AI agent to access Ethos capabilities during voice calls.

## Architecture

```
ElevenLabs Voice Agent → Webhook Tools → This Service → Moltbot Gateway → Ethos
```

## Endpoints

### `/health`
Health check endpoint.

### `/check-lead`
Check if a business exists in Close.io CRM.
```json
{
  "business_name": "Example Store"
}
```

### `/product-recommendation`  
Get FÜM product package recommendation.
```json
{
  "store_type": "smoke shop",
  "transactions_per_day": 500
}
```

### `/close-query`
Query Close.io for aggregate data.
```json
{
  "query_type": "count_customers"
}
```

### `/ask-ethos` ⭐
**Key endpoint** - Proxy to full Ethos capabilities via Moltbot gateway.
```json
{
  "question": "What were we discussing before this call?",
  "context": "optional conversation context"
}
```

## Environment Variables

Required in Railway:
```
CLOSE_API_KEY=api_0DNymNGRDS9HOA9wcVtrJ8.6VbU5YobHNOU1pASVzSxKT
MOLTBOT_GATEWAY_URL=<needs_configuration>
MOLTBOT_GATEWAY_TOKEN=<needs_configuration>
```

## ElevenLabs Agent Configuration

**Agent ID:** `agent_9101kg8qh1v5f6htjjja0ax9jz5a`  
**Name:** Ethos  
**Phone:** `+15873302387`

Tools configured:
- check_lead
- get_product_recommendation  
- close_query
- ask_ethos

## Deployment

Deployed to Railway from this directory. Auto-deploys on git push.

## Usage

Voice agent can now:
- Check if businesses are existing customers
- Recommend FÜM product packages
- Query CRM for business data
- **Access full Ethos capabilities** during calls

This bridges the gap between voice conversations and text-based AI capabilities.