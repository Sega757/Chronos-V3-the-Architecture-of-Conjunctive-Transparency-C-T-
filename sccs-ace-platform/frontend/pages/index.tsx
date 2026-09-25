import React, { useState, useEffect } from 'react';

import Head from 'next/head';



// --- TYPE DEFINITIONS FOR SCCS / ACE DOMAIN ---

interface SiteConfig {

theme: string;

locale: string;

huber_delta: number;

}



interface Site {

id: number;

domain: string;

title: string;

config_json: string;

is_active: boolean;

}



interface Category {

id: number;

name: string;

slug: string;

frequency_type: 'LF' | 'MF' | 'HF';

}



interface ArticleBlock {

id: number;

block_type: 'text' | 'image' | 'youtube' | 'links' | 'code' | 'quote';

content: string;

position: number;

}



interface Article {

id: number;

title: string;

slug: string;

summary: string;

status: 'draft' | 'published' | 'archived';

views_count: number;

published_at: string;

category_name: string;

frequency_type: string;

blocks?: ArticleBlock[];

}



interface GenerationLog {

id: number;

model_used: string;

prompt_hash: string;

prompt_text: string;

response_text: string;

execution_time_ms: number;

status: 'success' | 'error';

created_at: string;

}



interface MetricSet {

views: number;

clicks: number;

avg_time_seconds: number;

bounce_rate: number;

}



