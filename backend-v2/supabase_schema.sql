-- RuleScribe v2 Supabase Database Schema
-- This file contains the SQL schema for setting up the database in Supabase

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Games table - Core game information
CREATE TABLE games (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    rules_content TEXT,
    player_count_min INTEGER,
    player_count_max INTEGER,
    play_time_min INTEGER, -- in minutes
    play_time_max INTEGER, -- in minutes
    complexity DECIMAL(3,2), -- 1.0 to 5.0 scale
    year_published INTEGER,
    rating DECIMAL(3,2), -- 1.0 to 5.0 scale
    genres JSONB DEFAULT '[]',
    mechanics JSONB DEFAULT '[]',
    image_url TEXT,
    bgg_id INTEGER UNIQUE, -- BoardGameGeek ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table - User profiles
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User favorites - Track user's favorite games
CREATE TABLE user_favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, game_id)
);

-- Search analytics - Track search behavior and performance
CREATE TABLE search_analytics (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    query TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    processing_time_ms DECIMAL(10,2),
    search_metadata JSONB DEFAULT '{}',
    filters_applied JSONB DEFAULT '{}',
    clicked_results JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game embeddings - Vector embeddings for semantic search
CREATE TABLE game_embeddings (
    id BIGSERIAL PRIMARY KEY,
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL, -- 'title', 'description', 'rules', 'full'
    content_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 embedding size
    chunk_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game reviews - User reviews and ratings
CREATE TABLE game_reviews (
    id BIGSERIAL PRIMARY KEY,
    game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Game collections - User-created game collections
CREATE TABLE game_collections (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    game_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI processing jobs - Track AI summarization and processing tasks
CREATE TABLE ai_processing_jobs (
    id BIGSERIAL PRIMARY KEY,
    game_id BIGINT REFERENCES games(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'summarize', 'extract', 'embed'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    ai_provider VARCHAR(50), -- 'openai', 'anthropic', 'google'
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX idx_games_title ON games USING GIN (title gin_trgm_ops);
CREATE INDEX idx_games_genres ON games USING GIN (genres);
CREATE INDEX idx_games_mechanics ON games USING GIN (mechanics);
CREATE INDEX idx_games_rating ON games(rating);
CREATE INDEX idx_games_complexity ON games(complexity);
CREATE INDEX idx_games_player_count ON games(player_count_min, player_count_max);
CREATE INDEX idx_games_play_time ON games(play_time_min, play_time_max);
CREATE INDEX idx_games_created_at ON games(created_at);

CREATE INDEX idx_search_analytics_user_id ON search_analytics(user_id);
CREATE INDEX idx_search_analytics_created_at ON search_analytics(created_at);
CREATE INDEX idx_search_analytics_query ON search_analytics USING GIN (query gin_trgm_ops);

CREATE INDEX idx_game_embeddings_game_id ON game_embeddings(game_id);
CREATE INDEX idx_game_embeddings_content_type ON game_embeddings(content_type);
CREATE INDEX idx_game_embeddings_vector ON game_embeddings USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_game_id ON user_favorites(game_id);

CREATE INDEX idx_game_reviews_game_id ON game_reviews(game_id);
CREATE INDEX idx_game_reviews_user_id ON game_reviews(user_id);
CREATE INDEX idx_game_reviews_rating ON game_reviews(rating);

-- Create RLS (Row Level Security) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_analytics ENABLE ROW LEVEL SECURITY;

-- Users can read their own data
CREATE POLICY "Users can read own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Favorites policies
CREATE POLICY "Users can manage own favorites" ON user_favorites
    FOR ALL USING (auth.uid() = user_id);

-- Reviews policies
CREATE POLICY "Users can manage own reviews" ON game_reviews
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Anyone can read reviews" ON game_reviews
    FOR SELECT USING (true);

-- Collections policies
CREATE POLICY "Users can manage own collections" ON game_collections
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Anyone can read public collections" ON game_collections
    FOR SELECT USING (is_public = true OR auth.uid() = user_id);

-- Search analytics policies (users can only see their own)
CREATE POLICY "Users can read own search analytics" ON search_analytics
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

-- Public tables (no RLS needed)
-- games, game_embeddings, ai_processing_jobs are public read

-- Functions for common operations

-- Get popular games based on search frequency
CREATE OR REPLACE FUNCTION get_popular_games(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    id BIGINT,
    title VARCHAR(255),
    description TEXT,
    rating DECIMAL(3,2),
    search_count BIGINT
) 
LANGUAGE sql
AS $$
    SELECT 
        g.id,
        g.title,
        g.description,
        g.rating,
        COALESCE(search_counts.count, 0) as search_count
    FROM games g
    LEFT JOIN (
        SELECT 
            unnest(string_to_array(lower(query), ' ')) as game_word,
            COUNT(*) as count
        FROM search_analytics 
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY game_word
    ) search_counts ON lower(g.title) LIKE '%' || search_counts.game_word || '%'
    ORDER BY search_count DESC, g.rating DESC
    LIMIT limit_count;
$$;

-- Semantic search function (requires vector extension)
CREATE OR REPLACE FUNCTION semantic_search_games(
    query_embedding vector(1536),
    similarity_threshold DECIMAL DEFAULT 0.7,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    game_id BIGINT,
    title VARCHAR(255),
    description TEXT,
    content_text TEXT,
    similarity_score DECIMAL
)
LANGUAGE sql
AS $$
    SELECT 
        ge.game_id,
        g.title,
        g.description,
        ge.content_text,
        (1 - (ge.embedding <=> query_embedding)) as similarity_score
    FROM game_embeddings ge
    JOIN games g ON ge.game_id = g.id
    WHERE (1 - (ge.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT limit_count;
$$;

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_reviews_updated_at BEFORE UPDATE ON game_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_collections_updated_at BEFORE UPDATE ON game_collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO games (title, description, rules_content, player_count_min, player_count_max, play_time_min, play_time_max, complexity, year_published, rating, genres, mechanics) VALUES
('カタン', '島の開拓と資源管理の戦略ゲーム', 'プレイヤーは開拓者となり、カタン島を開拓していきます。資源を集め、道路や建物を建設し、島の支配者を目指します。', 3, 4, 60, 90, 2.5, 1995, 4.5, '["戦略", "交渉", "資源管理"]', '["ダイスロール", "交渉", "建設"]'),
('ウィングスパン', '美しい鳥類をテーマにしたエンジンビルディングゲーム', 'プレイヤーは鳥類愛好家となり、最高の鳥類保護区を作ります。様々な鳥を呼び寄せ、エンジンを構築していきます。', 1, 5, 40, 70, 2.4, 2019, 4.7, '["戦略", "エンジンビルディング"]', '["カードドラフト", "エンジンビルディング"]'),
('アズール', 'タイル配置の美しいアブストラクトゲーム', 'プレイヤーは職人となり、美しい宮殿の壁を装飾します。タイルを配置してパターンを作り、得点を競います。', 2, 4, 30, 45, 2.3, 2017, 4.4, '["アブストラクト", "タイル配置"]', '["パターン構築", "セットコレクション"]'),
('スプレンダー', '宝石商として富を築く拡大再生産ゲーム', 'プレイヤーは宝石商となり、宝石を集めて発展カードを購入し、より多くの富を築きます。', 2, 4, 30, 30, 2.1, 2014, 4.3, '["戦略", "拡大再生産"]', '["拡大再生産", "セットコレクション"]'),
('ドミニオン', 'デッキ構築ゲームの元祖', 'プレイヤーは中世の君主となり、王国を拡大します。カードを購入してデッキを構築し、勝利点を競います。', 2, 4, 30, 30, 2.4, 2008, 4.6, '["戦略", "カード"]', '["デッキ構築", "カードドラフト"]');

-- Create a view for easy game searching
CREATE VIEW games_search_view AS
SELECT 
    g.*,
    COALESCE(avg_rating.avg_rating, g.rating) as computed_rating,
    COALESCE(review_count.review_count, 0) as review_count
FROM games g
LEFT JOIN (
    SELECT game_id, AVG(rating::DECIMAL) as avg_rating
    FROM game_reviews 
    GROUP BY game_id
) avg_rating ON g.id = avg_rating.game_id
LEFT JOIN (
    SELECT game_id, COUNT(*) as review_count
    FROM game_reviews 
    GROUP BY game_id
) review_count ON g.id = review_count.game_id;