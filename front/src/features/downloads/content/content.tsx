import styles from './content.module.css'

export default function Content() {
  return (
    <section className={styles.content}>
      <div className={styles.list}>
        <p>Здесь Вы можете повысить адаптивность системы под Ваше предприятие. Загрузите - документы, схемы бизнес-процессов, стандарты, чек-листы</p>
      </div>
      <div>
        <h2>История загрузок</h2>
        <div></div>
      </div>
    </section>
  );
}