export default function SCCSControlPanel() {

// --- STATE LAYER ---

const [activeSite, setActiveSite] = useState<Site | null>(null);

const [sites, setSites] = useState<Site[]>([]);

const [categories, setCategories] = useState<Category[]>([]);

const [articles, setArticles] = useState<Article[]>([]);

const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

const [logs, setLogs] = useState<GenerationLog[]>([]);

const [metrics, setMetrics] = useState<Record<number, MetricSet>>({});


// Simulation Interactive State

const [promptInput, setPromptInput] = useState('Verify the transaction tick baseline and execute rebalance order.');

const [isSimulating, setIsSimulating] = useState(false);

const [simulationStep, setSimulationStep] = useState<string>('Idle');

const [simEntropy, setSimEntropy] = useState<number>(0.0);

const [simHuber, setSimHuber] = useState<number>(0.0);

const [simLog, setSimLog] = useState<string[]>([]);

const [ctStatus, setCtStatus] = useState<{ logic: boolean; fact: boolean } | null>(null);



// --- COMPONENT DID MOUNT / SEEDING (HYDRATION) ---

useEffect(() => {

// Synchronous hydrate mimicking seeds.sql payload structure

const seededSites: Site[] = [

{

id: 1,

domain: 'sccs-cognition.ai',

title: 'Sovereign Cognitive Systems Hub',

config_json: '{"theme": "dark", "locale": "ru_RU", "huber_delta": 1.35}',

is_active: true,

},

{

id: 2,

domain: 'ace-engine.org',

title: 'Autonomous Content Engine Portal',

config_json: '{"theme": "light", "locale": "en_US", "huber_delta": 1.50}',

is_active: true,

}

];



const seededCategories: Category[] = [

{ id: 1, name: 'Когнитивная Архитектура', slug: 'cognitive-architecture', frequency_type: 'HF' },

{ id: 2, name: 'Двухпалатный Разум', slug: 'bicameral-mind', frequency_type: 'MF' },

{ id: 3, name: 'Фильтрация Реальности', slug: 'chronos-v3-filter', frequency_type: 'LF' }

];



const seededArticles: Article[] = [

{

id: 1,

title: 'Архитектурный Манифест Суверенной Когнитивной Системы',

slug: 'sovereign-cognitive-architecture-manifesto',

summary: 'Детальный разбор двухпалатной архитектуры SCCS, механизмов C-T и детерминированной фильтрации Chronos V3.',

status: 'published',

views_count: 1420,

published_at: '2026-08-01 10:00:00',

category_name: 'Когнитивная Архитектура',

frequency_type: 'HF',

blocks: [

{ id: 1, block_type: 'text', content: 'Современные фундаментальные исследования в области ИИ обращаются к двухпроцессной теории, разделяющей быструю Систему 1 и рефлексивную Систему 2.', position: 1 },

{ id: 2, block_type: 'quote', content: 'Conjunctive Transparency (C-T) требует одновременного выполнения условий внутренней логической целостности и внешней фактологической подлинности.', position: 2 }

]

},

{

id: 2,

title: 'Детерминированная Стерилизация Шума в Chronos V3',

slug: 'chronos-v3-noise-sterilization',

summary: 'Применение функции потерь Хубера и метода ALS-IRLS для подавления тяжелых хвостов в данных.',

status: 'published',

views_count: 890,

published_at: '2026-08-02 12:30:00',

category_name: 'Фильтрация Реальности',

frequency_type: 'LF',

blocks: [

{ id: 3, block_type: 'code', content: 'def compute_huber_loss(residuals, delta=1.35):\n    abs_res = np.abs(residuals)\n    mask = abs_res <= delta\n    return np.where(mask, 0.5 * (residuals ** 2), delta * (abs_res - 0.5 * delta))', position: 1 }

]

}

];



const seededLogs: GenerationLog[] = [

{

id: 1,

model_used: 'Neocortex-Chronos-V3-Hybrid',

prompt_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',

prompt_text: 'Сгенерировать архитектурный манифест SCCS с учетом C-T и Huber Loss',

response_text: 'Успешно сгенерирован лонгрид ID 1. Все логические швы изолированы.',

execution_time_ms: 245,

status: 'success',

created_at: '2026-08-21 07:00:00'

},

{

id: 2,

model_used: 'Chronos-Logos-Sterilizer',

prompt_hash: 'f2d81a26030d94f24381e27a00160a37269e60e306a728ddd718d9f109c31327',

prompt_text: 'Провести очистку телеметрии и сформировать Knowledge Object',

response_text: 'Сформирован Knowledge Object KO-7890-XY. Residual delta = 0.042.',

execution_time_ms: 112,

status: 'success',

created_at: '2026-08-21 07:15:00'

}

];



const seededMetrics: Record<number, MetricSet> = {

1: { views: 1420, clicks: 310, avg_time_seconds: 245.5, bounce_rate: 0.12 },

2: { views: 890, clicks: 185, avg_time_seconds: 190.2, bounce_rate: 0.18 }

};



setSites(seededSites);

setActiveSite(seededSites[0]);

setCategories(seededCategories);

setArticles(seededArticles);

setLogs(seededLogs);

setMetrics(seededMetrics);

setSelectedArticle(seededArticles[0]);

}, []);



// --- SIMULATION SEQUENCE PIPELINE (5-PHASE BI-CAMERAL PULSE) ---

const runVerificationSimulation = async () => {

setIsSimulating(true);

setCtStatus(null);

setSimLog([]);


const appendLog = (msg: string) => {

setSimLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

};



// Phase 1: Autoregressive Token Sequence Generation (System 1)

setSimulationStep('Phase 1: Generation');

appendLog('System 1 Neocortex initialized. Dispatching token stream proposal.');

setSimEntropy(0.42);

await new Promise(resolve => setTimeout(resolve, 800));



// Phase 2: Entropy Check & Spike Detection (System 0 Meta-Arbiter)

setSimulationStep('Phase 2: Entropy Audit');

appendLog('System 0 Meta-Arbiter monitoring Shannon Entropy H(X).');

// Emulate an injection/ambiguity logic seam spike

const targetEntropy = 2.45;

setSimEntropy(targetEntropy);

appendLog(`WARNING: Shannon Entropy spiked to ${targetEntropy} (Threshold tau = 2.20)`);

await new Promise(resolve => setTimeout(resolve, 800));



// Phase 3: Metacognitive Pause Intervention

setSimulationStep('Phase 3: Metacognitive Pause');

appendLog('Metacognitive Pause Intercept initiated. System 1 generation HALTED.');

await new Promise(resolve => setTimeout(resolve, 700));



// Phase 4: Reality Calibration Ingestion (Chronos V3 & Huber Sentry)

setSimulationStep('Phase 4: Reality Filtration');

appendLog('Invoking chronos_nexus.py system call. Ingesting raw external telemetry feeds.');

// Simulated Huber Loss Noise Sterilization

const rawSignals = [101.2, 101.5, 101.1, 800.4, 101.3]; // Includes outlier noise spike

appendLog(`Raw external feeds received: [${rawSignals.join(', ')}]`);

const huberResult = 0.038;

setSimHuber(huberResult);

appendLog(`Huber Loss M-Estimation applied (delta=1.35). Sterilized outlier spike 800.4.`);

appendLog(`Emitted Fact-checked Knowledge Object: KO_CHRONOS_VERIFIED_7701`);

await new Promise(resolve => setTimeout(resolve, 1000));



// Phase 5: Conjunctive Transparency Evaluation & Cryptographic Signing

setSimulationStep('Phase 5: CT Verification');

const internalLogicPassed = targetEntropy < 3.0; // Simulated logic sanity bounds

const externalFactPassed = huberResult <= 0.10;

setCtStatus({ logic: internalLogicPassed, fact: externalFactPassed });



if (internalLogicPassed && externalFactPassed) {

appendLog('Conjunctive Transparency conditions fully SATISFIED.');

appendLog('Emitting signed Proof-Carrying Output (PCO). Signature: Ed25519(CanonicalJSON)');


// Update local logs list dynamically with new mock success

const newLog: GenerationLog = {

id: logs.length + 1,

model_used: 'Neocortex-Chronos-V3-Hybrid',

prompt_hash: '9901ad85fbcbc073e51a602058066e3b0c44298fc1c149afbf4c8996fb92427f',

prompt_text: promptInput,

response_text: 'Verified state commit: C-T Validated PCO packaged.',

execution_time_ms: 310,

status: 'success',

created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)

};

setLogs(prev => [newLog, ...prev]);

} else {

appendLog('C-T Validation Failed. Rejecting state commit.');

}



setSimulationStep('Finished');

setIsSimulating(false);

};



