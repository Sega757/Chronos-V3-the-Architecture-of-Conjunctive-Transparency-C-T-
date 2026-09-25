import React from 'react';

export function renderBlock(block: any) {
    switch (block.block_type) {
        case 'text':
            return <p className="text-base text-[#c9d1d9] leading-relaxed">{block.content}</p>;
        case 'code':
            return (
                <div className="bg-[#161b22] border border-[#30363d] rounded-md p-4 overflow-x-auto">
                    <pre className="text-sm font-mono text-[#7ee787]">
                        <code>{block.content}</code>
                    </pre>
                </div>
            );
        case 'quote':
            return (
                <blockquote className="border-l-4 border-[#58a6ff] pl-4 italic text-[#8b949e] my-4">
                    {block.content}
                </blockquote>
            );
        case 'image':
            // content could be an image URL
            return (
                <div className="my-4 border border-[#30363d] rounded-md overflow-hidden">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    {/* ⚡ Bolt: Lazy load assets for better initial page performance */}
                    <img src={block.content} alt="Article graphic" className="w-full h-auto object-cover" loading="lazy" />
                </div>
            );
        case 'links':
            // assume content is comma separated or JSON string array
            return (
                <div className="bg-[#0d1117] border border-[#30363d] p-3 rounded text-sm text-[#58a6ff]">
                    References: {block.content}
                </div>
            );
        case 'youtube':
            return (
                <div className="aspect-w-16 aspect-h-9 my-4">
                    {/* ⚡ Bolt: Lazy load assets for better initial page performance */}
                    <iframe
                        src={block.content}
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                        loading="lazy"
                        className="w-full h-64 rounded-md border border-[#30363d]"
                    ></iframe>
                </div>
            );
        default:
            return <p className="text-[#c9d1d9]">{block.content}</p>;
    }
}
