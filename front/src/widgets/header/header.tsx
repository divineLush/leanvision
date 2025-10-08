import styles from './header.module.css'

export default function AppHeader() {
  return (
    <header className={styles.header}>
      <div className="container">
        <img className={styles.logo} src="/img/logo.svg" />
      </div>
    </header>
  );
}
