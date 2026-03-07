from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx
import os
import json
from datetime import datetime, timezone
import resend
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

app = FastAPI(title="Ethos Webhooks")

# ── Resend email client ───────────────────────────────────────────────────────
resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = "Lucas Senechal <lucas@lucassenechal.com>"

# ── Scheduler for timed emails ────────────────────────────────────────────────
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()

# ── Email helpers ─────────────────────────────────────────────────────────────
def send_confirmation_email(attendee_email: str, attendee_name: str, event_date: str, event_time: str, meeting_url: str):
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": attendee_email,
        "subject": "You're booked — AI Strategy Discovery Call with Lucas Senechal",
        "html": f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#000">
  <p>Hey {attendee_name},</p>
  <p>Your 30-minute AI Strategy Discovery Call is confirmed. I'm looking forward to it.</p>
  <p>📅 <strong>{event_date} at {event_time}</strong><br>
  🔗 <a href="{meeting_url}">{meeting_url}</a></p>
  <p>To make the most of our time, come prepared to share:</p>
  <ul>
    <li>Your biggest operational bottleneck right now</li>
    <li>Where your team spends the most manual time</li>
    <li>Any AI tools you've already tried (even if they didn't work)</li>
  </ul>
  <p>No prep required — but the more specific you are, the more value you'll walk away with.</p>
  <p>See you soon,<br>
  <strong>Lucas Senechal</strong><br>
  AI Strategy &amp; Implementation<br>
  <a href="https://lucassenechal.com">lucassenechal.com</a></p>
</div>
        """
    })

def send_reminder_email(attendee_email: str, attendee_name: str, event_date: str, event_time: str, meeting_url: str):
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": attendee_email,
        "subject": "Tomorrow: Your AI Discovery Call with Lucas",
        "html": f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#000">
  <p>Hey {attendee_name},</p>
  <p>Quick reminder — we're talking tomorrow.</p>
  <p>📅 <strong>{event_date} at {event_time}</strong><br>
  🔗 <a href="{meeting_url}">{meeting_url}</a></p>
  <p>One thing to think about before we connect: what would it mean for your business if your biggest time drain was fully automated?</p>
  <p>See you tomorrow.<br>
  <strong>Lucas Senechal</strong><br>
  <a href="https://lucassenechal.com">lucassenechal.com</a></p>
</div>
        """
    })

def send_followup_email(attendee_email: str, attendee_name: str):
    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": attendee_email,
        "subject": f"Great talking, {attendee_name} — next steps",
        "html": f"""
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#000">
  <p>Hey {attendee_name},</p>
  <p>Thanks for making time today.</p>
  <p>If you're ready to move forward, reply to this email and I'll send over a proposal with a clear scope, timeline, and investment.</p>
  <p>If you're still weighing your options — no pressure. I'm here when the timing is right.</p>
  <p>Either way, feel free to share the booking link with anyone on your team who might benefit:<br>
  👉 <a href="https://lucassenechal.com/call">lucassenechal.com/call</a></p>
  <p>Talk soon,<br>
  <strong>Lucas Senechal</strong><br>
  AI Strategy &amp; Implementation<br>
  <a href="https://lucassenechal.com">lucassenechal.com</a></p>
</div>
        """
    })


CLOSE_API_KEY = os.getenv("CLOSE_API_KEY", "api_0DNymNGRDS9HOA9wcVtrJ8.6VbU5YobHNOU1pASVzSxKT")
MOLTBOT_GATEWAY_URL = os.getenv("MOLTBOT_GATEWAY_URL", "")
MOLTBOT_GATEWAY_TOKEN = os.getenv("MOLTBOT_GATEWAY_TOKEN", "")

@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "service": "ethos-webhooks",
        "gateway_url": MOLTBOT_GATEWAY_URL,
        "gateway_token": bool(MOLTBOT_GATEWAY_TOKEN)
    }

@app.post("/check-lead")
async def check_lead(request: Request):
    """Check if a business exists in Close.io and get their status."""
    data = await request.json()
    business_name = data.get("business_name", "")
    
    if not business_name:
        return JSONResponse({"error": "business_name required"}, status_code=400)
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.close.com/api/v1/lead/",
            params={"query": f'name:"{business_name}"', "_fields": "id,display_name,status_label"},
            auth=(CLOSE_API_KEY, ""),
            timeout=15.0
        )
        result = resp.json()
    
    if result.get("data") and len(result["data"]) > 0:
        lead = result["data"][0]
        return {
            "found": True,
            "name": lead.get("display_name"),
            "status": lead.get("status_label"),
            "lead_id": lead.get("id")
        }
    return {"found": False, "status": "not_found"}

