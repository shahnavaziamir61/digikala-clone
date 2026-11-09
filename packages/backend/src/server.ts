import express from 'express';
import cors from 'cors';
import { createServer } from 'node:http';
import { WebSocketServer, WebSocket } from 'ws';
import { createStore } from './store.js';
import { registerRoutes } from './routes.js';
import { simulateEscapement, simulateDynamics, EscapementParams, RigidBody } from '@horology/engineering-core';

const PORT = Number(process.env.PORT ?? 3001);
const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' }));

const store = createStore();
registerRoutes(app, store);

const server = createServer(app);
const wss = new WebSocketServer({ server, path: '/ws/simulate' });

wss.on('connection', (ws: WebSocket) => {
  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw.toString()) as { type: string; payload?: unknown };
      if (msg.type === 'escapement') {
        const { params, durationS } = msg.payload as { params: EscapementParams; durationS: number };
        const result = simulateEscapement(params, durationS ?? 5);
        ws.send(JSON.stringify({ type: 'escapement-result', result }));
      } else if (msg.type === 'dynamics') {
        const { bodies, opts } = msg.payload as { bodies: RigidBody[]; opts: { mode: 'kinematic' | 'rigid-body' | 'contact' | 'escapement'; durationS: number; dtS: number; adaptive?: boolean } };
        const result = simulateDynamics(bodies, opts);
        // Stream samples in chunks (real-time style)
        const chunk = Math.max(1, Math.floor(result.samples.length / 20));
        let i = 0;
        const timer = setInterval(() => {
          if (i >= result.samples.length) {
            ws.send(JSON.stringify({ type: 'dynamics-done', summary: { stable: result.stable, energyDriftPct: result.energyDriftPct, warnings: result.warnings, mode: result.mode } }));
            clearInterval(timer);
            return;
          }
          ws.send(JSON.stringify({ type: 'dynamics-frame', samples: result.samples.slice(i, i + chunk) }));
          i += chunk;
        }, 50);
      } else {
        ws.send(JSON.stringify({ type: 'error', message: `Unknown message type: ${msg.type}` }));
      }
    } catch (e) {
      ws.send(JSON.stringify({ type: 'error', message: String(e) }));
    }
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Horology Engineering backend on http://0.0.0.0:${PORT} (REST /api, WS /ws/simulate)`);
});
