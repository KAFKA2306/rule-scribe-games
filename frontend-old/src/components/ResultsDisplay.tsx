import { AlertCircle, Lightbulb } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { GameCard, Game } from './GameCard';

interface ResultsDisplayProps {
  results: Game[];
  isLoading: boolean;
  error: string | null;
  query: string;
}

export const ResultsDisplay = ({ results, isLoading, error, query }: ResultsDisplayProps) => {
  // Loading state
  if (isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto px-6 mt-12">
        <div className="text-center">
          <div className="animate-pulse">
            <div className="h-32 bg-muted/30 rounded-xl mb-6"></div>
            <div className="h-24 bg-muted/30 rounded-xl mb-4"></div>
            <div className="h-24 bg-muted/30 rounded-xl"></div>
          </div>
          <p className="text-lg text-muted-foreground mt-6">
            「{query}」を検索しています...
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto px-6 mt-12">
        <Alert className="border-destructive/50 bg-destructive/10">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-foreground">
            <strong>検索エラー:</strong> {error}
          </AlertDescription>
        </Alert>

        <div className="mt-8 text-center">
          <div className="bg-muted/20 rounded-xl p-6">
            <Lightbulb className="w-8 h-8 text-primary mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-foreground mb-2">検索のヒント</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• ゲームの正式名称で検索してみてください</li>
              <li>• ひらがな・カタカナ・漢字を変えて試してみてください</li>
              <li>• 英語名でも検索できます</li>
              <li>• 略称や愛称でも見つかることがあります</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // No results yet (initial state)
  if (!query) {
    return null;
  }

  // Empty results
  if (results.length === 0) {
    return (
      <div className="w-full max-w-4xl mx-auto px-6 mt-12">
        <div className="text-center">
          <div className="bg-muted/20 rounded-xl p-8">
            <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">
              「{query}」の検索結果が見つかりませんでした
            </h3>
            <p className="text-muted-foreground mb-6">
              このゲームはまだデータベースに登録されていません。
            </p>
            
            <div className="bg-primary/10 rounded-lg p-4 border border-primary/20">
              <Lightbulb className="w-6 h-6 text-primary mx-auto mb-2" />
              <p className="text-sm text-foreground">
                <strong>近日追加予定:</strong> 未登録のゲームも自動的に検索・要約する機能を開発中です。
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Results found
  return (
    <div className="w-full max-w-4xl mx-auto px-6 mt-12">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          検索結果
        </h2>
        <p className="text-muted-foreground">
          「{query}」で{results.length}件のゲームが見つかりました
        </p>
      </div>

      <div className="space-y-6">
        {results.map((game, index) => (
          <GameCard 
            key={game.game_id} 
            game={game} 
            index={index}
          />
        ))}
      </div>

      {/* Feedback Section */}
      <div className="mt-12 text-center">
        <div className="bg-muted/20 rounded-xl p-6">
          <p className="text-sm text-muted-foreground">
            より正確な情報やルールの改善提案がございましたら、
            <a href="#" className="text-primary hover:underline ml-1">
              フィードバックをお寄せください
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};