@app.post("/product-recommendation")
async def product_recommendation(request: Request):
    """Get FÜM product package recommendation based on store profile."""
    data = await request.json()
    store_type = data.get("store_type", "").lower()
    transactions = data.get("transactions_per_day", 0)
    
    if transactions < 200:
        package = "Starter A"
        units = "30-50 units"
        skus = "4 SKUs"
        desc = "Perfect for smaller stores - our entry-level package"
    elif transactions < 800:
        package = "Starter B"
        units = "80-120 units"
        skus = "8 SKUs"
        desc = "Most popular for mid-size retail"
    else:
        package = "Starter C"
        units = "150-300 units"
        skus = "Full range"
        desc = "High-volume stores get our complete lineup"
    
    if "smoke" in store_type:
        package = "Smoke Shop Kit"
        units = "200-400 units"
        skus = "12-16 SKUs + training materials"
        desc = "Designed specifically for smoke shops with full merchandising support"
    
    return {
        "recommended_package": package,
        "units": units,
        "skus": skus,
        "description": desc,
        "wholesale_core_price": "$59.99 per 10-pack"
    }

@app.post("/ask-ethos")
async def ask_ethos(request: Request):
    """
    Proxy endpoint for ElevenLabs voice agent.
    Sends the user's question to Moltbot (Ethos) and returns the response.
    This gives the voice agent full access to all of Ethos's capabilities.
    """
    data = await request.json()
    question = data.get("question", "")
    context = data.get("context", "")
    
    if not question:
        return {"error": "question required", "response": "I didn't catch that. Could you repeat?"}
    
    # Build the prompt for Moltbot
    prompt = f"""[Voice Call Query from ElevenLabs]
    
User asked via voice: "{question}"

{f'Context from conversation: {context}' if context else ''}

Respond concisely (1-3 sentences) for voice delivery. Use your full capabilities - check Close.io, search emails, access calendar, query databases, whatever is needed to answer."""

    if not MOLTBOT_GATEWAY_URL:
        return {
            "response": "I don't have my full capabilities connected yet. Lucas needs to configure the Moltbot gateway connection.",
            "error": "moltbot_not_configured"
        }
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if MOLTBOT_GATEWAY_TOKEN:
                headers["Authorization"] = f"Bearer {MOLTBOT_GATEWAY_TOKEN}"
            
            resp = await client.post(
                f"{MOLTBOT_GATEWAY_URL}/webhook/ask-ethos",
                headers=headers,
                json={
                    "question": question,
                    "context": context
                },
                timeout=35.0
            )
            result = resp.json()
            
            if result.get("response"):
                return {"response": result.get("response")}
            else:
                return {"response": "I had trouble processing that. Could you try again?", "error": result}
    except Exception as e:
        return {
            "response": "I'm having connection issues. Try asking again in a moment.",
            "error": str(e)
        }

@app.post("/close-query")
async def close_query(request: Request):
    """
    Run arbitrary Close.io queries for the voice agent.
    Supports: count customers, list recent leads, search by status, etc.
    """
    data = await request.json()
    query_type = data.get("query_type", "")
    
    async with httpx.AsyncClient() as client:
        if query_type == "count_customers":
            # Use params dict with unencoded query - httpx will encode properly
            resp = await client.get(
                'https://api.close.com/api/v1/lead/',
                params={
                    'query': 'lead_status:"Customer"',
                    '_fields': 'id,display_name,status_label',
                    '_limit': '200'
                },
                auth=(CLOSE_API_KEY, ""),
                timeout=15.0
            )
            result = resp.json()
            count = result.get("total_results") or len(result.get("data", []))
            has_more = result.get("has_more", False)
            return {
                "count": count,
                "has_more": has_more,
                "message": f"You have {'at least ' if has_more else ''}{count} customers in Close.io"
            }
        
        elif query_type == "count_by_status":
            status = data.get("status", "")
            resp = await client.get(
                'https://api.close.com/api/v1/lead/',
                params={
                    'query': f'lead_status:"{status}"',
                    '_fields': 'id',
                    '_limit': '200'
                },
                auth=(CLOSE_API_KEY, ""),
                timeout=15.0
            )
            result = resp.json()
            count = len(result.get("data", []))
            return {"status": status, "count": count, "message": f"You have {count} leads with status '{status}'"}
        
        elif query_type == "recent_leads":
            limit = data.get("limit", 5)
            resp = await client.get(
                "https://api.close.com/api/v1/lead/",
                params={"_fields": "id,display_name,status_label,date_created", "_limit": limit, "_order_by": "-date_created"},
                auth=(CLOSE_API_KEY, ""),
                timeout=15.0
            )
            result = resp.json()
            leads = [{"name": l.get("display_name"), "status": l.get("status_label")} for l in result.get("data", [])]
            return {"leads": leads, "count": len(leads)}
        
        else:
            return {"error": "Unknown query_type. Supported: count_customers, count_by_status, recent_leads"}

