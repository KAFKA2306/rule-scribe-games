import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Game } from '../../domain/entities/Game'
import { useGameRepository } from '../context/GameRepositoryContext'
import styles from './GameDetailPage.module.css'

export default function GameDetailPage() {
    const repository = useGameRepository()
    const { id } = useParams<{ id: string }>()
    const [game, setGame] = useState<Game | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) {
            repository
                .getGameById(id)
                .then(setGame)
                .finally(() => setLoading(false))
        }
    }, [id])

    if (loading) return <div className={styles.loading}>読み込み中...</div>
    if (!game) return <div className={styles.error}>ゲームが見つかりません</div>

    return (
        <div className={styles.container}>
            <Link to="/" className={styles.backLink}>
                &larr; ゲーム一覧に戻る
            </Link>
            <h1 className={styles.title}>{game.title}</h1>
            <p className={styles.description}>{game.description}</p>

            <div className={styles.card}>
                <h2 className={styles.sectionTitle}>Rules</h2>

                <div className={styles.subSection}>
                    <h3 className={styles.subTitle}>Summary</h3>
                    <p className={styles.text}>{game.rules.summary}</p>
                </div>

                {game.rules.players && (
                    <div className={styles.subSection}>
                        <h3 className={styles.subTitle}>Players</h3>
                        <p className={styles.text}>{game.rules.players}</p>
                    </div>
                )}

                {game.rules.equipment && (
                    <div className={styles.subSection}>
                        <h3 className={styles.subTitle}>Equipment</h3>
                        <p className={styles.text}>{game.rules.equipment}</p>
                    </div>
                )}

                {game.rules.sections.map((section, idx) => (
                    <div key={idx} className={styles.subSection}>
                        <h3 className={styles.subTitle}>{section.title}</h3>
                        <ul className={styles.list}>
                            {section.steps.map((step, sIdx) => (
                                <li key={sIdx}>{step}</li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    )
}
