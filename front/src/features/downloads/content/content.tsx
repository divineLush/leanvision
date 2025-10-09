import styles from './content.module.css'

export default function Content() {
  return (
    <section className={styles.content}>
      <div className={styles.upload}>
        <p className={styles.hint}>Здесь Вы можете повысить адаптивность системы под Ваше предприятие. Загрузите - документы, схемы бизнес-процессов, стандарты, чек-листы</p>
        <img src="/img/upload.svg" className={styles['upload-btn']} />
        <p className={styles.valiadtion}>Максимальный размер: 30 МБ</p>
        <p className={styles.valiadtion}>Расширения: pdf, docx</p>
      </div>
      <div className={styles.files}>
        <h2 className={styles.heading}>История загрузок</h2>
        <div className={styles.list}>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
          <div className={styles.item}>
            <img src="/img/doc.svg" className={styles['doc-icon']} />
            <p className={styles['doc-name']}>Чек-лист по операционному аудиту 2025</p>
            <p className={styles['doc-size']}>15,5 МБ</p>
            <img src="/img/delete.svg"className={styles['doc-download']} />
          </div>
        </div>
      </div>
    </section>
  );
}