return (

<div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] font-sans">

<Head>

<title>SCCS / ACE Control Panel & Platform Audit</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0" />

</Head>



{/* --- HEADER --- */}

<header className="border-b border-[#21262d] bg-[#161b22] px-6 py-4 flex flex-wrap items-center justify-between gap-4">

<div className="flex items-center gap-3">

<div className="w-4 h-4 rounded-full bg-[#238636] animate-pulse" />

<h1 className="text-xl font-bold tracking-tight text-[#f0f6fc]">

Sovereign Self-Correcting Cognitive System (SCCS)

</h1>

<span className="text-xs bg-[#21262d] px-2 py-1 rounded text-[#8b949e]">

v3.2.0-Sovereign

</span>

</div>



{/* Site Context Selector */}

<div className="flex items-center gap-2">

<label htmlFor="node-instance" className="text-xs text-[#8b949e] uppercase tracking-wider">Node Instance:</label>

<select

id="node-instance"

className="bg-[#0d1117] border border-[#30363d] text-[#c9d1d9] rounded px-3 py-1 text-sm focus:outline-none focus:border-[#58a6ff]"

value={activeSite?.id || ''}

onChange={(e) => {

const matched = sites.find(s => s.id === Number(e.target.value));

if (matched) setActiveSite(matched);

}}

>

{sites.map(s => (

<option key={s.id} value={s.id}>{s.domain}</option>

))}

</select>

</div>

</header>



<main className="p-6 grid grid-cols-1 xl:grid-cols-12 gap-6">

{/* ================= LEFT HALF: DEPLOYED SITES, CATEGORIES, & CONTENT ARCHITECTURE ================= */}

<section className="xl:col-span-7 flex flex-col gap-6">


{/* Active Site Configuration */}

<div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">

<h2 className="text-sm font-semibold uppercase text-[#8b949e] mb-4 tracking-wider">

Node Configuration Overview

</h2>

