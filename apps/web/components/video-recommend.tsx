"use client";

import React, { useEffect, useState } from "react";
import { PlayCircle, Video } from "lucide-react";

interface VideoData {
  bvid: string;
  title: string;
  pic: string;
  author: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function VideoRecommend({ keyword }: { keyword: string }) {
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeVideo, setActiveVideo] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/resources/bilibili/search?keyword=${encodeURIComponent(keyword)}`)
      .then(res => res.json())
      .then(data => {
        setVideos(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to search bilibili:", err);
        setLoading(false);
      });
  }, [keyword]);

  if (loading) {
    return (
      <div className="my-4 p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] flex flex-col items-center justify-center animate-pulse gap-2">
        <Video className="w-6 h-6 text-[#617a55]/50" />
        <span className="text-sm text-[#757a6b]">正在藏经阁中检索推荐视频...</span>
      </div>
    );
  }

  if (videos.length === 0) {
    return null;
  }

  return (
    <div className="my-6 space-y-3">
      <div className="flex items-center gap-2 text-sm font-bold text-[#617a55] border-b border-[#617a55]/20 pb-2">
        <PlayCircle className="w-4 h-4" />
        推荐视听讲解 (Top 3)
      </div>
      
      {activeVideo ? (
        <div className="relative w-full overflow-hidden rounded-xl border border-[#d6d0ba] shadow-lg bg-black" style={{ paddingTop: '56.25%' }}>
          <iframe 
            src={`https://player.bilibili.com/player.html?bvid=${activeVideo}&high_quality=1&danmaku=0&autoplay=1`} 
            className="absolute top-0 left-0 w-full h-full border-0"
            referrerPolicy="no-referrer"
            sandbox="allow-top-navigation allow-same-origin allow-forms allow-scripts allow-popups"
            allowFullScreen
          />
          <button 
            onClick={() => setActiveVideo(null)}
            className="absolute top-2 right-2 z-10 bg-black/60 text-white px-3 py-1 rounded-full text-xs hover:bg-black/80 transition"
          >
            关闭播放
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {videos.map(v => (
            <div 
              key={v.bvid} 
              className="group cursor-pointer flex flex-col rounded-xl overflow-hidden border border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-[#617a55] hover:shadow-md transition-all relative"
              onClick={() => setActiveVideo(v.bvid)}
            >
              <div className="relative w-full aspect-video bg-black/10 overflow-hidden">
                <img src={v.pic} alt={v.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90" referrerPolicy="no-referrer" />
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity">
                  <PlayCircle className="w-10 h-10 text-white drop-shadow-lg" />
                </div>
              </div>
              <div className="p-3">
                <div className="text-xs font-bold line-clamp-2 leading-tight text-[var(--text-primary)] mb-1" dangerouslySetInnerHTML={{ __html: v.title }} />
                <div className="text-[10px] text-[var(--text-muted)] truncate">{v.author}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
