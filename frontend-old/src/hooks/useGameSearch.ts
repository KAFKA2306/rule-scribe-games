import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { gameService } from '@/services/gameService';
import { Game } from '@/components/GameCard';

export const useGameSearch = () => {
  const [query, setQuery] = useState('');
  const [isSearchTriggered, setIsSearchTriggered] = useState(false);

  const {
    data: results = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['games', query],
    queryFn: () => gameService.searchGames(query),
    enabled: isSearchTriggered && !!query.trim(),
    retry: (failureCount, error) => {
      // Don't retry if it's a 404 (no results found)
      if (error instanceof Error && error.message.includes('404')) {
        return false;
      }
      return failureCount < 2;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  const search = useCallback((searchQuery: string) => {
    setQuery(searchQuery.trim());
    setIsSearchTriggered(true);
  }, []);

  const reset = useCallback(() => {
    setQuery('');
    setIsSearchTriggered(false);
  }, []);

  return {
    results: results as Game[],
    isLoading,
    error: error as Error | null,
    search,
    reset,
    refetch,
    query,
  };
};