@app.post("/cal-webhook")
async def cal_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives cal.com booking events and sends branded emails via Resend.
    Handles: BOOKING_CREATED (confirmation + schedules reminder + follow-up)
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    trigger_event = payload.get("triggerEvent", "")
    booking = payload.get("payload", {})

    attendee = {}
    attendees = booking.get("attendees", [])
    if attendees:
        attendee = attendees[0]
    
    attendee_name  = attendee.get("name", "there")
    attendee_email = attendee.get("email", "")
    meeting_url    = booking.get("metadata", {}).get("videoCallUrl", "") or booking.get("videoCallUrl", "")
    start_time_str = booking.get("startTime", "")
    end_time_str   = booking.get("endTime", "")

    if not attendee_email:
        return JSONResponse({"status": "skipped", "reason": "no attendee email"})

    # Parse times
    try:
        start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        end_dt   = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        # Convert to Pacific for display
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("America/Vancouver")
        start_local = start_dt.astimezone(pacific)
        end_local   = end_dt.astimezone(pacific)
        event_date  = start_local.strftime("%A, %B %-d, %Y")
        event_time  = start_local.strftime("%-I:%M %p PT")
    except Exception:
        event_date = start_time_str
        event_time = ""
        start_dt   = datetime.now(timezone.utc)
        end_dt     = datetime.now(timezone.utc)

    if trigger_event == "BOOKING_CREATED":
        # 1. Send confirmation immediately
        background_tasks.add_task(
            send_confirmation_email,
            attendee_email, attendee_name, event_date, event_time, meeting_url
        )

        # 2. Schedule 24hr reminder (fires 24h before start)
        from datetime import timedelta
        reminder_time = start_dt - timedelta(hours=24)
        now = datetime.now(timezone.utc)

        if reminder_time > now:
            scheduler.add_job(
                send_reminder_email,
                trigger=DateTrigger(run_date=reminder_time),
                args=[attendee_email, attendee_name, event_date, event_time, meeting_url],
                id=f"reminder_{booking.get('uid', attendee_email)}",
                replace_existing=True
            )

        # 3. Schedule follow-up 1hr after end
        followup_time = end_dt + timedelta(hours=1)
        if followup_time > now:
            scheduler.add_job(
                send_followup_email,
                trigger=DateTrigger(run_date=followup_time),
                args=[attendee_email, attendee_name],
                id=f"followup_{booking.get('uid', attendee_email)}",
                replace_existing=True
            )

        return JSONResponse({
            "status": "ok",
            "sent": "confirmation",
            "scheduled": ["reminder_24h_before", "followup_1h_after"],
            "attendee": attendee_email
        })

    elif trigger_event == "BOOKING_CANCELLED":
        # Remove any scheduled jobs for this booking
        uid = booking.get("uid", "")
        for job_id in [f"reminder_{uid}", f"followup_{uid}"]:
            try:
                scheduler.remove_job(job_id)
            except Exception:
                pass
        return JSONResponse({"status": "ok", "cancelled_jobs": uid})

    return JSONResponse({"status": "ignored", "trigger": trigger_event})


@app.post("/health-data")
async def health_data(request: Request):
    """
    Receives Apple Health data from Health Auto Export app.
    Appends to ~/clawd/health/apple-health-log.csv on the local machine via webhook.
    Since this runs on Railway (not local), we forward a Telegram notification
    and store the raw payload for Ethos to process.
    """
    import csv, io
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    # Log the raw payload as JSON lines to a rolling file
    # We notify via Telegram so Ethos can process it
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Extract key metrics if present (Health Auto Export format)
    metrics = payload.get("data", {}).get("metrics", []) or payload.get("metrics", [])
    
    summary = {}
    for metric in metrics:
        name = metric.get("name", "")
        data_points = metric.get("data", [])
        if data_points:
            latest = data_points[-1]
            summary[name] = latest.get("qty") or latest.get("value") or latest.get("avg")

    # Forward to Telegram via gateway if configured
    GATEWAY_URL = os.getenv("MOLTBOT_GATEWAY_URL", "")
    GATEWAY_TOKEN = os.getenv("MOLTBOT_GATEWAY_TOKEN", "")
    
    if GATEWAY_URL and summary:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{GATEWAY_URL}/webhook/health-data",
                    headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"},
                    json={"timestamp": timestamp, "summary": summary, "raw": payload},
                    timeout=10.0
                )
        except Exception:
            pass  # best effort

    return JSONResponse({
        "status": "ok",
        "received_at": timestamp,
        "metrics_received": len(metrics),
        "summary": summary
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
