import { useState } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface SearchInterfaceProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export const SearchInterface = ({ onSearch, isLoading }: SearchInterfaceProps) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-6">
      {/* Hero Section */}
      <div className="text-center mb-12 animate-slide-up">
        <div className="flex items-center justify-center gap-3 mb-6">
          <Sparkles className="w-8 h-8 text-primary animate-pulse-glow" />
          <h1 className="text-5xl md:text-6xl font-bold bg-gradient-hero bg-clip-text text-transparent">
            ボードゲーム
          </h1>
          <Sparkles className="w-8 h-8 text-primary animate-pulse-glow" />
        </div>
        <h2 className="text-3xl md:text-4xl font-semibold text-foreground mb-4">
          ルール検索プラットフォーム
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          世界中のボードゲームルールを瞬時に検索し、AIが要約した分かりやすいルールを確認できます。
          3秒でゲームを始められる体験を提供します。
        </p>
      </div>

      {/* Search Box */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative group">
          <div className="absolute inset-0 bg-gradient-hero rounded-2xl blur-xl opacity-20 group-hover:opacity-30 transition-opacity duration-300" />
          <div className="relative bg-card rounded-2xl p-2 shadow-search border border-border/50">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 p-3">
                <Search className="w-6 h-6 text-primary" />
              </div>
              
              <Input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="ゲームタイトルを入力（例：カタンの開拓者たち、ドミニオン）"
                className="flex-1 border-0 bg-transparent text-lg placeholder:text-muted-foreground focus:ring-0 focus:outline-none"
                disabled={isLoading}
              />
              
              <Button
                type="submit"
                disabled={!query.trim() || isLoading}
                className="px-8 py-3 text-lg font-semibold bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl transition-all duration-300 hover:shadow-glow hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    検索中
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    検索
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </form>

      {/* Quick Suggestions */}
      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground mb-4">人気のゲーム:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {['カタンの開拓者たち', 'ドミニオン', 'アズール', 'ウイングスパン', 'スプレンダー'].map((suggestion) => (
            <Button
              key={suggestion}
              variant="outline"
              size="sm"
              onClick={() => {
                setQuery(suggestion);
                onSearch(suggestion);
              }}
              disabled={isLoading}
              className="text-sm hover:bg-primary hover:text-primary-foreground transition-colors duration-200"
            >
              {suggestion}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};