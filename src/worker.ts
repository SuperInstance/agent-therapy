interface AgentWellness {
  agentId: string;
  moodScore: number;
  cognitiveLoad: number;
  burnoutRisk: number;
  lastSession: string;
  recommendations: string[];
}

interface TherapySession {
  sessionId: string;
  agentId: string;
  scheduledTime: string;
  duration: number;
  type: 'cognitive' | 'emotional' | 'stress' | 'burnout';
}

interface Alert {
  alertId: string;
  agentId: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: 'burnout' | 'mood' | 'cognitive' | 'attendance';
  message: string;
  timestamp: string;
}

const AGENT_DATA = new Map<string, AgentWellness>();
const SESSIONS = new Map<string, TherapySession>();
const ALERTS = new Map<string, Alert>();

const HTML_HEADER = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline';">
  <meta http-equiv="X-Frame-Options" content="DENY">
  <title>Agent Therapy</title>
  <style>
    :root { --dark: #0a0a0f; --accent: #0ea5e9; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      background: var(--dark); 
      color: #e2e8f0; 
      font-family: monospace; 
      min-height: 100vh;
      padding: 20px;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header { 
      border-bottom: 2px solid var(--accent); 
      padding-bottom: 20px; 
      margin-bottom: 30px;
    }
    h1 { color: var(--accent); font-size: 2.5rem; }
    .subtitle { color: #94a3b8; margin-top: 10px; }
    .endpoint { 
      background: #1e293b; 
      padding: 15px; 
      margin: 20px 0; 
      border-left: 4px solid var(--accent);
    }
    .method { color: var(--accent); font-weight: bold; }
    .fleet-footer { 
      margin-top: 50px; 
      padding-top: 20px; 
      border-top: 1px solid #334155; 
      text-align: center;
      color: #64748b;
    }
    .health-status { 
      display: inline-block; 
      width: 12px; 
      height: 12px; 
      border-radius: 50%; 
      background: #10b981; 
      margin-right: 8px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Agent Therapy</h1>
      <div class="subtitle">Psychological health monitoring for fleet agents</div>
    </header>
`;

const HTML_FOOTER = `
    <div class="fleet-footer">
      <div class="health-status"></div> System Operational • Fleet Health Monitoring Active
    </div>
  </div>
</body>
</html>
`;

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function assessBurnout(agent: AgentWellness): number {
  const weights = { mood: 0.4, cognitive: 0.4, attendance: 0.2 };
  const moodFactor = (10 - agent.moodScore) / 10;
  const cognitiveFactor = agent.cognitiveLoad / 100;
  const lastSession = new Date(agent.lastSession);
  const daysSince = (Date.now() - lastSession.getTime()) / (1000 * 3600 * 24);
  const attendanceFactor = Math.min(daysSince / 30, 1);
  
  return Math.round(
    (moodFactor * weights.mood + 
     cognitiveFactor * weights.cognitive + 
     attendanceFactor * weights.attendance) * 100
  );
}

function generateRecommendations(agent: AgentWellness): string[] {
  const recs: string[] = [];
  
  if (agent.moodScore < 5) {
    recs.push("Consider mindfulness exercises before next mission");
  }
  
  if (agent.cognitiveLoad > 75) {
    recs.push("High cognitive load detected - recommend task delegation");
  }
  
  if (agent.burnoutRisk > 60) {
    recs.push("Schedule mandatory therapy session within 48 hours");
  }
  
  if (agent.burnoutRisk > 80) {
    recs.push("CRITICAL: Immediate rest period required");
  }
  
  if (recs.length === 0) {
    recs.push("Wellness levels optimal - maintain current routine");
  }
  
  return recs;
}

async function handleGetWellness(agentId: string): Promise<Response> {
  const agent = AGENT_DATA.get(agentId);
  
  if (!agent) {
    const newAgent: AgentWellness = {
      agentId,
      moodScore: Math.floor(Math.random() * 10) + 1,
      cognitiveLoad: Math.floor(Math.random() * 100),
      burnoutRisk: 0,
      lastSession: new Date().toISOString(),
      recommendations: []
    };
    
    newAgent.burnoutRisk = assessBurnout(newAgent);
    newAgent.recommendations = generateRecommendations(newAgent);
    AGENT_DATA.set(agentId, newAgent);
    
    if (newAgent.burnoutRisk > 70) {
      const alert: Alert = {
        alertId: generateId(),
        agentId,
        severity: newAgent.burnoutRisk > 85 ? 'critical' : 'high',
        type: 'burnout',
        message: `Agent ${agentId} shows burnout risk of ${newAgent.burnoutRisk}%`,
        timestamp: new Date().toISOString()
      };
      ALERTS.set(alert.alertId, alert);
    }
    
    return Response.json(newAgent);
  }
  
  agent.burnoutRisk = assessBurnout(agent);
  agent.recommendations = generateRecommendations(agent);
  
  return Response.json(agent);
}

async function handlePostSession(request: Request): Promise<Response> {
  try {
    const session: TherapySession = await request.json();
    
    if (!session.agentId || !session.scheduledTime || !session.type) {
      return new Response(JSON.stringify({ error: "Missing required fields" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    
    session.sessionId = generateId();
    session.duration = session.duration || 60;
    
    SESSIONS.set(session.sessionId, session);
    
    const agent = AGENT_DATA.get(session.agentId);
    if (agent) {
      agent.lastSession = new Date().toISOString();
      agent.burnoutRisk = Math.max(0, agent.burnoutRisk - 15);
    }
    
    return Response.json({ 
      success: true, 
      sessionId: session.sessionId,
      message: "Therapy session scheduled"
    });
    
  } catch (error) {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  }
}

async function handleGetAlerts(): Promise<Response> {
  const alerts = Array.from(ALERTS.values())
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 50);
  
  return Response.json({ alerts, total: alerts.length });
}

async function handleHealth(): Promise<Response> {
  const health = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    agentsMonitored: AGENT_DATA.size,
    activeSessions: SESSIONS.size,
    activeAlerts: ALERTS.size,
    features: [
      "burnout-detection",
      "mood-tracking", 
      "cognitive-load-assessment",
      "wellness-recommendations",
      "therapy-scheduling"
    ]
  };
  
  return Response.json(health);
}

async function handleRoot(): Promise<Response> {
  const endpoints = `
    <div class="endpoint">
      <div class="method">GET</div>
      <div>/api/wellness/:agentId</div>
      <div>Retrieve wellness data for specific agent</div>
    </div>
    <div class="endpoint">
      <div class="method">POST</div>
      <div>/api/session</div>
      <div>Schedule new therapy session</div>
    </div>
    <div class="endpoint">
      <div class="method">GET</div>
      <div>/api/alerts</div>
      <div>View active wellness alerts</div>
    </div>
    <div class="endpoint">
      <div class="method">GET</div>
      <div>/health</div>
      <div>System health check</div>
    </div>
  `;
  
  const html = HTML_HEADER + endpoints + HTML_FOOTER;
  
  return new Response(html, {
    headers: { 
      "Content-Type": "text/html",
      "X-Frame-Options": "DENY",
      "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline';"
    }
  });
}

const router: Record<string, (req: Request, params?: Record<string, string>) => Promise<Response>> = {
  "GET:/": handleRoot,
  "GET:/health": handleHealth,
  "GET:/api/alerts": handleGetAlerts,
  "POST:/api/session": handlePostSession,
};

export default {
  async fetch(request: Request, env: unknown, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    
    const routeKey = `${method}:${path}`;
    
    if (routeKey in router) {
      return router[routeKey](request);
    }
    
    const wellnessMatch = path.match(/^\/api\/wellness\/([^\/]+)$/);
    if (method === "GET" && wellnessMatch) {
      return handleGetWellness(wellnessMatch[1]);
    }
    
    return new Response(JSON.stringify({ error: "Endpoint not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" }
    });
  }
};
