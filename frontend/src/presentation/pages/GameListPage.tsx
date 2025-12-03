import { useEffect, useState } from 'react'
import { Game } from '../../domain/entities/Game'
import { useGameRepository } from '../context/GameRepositoryContext'
import GameCard from '../components/GameCard'
import SearchBar from '../components/SearchBar'
import styles from './GameListPage.module.css'

export default function GameListPage() {
    const repository = useGameRepository()
    const [games, setGames] = useState<Game[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [searchQuery, setSearchQuery] = useState('')

    const [generating, setGenerating] = useState(false)

    const fetchGames = async (query: string = '') => {
        setLoading(true);
        setError(null);
        try {
            let data;
            if (query.trim()) {
                data = await repository.searchGames(query);
            } else {
                data = await repository.getGames();
            }
            setGames(data);
        } catch (err: any) {
            const errorMessage = err?.message || 'ゲームの読み込みに失敗しました';
            setError(errorMessage);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Initial load
    useEffect(() => {
        fetchGames()
    }, [repository])

    const handleSearch = () => {
        fetchGames(searchQuery)
    }

    const handleGenerate = async () => {
        if (!searchQuery.trim()) return;
        setGenerating(true);
        setError(null);
        try {
            await repository.generateGame(searchQuery);
            // After generation, refresh the list with the search query to show the new game
            await fetchGames(searchQuery);
            // Optional: clear search query? No, user might want to see what they searched.
        } catch (err: any) {
            const errorMessage = err?.message || 'AI生成に失敗しました';
            console.error('Generation failed:', err);
            alert(errorMessage);
        } finally {
            setGenerating(false);
        }
    };

    if (loading && !games.length) {
        return (
            <div className={styles.loading}>
                読み込み中...
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.error}>
                {error}
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>ボドゲのミカタ</h1>

            <div className={styles.controls}>
                <div className={styles.searchWrapper}>
                    <SearchBar
                        value={searchQuery}
                        onChange={setSearchQuery}
                        onSearch={handleSearch}
                    />
                </div>
                <button
                    onClick={handleGenerate}
                    disabled={generating || !searchQuery.trim()}
                    className={styles.generateButton}
                >
                    {generating ? 'AI生成中...' : 'AIで生成'}
                </button>
            </div>

            {games.length === 0 ? (
                <div className={styles.emptyState}>
                    ゲームが見つかりません。検索またはAI生成をお試しください。
                </div>
            ) : (
                <div className={styles.grid}>
                    {games.map((game) => (
                        <GameCard key={game.id} game={game} />
                    ))}
                </div>
            )}
        </div>
    );
}
