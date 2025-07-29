# 🗄️ Supabase Integration Setup Guide

This guide will help you set up Supabase as the production database for RuleScribe v2.

## 📋 Prerequisites

- Supabase account (https://supabase.com)
- PostgreSQL knowledge (basic)
- Access to Supabase dashboard

---

## 🚀 Quick Setup

### 1. **Create Supabase Project**

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Click "New Project"
3. Choose your organization
4. Enter project details:
   - **Name**: `rulescribe-v2`
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
5. Click "Create new project"

### 2. **Get Connection Details**

Once your project is ready:

1. Go to **Settings** → **Database**
2. Copy the connection strings:
   - **URL**: `https://your-project-ref.supabase.co`
   - **Anon Key**: Public API key
   - **Service Role Key**: Private API key (keep secret!)
   - **Database URL**: PostgreSQL connection string

### 3. **Set Up Database Schema**

1. Go to **SQL Editor** in Supabase dashboard
2. Copy the contents of `supabase_schema.sql`
3. Paste and run the SQL to create all tables and functions

### 4. **Configure Environment Variables**

Copy `.env.example` to `.env` and fill in your Supabase details:

```bash
cp .env.example .env
```

Update these values in `.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
DATABASE_URL=postgresql+asyncpg://postgres.your-project-ref:your-password@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

---

## 🏗️ Database Schema Overview

### **Core Tables**

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `games` | Game information | Full-text search, JSON metadata |
| `users` | User profiles | Auth integration, preferences |
| `user_favorites` | User's favorite games | Many-to-many relationship |
| `search_analytics` | Search tracking | Performance metrics, user behavior |
| `game_embeddings` | Vector embeddings | Semantic search capabilities |
| `game_reviews` | User reviews | Rating system, moderation |
| `game_collections` | User collections | Public/private lists |
| `ai_processing_jobs` | AI task tracking | Multi-provider support |

### **Key Features**

- ✅ **Full-text search** with PostgreSQL `pg_trgm`
- ✅ **Vector search** with `pgvector` extension
- ✅ **Row Level Security (RLS)** for data protection
- ✅ **Automatic timestamps** with triggers
- ✅ **JSON support** for flexible metadata
- ✅ **Performance indexes** for fast queries
- ✅ **Analytics functions** for insights

---

## 🔧 Advanced Configuration

### **Enable Extensions**

Ensure these extensions are enabled in Supabase:

```sql
-- In SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### **Set Up Authentication**

1. Go to **Authentication** → **Settings**
2. Configure sign-up settings:
   - Enable email confirmations (recommended)
   - Set up email templates
   - Configure OAuth providers (optional)

### **Configure Storage (Optional)**

For game images and file uploads:

1. Go to **Storage** → **Buckets**
2. Create bucket: `game-images`
3. Set up RLS policies for public read access

### **API Rate Limiting**

Supabase provides built-in rate limiting, but you can enhance it:

1. Go to **Settings** → **API**
2. Review rate limit settings
3. Set up custom limits if needed

---

## 🔒 Security Best Practices

### **Row Level Security (RLS)**

The schema includes RLS policies for:

- ✅ Users can only access their own data
- ✅ Public read access for games and reviews
- ✅ Private access for favorites and collections
- ✅ Analytics data protection

### **API Key Management**

- 🔑 **Anon Key**: Use in frontend (public)
- 🔑 **Service Key**: Use in backend only (private)
- 🚫 Never expose service key in client-side code
- 🔄 Rotate keys regularly

### **Environment Variables**

- ✅ Use environment variables for all secrets
- ✅ Never commit `.env` files to version control
- ✅ Use different projects for dev/staging/production

---

## 📊 Monitoring & Analytics

### **Built-in Monitoring**

Supabase provides:

- **Database metrics**: Query performance, connections
- **API analytics**: Request counts, response times
- **Storage usage**: File uploads, bandwidth
- **Auth metrics**: User sign-ups, sessions

### **Custom Analytics**

The `search_analytics` table tracks:

- Search queries and results
- User behavior patterns
- Performance metrics
- Popular games and trends

### **Logging**

Enable query logging in Supabase:

1. Go to **Settings** → **Database**
2. Enable "Log all queries"
3. Set log retention period

---

## 🚀 Production Deployment

### **Database Optimization**

1. **Connection Pooling**: Supabase provides built-in pooling
2. **Query Optimization**: Use EXPLAIN ANALYZE for slow queries
3. **Index Monitoring**: Check index usage and performance
4. **Regular Maintenance**: Update statistics, vacuum tables

### **Backup Strategy**

Supabase automatically:

- ✅ Creates daily backups (7-day retention)
- ✅ Provides point-in-time recovery
- ✅ Offers backup downloads

For production:

- Set up additional backup automation
- Test restore procedures regularly
- Monitor backup completion

### **Scaling Considerations**

- **Compute**: Upgrade database size as needed
- **Storage**: Monitor storage usage and growth
- **Connections**: Adjust connection limits for high traffic
- **Read Replicas**: Consider for read-heavy workloads

---

## 🧪 Testing with Supabase

### **Local Development**

Use Supabase CLI for local development:

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize local project
supabase init

# Start local development
supabase start

# Apply migrations
supabase db push
```

### **Test Data**

The schema includes sample games:

- カタン (Catan)
- ウィングスパン (Wingspan)  
- アズール (Azul)
- スプレンダー (Splendor)
- ドミニオン (Dominion)

### **API Testing**

Test endpoints with:

```bash
# Health check
curl https://your-project-ref.supabase.co/rest/v1/games

# Search games
curl "https://your-project-ref.supabase.co/rest/v1/games?title=like.*カタン*"
```

---

## 🆘 Troubleshooting

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Connection timeout | Check database URL and credentials |
| RLS errors | Verify user authentication and policies |
| Slow queries | Add indexes, optimize query structure |
| Storage errors | Check bucket permissions and file size limits |

### **Debug Queries**

```sql
-- Check table sizes
SELECT schemaname,tablename,attname,n_distinct,correlation FROM pg_stats;

-- Monitor active connections
SELECT * FROM pg_stat_activity;

-- Check index usage
SELECT * FROM pg_stat_user_indexes;
```

### **Support Resources**

- 📖 [Supabase Documentation](https://supabase.com/docs)
- 💬 [Supabase Discord](https://discord.supabase.com)
- 🐛 [GitHub Issues](https://github.com/supabase/supabase/issues)
- 📧 Email support for paid plans

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] Database schema applied successfully
- [ ] Sample data inserted and visible
- [ ] Environment variables configured
- [ ] RLS policies tested
- [ ] Authentication working
- [ ] API endpoints responding
- [ ] Monitoring dashboards accessible
- [ ] Backup strategy implemented
- [ ] Security review completed

---

**🎯 Your Supabase integration is now ready for production!**

The backend will automatically use Supabase when `SUPABASE_URL` is configured, with graceful fallback to SQLite for local development.