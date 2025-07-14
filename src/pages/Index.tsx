import { SearchInterface } from '@/components/SearchInterface';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { useGameSearch } from '@/hooks/useGameSearch';
import heroImage from '@/assets/hero-boardgames.jpg';

const Index = () => {
  const { results, isLoading, error, search, query } = useGameSearch();

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-10"
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/90 to-background" />
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        {/* Header Section */}
        <header className="pt-20 pb-12">
          <SearchInterface onSearch={search} isLoading={isLoading} />
        </header>

        {/* Results Section */}
        <main>
          <ResultsDisplay 
            results={results}
            isLoading={isLoading}
            error={error?.message || null}
            query={query}
          />
        </main>

        {/* Footer */}
        <footer className="mt-20 py-8 text-center text-sm text-muted-foreground border-t border-border/20">
          <p>
            © 2024 ボードゲームルール検索プラットフォーム - 
            すべてのゲーマーのために
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Index;
