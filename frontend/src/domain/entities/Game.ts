export interface RuleSection {
  title: string
  steps: string[]
}

export interface GameRules {
  summary: string
  players?: string
  equipment?: string
  sections: RuleSection[]
}

export interface Game {
  id: string
  title: string
  description: string
  rules: GameRules
}
