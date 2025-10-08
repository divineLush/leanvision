import Link from 'next/link'
import styles from './aside.module.css'

export default function Aside() {
  return (
    <aside className={styles.aside}>
      <div className={styles.top}>
        <img className={styles.avatar} src="/img/avatar.png" />
        <p className={styles.name}>Ковалева Ксения</p>
        <p className={styles.org}>ООО LeanVision</p>
      </div>
      <div className={styles.bottom}>
        <h2 className={styles.heading}>Статистика</h2>
        <nav>
          <Link className={styles.link} href="/recs">Рекомендации</Link>
          <Link className={styles.link} href="/docs">Документы</Link>
        </nav>
      </div>
    </aside>
  );
}
