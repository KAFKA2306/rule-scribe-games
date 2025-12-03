import { Game } from '../entities/Game'

export interface GameRepository {
  getGames(): Promise<Game[]>
  getGameById(id: string): Promise<Game | null>
  searchGames(query: string): Promise<Game[]>
  generateGame(title: string): Promise<Game>
}
