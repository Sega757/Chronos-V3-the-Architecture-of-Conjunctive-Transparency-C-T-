import React from 'react';
import Head from 'next/head';
import { GetServerSideProps } from 'next';
import { renderBlock } from '../../lib/renderer';

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
  category_name: string;
  published_at: string;
  blocks: ArticleBlock[];
}

interface Props {
  article: Article | null;
  error?: string;
}

export default function ArticleODR({ article, error }: Props) {
  if (error || !article) {
    return (
      <div className="min-h-screen bg-[#0d1117] text-[#f85149] font-sans p-6">
        <h1 className="text-xl font-bold">Error 404: Knowledge Object Not Found</h1>
        <p>{error || "Article does not exist."}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] font-sans p-6 max-w-4xl mx-auto">
      <Head>
        <title>{article.title} - SCCS / ACE</title>
      </Head>

      <header className="mb-8 border-b border-[#21262d] pb-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-mono bg-[#1f242c] text-[#58a6ff] px-2 py-1 rounded">
            {article.category_name}
          </span>
          <span className="text-xs text-[#8b949e]">
            {new Date(article.published_at).toLocaleString()}
          </span>
        </div>
        <h1 className="text-3xl font-bold text-[#f0f6fc] mb-3">{article.title}</h1>
        <p className="text-lg text-[#8b949e]">{article.summary}</p>
      </header>

      <main className="flex flex-col gap-6">
        {article.blocks.map((block) => (
          <div key={block.id} className="article-block">
            {renderBlock(block)}
          </div>
        ))}
      </main>

      <footer className="mt-12 pt-6 border-t border-[#21262d] text-center text-xs text-[#8b949e] font-mono">
         &copy; 2026 SCCS-ACE PLATFORM // CONJUNCTIVE TRANSPARENCY PROTOCOLS
      </footer>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { slug } = context.params as { slug: string };
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://backend:3000/api';

  try {
    // Determine host. If running locally vs docker.
    // For SSR, backend container name usually works if in same docker network.
    // Fallback to localhost if not found
    let fetchUrl = `${apiUrl}/articles/slug/${slug}`;
    if (process.env.NODE_ENV !== 'production' && typeof window === 'undefined') {
       fetchUrl = `http://localhost:3000/api/articles/slug/${slug}`;
    }

    const res = await fetch(fetchUrl);

    if (!res.ok) {
      return { props: { article: null, error: 'Article not found.' } };
    }

    const article: Article = await res.json();
    return { props: { article } };
  } catch (err: any) {
    console.error("Fetch error:", err);
    return { props: { article: null, error: 'Internal Server Error fetching data.' } };
  }
};
