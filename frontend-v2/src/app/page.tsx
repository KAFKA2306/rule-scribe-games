'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Sparkles, BookOpen, Zap, Users, Clock, Gamepad2, Bot, ChevronRight, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

interface GameResult {
  id: number
  title: string
  description: string
  playerCount: string
  playTime: string
  genres: string[]
  rating: number
  status: string
}

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<GameResult[]>([])

  const handleSearch = async (query: string) => {
    if (!query.trim()) return
    
    setIsSearching(true)
    try {
      // Simulate API call - replace with actual API integration
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Mock results
      setSearchResults([
        {
          id: 1,
          title: 'カタン',
          description: '島の開拓と資源管理の戦略ゲーム',
          playerCount: '3-4人',
          playTime: '60-90分',
          genres: ['戦略', '交渉', '資源管理'],
          rating: 4.5,
          status: 'completed'
        },
        {
          id: 2,
          title: 'スプレンダー',
          description: '宝石商として富を築く拡大再生産ゲーム',
          playerCount: '2-4人',
          playTime: '30分',
          genres: ['戦略', '拡大再生産', 'カード'],
          rating: 4.3,
          status: 'completed'
        }
      ])
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const featuredGames = [
    { title: 'カタン', image: '/hero-boardgames.jpg', rating: 4.5 },
    { title: 'ウィングスパン', image: '/hero-boardgames.jpg', rating: 4.7 },
    { title: 'アズール', image: '/hero-boardgames.jpg', rating: 4.4 },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[url('/hero-boardgames.jpg')] bg-cover bg-center opacity-10" />
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20"
          animate={{
            background: [
              'linear-gradient(45deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2))',
              'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2))',
              'linear-gradient(225deg, rgba(236, 72, 153, 0.2), rgba(59, 130, 246, 0.2))',
            ]
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <motion.div 
            className="flex items-center space-x-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Gamepad2 className="h-8 w-8 text-purple-400" />
            <h1 className="text-2xl font-bold text-white">RuleScribe</h1>
            <Badge variant="secondary" className="bg-purple-500/20 text-purple-300">
              AI-Powered
            </Badge>
          </motion.div>
          
          <motion.div 
            className="flex items-center space-x-4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Button variant="ghost" className="text-white hover:bg-white/10">
              ゲーム一覧
            </Button>
            <Button variant="ghost" className="text-white hover:bg-white/10">
              使い方
            </Button>
            <Avatar>
              <AvatarImage src="/avatar.jpg" />
              <AvatarFallback>U</AvatarFallback>
            </Avatar>
          </motion.div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        {/* Hero Section */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <motion.div
            className="flex items-center justify-center mb-6"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <div className="relative">
              <Bot className="h-16 w-16 text-purple-400" />
              <motion.div
                className="absolute -top-2 -right-2 h-6 w-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center"
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="h-3 w-3 text-white" />
              </motion.div>
            </div>
          </motion.div>
          
          <h2 className="text-5xl md:text-7xl font-bold text-white mb-6 bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">
            ボードゲームルール
            <br />
            <span className="text-purple-400">AI検索プラットフォーム</span>
          </h2>
          
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            最新のAI技術を使って、あらゆるボードゲームのルールを瞬時に検索・要約。
            複雑なルールも分かりやすく、ゲームをもっと楽しく。
          </p>

          {/* Search Section */}
          <motion.div
            className="max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full blur-xl opacity-30" />
              <div className="relative bg-white/10 backdrop-blur-lg rounded-full p-2 border border-white/20">
                <div className="flex items-center space-x-4">
                  <div className="flex-1 flex items-center space-x-3 px-4">
                    <Search className="h-5 w-5 text-gray-400" />
                    <Input
                      placeholder="ゲーム名を入力してください（例：カタン、ウィングスパン）"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch(searchQuery)}
                      className="border-0 bg-transparent text-white placeholder-gray-400 focus:ring-0"
                    />
                  </div>
                  <Button
                    onClick={() => handleSearch(searchQuery)}
                    disabled={isSearching}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-full px-8"
                  >
                    {isSearching ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <Zap className="h-4 w-4" />
                      </motion.div>
                    ) : (
                      <>
                        <Search className="h-4 w-4 mr-2" />
                        検索
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Search Progress */}
        <AnimatePresence>
          {isSearching && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8"
            >
              <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <p className="text-white mb-2">AI がゲームルールを検索中...</p>
                      <Progress value={85} className="bg-white/20" />
                    </div>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                      <Bot className="h-8 w-8 text-purple-400" />
                    </motion.div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search Results */}
        <AnimatePresence>
          {searchResults.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-16"
            >
              <h3 className="text-2xl font-bold text-white mb-6">検索結果</h3>
              <div className="grid gap-6 md:grid-cols-2">
                {searchResults.map((game, index) => (
                  <motion.div
                    key={game.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="bg-white/10 backdrop-blur-lg border-white/20 hover:bg-white/15 transition-all duration-300 cursor-pointer group">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-white text-xl">{game.title}</CardTitle>
                          <div className="flex items-center space-x-1">
                            <Star className="h-4 w-4 text-yellow-400 fill-current" />
                            <span className="text-yellow-400">{game.rating}</span>
                          </div>
                        </div>
                        <CardDescription className="text-gray-300">
                          {game.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center space-x-4 text-sm text-gray-400">
                            <div className="flex items-center">
                              <Users className="h-4 w-4 mr-1" />
                              {game.playerCount}
                            </div>
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-1" />
                              {game.playTime}
                            </div>
                          </div>
                          <Badge className="bg-green-500/20 text-green-300">
                            ルール完成
                          </Badge>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-4">
                          {game.genres.map((genre: string, i: number) => (
                            <Badge key={i} variant="secondary" className="bg-purple-500/20 text-purple-300">
                              {genre}
                            </Badge>
                          ))}
                        </div>
                        <Button className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white group-hover:shadow-lg transition-all duration-300">
                          ルールを見る
                          <ChevronRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                        </Button>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Featured Games */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mb-16"
        >
          <h3 className="text-3xl font-bold text-white mb-8 text-center">
            人気のゲーム
          </h3>
          <div className="grid gap-6 md:grid-cols-3">
            {featuredGames.map((game, index) => (
              <motion.div
                key={index}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="group cursor-pointer"
              >
                <Card className="bg-white/10 backdrop-blur-lg border-white/20 hover:bg-white/15 transition-all duration-300 overflow-hidden">
                  <div className="aspect-video bg-gradient-to-r from-purple-500 to-pink-500 relative">
                    <div className="absolute inset-0 bg-black/20" />
                    <div className="absolute bottom-4 left-4 right-4">
                      <h4 className="text-white font-bold text-lg">{game.title}</h4>
                      <div className="flex items-center space-x-1">
                        <Star className="h-4 w-4 text-yellow-400 fill-current" />
                        <span className="text-yellow-400">{game.rating}</span>
                      </div>
                    </div>
                  </div>
                  <CardContent className="p-4">
                    <Button variant="ghost" size="sm" className="w-full text-white hover:bg-white/10">
                      ルールを見る
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.section>

        {/* Features Section */}
        <motion.section
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="text-center"
        >
          <h3 className="text-3xl font-bold text-white mb-12">
            なぜ RuleScribe を選ぶのか？
          </h3>
          <div className="grid gap-8 md:grid-cols-3">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-4">
                  <Bot className="h-8 w-8 text-white" />
                </div>
                <h4 className="text-xl font-bold text-white mb-2">AI 要約</h4>
                <p className="text-gray-300">
                  複雑なルールもAIが分かりやすく要約。
                  初心者でもすぐに理解できます。
                </p>
              </CardContent>
            </Card>
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mb-4">
                  <Zap className="h-8 w-8 text-white" />
                </div>
                <h4 className="text-xl font-bold text-white mb-2">高速検索</h4>
                <p className="text-gray-300">
                  瞬時にゲームルールを検索。
                  ゲーム中でもすぐに疑問を解決。
                </p>
              </CardContent>
            </Card>
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-pink-500 to-orange-500 rounded-full mb-4">
                  <BookOpen className="h-8 w-8 text-white" />
                </div>
                <h4 className="text-xl font-bold text-white mb-2">豊富なデータベース</h4>
                <p className="text-gray-300">
                  数千のボードゲームルールを網羅。
                  マイナーなゲームも見つかります。
                </p>
              </CardContent>
            </Card>
          </div>
        </motion.section>
      </div>

      {/* Footer */}
      <footer className="relative z-10 mt-20 py-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-gray-400">
            © 2024 RuleScribe - AIによるボードゲームルール検索プラットフォーム
          </p>
        </div>
      </footer>
    </div>
  )
}
