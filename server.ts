/**
 * TrustTag - Full-Stack Express Server & Python Engine Bridge (server.ts)
 */

import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { exec } from 'child_process';
import util from 'util';

const execPromise = util.promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

  app.use(express.json());

  // 1. Check Pre-Purchase Trust
  app.post('/api/check-trust', async (req, res) => {
    try {
      const { seller_query, serial_or_qr, category, listed_price, batch_code, claimed_packaging, offline_mode } = req.body;
      
      const payload = {
        seller_query: String(seller_query || ''),
        serial_or_qr: String(serial_or_qr || ''),
        category: String(category || 'charger'),
        listed_price: Number(listed_price || 0),
        batch_code: batch_code ? String(batch_code) : '',
        claimed_packaging: claimed_packaging ? String(claimed_packaging) : '',
        offline_mode: offline_mode !== false
      };

      const pyScript = `
import json, sys
import agents

data = json.loads('''${JSON.stringify(payload).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}''')
report = agents.run_trust_evaluation(
    seller_query=data['seller_query'],
    serial_or_qr=data['serial_or_qr'],
    category=data['category'],
    listed_price=data['listed_price'],
    batch_code=data.get('batch_code') or None,
    claimed_packaging=data.get('claimed_packaging') or None,
    force_offline=data.get('offline_mode', True)
)
print(json.dumps(report))
`;

      const { stdout, stderr } = await execPromise(`python3 -c "${pyScript.replace(/"/g, '\\"')}"`, {
        cwd: __dirname,
        timeout: 10000
      });

      if (stderr && !stdout) {
        throw new Error(stderr);
      }

      const parsed = JSON.parse(stdout.trim());
      res.json({ success: true, report: parsed });
    } catch (err: any) {
      console.error('Error in /api/check-trust:', err);
      res.status(500).json({ success: false, error: err.message || 'Execution failed' });
    }
  });

  // 2. Report a Problem & Trigger Dispute Arbitrator
  app.post('/api/report-complaint', async (req, res) => {
    try {
      const complaintData = req.body;
      const pyScript = `
import json, sys
import agents

data = json.loads('''${JSON.stringify(complaintData).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}''')
result = agents.run_dispute_resolution_workflow(data, force_offline=True)
print(json.dumps(result))
`;

      const { stdout } = await execPromise(`python3 -c "${pyScript.replace(/"/g, '\\"')}"`, {
        cwd: __dirname,
        timeout: 10000
      });

      const parsed = JSON.parse(stdout.trim());
      res.json({ success: true, result: parsed });
    } catch (err: any) {
      console.error('Error in /api/report-complaint:', err);
      res.status(500).json({ success: false, error: err.message || 'Dispute execution failed' });
    }
  });

  // 3. Seller "Get Verified"
  app.post('/api/verify-seller', async (req, res) => {
    try {
      const verifData = req.body;
      const pyScript = `
import json, sys
import tools, database

data = json.loads('''${JSON.stringify(verifData).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}''')
eval_res = tools.evaluate_seller_verification_application(
    seller_id=data.get('seller_id', 'SEL-NEW'),
    business_name=data.get('business_name', ''),
    tax_id=data.get('tax_id', ''),
    id_document_type=data.get('id_document_type', 'PASSPORT'),
    contact_email=data.get('contact_email', ''),
    phone=data.get('phone', '')
)
save_payload = {
    'seller_id': data.get('seller_id', 'SEL-NEW'),
    'business_name': data.get('business_name', ''),
    'tax_id': data.get('tax_id', ''),
    'id_document_type': data.get('id_document_type', 'PASSPORT'),
    'contact_email': data.get('contact_email', ''),
    'phone': data.get('phone', ''),
    'verification_score': eval_res['verification_score'],
    'remarks': '; '.join(eval_res['feedback'])
}
db_res = database.save_seller_verification(save_payload)
combined = {**eval_res, **db_res}
print(json.dumps(combined))
`;

      const { stdout } = await execPromise(`python3 -c "${pyScript.replace(/"/g, '\\"')}"`, {
        cwd: __dirname,
        timeout: 10000
      });

      const parsed = JSON.parse(stdout.trim());
      res.json({ success: true, verification: parsed });
    } catch (err: any) {
      console.error('Error in /api/verify-seller:', err);
      res.status(500).json({ success: false, error: err.message || 'Verification failed' });
    }
  });

  // 4. Get Sellers
  app.get('/api/sellers', async (_req, res) => {
    try {
      const pyScript = `
import json, database
sellers = database.get_all_sellers()
print(json.dumps(sellers))
`;
      const { stdout } = await execPromise(`python3 -c "${pyScript.replace(/"/g, '\\"')}"`, { cwd: __dirname });
      res.json({ success: true, sellers: JSON.parse(stdout.trim()) });
    } catch (err: any) {
      res.status(500).json({ success: false, error: err.message });
    }
  });

  // 5. Risk Board (Clusters & Complaints)
  app.get('/api/risk-board', async (_req, res) => {
    try {
      const pyScript = `
import json, database
clusters = database.find_complaint_clusters(min_reports=2, max_days_threshold=7)
complaints = database.get_all_complaints(limit=30)
print(json.dumps({"clusters": clusters, "complaints": complaints}))
`;
      const { stdout } = await execPromise(`python3 -c "${pyScript.replace(/"/g, '\\"')}"`, { cwd: __dirname });
      res.json({ success: true, ...JSON.parse(stdout.trim()) });
    } catch (err: any) {
      res.status(500).json({ success: false, error: err.message });
    }
  });

  // 6. Python Project Deliverables & File Viewer
  app.get('/api/python-files', (_req, res) => {
    try {
      const files = [
        'app.py',
        'agents.py',
        'tasks.py',
        'tools.py',
        'database.py',
        'seed_data.json',
        'requirements.txt',
        '.env.example',
        'README.md'
      ];

      const result: Record<string, string> = {};
      for (const f of files) {
        const fullPath = path.join(__dirname, f);
        if (fs.existsSync(fullPath)) {
          result[f] = fs.readFileSync(fullPath, 'utf-8');
        } else {
          result[f] = '# File not found';
        }
      }

      res.json({ success: true, files: result });
    } catch (err: any) {
      res.status(500).json({ success: false, error: err.message });
    }
  });

  // 7. Run Python Test Command
  app.post('/api/run-python-test', async (req, res) => {
    try {
      const { command } = req.body;
      const allowedCommands: Record<string, string> = {
        'init_db': 'python3 database.py',
        'test_honest': 'python3 -c "import tools; r=tools.compute_composite_trusttag_report(\'SEL-HONEST-01\', \'ANK-735-882190\', \'charger\', 54.99, \'BATCH-ANK-2024-Q1\'); print(\'TrustTag Score:\', r[\'trusttag_score\'], r[\'badge_label\']); print(\'Reasons:\', r[\'reasons\'])"',
        'test_fraud': 'python3 -c "import tools; r=tools.compute_composite_trusttag_report(\'SEL-FRAUD-01\', \'CLONE-BATCH-BL2024-X9\', \'charger\', 7.99, \'BL-2024-X9\'); print(\'TrustTag Score:\', r[\'trusttag_score\'], r[\'badge_label\']); print(\'Reasons:\', r[\'reasons\'])"',
        'crewai_check': 'python3 -c "import crewai, agents; print(\'CrewAI Version:\', crewai.__version__); r=agents.run_trust_evaluation(\'SEL-FRAUD-01\', \'CLONE-BATCH-BL2024-X9\', \'charger\', 7.99, \'BL-2024-X9\'); print(\'Multi-Agent Logs:\', len(r[\'agent_logs\']))"',
        'streamlit_check': 'streamlit --version'
      };

      const cmd = allowedCommands[command] || 'python3 database.py';
      const { stdout, stderr } = await execPromise(cmd, { cwd: __dirname });
      res.json({ success: true, output: (stdout + '\n' + (stderr || '')).trim() });
    } catch (err: any) {
      res.json({ success: false, error: err.message });
    }
  });

  // Mount Vite or serve static dist
  if (process.env.NODE_ENV === 'production' && fs.existsSync(path.join(__dirname, 'dist'))) {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  } else {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[TrustTag Server] Listening on http://0.0.0.0:${PORT}`);
  });
}

startServer().catch(err => {
  console.error('[TrustTag Server Error]:', err);
});
