import styles from './content.module.css'

export default function Content() {
  return (
    <section className={styles.content}>
      <div className={styles['top-block']}>
        <div className={styles.item}>
          <p className={styles.value}>93%</p>
          <div className={styles.bar}>
            <div className={styles['bar-inner']} style={{ width: '93%' }}></div>
          </div>
          <p className={styles.metric}>Индекс соответствия СанПиН</p>
        </div>
        <div className={styles.item}>
          <p className={styles.value}>93%</p>
          <div className={styles.bar}>
            <div className={styles['bar-inner']} style={{ width: '93%' }}></div>
          </div>
          <p className={styles.metric}>Индекс соответствия СанПиН</p>
        </div>
        <div className={`${styles.item} ${styles.violations}`}>
          <p className={styles['violations-types']}>Типы<br />нарушений</p>
          <p className={styles['violations-value']}>20</p>
        </div>
        <div className={`${styles.item} ${styles.distribution}`}>
          <p className={styles['distribution-heading']}>Распределение нарушений по дням недели</p>
          <div className={styles.day}>
            <div className={styles.col}></div>
            пн
          </div>
          <div className={styles.day}>
            <div className={styles.col}></div>
            вт
          </div>
          <div className={styles.day}>
            <div className={styles.col}></div>
            ср
          </div>
          <div className={styles.day}>
            <div className={styles.col}></div>
            чт
          </div>
          <div className={styles.day}>
            <div className={styles.col}></div>
            пт
          </div>
          <div className={styles.day}>
            <div className={styles.col}></div>
            сб
          </div>
          <div className={styles.day}>
            <div className={styles.col}></div>
            вс
          </div>
        </div>
      </div>

      <h2 className={styles.heading}>Технология приготовления</h2>

      <div>
        <div>
          <h2 className={styles.heading}>Внешний вид</h2>
        </div>

        <div>
          <h2 className={styles.heading}>Санитария</h2>
        </div>
      </div>
    </section>
  );
}
