import { useState } from 'react';
import { Users, Clock, Tag, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

export interface Game {
  game_id: string;
  title: string;
  player_count: string;
  play_time: number;
  genre: string[];
  markdown_rules: string;
  image_url?: string;
  bgg_link?: string;
}

interface GameCardProps {
  game: Game;
  index: number;
}

export const GameCard = ({ game, index }: GameCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card 
      className="group hover:shadow-game-card transition-all duration-300 hover:-translate-y-1 bg-gradient-card border-border/50 animate-slide-up"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-2xl font-bold text-foreground group-hover:text-primary transition-colors duration-200">
              {game.title}
            </h3>
            
            {/* Game Metadata */}
            <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                <span>{game.player_count}人</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>{game.play_time}分</span>
              </div>
              {game.bgg_link && (
                <a 
                  href={game.bgg_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 hover:text-primary transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>BGG</span>
                </a>
              )}
            </div>

            {/* Genre Tags */}
            <div className="flex flex-wrap gap-2 mt-3">
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Tag className="w-4 h-4" />
                <span>ジャンル:</span>
              </div>
              {game.genre.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          {game.image_url && (
            <div className="flex-shrink-0">
              <img 
                src={game.image_url}
                alt={`${game.title}のボックスアート`}
                className="w-20 h-20 rounded-lg object-cover border border-border/50"
              />
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          <CollapsibleTrigger asChild>
            <Button 
              variant="outline" 
              className="w-full justify-between hover:bg-primary hover:text-primary-foreground transition-colors duration-200"
            >
              <span className="font-medium">
                {isExpanded ? 'ルール要約を隠す' : 'ルール要約を表示'}
              </span>
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          
          <CollapsibleContent className="mt-4">
            <div className="bg-muted/30 rounded-xl p-6 border border-border/30">
              <div 
                className="prose prose-invert max-w-none text-sm leading-relaxed"
                dangerouslySetInnerHTML={{ 
                  __html: formatMarkdownToHTML(game.markdown_rules) 
                }}
              />
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
};

// Simple markdown to HTML converter for basic formatting
function formatMarkdownToHTML(markdown: string): string {
  return markdown
    // Headers
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-primary mb-2 mt-4 first:mt-0">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold text-foreground mb-3 mt-5 first:mt-0">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-foreground mb-4 mt-6 first:mt-0">$1</h1>')
    // Bold and italic
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-foreground">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
    // Lists
    .replace(/^\-\s+(.*)$/gim, '<li class="ml-4 mb-1">• $1</li>')
    .replace(/^\d+\.\s+(.*)$/gim, '<li class="ml-4 mb-1 list-decimal">$1</li>')
    // Paragraphs
    .replace(/\n\n/g, '</p><p class="mb-3">')
    .replace(/^(.+)$/gm, '<p class="mb-3">$1</p>')
    // Clean up
    .replace(/<p class="mb-3"><\/p>/g, '')
    .replace(/<p class="mb-3">(<h[1-6])/g, '$1')
    .replace(/(<\/h[1-6]>)<\/p>/g, '$1');
}