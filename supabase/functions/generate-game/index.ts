import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const { title } = await req.json()
        if (!title) throw new Error('Title is required')

        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        const geminiApiKey = Deno.env.get('GEMINI_API_KEY') ?? 'AIzaSyBv_Q2UJZWicqXjDCMLf9cSgNslv9mOw_U'

        if (!geminiApiKey) {
            throw new Error('GEMINI_API_KEY is not set')
        }

        // Initialize Supabase Client
        const supabaseClient = createClient(supabaseUrl, supabaseServiceKey)

        console.log('Request received for title:', title);
        console.log('GEMINI_API_KEY present:', !!geminiApiKey);

        // Call Google Gemini API
        // Model: gemini-2.5-flash (User requested always)
        const modelName = 'gemini-2.5-flash'
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${geminiApiKey}`

        const systemPrompt = `You are a board game expert. Generate a JSON object for the requested game with the following structure:
    {
      "summary": "Short description in Japanese",
      "players": "e.g. 2-4 players (in Japanese)",
      "equipment": "List of items (in Japanese)",
      "sections": [
        { "title": "Section Title (in Japanese)", "steps": ["Step 1 (in Japanese)", "Step 2 (in Japanese)"] }
      ]
    }
    Return ONLY the JSON. Do not include markdown formatting or backticks. Ensure all text values are in Japanese.`

        console.log('Calling Gemini API:', modelName);

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: `${systemPrompt}\n\nGenerate rules for: ${title}`
                    }]
                }]
            })
        })

        console.log('Gemini API Status:', response.status);
        const data = await response.json()

        if (data.error) {
            console.error('Gemini API Error Details:', JSON.stringify(data.error));
            throw new Error(`Gemini API Error: ${data.error.message}`)
        }

        // Parse Gemini Response
        // Structure: data.candidates[0].content.parts[0].text
        const content = data.candidates?.[0]?.content?.parts?.[0]?.text
        if (!content) {
            throw new Error('No content returned from Gemini')
        }

        // Clean up potential markdown code blocks
        const cleanContent = content.replace(/^```json\n/, '').replace(/\n```$/, '').trim()
        const rules = JSON.parse(cleanContent)

        // Upsert into Supabase
        const { data: existingGame } = await supabaseClient
            .from('games')
            .select('id')
            .eq('title', title)
            .single()

        const gameData = {
            title: title,
            description: rules.summary,
            rules: rules,
        }

        let result
        if (existingGame) {
            result = await supabaseClient
                .from('games')
                .update(gameData)
                .eq('id', existingGame.id)
                .select()
                .single()
        } else {
            result = await supabaseClient
                .from('games')
                .insert(gameData)
                .select()
                .single()
        }

        if (result.error) throw result.error

        return new Response(JSON.stringify(result.data), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
        })

    } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400,
        })
    }
})
