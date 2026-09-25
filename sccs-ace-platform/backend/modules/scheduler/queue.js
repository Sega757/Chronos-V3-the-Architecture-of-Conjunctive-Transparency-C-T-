const { Queue, Worker } = require('bullmq');
const Redis = require('ioredis');
const { Pool } = require('pg');
const crypto = require('crypto');

const connection = new Redis(process.env.REDIS_URL || 'redis://redis:6379');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://sccs_user:sccs_password@postgres:5432/sccs_db'
});

const sccsQueue = new Queue('sccsGenerationQueue', { connection });

const worker = new Worker('sccsGenerationQueue', async job => {
    console.log(`Processing job ${job.id}: ${job.name}`);
    const prompt = job.data.prompt || "Auto-generated prompt";
    const hash = crypto.createHash('sha256').update(prompt).digest('hex');

    // Simulate generation time
    const start = Date.now();
    await new Promise(res => setTimeout(res, 500));
    const executionTime = Date.now() - start;

    try {
        await pool.query(
            `INSERT INTO generation_logs (model_used, prompt_hash, prompt_text, response_text, execution_time_ms, status)
             VALUES ($1, $2, $3, $4, $5, $6)`,
            ['Neocortex-Chronos-V3-Hybrid', hash, prompt, 'Generated via BullMQ Worker.', executionTime, 'success']
        );
        console.log(`Job ${job.id} saved to DB.`);
    } catch (e) {
        console.error(`DB Error on job ${job.id}`, e);
    }
    return { status: 'success' };
}, { connection });

worker.on('failed', (job, err) => {
    console.error(`Job ${job.id} failed with ${err.message}`);
});

module.exports = { sccsQueue };
