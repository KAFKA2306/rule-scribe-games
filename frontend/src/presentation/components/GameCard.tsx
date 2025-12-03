import { Link } from 'react-router-dom'
import { Game } from '../../domain/entities/Game'
import styles from './GameCard.module.css'

interface Props {
  game: Game
}

export default function GameCard({ game }: Props) {
  return (
    <Link to={`/game/${game.id}`} className={styles.card}>
      <h2 className={styles.title}>{game.title}</h2>
      <p className={styles.description}>{game.description}</p>
    </Link>
  )
}
