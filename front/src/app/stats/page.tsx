import AppHeader from '@/widgets/header/header'
import Aside from '@/widgets/aside/aside'
import Content from '@/features/stats/content/content'

export default function Stats() {
  return (
    <>
      <AppHeader />
      <div className="flex container">
        <Aside />
        <Content />
      </div>
    </>
  );
}
