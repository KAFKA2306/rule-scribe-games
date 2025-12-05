import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://wazgoplarevypdfbgeau.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhemdvcGxhcmV2eXBkZmJnZWF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1ODU2MzAsImV4cCI6MjA4MDE2MTYzMH0.jxM3I8Tul-YszD6rd8asfpqHZCHo1bInScdK74d2s5I'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
