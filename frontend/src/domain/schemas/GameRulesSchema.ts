import { z } from 'zod'

export const RuleSectionSchema = z.object({
  title: z.string(),
  steps: z.array(z.string()),
})

export const GameRulesSchema = z.object({
  summary: z.string(),
  players: z.string().optional(),
  equipment: z
    .union([z.string(), z.array(z.string()).transform((val) => val.join(', '))])
    .optional(),
  sections: z.array(RuleSectionSchema),
})

export type GameRules = z.infer<typeof GameRulesSchema>