{activeSite ? (

<div className="grid grid-cols-1 md:grid-cols-3 gap-4">

<div className="bg-[#0d1117] p-3 rounded border border-[#21262d]">

<span className="text-xs text-[#8b949e] block">Logical Domain</span>

<span className="text-sm font-mono text-[#58a6ff]">{activeSite.domain}</span>

</div>

<div className="bg-[#0d1117] p-3 rounded border border-[#21262d]">

<span className="text-xs text-[#8b949e] block">State Engine Status</span>

<span className="text-sm font-mono text-[#3fb950]">Active SCCS Gate</span>

</div>

<div className="bg-[#0d1117] p-3 rounded border border-[#21262d]">

<span className="text-xs text-[#8b949e] block">Huber Target Delta</span>

<span className="text-sm font-mono text-[#e3b341]">

{JSON.parse(activeSite.config_json).huber_delta || 1.35}

</span>

</div>

</div>

) : (

<p className="text-sm text-[#8b949e]">No active site loaded.</p>

)}

</div>



{/* Categories Grid (Link Topology) */}

<div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">

<h2 className="text-sm font-semibold uppercase text-[#8b949e] mb-4 tracking-wider">

Category Matrix & Link Topology

</h2>

<div className="grid grid-cols-1 md:grid-cols-3 gap-3">

