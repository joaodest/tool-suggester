import React from 'react';
import { Tool } from '../types';

interface SuggestionItemProps {
  tool: Tool;
  onClick: (tool: Tool) => void;
}

export const SuggestionItem: React.FC<SuggestionItemProps> = ({ tool, onClick }) => {
  return (
    <div
      onClick={() => onClick(tool)}
      className="group relative flex items-center gap-3 p-3 bg-slate-800/50 border border-slate-700/50 rounded-xl 
                 hover:bg-indigo-600/20 hover:border-indigo-500/50 transition-all duration-200 cursor-pointer backdrop-blur-md"
    >
      {/* Icon Placeholder */}
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
        </svg>
      </div>

      <div className="flex-grow min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold text-slate-200 group-hover:text-indigo-200 truncate">
            {tool.name}
          </h4>
          <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400 group-hover:bg-indigo-900/50 group-hover:text-indigo-300">
            {tool.category}
          </span>
        </div>
        
        {/* Description - normally truncated, full on hover via tooltip or expansion */}
        <p className="text-xs text-slate-400 truncate group-hover:text-slate-300 transition-colors">
           {tool.description}
        </p>
      </div>

      {/* Hover Detail Tooltip (Visual enhancement) */}
      <div className="absolute bottom-full left-0 mb-2 w-64 bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl 
                      opacity-0 group-hover:opacity-100 invisible group-hover:visible transition-all duration-200 pointer-events-none z-50 translate-y-2 group-hover:translate-y-0">
        <p className="text-xs font-bold text-indigo-400 mb-1">Function Signature</p>
        <code className="block text-xs font-mono text-slate-300 bg-slate-950 p-1.5 rounded mb-2">
          {tool.name}(params...)
        </code>
        <p className="text-xs text-slate-400 leading-relaxed">
          {tool.description}
        </p>
      </div>
    </div>
  );
};
