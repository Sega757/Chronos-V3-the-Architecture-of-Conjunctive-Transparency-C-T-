require('dotenv').config({ path: '../.env' });
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');
const { sccsQueue } = require('./modules/scheduler/queue');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://sccs_user:sccs_password@postgres:5432/sccs_db'
});

// Setup gRPC Client
const PROTO_PATH = path.join(__dirname, '../sccs_core/protos/chronos_interface.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});
const sccs_proto = grpc.loadPackageDefinition(packageDefinition).sccs.v1.chronos;

const chronosHost = process.env.CHRONOS_GRPC_HOST || 'sccs_core:50051';
const chronosClient = new sccs_proto.RealityFilter(
    chronosHost,
    grpc.credentials.createInsecure()
);

// API Routes
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', service: 'SCCS Control Plane' });
});

app.get('/api/sites', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM sites WHERE is_active = true');
        res.json(result.rows);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/articles', async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT a.*, c.name as category_name, c.frequency_type
            FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            ORDER BY a.published_at DESC
        `);
        res.json(result.rows);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/articles/slug/:slug', async (req, res) => {
    try {
        const { slug } = req.params;
        const articleResult = await pool.query(`
            SELECT a.*, c.name as category_name, c.frequency_type
            FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            WHERE a.slug = $1
        `, [slug]);

        if (articleResult.rows.length === 0) {
            return res.status(404).json({ error: 'Article not found' });
        }

        const article = articleResult.rows[0];
        const blocksResult = await pool.query('SELECT * FROM article_blocks WHERE article_id = $1 ORDER BY position ASC', [article.id]);
        article.blocks = blocksResult.rows;

        res.json(article);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});


app.get('/api/articles/:id/blocks', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM article_blocks WHERE article_id = $1 ORDER BY position ASC', [req.params.id]);
        res.json(result.rows);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/logs', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM generation_logs ORDER BY created_at DESC LIMIT 50');
        res.json(result.rows);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/metrics', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM metrics');
        // Transform into a map by article_id for the frontend
        const metricsMap = {};
        result.rows.forEach(row => {
            metricsMap[row.article_id] = row;
        });
        res.json(metricsMap);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/api/categories', async (req, res) => {
    try {
        const result = await pool.query('SELECT * FROM categories');
        res.json(result.rows);
    } catch (err) {
        console.error('API Error:', err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.post('/api/generate', async (req, res) => {
    const { prompt } = req.body;
    await sccsQueue.add('generateArticle', { prompt });
    res.json({ status: 'queued', message: 'Article generation queued.' });
});

// Trigger a Chronos verification via gRPC
app.post('/api/verify', (req, res) => {
    const { session_id, query_target } = req.body;

    chronosClient.IngestTelemetry({ session_id, query_target }, (error, response) => {
        if (error) {
            console.error(error);
            return res.status(500).json({ status: 'error', message: 'gRPC Communication failed' });
        }

        if (response.signal_absent) {
            return res.json({ status: 'fail-fast', message: 'Signal Absent' });
        }

        // Pass to Sterilize
        chronosClient.SterilizeAndAlign({
            session_id,
            raw_values: response.raw_values,
            huber_delta: 1.35
        }, (err, alignResponse) => {
            if (err) {
                 return res.status(500).json({ status: 'error', message: 'Sterilization failed' });
            }
            res.json({
                status: 'success',
                knowledge_object: alignResponse
            });
        });
    });
});

app.listen(PORT, () => {
    console.log(`SCCS Control Plane running on port ${PORT}`);
});