{categories.map(cat => (

<div key={cat.id} className="bg-[#0d1117] border border-[#30363d] p-4 rounded-md">

<div className="flex justify-between items-start mb-2">

<span className="text-xs text-[#8b949e] font-mono">ID: 0{cat.id}</span>

<span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${

cat.frequency_type === 'HF' ? 'bg-[#da3637] text-[#ff7b72]' :

cat.frequency_type === 'MF' ? 'bg-[#d29922] text-[#f8e3a1]' : 'bg-[#238636] text-[#56d364]'

}`}>

{cat.frequency_type} frequency

</span>

</div>

<h3 className="text-sm font-bold text-[#f0f6fc]">{cat.name}</h3>

<p className="text-xs text-[#8b949e] mt-1 font-mono">/{cat.slug}</p>

</div>

))}

</div>

</div>



{/* Articles Feed */}

<div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">

<h2 className="text-sm font-semibold uppercase text-[#8b949e] mb-4 tracking-wider">

Autonomous Content Feed (SCCS Verified PCOs)

</h2>

<div className="flex flex-col gap-3">

{articles.map(art => {

const metric = metrics[art.id];

return (

<button

key={art.id}

className={`w-full text-left border p-4 rounded-md transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#58a6ff] focus-visible:border-transparent ${

selectedArticle?.id === art.id

? 'bg-[#1f242c] border-[#58a6ff]'

: 'bg-[#0d1117] border-[#30363d] hover:bg-[#161b22]'

}`}

onClick={() => setSelectedArticle(art)}

>

<div className="flex flex-wrap justify-between items-center gap-2 mb-2">

<span className="text-xs text-[#58a6ff] font-mono bg-[#1f242c] px-2 py-0.5 rounded">

/{art.slug}

</span>

<div className="flex gap-2">

<span className="text-[10px] bg-[#238636]/20 text-[#56d364] px-2 py-0.5 rounded border border-[#238636]/40">

Logic: Valid

</span>

<span className="text-[10px] bg-[#238636]/20 text-[#56d364] px-2 py-0.5 rounded border border-[#238636]/40">

Fact: Verified

</span>

</div>

</div>



<h3 className="text-base font-bold text-[#f0f6fc] mb-1">{art.title}</h3>

<p className="text-sm text-[#8b949e] line-clamp-2">{art.summary}</p>



{metric && (

<div className="mt-3 pt-3 border-t border-[#21262d] flex flex-wrap gap-4 text-xs text-[#8b949e] font-mono">

<span>Views: <strong className="text-[#c9d1d9]">{metric.views}</strong></span>

<span>Clicks: <strong className="text-[#c9d1d9]">{metric.clicks}</strong></span>

<span>Avg Read: <strong className="text-[#c9d1d9]">{metric.avg_time_seconds}s</strong></span>

<span>Bounce: <strong className="text-[#ff7b72]">{Math.round(metric.bounce_rate * 100)}%</strong></span>

</div>

)}

</button>

);

})}

</div>

</div>



{/* Detailed Article Core Viewer */}

{selectedArticle && (

<div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">

<span className="text-xs uppercase text-[#8b949e] tracking-wider block mb-2">

Dynamic AST Blocks / Article Payload

</span>

<h2 className="text-xl font-bold text-[#f0f6fc] mb-4">{selectedArticle.title}</h2>


<div className="flex flex-col gap-4">

{selectedArticle.blocks?.map(blk => (

<div key={blk.id} className="p-4 bg-[#0d1117] rounded border border-[#21262d]">

<div className="flex justify-between items-center mb-2 border-b border-[#21262d] pb-2">

<span className="text-xs text-[#8b949e] font-mono uppercase">Block Type: {blk.block_type}</span>

<span className="text-xs text-[#8b949e] font-mono">Pos: {blk.position}</span>

</div>



{blk.block_type === 'code' ? (

<pre className="text-xs bg-[#161b22] p-3 rounded overflow-x-auto text-[#7ee787] font-mono">

<code>{blk.content}</code>

</pre>

) : blk.block_type === 'quote' ? (

<blockquote className="border-l-4 border-[#58a6ff] pl-3 italic text-[#8b949e]">

{blk.content}

</blockquote>

) : (

<p className="text-sm text-[#c9d1d9] leading-relaxed">{blk.content}</p>

)}

</div>

))}

</div>

</div>

)}



</section>



{/* ================= RIGHT HALF: SCCS VERIFICATION ENGINE & FORENSIC LOGS ================= */}

<section className="xl:col-span-5 flex flex-col gap-6">


{/* SCCS Verification Core Simulation Simulator */}

<div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">

<h2 className="text-sm font-semibold uppercase text-[#8b949e] mb-3 tracking-wider">

Verification Engine Simulation (System 0 &amp; 2)

</h2>



<div className="flex flex-col gap-4">

<div>

<label htmlFor="prompt-input" className="text-xs text-[#8b949e] block mb-1">Simulate Prompts Injection or Core Query:</label>

<textarea

id="prompt-input"

className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-sm text-[#c9d1d9] font-mono focus:outline-none focus:border-[#58a6ff] disabled:opacity-50 disabled:cursor-not-allowed"

rows={3}

value={promptInput}

onChange={(e) => setPromptInput(e.target.value)}

placeholder="Insert execution prompt..."


disabled={isSimulating}
/>

</div>



<div className="flex flex-wrap gap-2">

<button

className="bg-[#238636] hover:bg-[#2ea043] text-white font-bold py-2 px-4 rounded text-sm transition-all flex-1 disabled:opacity-50 disabled:cursor-not-allowed"

onClick={runVerificationSimulation}

disabled={isSimulating}

>

{isSimulating ? 'Processing Pulse...' : 'Execute Audit Pulse'}

</button>

<button

className="bg-[#30363d] hover:bg-[#8b949e]/20 text-[#c9d1d9] py-2 px-4 rounded text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"

onClick={() => {

setSimLog([]);

setCtStatus(null);

setSimEntropy(0.0);

setSimHuber(0.0);

setSimulationStep('Idle');

}}

disabled={isSimulating}

>

Clear Terminal

</button>

</div>



{/* Real-time Telemetry Monitor */}

<div className="grid grid-cols-2 gap-3">

<div className="bg-[#0d1117] border border-[#30363d] p-3 rounded">

<span className="text-xs text-[#8b949e] block">Shannon Entropy H(X)</span>

<span className={`text-lg font-mono font-bold ${simEntropy > 2.20 ? 'text-[#f85149]' : 'text-[#56d364]'}`}>

{simEntropy.toFixed(3)}

</span>

<span className="text-[10px] text-[#8b949e] block mt-1">Metacognitive Trigger: &gt; 2.20</span>

</div>



<div className="bg-[#0d1117] border border-[#30363d] p-3 rounded">

<span className="text-xs text-[#8b949e] block">Huber Residual Delta</span>

<span className={`text-lg font-mono font-bold ${simHuber > 0.10 ? 'text-[#ff7b72]' : 'text-[#58a6ff]'}`}>

{simHuber.toFixed(4)}

</span>

<span className="text-[10px] text-[#8b949e] block mt-1">Noise Target Delta: &lt; 0.100</span>

</div>

</div>



{/* Simulation Sequence Log Terminal */}

<div className="bg-[#0d1117] rounded-md border border-[#30363d] p-4">

<div className="flex justify-between items-center border-b border-[#21262d] pb-2 mb-3">

<span className="text-xs text-[#8b949e] uppercase font-mono tracking-wider">

SCCS Real-time Output Terminal

</span>

<span className="text-xs font-mono text-[#e3b341]">

{simulationStep}

</span>

</div>



<div className="h-64 overflow-y-auto font-mono text-xs text-[#39d353] flex flex-col gap-2" role="log" aria-live="polite">

{simLog.length === 0 ? (

<span className="text-[#8b949e] italic">[Terminal ready for verification execution pulse]</span>

) : (

simLog.map((logStr, i) => <div key={i}>{logStr}</div>)

)}

</div>



{ctStatus && (

<div className="mt-4 pt-4 border-t border-[#21262d] grid grid-cols-2 gap-3 text-xs font-mono">

<div className="flex items-center gap-2">

<span className="text-[#8b949e]">Internal Logic:</span>

<span className={ctStatus.logic ? 'text-[#36b356] font-bold' : 'text-[#f85149] font-bold'}>

{ctStatus.logic ? 'PASSED' : 'FAILED'}

</span>

</div>

<div className="flex items-center gap-2">

<span className="text-[#8b949e]">External Fact Check:</span>

<span className={ctStatus.fact ? 'text-[#36b356] font-bold' : 'text-[#f85149] font-bold'}>

{ctStatus.fact ? 'VERIFIED' : 'OUTLIER REJECT'}

</span>

</div>

</div>

)}

</div>

</div>

</div>



{/* Forensic Audit Generation Logs Ledger */}

<div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">

<h2 className="text-sm font-semibold uppercase text-[#8b949e] mb-4 tracking-wider">

Forensic Reasoning Ledger (L-E-J-D-A-S)

</h2>



<div className="flex flex-col gap-4 max-h-[450px] overflow-y-auto">

{logs.map(log => (

<div key={log.id} className="bg-[#0d1117] border border-[#21262d] p-3 rounded text-xs font-mono">

<div className="flex justify-between items-center mb-2 border-b border-[#21262d] pb-2 text-[#8b949e]">

<span>Log ID: {log.id}</span>

<span>{log.created_at}</span>

</div>



<p className="text-xs text-[#c9d1d9] mb-2 font-sans line-clamp-2">

<strong className="text-[#8b949e] font-mono">Prompt:</strong> {log.prompt_text}

</p>



<div className="space-y-1 text-[11px] text-[#8b949e]">

<div className="flex justify-between">

<span>Model Host:</span>

<span className="text-[#58a6ff]">{log.model_used}</span>

</div>

<div className="flex justify-between">

<span>Execution Time:</span>

<span className="text-[#7ee787]">{log.execution_time_ms} ms</span>

</div>

<div className="flex justify-between">

<span>Status Badge:</span>

<span className="text-[#3fb950] uppercase font-bold">{log.status}</span>

</div>

</div>



<div className="mt-2 bg-[#161b22] p-2 rounded border border-[#21262d] flex flex-col gap-1 text-[10px] text-[#8b949e]">

<div className="truncate">

<strong>Prompt Hash:</strong> <span className="text-[#e3b341]">{log.prompt_hash}</span>

</div>

<div className="truncate">

<strong>Merkle Root:</strong> <span className="text-[#e3b341]">0xae77d01bc1e34cb9de3347c617e9...</span>

</div>

</div>

</div>

))}

</div>

</div>



</section>

</main>



{/* --- FOOTER --- */}

<footer className="border-t border-[#21262d] bg-[#161b22] py-4 text-center text-xs text-[#8b949e] font-mono">

&copy; 2026 SCCS-ACE PLATFORM // CONJUNCTIVE TRANSPARENCY PROTOCOLS // ALL STATES RECORDED UNDER WRITE-SIDE CUSTODY

</footer>

</div>

);

}
