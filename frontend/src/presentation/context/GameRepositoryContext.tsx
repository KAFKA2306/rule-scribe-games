import React, { createContext, useContext, ReactNode } from 'react'
import { GameRepository } from '../../domain/repositories/GameRepository'
import { SupabaseGameRepository } from '../../data/repositories/SupabaseGameRepository'

const GameRepositoryContext = createContext<GameRepository | null>(null)

interface Props {
  children: ReactNode
  repository?: GameRepository
}

export const GameRepositoryProvider: React.FC<Props> = ({ children, repository }) => {
  // Default to Supabase implementation if not provided (allows for easy testing overrides)
  const repo = repository || new SupabaseGameRepository()

  return <GameRepositoryContext.Provider value={repo}>{children}</GameRepositoryContext.Provider>
}

export const useGameRepository = (): GameRepository => {
  const context = useContext(GameRepositoryContext)
  if (!context) {
    throw new Error('useGameRepository must be used within a GameRepositoryProvider')
  }
  return context
}
