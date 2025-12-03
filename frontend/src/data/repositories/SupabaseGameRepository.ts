import { GameRepository } from '../../domain/repositories/GameRepository'
import { Game } from '../../domain/entities/Game'
import { GameRulesSchema } from '../../domain/schemas/GameRulesSchema'
import { supabase } from '../sources/supabaseClient'

export class SupabaseGameRepository implements GameRepository {
  private mapToGameRules(row: any): any {
    if (row.structured_data) {
      const sd = row.structured_data
      // Helper to format players
      let playersStr = ''
      if (sd.players) {
        if (typeof sd.players === 'string') playersStr = sd.players
        else if (typeof sd.players === 'object') {
          playersStr = `${sd.players.min}-${sd.players.max} players`
        }
      }

      // Helper to format equipment
      let equipment: string | string[] = []
      if (Array.isArray(sd.components)) {
        equipment = sd.components.map((c: any) =>
          typeof c === 'string' ? c : `${c.count ? c.count + 'x ' : ''}${c.name}`
        )
      }

      // Build sections
      const sections = []
      if (sd.setup_instructions && Array.isArray(sd.setup_instructions)) {
        sections.push({ title: 'Setup', steps: sd.setup_instructions })
      }
      if (sd.winning_condition) {
        sections.push({ title: 'Victory Condition', steps: [sd.winning_condition] })
      }
      if (sections.length === 0 && row.rules_content) {
        sections.push({ title: 'Rules', steps: [row.rules_content] })
      }

      return {
        summary: sd.summary || row.description || 'No summary',
        players: playersStr,
        equipment: equipment,
        sections: sections,
      }
    }
    // Fallback to old rules column
    return row.rules
  }

  async getGames(): Promise<Game[]> {
    const { data, error } = await supabase
      .from('games')
      .select('id, title, description, rules, structured_data, rules_content')

    if (error) {
      throw new Error(error.message)
    }

    return data.map((row: any) => {
      try {
        const rawRules = this.mapToGameRules(row)
        const rules = GameRulesSchema.parse(rawRules)
        return {
          id: row.id,
          title: row.title,
          description: row.description,
          rules: rules,
        }
      } catch (e) {
        console.error(`Failed to parse rules for game ${row.id}: `, e)
        return {
          id: row.id,
          title: row.title,
          description: row.description,
          rules: { summary: 'Error loading rules', sections: [] },
        }
      }
    })
  }

  async getGameById(id: string): Promise<Game | null> {
    const { data, error } = await supabase
      .from('games')
      .select('id, title, description, rules, structured_data, rules_content')
      .eq('id', id)
      .single()

    if (error) {
      return null
    }

    try {
      const rawRules = this.mapToGameRules(data)
      const rules = GameRulesSchema.parse(rawRules)
      return {
        id: data.id,
        title: data.title,
        description: data.description,
        rules: rules,
      }
    } catch (e) {
      console.error(`Failed to parse rules for game ${id}: `, e)
      return {
        id: data.id,
        title: data.title,
        description: data.description,
        rules: { summary: 'Error loading rules', sections: [] },
      }
    }
  }

  async searchGames(query: string): Promise<Game[]> {
    const { data, error } = await supabase
      .from('games')
      .select('id, title, description, rules, structured_data, rules_content')
      .or(`title.ilike.%${query}%,description.ilike.%${query}%`)

    if (error) {
      throw new Error(error.message)
    }

    return data.map((row: any) => {
      try {
        const rawRules = this.mapToGameRules(row)
        const rules = GameRulesSchema.parse(rawRules)
        return {
          id: row.id,
          title: row.title,
          description: row.description,
          rules: rules,
        }
      } catch (e) {
        console.error(`Failed to parse rules for game ${row.id}:`, e)
        return {
          id: row.id,
          title: row.title,
          description: row.description,
          rules: { summary: 'Error loading rules', sections: [] },
        }
      }
    })
  }

  async generateGame(title: string): Promise<Game> {
    // Call Python Backend via Vite Proxy
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: title }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Python Backend Error:', errorText)
      throw new Error(`Failed to generate game: ${response.statusText}`)
    }

    const results = await response.json()
    if (!results || results.length === 0) {
      throw new Error('No game found or generated')
    }

    const data = results[0]

    // Map Python Backend structure to Frontend Game entity
    // structured_data: { summary, players, components, setup_instructions, winning_condition, ... }
    const sd = data.structured_data || {}

    // Helper to format players
    let playersStr = ''
    if (sd.players) {
      if (typeof sd.players === 'string') playersStr = sd.players
      else if (typeof sd.players === 'object') {
        playersStr = `${sd.players.min}-${sd.players.max} players`
      }
    }

    // Helper to format equipment/components
    let equipment: string | string[] = []
    if (Array.isArray(sd.components)) {
      equipment = sd.components.map((c: any) =>
        typeof c === 'string' ? c : `${c.count ? c.count + 'x ' : ''}${c.name}`
      )
    }

    // Build sections
    const sections = []

    if (sd.setup_instructions && Array.isArray(sd.setup_instructions)) {
      sections.push({
        title: 'Setup',
        steps: sd.setup_instructions,
      })
    }

    if (sd.winning_condition) {
      sections.push({
        title: 'Victory Condition',
        steps: [sd.winning_condition],
      })
    }

    // Fallback: if no structured sections, use rules_content as a raw section
    if (sections.length === 0 && data.rules_content) {
      sections.push({
        title: 'Rules',
        steps: [data.rules_content],
      })
    }

    const rules = {
      summary: sd.summary || data.description || 'No summary available',
      players: playersStr,
      equipment: equipment,
      sections: sections,
    }

    // Validate with Zod to be safe, though we constructed it manually
    const validatedRules = GameRulesSchema.parse(rules)

    return {
      id: String(data.id),
      title: data.title,
      description: data.description || '',
      rules: validatedRules,
    }
  }
}
