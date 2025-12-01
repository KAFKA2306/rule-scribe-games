import { Game } from '@/components/GameCard';
import { searchGames as searchMockGames } from '@/data/mockGames';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true' || false;

export class GameService {
  private static instance: GameService;

  public static getInstance(): GameService {
    if (!GameService.instance) {
      GameService.instance = new GameService();
    }
    return GameService.instance;
  }

  async searchGames(query: string): Promise<Game[]> {
    if (!query.trim()) {
      return [];
    }

    // Use mock data for demo purposes
    if (USE_MOCK_DATA) {
      return searchMockGames(query);
    }

    // Production API call
    try {
      const response = await fetch(
        `${API_BASE_URL}/search?q=${encodeURIComponent(query)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        if (response.status === 404) {
          return [];
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: 検索に失敗しました`);
      }

      const games = await response.json();
      return games;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        // Fallback to mock data if API is unavailable
        console.warn('API unavailable, falling back to mock data');
        return searchMockGames(query);
      }
      throw error;
    }
  }

  // Future: AI-powered search for unindexed games
  async searchUnindexedGame(query: string): Promise<Game | null> {
    // Placeholder for future implementation
    // This would integrate with LLM services to search and summarize rules
    console.log('Future feature: AI search for', query);
    return null;
  }

  // Future: Submit new game for indexing
  async submitGameForIndexing(gameData: Partial<Game>): Promise<void> {
    // Placeholder for future implementation
    console.log('Future feature: Submit game', gameData);
  }
}

export const gameService = GameService.getInstance();